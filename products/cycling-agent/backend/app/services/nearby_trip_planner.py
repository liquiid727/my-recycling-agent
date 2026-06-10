"""CN: Phase 2 周边游确定性规划器，把路线、目的地、停留、风险和返程组织成 trip。
EN: Phase 2 deterministic nearby-trip planner composing route, destination, stay, risk, and return plan.
"""

from __future__ import annotations

from app.services.risk_scoring_service import score_route_risk


def rank_nearby_trip_candidates(
    *,
    trips: list[dict],
    destinations: list[dict],
    routes: list[dict],
    constraints: dict,
    weather_snapshot: dict,
    user_profile: dict,
    risk_rules: list[dict] | None = None,
) -> list[dict]:
    destination_by_no = {item["destination_no"]: item for item in destinations}
    route_by_code = {item["route_code"]: item for item in routes}
    ranked: list[dict] = []
    for trip in trips:
        destination = destination_by_no.get(trip["destination_no"])
        route = route_by_code.get(trip["route_template_id"])
        if not destination or not route:
            continue
        risk = score_route_risk(route, weather_snapshot, user_profile, risk_rules)
        trip_score = _score_trip(trip, destination, route, constraints) - risk["overall_risk_score"]
        if trip_score < 0.45:
            continue
        ranked.append(
            {
                "trip": trip,
                "destination": destination,
                "route": route,
                "risk": risk,
                "score": round(trip_score, 3),
            }
        )
    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def build_nearby_trip_card(candidate: dict) -> dict:
    trip = candidate["trip"]
    destination = candidate["destination"]
    route = candidate["route"]
    risk = candidate["risk"]
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


def _score_trip(trip: dict, destination: dict, route: dict, constraints: dict) -> float:
    duration_bucket = constraints.get("duration_bucket")
    target_hours = constraints.get("available_hours") or _default_hours_for_duration(duration_bucket)
    duration_gap = abs(float(trip["total_duration_hours"]) - float(target_hours))
    score = 1 - duration_gap / 24

    origin_region = constraints.get("origin_region")
    if origin_region and origin_region in trip.get("origin_region_tags", []):
        score += 0.3
    if origin_region and origin_region in route.get("district_tags", []):
        score += 0.15

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

    if route.get("difficulty_level") == "easy":
        score += 0.1
    return round(score, 3)


def _build_suitable_for(trip: dict, destination: dict) -> str:
    return f"适合想要{destination['destination_type']}停留、{trip['total_duration_hours']}小时内完成的周边骑行用户"


def _build_why_recommended(candidate: dict) -> str:
    trip = candidate["trip"]
    route = candidate["route"]
    destination = candidate["destination"]
    reason = f"{trip['name']}匹配出发区域和时长；{route['name']}提供骑行节奏，{destination['name']}提供明确停留与返程锚点。"
    if trip.get("lodging_plan"):
        reason += " 该方案已经包含住宿和多天节奏，适合周末出行。"
    return reason


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
