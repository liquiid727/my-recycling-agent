"""CN: Phase 2 周边游确定性规划器，把路线、目的地、停留、风险和返程组织成 trip。
EN: Phase 2 deterministic nearby-trip planner composing route, destination, stay, risk, and return plan.
"""

from __future__ import annotations

from copy import deepcopy

from app.services.risk_scoring_service import score_route_risk


def rank_nearby_trip_route_candidates(*, routes: list[dict], constraints: dict) -> list[dict]:
    ranked: list[dict] = []
    for raw_route in routes:
        route = deepcopy(raw_route)
        if _is_hard_blocked_route(route, constraints):
            continue

        route_context = route.get("route_context") or {}
        total_duration_hours = float(route_context.get("total_duration_hours") or route.get("estimated_duration_hours") or 0)
        total_distance_km = float(route_context.get("total_distance_km") or route.get("distance_km") or 0)
        approach_distance_km = route_context.get("approach_distance_km")
        target_route_hours = _target_route_hours(constraints)

        warnings = list(route.get("constraint_warnings") or [])
        if total_duration_hours > target_route_hours + 1.0:
            warnings.append("total-duration-over-target")
        if approach_distance_km is not None and float(approach_distance_km) > _max_weekend_approach_distance_km(constraints):
            warnings.append("approach-distance-over-limit")
        if constraints.get("target_distance_km"):
            distance_gap = abs(total_distance_km - float(constraints["target_distance_km"]))
            if distance_gap > max(18.0, float(constraints["target_distance_km"]) * 0.5):
                warnings.append("target-distance-out-of-range")
        if constraints.get("slope_tolerance") == "avoid" and float(route.get("elevation_gain_m", 0)) >= 320:
            warnings.append("slope-tolerance-stretched")

        score = 1.0
        score -= abs(total_duration_hours - target_route_hours) / max(target_route_hours, 1.0) * 0.45
        if constraints.get("target_distance_km"):
            target_distance = float(constraints["target_distance_km"])
            distance_gap = abs(total_distance_km - target_distance)
            score += max(-0.28, 0.16 - distance_gap / max(target_distance, 1.0) * 0.32)
        if constraints.get("origin_region") and constraints["origin_region"] in route.get("district_tags", []):
            score += 0.22
        score += min(_shared_trip_route_tags(route, constraints), 3) * 0.08
        score += min(float(route.get("scenic_score", 0)) / 50, 0.18)
        if route.get("difficulty_level") == "easy":
            score += 0.1
        elif constraints.get("slope_tolerance") == "avoid":
            score -= 0.06
        if approach_distance_km is not None:
            score -= min(float(approach_distance_km) / 70, 0.35)

        route["constraint_warnings"] = list(dict.fromkeys(warnings))
        route["weekend_route_score"] = round(score, 3)
        if route["weekend_route_score"] >= 0.35:
            ranked.append(route)

    return sorted(ranked, key=lambda item: item.get("weekend_route_score", 0.0), reverse=True)[:5]


def rank_nearby_trip_candidates(
    *,
    trips: list[dict],
    destinations: list[dict],
    route_candidates: list[dict],
    constraints: dict,
    weather_snapshot: dict,
    user_profile: dict,
    risk_rules: list[dict] | None = None,
) -> list[dict]:
    destination_by_no = {item["destination_no"]: item for item in destinations}
    best_by_trip: dict[str, dict] = {}
    for trip in trips:
        destination = destination_by_no.get(trip["destination_no"])
        if not destination:
            continue
        for route, compatibility_score in _match_trip_routes(trip, destination, route_candidates, constraints):
            risk = score_route_risk(route, weather_snapshot, user_profile, risk_rules)
            binding_audit = _build_route_binding_audit(trip, route, route_candidates)
            trip_score = (
                _score_trip_skeleton(trip, destination, constraints)
                + compatibility_score
                + float(route.get("weekend_route_score", 0.0)) * 0.35
                - risk["overall_risk_score"]
            )
            if trip_score < 0.55:
                continue
            candidate = {
                "trip": trip,
                "destination": destination,
                "route": route,
                "risk": risk,
                "score": round(trip_score, 3),
                "route_compatibility_score": compatibility_score,
                "binding_audit": binding_audit,
            }
            current = best_by_trip.get(trip["trip_no"])
            if current is None or candidate["score"] > current["score"]:
                best_by_trip[trip["trip_no"]] = candidate
    return sorted(best_by_trip.values(), key=lambda item: item["score"], reverse=True)


def build_nearby_trip_card(candidate: dict) -> dict:
    trip = candidate["trip"]
    destination = candidate["destination"]
    route = candidate["route"]
    risk = candidate["risk"]
    binding_audit = candidate.get("binding_audit") or {}
    route_context = route.get("route_context") or {}
    total_distance_km = route_context.get("total_distance_km") or route["distance_km"]
    ride_duration_hours = route_context.get("total_duration_hours") or trip["ride_duration_hours"]
    stay_duration_hours = float(destination.get("stay_duration_minutes", 0)) / 60
    return {
        "trip_no": trip["trip_no"],
        "trip_name": trip["name"],
        "destination_name": destination["name"],
        "suitable_for": _build_suitable_for(trip, destination),
        "total_distance_km": total_distance_km,
        "ride_duration_hours": ride_duration_hours,
        "total_duration_hours": round(float(ride_duration_hours) + stay_duration_hours, 2),
        "recommended_departure_time": (route.get("best_time_slots") or ["07:30-09:00"])[0].split("-")[0],
        "stay_suggestion": destination["stay_suggestion"],
        "why_recommended": _build_why_recommended(candidate),
        "risk_level": risk["risk_level"],
        "return_options": trip.get("return_mode_options", []),
        "duration_bucket": trip.get("duration_bucket") or _first_duration(destination),
        "itinerary_days": trip.get("itinerary_days", []),
        "lodging_plan": trip.get("lodging_plan") or destination.get("lodging_summary"),
        "equipment_advice": trip.get("equipment_advice") or destination.get("gear_advice", []),
        "weather_window_notes": trip.get("weather_window_notes") or destination.get("weather_window_notes"),
        "source_meta": {
            "trip_template": {
                "trip_no": trip["trip_no"],
                "route_template_id": trip.get("route_template_id"),
                "duration_bucket": trip.get("duration_bucket"),
            },
            "destination_template": {
                "destination_no": destination.get("destination_no"),
                "destination_type": destination.get("destination_type"),
                "region_tags": destination.get("region_tags", []),
            },
            "route_binding": {
                "selected_route_code": route.get("route_code"),
                "selected_route_name": route.get("name"),
                "selected_route_source": route.get("route_source") or route_context.get("fact_source") or "template",
                "is_template_route_match": route.get("route_code") == trip.get("route_template_id"),
                "canonical_route_code": binding_audit.get("canonical_route_code"),
                "canonical_route_feasible": binding_audit.get("canonical_route_feasible"),
                "canonical_route_rank": binding_audit.get("canonical_route_rank"),
                "selected_route_rank": binding_audit.get("selected_route_rank"),
                "feasible_route_count": binding_audit.get("feasible_route_count"),
                "audit_summary": binding_audit.get("summary"),
            },
            "resolved_metrics": {
                "distance_km": total_distance_km,
                "ride_duration_hours": ride_duration_hours,
                "metric_source": ((route_context.get("resolved") or {}).get("metric_source") or route_context.get("fact_source") or "template"),
            },
        },
    }


def build_trip_rhythm(candidate: dict, *, departure_time: str | None = None) -> dict:
    trip = candidate["trip"]
    destination = candidate["destination"]
    route = candidate["route"]
    if trip.get("itinerary_days"):
        return {
            "segments": [
                {
                    "stage": f"第{item['day']}天：{item['title']}",
                    "time_window": f"{item.get('ride_hours', 0)} 小时骑行",
                    "description": item.get("notes", "按当天体感和天气执行。"),
                }
                for item in trip["itinerary_days"]
            ]
        }
    route_context = route.get("route_context") or {}
    ride_duration_hours = route_context.get("total_duration_hours") or trip["ride_duration_hours"]
    start_time = departure_time or (route.get("best_time_slots") or ["07:30-09:00"])[0].split("-")[0]
    return {
        "segments": [
            {
                "stage": "出发前准备",
                "time_window": f"{start_time} 前 30 分钟",
                "description": "确认天气、补水、返程方式和是否需要缩短路线。",
            },
            {
                "stage": "去程骑行",
                "time_window": f"{start_time} 起",
                "description": f"从你的出发点进入 {route['name']}，预计骑行 {ride_duration_hours} 小时。",
            },
            {
                "stage": "中途补给或休息",
                "time_window": "去程中段",
                "description": route.get("supply_points", [{}])[0].get("name", "中途补给点"),
            },
            {
                "stage": "到达目的地后的停留",
                "time_window": f"{destination['stay_duration_minutes']} 分钟",
                "description": destination["stay_suggestion"],
            },
            {
                "stage": "返程方式",
                "time_window": "停留结束后",
                "description": " / ".join(trip.get("return_mode_options", [])),
            },
        ]
    }


def build_trip_risks(candidate: dict, weather_snapshot: dict) -> dict:
    trip = candidate["trip"]
    destination = candidate["destination"]
    route = candidate["route"]
    risk = candidate["risk"]
    return {
        "risk_items": [
            f"天气风险：{weather_snapshot.get('weather_summary')}，最高温 {weather_snapshot.get('temperature_max')} C，降雨概率 {weather_snapshot.get('precipitation_probability')}",
            f"热度 / 拥挤风险：目的地周末 {destination.get('crowd_level', {}).get('weekend', 'medium')}，节假日 {destination.get('crowd_level', {}).get('holiday', 'high')}",
            f"爬坡或体力风险：路线爬升 {route.get('elevation_gain_m')} m，风险等级 {risk['risk_level']}",
            f"返程风险：可选 {', '.join(trip.get('return_mode_options', []))}",
            f"天气窗口：{trip.get('weather_window_notes') or destination.get('weather_window_notes', '按出发前天气更新判断。')}",
        ],
        "fallback_plan": trip["fallback_plan"],
    }


def _score_trip_skeleton(trip: dict, destination: dict, constraints: dict) -> float:
    duration_bucket = constraints.get("duration_bucket")
    target_hours = constraints.get("available_hours") or _default_hours_for_duration(duration_bucket)
    duration_gap = abs(float(trip["total_duration_hours"]) - float(target_hours))
    score = 1 - duration_gap / 24

    origin_region = constraints.get("origin_region")
    if origin_region and origin_region in trip.get("origin_region_tags", []):
        score += 0.3

    if duration_bucket and duration_bucket in destination.get("suitable_duration", []):
        score += 0.35
    if duration_bucket and duration_bucket == trip.get("duration_bucket"):
        score += 0.45

    requested_preferences = set(constraints.get("destination_preferences") or [])
    trip_tags = set(trip.get("trip_style_tags", [])) | set(destination.get("region_tags", []))
    score += 0.25 * len(requested_preferences.intersection(trip_tags))

    if constraints.get("overnight_preference") == "required" and trip.get("lodging_plan"):
        score += 0.3

    if constraints.get("return_preference") == "public_transport" and any("公共交通" in item or "地铁" in item for item in trip.get("return_mode_options", [])):
        score += 0.2

    return round(score, 3)


def _build_suitable_for(trip: dict, destination: dict) -> str:
    return f"适合想要{destination['destination_type']}停留、{trip['total_duration_hours']}小时内完成的周边骑行用户"


def _build_why_recommended(candidate: dict) -> str:
    trip = candidate["trip"]
    route = candidate["route"]
    destination = candidate["destination"]
    reason = f"{trip['name']}匹配出发区域和时长；{route['name']}提供骑行节奏，{destination['name']}提供明确停留与返程锚点。"
    if route["route_code"] != trip.get("route_template_id"):
        reason += " 这次按你的出发点和偏好，换成了更可行的路线段再去承接这个周末骨架。"
    if trip.get("lodging_plan"):
        reason += " 该方案已经包含住宿和多天节奏，适合周末出行。"
    return reason


def _build_route_binding_audit(trip: dict, selected_route: dict, route_candidates: list[dict]) -> dict:
    canonical_route_code = trip.get("route_template_id")
    selected_route_code = selected_route.get("route_code")
    selected_route_rank = None
    canonical_route_rank = None
    canonical_route = None
    for index, route in enumerate(route_candidates, start=1):
        if route.get("route_code") == selected_route_code and selected_route_rank is None:
            selected_route_rank = index
        if canonical_route_code and route.get("route_code") == canonical_route_code and canonical_route_rank is None:
            canonical_route_rank = index
            canonical_route = route

    canonical_route_feasible = canonical_route_rank is not None
    feasible_route_count = len(route_candidates)
    if not canonical_route_code:
        summary = f"未声明模板路线，当前从 {feasible_route_count} 条可行路线里选中 {selected_route_code}。"
    elif selected_route_code == canonical_route_code:
        summary = f"沿用模板路线 {canonical_route_code}；它在 {feasible_route_count} 条可行路线里排第 {selected_route_rank}。"
    elif canonical_route_feasible:
        summary = (
            f"未沿用模板路线 {canonical_route_code}，改选 {selected_route_code}；"
            f"当前路线排第 {selected_route_rank}，模板路线排第 {canonical_route_rank}。"
        )
    else:
        summary = (
            f"未沿用模板路线 {canonical_route_code}，改选 {selected_route_code}；"
            f"模板路线未进入 {feasible_route_count} 条可行候选。"
        )

    if canonical_route and canonical_route.get("constraint_warnings"):
        summary += f" 模板路线告警：{'，'.join(canonical_route['constraint_warnings'][:2])}。"

    return {
        "canonical_route_code": canonical_route_code,
        "canonical_route_feasible": canonical_route_feasible,
        "canonical_route_rank": canonical_route_rank,
        "selected_route_rank": selected_route_rank,
        "feasible_route_count": feasible_route_count,
        "summary": summary,
    }


def _default_hours_for_duration(duration_bucket: str | None) -> float:
    if duration_bucket == "evening":
        return 2
    if duration_bucket == "half_day":
        return 4
    if duration_bucket == "one_day":
        return 7
    if duration_bucket == "two_day":
        return 30
    if duration_bucket == "three_day":
        return 54
    return 4


def _first_duration(destination: dict) -> str | None:
    durations = destination.get("suitable_duration") or []
    return durations[0] if durations else None


def _match_trip_routes(trip: dict, destination: dict, route_candidates: list[dict], constraints: dict) -> list[tuple[dict, float]]:
    matched: list[tuple[dict, float]] = []
    for route in route_candidates:
        compatibility_score = _score_trip_route_compatibility(trip, destination, route, constraints)
        if compatibility_score < 0.25:
            continue
        matched.append((route, round(compatibility_score, 3)))
    return sorted(matched, key=lambda item: (item[1], item[0].get("weekend_route_score", 0.0)), reverse=True)


def _score_trip_route_compatibility(trip: dict, destination: dict, route: dict, constraints: dict) -> float:
    score = 0.0
    if route["route_code"] == trip.get("route_template_id"):
        score += 0.45

    shared_tags = _shared_route_destination_tags(route, trip, destination)
    score += min(shared_tags, 3) * 0.12

    requested_preferences = set(constraints.get("destination_preferences") or [])
    route_tags = set(route.get("district_tags", [])) | set(route.get("ride_style_tags", []))
    score += min(len(requested_preferences.intersection(route_tags)), 2) * 0.08

    if constraints.get("return_preference") == "public_transport" and any(
        token in option for token in ("公共交通", "地铁", "高铁") for option in trip.get("return_mode_options", [])
    ):
        score += 0.08
    return score


def _shared_route_destination_tags(route: dict, trip: dict, destination: dict) -> int:
    route_tags = set(route.get("district_tags", [])) | set(route.get("ride_style_tags", []))
    trip_tags = set(trip.get("trip_style_tags", []))
    destination_tags = set(destination.get("region_tags", []))
    return len(route_tags.intersection(trip_tags | destination_tags))


def _shared_trip_route_tags(route: dict, constraints: dict) -> int:
    route_tags = set(route.get("district_tags", [])) | set(route.get("ride_style_tags", []))
    requested = set(constraints.get("destination_preferences") or [])
    ride_style = constraints.get("ride_style")
    if ride_style == "scenic_relaxed":
        requested |= {"relaxed", "scenic"}
    elif ride_style:
        requested.add(ride_style)
    return len(route_tags.intersection(requested))


def _is_hard_blocked_route(route: dict, constraints: dict) -> bool:
    route_context = route.get("route_context") or {}
    total_duration_hours = float(route_context.get("total_duration_hours") or route.get("estimated_duration_hours") or 0)
    approach_distance_km = route_context.get("approach_distance_km")
    elevation_gain_m = float(route.get("elevation_gain_m", 0))
    difficulty_level = route.get("difficulty_level")
    fitness_level = constraints.get("fitness_level")
    slope_tolerance = constraints.get("slope_tolerance")

    if total_duration_hours > _max_route_hours(constraints):
        return True
    if approach_distance_km is not None and float(approach_distance_km) > _max_weekend_approach_distance_km(constraints):
        return True
    if slope_tolerance == "avoid" and (difficulty_level == "high" or elevation_gain_m >= 500):
        return True
    if fitness_level == "low" and (difficulty_level in {"medium", "high"} and elevation_gain_m >= 420):
        return True
    return False


def _target_route_hours(constraints: dict) -> float:
    if constraints.get("available_hours"):
        return min(float(constraints["available_hours"]), 6.5)
    duration_bucket = constraints.get("duration_bucket")
    if duration_bucket == "half_day":
        return 4.0
    if duration_bucket == "one_day":
        return 6.5
    if duration_bucket in {"two_day", "three_day"}:
        return 4.5
    return 4.0


def _max_route_hours(constraints: dict) -> float:
    if constraints.get("available_hours"):
        return float(constraints["available_hours"]) + 1.25
    duration_bucket = constraints.get("duration_bucket")
    if duration_bucket == "half_day":
        return 6.5
    if duration_bucket == "one_day":
        return 9.5
    if duration_bucket in {"two_day", "three_day"}:
        return 7.5
    return 6.5


def _max_weekend_approach_distance_km(constraints: dict) -> float:
    duration_bucket = constraints.get("duration_bucket")
    if duration_bucket == "half_day":
        return 24.0
    if duration_bucket == "one_day":
        return 34.0
    if duration_bucket == "two_day":
        return 48.0
    if duration_bucket == "three_day":
        return 60.0
    return 30.0
