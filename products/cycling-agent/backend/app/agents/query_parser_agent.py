"""CN: 自然语言骑行需求解析器，先尝试结构化理解用户意图，失败时提供规则兜底。
EN: Natural-language ride-query parser that structures user intent and keeps a deterministic fallback.
"""

from __future__ import annotations

import re


REGION_KEYWORDS = ("滨江", "西湖", "龙井", "湘湖", "余杭", "萧山")
WEEKEND_DESTINATION_KEYWORDS = ("千岛湖", "湖州", "莫干山", "安吉")
RIDE_TODAY_DECISION_KEYWORDS = ("适合", "能不能", "可不可以", "值不值得", "要不要", "去不去")
RIDE_TODAY_TIME_KEYWORDS = ("今天", "今晚", "下午", "下班", "现在")


def parse_query_fallback(query: str) -> dict:
    available_hours = _parse_available_hours(query)
    distance_match = re.search(r"(\d+(?:\.\d+)?)公里", query)
    origin_region = next((name for name in REGION_KEYWORDS if name in query), None)
    start_point = _parse_start_point(query, origin_region)
    planning_scene = _parse_planning_scene(query)

    ride_style = _parse_ride_style(query)
    slope_tolerance = _parse_slope_tolerance(query)
    destination_preferences = _parse_destination_preferences(query)
    duration_bucket = _parse_duration_bucket(query)
    return_preference = "public_transport" if "公共交通" in query or "地铁" in query else None
    overnight_preference = _parse_overnight_preference(query)

    missing_fields: list[str] = []
    if start_point is None:
        missing_fields.append("start_point")
    if planning_scene == "weekend_trip":
        if duration_bucket is None:
            missing_fields.append("duration_bucket")
        if _requires_overnight_preference(duration_bucket) and overnight_preference is None:
            missing_fields.append("overnight_preference")
    elif available_hours is None and distance_match is None:
        missing_fields.append("available_hours_or_target_distance_km")

    confidence = 0.92
    if missing_fields:
        confidence = 0.68 if len(missing_fields) == 1 else 0.52

    parsed = {
        "planning_scene": planning_scene,
        "origin_region": origin_region,
        "start_point": start_point,
        "available_hours": available_hours,
        "target_distance_km": float(distance_match.group(1)) if distance_match else None,
        "ride_style": ride_style,
        "slope_tolerance": slope_tolerance,
        "duration_bucket": duration_bucket,
        "destination_preferences": destination_preferences,
        "return_preference": return_preference,
        "overnight_preference": overnight_preference,
        "lodging_preference": _parse_lodging_preference(query),
        "cross_city_allowed": True if planning_scene == "weekend_trip" else None,
        "missing_fields": missing_fields,
        "confidence": confidence,
    }
    parsed["intent"] = resolve_intent(query=query, planning_scene=planning_scene, parsed_constraints=parsed)
    return parsed


def enrich_parsed_constraints(parsed_constraints: dict, user_profile: dict | None = None) -> dict:
    enriched = dict(parsed_constraints)
    profile = user_profile or {}

    if "target_distance_km" not in enriched:
        enriched["target_distance_km"] = None
    if "fitness_level" not in enriched:
        enriched["fitness_level"] = profile.get("fitness_level")
    elif enriched["fitness_level"] in (None, ""):
        enriched["fitness_level"] = profile.get("fitness_level")

    if "slope_tolerance" not in enriched:
        enriched["slope_tolerance"] = profile.get("slope_tolerance")
    elif enriched["slope_tolerance"] in (None, ""):
        enriched["slope_tolerance"] = profile.get("slope_tolerance")

    return enriched


def build_structured_constraints(payload: dict | None, user_profile: dict | None = None) -> dict:
    structured = payload or {}
    profile = user_profile or {}
    defaults_applied: list[str] = []
    fitness_level = structured.get("fitness_level") or profile.get("fitness_level") or "medium"
    slope_tolerance = structured.get("slope_tolerance") or profile.get("slope_tolerance") or "neutral"
    ride_style = structured.get("ride_style") or "general"
    duration_bucket = structured.get("duration_bucket")
    destination_preferences = structured.get("destination_preferences") or []
    return_preference = structured.get("return_preference")
    overnight_preference = structured.get("overnight_preference")
    origin_location = structured.get("origin_location")

    if not structured.get("fitness_level") and not profile.get("fitness_level"):
        defaults_applied.append("fitness_level")
    if not structured.get("slope_tolerance") and not profile.get("slope_tolerance"):
        defaults_applied.append("slope_tolerance")
    if not structured.get("ride_style"):
        defaults_applied.append("ride_style")

    parsed = {
        "planning_scene": structured.get("planning_scene"),
        "origin_region": structured.get("origin_region"),
        "start_point": structured.get("start_point"),
        "origin_location": origin_location,
        "departure_time": structured.get("departure_time"),
        "available_hours": structured.get("available_hours"),
        "target_distance_km": structured.get("target_distance_km"),
        "ride_style": ride_style,
        "fitness_level": fitness_level,
        "slope_tolerance": slope_tolerance,
        "priority": structured.get("priority"),
        "duration_bucket": duration_bucket,
        "destination_preferences": destination_preferences,
        "return_preference": return_preference,
        "overnight_preference": overnight_preference,
        "lodging_preference": structured.get("lodging_preference"),
        "cross_city_allowed": structured.get("cross_city_allowed"),
        "missing_fields": [],
        "confidence": 1.0,
        "defaults_applied": defaults_applied,
    }
    parsed["missing_fields"] = _missing_core_fields(parsed)
    return parsed


def missing_core_fields(parsed_constraints: dict, *, target_date: object | None) -> list[str]:
    missing = []
    if target_date is None:
        missing.append("target_date")
    missing.extend(_missing_core_fields(parsed_constraints))
    return missing


def resolve_planning_context(
    *,
    intent: str | None = None,
    planning_mode: str | None = None,
    planning_scene: str | None = None,
    query: str | None = None,
    parsed_constraints: dict | None = None,
) -> dict:
    parsed = parsed_constraints or {}
    weekend_requested = any(
        value == "weekend_trip"
        for value in (
            planning_scene,
            parsed.get("planning_scene"),
        )
    ) or any(value == "nearby_trip" for value in (planning_mode, parsed.get("planning_mode"))) or intent == "weekend_recommendation"

    resolved_intent = "weekend_recommendation" if weekend_requested else resolve_intent(
        intent=intent,
        planning_mode=planning_mode,
        planning_scene=planning_scene,
        query=query,
        parsed_constraints=parsed,
    )
    if resolved_intent == "weekend_recommendation":
        return {
            "intent": "weekend_recommendation",
            "planning_mode": "nearby_trip",
            "planning_scene": "weekend_trip",
        }
    return {
        "intent": resolved_intent,
        "planning_mode": "route",
        "planning_scene": "city_ride",
    }


def resolve_intent(
    *,
    intent: str | None = None,
    planning_mode: str | None = None,
    planning_scene: str | None = None,
    query: str | None = None,
    parsed_constraints: dict | None = None,
) -> str:
    if intent in {"ride_today", "ride_plan", "weekend_recommendation"}:
        return intent
    if planning_scene == "weekend_trip" or planning_mode == "nearby_trip":
        return "weekend_recommendation"

    parsed = parsed_constraints or {}
    if parsed.get("planning_scene") == "weekend_trip":
        return "weekend_recommendation"
    if _has_ready_city_ride_constraints(parsed):
        return "ride_plan"

    text = query or ""
    if any(keyword in text for keyword in RIDE_TODAY_DECISION_KEYWORDS):
        return "ride_today"
    if any(keyword in text for keyword in RIDE_TODAY_TIME_KEYWORDS) and not _has_ready_city_ride_constraints(parsed):
        return "ride_today"
    return "ride_plan"


def _parse_destination_preferences(query: str) -> list[str]:
    keywords = ("江边", "亲水", "咖啡", "古镇", "公园", "茶村", "湖区", "观景", "早餐", *WEEKEND_DESTINATION_KEYWORDS)
    return [keyword for keyword in keywords if keyword in query]


def _parse_available_hours(query: str) -> float | None:
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|~|到|至)\s*(\d+(?:\.\d+)?)\s*(?:小时|h|H)", query)
    if range_match:
        return float(range_match.group(2))
    hours_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:小时|h|H)", query)
    if hours_match:
        return float(hours_match.group(1))
    chinese_hours = {
        "一": 1.0,
        "一个": 1.0,
        "两": 2.0,
        "两个": 2.0,
        "二": 2.0,
        "三": 3.0,
        "四": 4.0,
    }
    chinese_match = re.search(r"(一两个|一个|两个|一|两|二|三|四)\s*小时", query)
    if chinese_match:
        value = chinese_match.group(1)
        return 2.0 if value == "一两个" else chinese_hours.get(value)
    return None


def _parse_ride_style(query: str) -> str:
    if "刷圈" in query:
        return "training_loop"
    if "轻松" in query or "不想太累" in query or "休闲" in query:
        return "scenic_relaxed"
    if "风景" in query:
        return "scenic_relaxed"
    if "爬坡" in query:
        return "climb"
    return "general"


def _parse_slope_tolerance(query: str) -> str | None:
    if any(keyword in query for keyword in ("不要爬坡", "不想爬坡", "不要坡", "少爬坡", "轻松点", "轻松一点", "不想太累")):
        return "avoid"
    return None


def _parse_planning_scene(query: str) -> str:
    if any(keyword in query for keyword in ("周末", "节假日", "两天", "三天", "2天", "3天", "过夜", *WEEKEND_DESTINATION_KEYWORDS)):
        return "weekend_trip"
    return "city_ride"


def _parse_duration_bucket(query: str) -> str | None:
    if "今晚" in query or "今天晚上" in query or "夜骑" in query or "下班" in query:
        return "evening"
    if "三天" in query or "3天" in query:
        return "three_day"
    if "两天" in query or "2天" in query:
        return "two_day"
    if "一天" in query or "一日" in query:
        return "one_day"
    if "半天" in query or "半日" in query or "下午" in query:
        return "half_day"
    return None


def _parse_overnight_preference(query: str) -> str | None:
    if "不过夜" in query or "不住宿" in query:
        return "avoid"
    if "过夜" in query or "住宿" in query or "酒店" in query or "民宿" in query or "两天" in query or "三天" in query or "2天" in query or "3天" in query:
        return "required"
    return None


def _parse_lodging_preference(query: str) -> str | None:
    if "民宿" in query:
        return "民宿"
    if "酒店" in query:
        return "酒店"
    if "住宿" in query or "过夜" in query:
        return "住宿方便"
    return None


def _parse_start_point(query: str, origin_region: str | None) -> str | None:
    patterns = (
        r"从(.{2,20}?)(?:出发|开始|起步|骑)",
        r"我在(.{2,20}?)(?:，|,|。|；|;|\s|就|附近|$)",
        r"当前位置在(.{2,20}?)(?:，|,|。|；|;|\s|附近|$)",
        r"(?:^|；|;)\s*([\u4e00-\u9fa5A-Za-z0-9·]{2,20}(?:路地铁站|地铁站|路|街|桥|站|广场|公园|中心|码头|口|村|湖|附近))(?:\s|，|,|。|；|;|啊|吧|$)",
        r"(?:^|；|;)([\u4e00-\u9fa5A-Za-z0-9·]{2,12})(?:，|,)?(?:我这里|这里|这边|附近)",
    )
    candidate = None
    for pattern in patterns:
        match = re.search(pattern, query)
        if match is not None:
            candidate = match.group(1).strip(" ，,。；;")
            break
    if candidate is None:
        return None
    candidate = re.sub(r"(这里|这边|附近|啊|吧)$", "", candidate).strip(" ，,。；;")
    if not candidate or candidate == origin_region or candidate in REGION_KEYWORDS:
        return None
    if any(token in candidate for token in ("想", "骑", "周末", "今晚", "今天", "明天", "出去", "推荐", "线路", "路线")):
        return None
    return candidate


def _missing_core_fields(parsed_constraints: dict) -> list[str]:
    missing = []
    if not parsed_constraints.get("start_point"):
        missing.append("start_point")
    if parsed_constraints.get("planning_scene") == "weekend_trip":
        if not parsed_constraints.get("duration_bucket"):
            missing.append("duration_bucket")
        if _requires_overnight_preference(parsed_constraints.get("duration_bucket")) and not parsed_constraints.get("overnight_preference"):
            missing.append("overnight_preference")
    elif not (parsed_constraints.get("available_hours") or parsed_constraints.get("target_distance_km")):
        missing.append("available_hours_or_target_distance_km")
    return missing


def _has_ready_city_ride_constraints(parsed_constraints: dict) -> bool:
    if not parsed_constraints.get("start_point"):
        return False
    return bool(parsed_constraints.get("available_hours") or parsed_constraints.get("target_distance_km"))


def _requires_overnight_preference(duration_bucket: str | None) -> bool:
    return duration_bucket in {"two_day", "three_day"}


def build_clarification_prompt(parsed_constraints: dict) -> str | None:
    missing_fields = parsed_constraints.get("missing_fields", [])
    if not missing_fields:
        return None

    label_map = {
        "target_date": "目标日期",
        "origin_region": "出发区域",
        "start_point": "准确出发地点",
        "available_hours": "可骑时长",
        "available_hours_or_target_distance_km": "可骑时长或目标距离",
        "duration_bucket": "出行时长",
        "overnight_preference": "是否接受过夜",
    }
    missing_labels = [label_map.get(item, item) for item in missing_fields]
    return f"当前还缺少关键信息：{'、'.join(missing_labels)}。补充后推荐结果会更稳。"
