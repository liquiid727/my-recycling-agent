"""CN: C 端聊天规划回合 agent，负责槽位合并、亲切回复和规划请求生成。
EN: Consumer chat planning turn agent for slot merging, friendly replies, and planner request assembly.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import date
from typing import Any

from app.agents.query_parser_agent import parse_query_fallback


ASSISTANT_NAME = "AAA骑车帮帮"
LLM_CHAT_TIMEOUT_SECONDS = 8.0


def build_chat_turn(
    *,
    messages: list[dict],
    planning_scene: str,
    target_date: date,
    slot_state: dict | None = None,
    user_profile: dict | None = None,
    llm_provider: Any = None,
) -> dict:
    current_slots = dict(slot_state or {})
    current_slots["planning_scene"] = planning_scene

    llm_payload = _try_llm_chat_turn(
        llm_provider=llm_provider,
        messages=messages,
        slot_state=current_slots,
        planning_scene=planning_scene,
        target_date=target_date,
        user_profile=user_profile,
    )
    if llm_payload is not None:
        return _normalize_chat_turn(llm_payload, current_slots=current_slots, target_date=target_date)

    return _build_fallback_chat_turn(
        messages=messages,
        planning_scene=planning_scene,
        target_date=target_date,
        slot_state=current_slots,
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


def _normalize_chat_turn(payload: dict, *, current_slots: dict, target_date: date) -> dict:
    merged_slots = _merge_slots(current_slots, payload.get("slot_state") if isinstance(payload.get("slot_state"), dict) else {})
    missing_slots = _missing_slots(merged_slots)
    ready_to_plan = not missing_slots
    assistant_message = str(payload.get("assistant_message") or _build_assistant_message(merged_slots, missing_slots, ready_to_plan))
    if ready_to_plan and payload.get("ready_to_plan") is False:
        assistant_message = _build_assistant_message(merged_slots, missing_slots, ready_to_plan)
    return {
        "assistant_name": ASSISTANT_NAME,
        "assistant_message": _strip_engineering_language(assistant_message),
        "slot_state": merged_slots,
        "missing_slots": missing_slots,
        "ready_to_plan": ready_to_plan,
        "planner_request": _build_planner_request(merged_slots, target_date) if ready_to_plan else None,
        "ui_hints": _build_ui_hints(missing_slots, ready_to_plan),
    }


def _build_fallback_chat_turn(*, messages: list[dict], planning_scene: str, target_date: date, slot_state: dict) -> dict:
    user_text = "；".join(message.get("content", "") for message in messages if message.get("role") == "user")
    parsed = parse_query_fallback(user_text)
    parsed["planning_scene"] = planning_scene
    merged_slots = _merge_slots(slot_state, parsed)
    missing_slots = _missing_slots(merged_slots)
    ready_to_plan = not missing_slots
    return {
        "assistant_name": ASSISTANT_NAME,
        "assistant_message": _build_assistant_message(merged_slots, missing_slots, ready_to_plan),
        "slot_state": merged_slots,
        "missing_slots": missing_slots,
        "ready_to_plan": ready_to_plan,
        "planner_request": _build_planner_request(merged_slots, target_date) if ready_to_plan else None,
        "ui_hints": _build_ui_hints(missing_slots, ready_to_plan),
    }


def _merge_slots(current: dict, incoming: dict) -> dict:
    merged = dict(current)
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


def _build_assistant_message(slots: dict, missing_slots: list[str], ready_to_plan: bool) -> str:
    if ready_to_plan:
        if slots.get("planning_scene") == "weekend_trip":
            destination = "、".join(slots.get("destination_preferences") or []) or "周边"
            return f"收到，我按{destination}方向帮你看一个周末方案，先判断天气窗口、住宿和返程，再给你稳妥路线。"
        hours = _format_hours(slots.get("available_hours"))
        start = slots.get("start_point")
        style = "轻松一点，" if slots.get("ride_style") == "scenic_relaxed" or slots.get("slope_tolerance") == "avoid" else ""
        return f"收到，{start}出发，骑 {hours}，{style}我先帮你看今晚适不适合骑，再给你几条稳妥路线。"

    if "start_point" in missing_slots and "available_hours_or_target_distance_km" in missing_slots:
        return "可以呀～今晚轻松骑挺合适。我先确认两件事：你现在从哪里出发？大概想骑多久？"
    if "start_point" in missing_slots:
        return "时长我收到了。还差一个出发点，我才能帮你避开绕路。你现在大概在哪？"
    if "available_hours_or_target_distance_km" in missing_slots:
        return f"{slots.get('start_point')}收到啦。你今晚大概想骑多久？比如 1 小时、2 小时都可以。"
    if "duration_bucket" in missing_slots:
        return "周末可以安排。你这次想骑几天？一天、两天还是三天？"
    if "overnight_preference" in missing_slots:
        return "路线方向可以看。你能接受住一晚吗？如果不想过夜，我会优先找当天往返。"
    return "可以，我还需要再确认一个小信息，补上后就能给你方案。"


def _build_planner_request(slots: dict, target_date: date) -> dict:
    planning_scene = slots.get("planning_scene") or "city_ride"
    planning_mode = "nearby_trip" if planning_scene == "weekend_trip" else "route"
    structured_constraints = {
        "planning_scene": planning_scene,
        "start_point": slots.get("start_point"),
        "origin_region": slots.get("origin_region"),
        "available_hours": slots.get("available_hours"),
        "target_distance_km": slots.get("target_distance_km"),
        "duration_bucket": slots.get("duration_bucket"),
        "ride_style": slots.get("ride_style") or "scenic_relaxed",
        "slope_tolerance": slots.get("slope_tolerance") or "avoid",
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


def _build_ui_hints(missing_slots: list[str], ready_to_plan: bool) -> dict:
    if ready_to_plan:
        return {
            "quick_replies": ["换轻松点", "缩短到 1 小时", "避开爬坡"],
            "show_advanced_controls": False,
            "planning_status_label": "我在看天气和路线难度",
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


def _format_hours(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:g} 小时"
    return "一段时间"


def _strip_engineering_language(message: str) -> str:
    blocked = ("missing_fields", "当前还缺少关键信息", "我先看一下这句话里够不够生成方案")
    if any(item in message for item in blocked):
        return "我理解了，我再用更自然的方式确认一下：你现在从哪里出发，准备骑多久？"
    return message
