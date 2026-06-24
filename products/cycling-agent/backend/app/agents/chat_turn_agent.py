"""CN: C 端聊天规划回合 agent，负责槽位合并、亲切回复和规划请求生成。
EN: Consumer chat planning turn agent for slot merging, friendly replies, and planner request assembly.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import date
from typing import Any

from app.agents.query_parser_agent import parse_query_fallback
from app.agents.query_parser_agent import infer_explicit_planning_scene


ASSISTANT_NAME = "AAA骑车帮帮"
LLM_CHAT_TIMEOUT_SECONDS = 8.0


def build_chat_turn(
    *,
    messages: list[dict],
    planning_scene: str,
    target_date: date,
    slot_state: dict | None = None,
    user_profile: dict | None = None,
    rider_state: dict | None = None,
    llm_provider: Any = None,
) -> dict:
    effective_planning_scene = infer_explicit_planning_scene(_latest_user_text(messages)) or planning_scene
    current_slots = dict(slot_state or {})
    current_slots["planning_scene"] = effective_planning_scene

    # 优先尝试 LLM 生成更自然的对话回合；失败后仍可用规则链路保持可规划状态。
    llm_payload = _try_llm_chat_turn(
        llm_provider=llm_provider,
        messages=messages,
        slot_state=current_slots,
        planning_scene=effective_planning_scene,
        target_date=target_date,
        user_profile=user_profile,
    )
    if llm_payload is not None:
        return _normalize_chat_turn(
            llm_payload,
            current_slots=current_slots,
            target_date=target_date,
            user_profile=user_profile,
            rider_state=rider_state,
        )

    return _build_fallback_chat_turn(
        messages=messages,
        planning_scene=effective_planning_scene,
        target_date=target_date,
        slot_state=current_slots,
        user_profile=user_profile,
        rider_state=rider_state,
    )


def _try_llm_chat_turn(
    *,
    llm_provider: Any,
    messages: list[dict],
    slot_state: dict,
    planning_scene: str,
    target_date: date,
    user_profile: dict | None,
) -> dict | None:
    if llm_provider is None or not hasattr(llm_provider, "generate_chat_turn"):
        return None
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(
            llm_provider.generate_chat_turn,
            messages=messages,
            slot_state=slot_state,
            planning_scene=planning_scene,
            target_date=target_date,
            user_profile=user_profile,
        )
        timeout_seconds = min(float(getattr(llm_provider, "timeout_seconds", LLM_CHAT_TIMEOUT_SECONDS)), LLM_CHAT_TIMEOUT_SECONDS)
        payload = future.result(timeout=timeout_seconds)
    except TimeoutError:
        executor.shutdown(wait=False, cancel_futures=True)
        return None
    except Exception:
        executor.shutdown(wait=False, cancel_futures=True)
        return None
    executor.shutdown(wait=False)
    return payload if isinstance(payload, dict) else None


def _normalize_chat_turn(
    payload: dict,
    *,
    current_slots: dict,
    target_date: date,
    user_profile: dict | None,
    rider_state: dict | None,
) -> dict:
    merged_slots = _merge_slots(current_slots, payload.get("slot_state") if isinstance(payload.get("slot_state"), dict) else {})
    missing_slots = _missing_slots(merged_slots)
    ready_to_plan = not missing_slots
    assistant_message = str(
        payload.get("assistant_message")
        or _build_assistant_message(
            merged_slots,
            missing_slots,
            ready_to_plan,
            user_profile=user_profile,
            rider_state=rider_state,
        )
    )
    if ready_to_plan and payload.get("ready_to_plan") is False:
        assistant_message = _build_assistant_message(
            merged_slots,
            missing_slots,
            ready_to_plan,
            user_profile=user_profile,
            rider_state=rider_state,
        )
    return {
        "assistant_name": ASSISTANT_NAME,
        "assistant_message": _strip_engineering_language(assistant_message),
        "slot_state": merged_slots,
        "missing_slots": missing_slots,
        "ready_to_plan": ready_to_plan,
        "planner_request": _build_planner_request(merged_slots, target_date) if ready_to_plan else None,
        "ui_hints": _build_ui_hints(merged_slots, missing_slots, ready_to_plan),
        "rider_state": rider_state,
    }


def _build_fallback_chat_turn(
    *,
    messages: list[dict],
    planning_scene: str,
    target_date: date,
    slot_state: dict,
    user_profile: dict | None,
    rider_state: dict | None,
) -> dict:
    user_text = "；".join(message.get("content", "") for message in messages if message.get("role") == "user")
    parsed = parse_query_fallback(user_text)
    if infer_explicit_planning_scene(_latest_user_text(messages)) is None:
        parsed["planning_scene"] = planning_scene
    merged_slots = _merge_slots(slot_state, parsed)
    missing_slots = _missing_slots(merged_slots)
    ready_to_plan = not missing_slots
    return {
        "assistant_name": ASSISTANT_NAME,
        "assistant_message": _build_assistant_message(
            merged_slots,
            missing_slots,
            ready_to_plan,
            user_profile=user_profile,
            rider_state=rider_state,
        ),
        "slot_state": merged_slots,
        "missing_slots": missing_slots,
        "ready_to_plan": ready_to_plan,
        "planner_request": _build_planner_request(merged_slots, target_date) if ready_to_plan else None,
        "ui_hints": _build_ui_hints(merged_slots, missing_slots, ready_to_plan),
        "rider_state": rider_state,
    }


def _merge_slots(current: dict, incoming: dict) -> dict:
    merged = dict(current)
    # 只允许写入规划链路真正消费的槽位，避免对话模型回传的噪声字段污染状态。
    allowed = {
        "planning_scene",
        "start_point",
        "available_hours",
        "target_distance_km",
        "departure_time",
        "duration_bucket",
        "ride_style",
        "slope_tolerance",
        "destination_preferences",
        "overnight_preference",
        "lodging_preference",
        "cross_city_allowed",
        "origin_region",
    }
    for key in allowed:
        value = incoming.get(key)
        if value not in (None, "", []):
            normalized_value = _normalize_slot_value(key, value)
            if normalized_value not in (None, "", []):
                merged[key] = normalized_value
    if merged.get("slope_tolerance") == "avoid" and merged.get("ride_style") == "climb":
        merged["ride_style"] = "scenic_relaxed"
    return merged


def _normalize_slot_value(key: str, value: Any) -> Any:
    if key == "slope_tolerance":
        if value in {"avoid", "neutral", "prefer"}:
            return value
        text = str(value).lower()
        if any(token in text for token in ("avoid", "no", "low", "不要", "不爬", "少爬", "避开")):
            return "avoid"
        if any(token in text for token in ("prefer", "climb", "hill", "爬坡")):
            return "prefer"
        return "neutral"
    if key == "duration_bucket":
        return value if value in {"evening", "half_day", "one_day", "two_day", "three_day"} else None
    if key == "overnight_preference":
        return value if value in {"avoid", "optional", "required"} else None
    if key == "return_preference":
        return value if value in {"ride_back", "public_transport", "shorten_route"} else None
    if key == "cross_city_allowed":
        return value if isinstance(value, bool) else None
    return value


def _missing_slots(slots: dict) -> list[str]:
    if slots.get("planning_scene") == "weekend_trip":
        missing = []
        if not slots.get("start_point"):
            missing.append("start_point")
        if not slots.get("duration_bucket"):
            missing.append("duration_bucket")
        if not slots.get("overnight_preference"):
            missing.append("overnight_preference")
        return missing

    missing = []
    if not slots.get("start_point"):
        missing.append("start_point")
    if not (slots.get("available_hours") or slots.get("target_distance_km")):
        missing.append("available_hours_or_target_distance_km")
    return missing


def _build_assistant_message(
    slots: dict,
    missing_slots: list[str],
    ready_to_plan: bool,
    *,
    user_profile: dict | None,
    rider_state: dict | None,
) -> str:
    if ready_to_plan:
        if slots.get("planning_scene") == "weekend_trip":
            return _build_weekend_ready_message(slots, rider_state=rider_state)
        return _build_city_ready_message(slots, user_profile=user_profile, rider_state=rider_state)

    if slots.get("planning_scene") == "weekend_trip":
        return _build_weekend_follow_up_message(slots, missing_slots)

    return _build_city_follow_up_message(slots, missing_slots)


def _build_city_ready_message(slots: dict, *, user_profile: dict | None, rider_state: dict | None) -> str:
    start = slots.get("start_point") or "你附近"
    ride_summary = _describe_city_plan(slots)
    pace = _describe_ride_pace(slots, user_profile=user_profile, rider_state=rider_state)
    departure = _describe_departure_time(slots)
    return (
        f"收到，先按{start}出发、{ride_summary}、{pace}来帮你看。"
        f"{departure}我先判断风和温度，再给你 2 到 3 条更顺手的路线。"
    )


def _build_weekend_ready_message(slots: dict, *, rider_state: dict | None) -> str:
    destination = "、".join(slots.get("destination_preferences") or []) or "杭州周边"
    duration = _describe_duration_bucket(slots.get("duration_bucket"))
    overnight = _describe_overnight_preference(slots.get("overnight_preference"))
    state_prefix = "先按轻一点的节奏，" if (rider_state or {}).get("fatigue_level") == "tired" else ""
    return (
        f"收到，{state_prefix}我先按{duration}、{overnight}来筛 {destination} 方向。"
        "接下来先看天气窗口、住宿和返程，再给你一个主方案加备选。"
    )


def _build_city_follow_up_message(slots: dict, missing_slots: list[str]) -> str:
    if "start_point" in missing_slots and "available_hours_or_target_distance_km" in missing_slots:
        return "可以，我们先把这次出发收清楚：你现在从哪里出发？准备骑多久，或者大概多少公里？"
    if "start_point" in missing_slots:
        ride_summary = _describe_city_plan(slots)
        return f"{ride_summary}我先记下了。再告诉我你从哪里出发，我就能把路线收得更顺。"
    if "available_hours_or_target_distance_km" in missing_slots:
        return f"{slots.get('start_point')}收到。你这次想骑多久，或者大概多少公里？"
    return "可以，我再确认一个小信息，补上后就能开始给你方案。"


def _build_weekend_follow_up_message(slots: dict, missing_slots: list[str]) -> str:
    if {"start_point", "duration_bucket", "overnight_preference"}.issubset(set(missing_slots)):
        return "周末可以安排。我先收三件事：你从哪里出发？想骑一天、两天还是三天？能不能接受住一晚？"
    if "start_point" in missing_slots and "duration_bucket" in missing_slots:
        return "可以，我先帮你收窄范围：你从哪里出发？这次准备骑一天、两天还是三天？"
    if "start_point" in missing_slots and "overnight_preference" in missing_slots:
        return "方向我可以开始筛。再告诉我你从哪里出发，以及能不能接受住一晚？"
    if "duration_bucket" in missing_slots and "overnight_preference" in missing_slots:
        return "出发点我收到了。你这次想骑一天、两天还是三天？能不能接受住一晚？"
    if "start_point" in missing_slots:
        return "周末方向可以看。再告诉我你从哪里出发，我好把接驳和返程一起算顺。"
    if "duration_bucket" in missing_slots:
        return "可以。你这次准备骑一天、两天还是三天？"
    if "overnight_preference" in missing_slots:
        return "路线方向可以开始筛了。你能接受住一晚吗？如果不想过夜，我会优先找当天往返。"
    return "可以，我再确认一个小信息，补上后就给你周末方案。"


def _build_planner_request(slots: dict, target_date: date) -> dict:
    planning_scene = slots.get("planning_scene") or "city_ride"
    planning_mode = "nearby_trip" if planning_scene == "weekend_trip" else "route"
    # chat 场景最终也统一转成结构化请求，后面直接复用主规划 API 的 schema 和编排逻辑。
    structured_constraints = {
        "planning_scene": planning_scene,
        "start_point": slots.get("start_point"),
        "origin_region": slots.get("origin_region"),
        "available_hours": slots.get("available_hours"),
        "target_distance_km": slots.get("target_distance_km"),
        "duration_bucket": slots.get("duration_bucket"),
        "ride_style": slots.get("ride_style"),
        "slope_tolerance": slots.get("slope_tolerance"),
        "destination_preferences": slots.get("destination_preferences") or [],
        "overnight_preference": slots.get("overnight_preference"),
        "lodging_preference": slots.get("lodging_preference"),
        "cross_city_allowed": slots.get("cross_city_allowed"),
    }
    return {
        "query": f"AAA骑车帮帮结构化规划：{slots.get('start_point', '杭州')}出发",
        "target_date": target_date.isoformat(),
        "planning_mode": planning_mode,
        "planning_scene": planning_scene,
        "input_mode": "structured",
        "structured_constraints": structured_constraints,
    }


def _build_ui_hints(slots: dict, missing_slots: list[str], ready_to_plan: bool) -> dict:
    planning_scene = slots.get("planning_scene") or "city_ride"
    if ready_to_plan:
        if planning_scene == "weekend_trip":
            return {
                "quick_replies": ["改成两天", "不要过夜", "千岛湖方向"],
                "show_advanced_controls": False,
                "planning_status_label": "我在看天气窗口、住宿和返程",
            }
        return {
            "quick_replies": ["换轻松点", "缩短到 1 小时", "江边一点"],
            "show_advanced_controls": False,
            "planning_status_label": "我在看天气、路线难度和补给",
        }

    if planning_scene == "weekend_trip":
        if "start_point" in missing_slots:
            quick_replies = ["滨江出发", "城西出发", "杭州东附近"]
        elif "duration_bucket" in missing_slots:
            quick_replies = ["一天往返", "两天一晚", "三天慢骑"]
        elif "overnight_preference" in missing_slots:
            quick_replies = ["不过夜", "可以住一晚", "住宿方便点"]
        else:
            quick_replies = ["千岛湖", "轻松点", "公共交通返程"]
        return {
            "quick_replies": quick_replies,
            "show_advanced_controls": False,
            "planning_status_label": "我在理解你的周末出行想法",
        }

    if "start_point" in missing_slots:
        quick_replies = ["沈塘桥", "闻涛路滨江段", "杭州东附近"]
    elif "available_hours_or_target_distance_km" in missing_slots:
        quick_replies = ["骑 1 小时", "骑 2 小时", "骑 40 公里"]
    else:
        quick_replies = ["现在出发", "不要爬坡", "轻松点"]
    return {
        "quick_replies": quick_replies,
        "show_advanced_controls": False,
        "planning_status_label": "我在理解你的骑行想法",
    }


def _latest_user_text(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def _format_hours(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:g} 小时"
    return "一段时间"


def _describe_city_plan(slots: dict) -> str:
    if isinstance(slots.get("available_hours"), (int, float)):
        return f"骑 {_format_hours(slots.get('available_hours'))}"
    if isinstance(slots.get("target_distance_km"), (int, float)):
        return f"骑 {float(slots['target_distance_km']):g} 公里左右"
    return "先按一段轻松骑来收"


def _describe_ride_pace(slots: dict, *, user_profile: dict | None, rider_state: dict | None) -> str:
    slope_tolerance = slots.get("slope_tolerance") or (user_profile or {}).get("slope_tolerance")
    ride_style = slots.get("ride_style")
    ride_style_preferences = (user_profile or {}).get("ride_style_preferences") or []
    if (rider_state or {}).get("fatigue_level") == "tired":
        return "轻松恢复一下"
    if slope_tolerance == "avoid":
        return "轻松一点"
    if ride_style == "training_loop":
        return "稍微练一练"
    if ride_style == "climb" or slope_tolerance == "prefer":
        return "带点爬坡"
    if ride_style == "scenic_relaxed" or slope_tolerance == "avoid" or "relaxed" in ride_style_preferences:
        return "轻松一点"
    return "顺一点"


def _describe_departure_time(slots: dict) -> str:
    departure_time = slots.get("departure_time")
    if isinstance(departure_time, str) and departure_time.strip():
        return f" {departure_time.strip()}前后"
    if slots.get("duration_bucket") == "evening":
        return " 今晚"
    return ""


def _describe_duration_bucket(value: Any) -> str:
    mapping = {
        "evening": "今晚",
        "half_day": "半天",
        "one_day": "一天",
        "two_day": "两天",
        "three_day": "三天",
    }
    return mapping.get(value, "这次周末")


def _describe_overnight_preference(value: Any) -> str:
    mapping = {
        "avoid": "尽量当天往返",
        "optional": "住宿可选",
        "required": "可以住一晚",
    }
    return mapping.get(value, "住宿灵活一点")


def _strip_engineering_language(message: str) -> str:
    # 对话层不直接暴露“missing_fields”之类的工程语汇，统一改写成用户可感知的追问。
    blocked = ("missing_fields", "当前还缺少关键信息", "我先看一下这句话里够不够生成方案")
    if any(item in message for item in blocked):
        return "我理解了，我再用更自然的方式确认一下：你现在从哪里出发，准备骑多久？"
    return message
