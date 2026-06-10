"""CN: 近场路线发现服务，基于出发点和周边 POI 生成动态骑行候选。
EN: Nearby route discovery service that builds dynamic candidates from origin and nearby POI anchors.
"""

from __future__ import annotations

from typing import Any


def discover_nearby_route_candidates(
    *,
    constraints: dict[str, Any],
    city_code: str,
    route_provider,
    poi_provider,
) -> list[dict[str, Any]]:
    start_point_name = constraints.get("start_point")
    if not start_point_name or route_provider is None or poi_provider is None:
        return []
    if not hasattr(route_provider, "resolve_point") or not hasattr(route_provider, "get_cycling_path"):
        return []
    if not hasattr(poi_provider, "search_route_anchors"):
        return []

    origin = route_provider.resolve_point(start_point_name, city_code=city_code)
    anchors = poi_provider.search_route_anchors(
        longitude=float(origin["longitude"]),
        latitude=float(origin["latitude"]),
        city_code=city_code,
        ride_style=constraints.get("ride_style"),
    )
    preferred_distance_km, preferred_duration_hours = _preferred_route_size(constraints)
    candidates = []
    viable_anchors = []
    for index, anchor in enumerate(anchors[:12], start=1):
        if _is_unsupported_anchor(anchor):
            continue
        if anchor.get("longitude") is None or anchor.get("latitude") is None:
            continue
        outbound = route_provider.get_cycling_path(origin, anchor)
        distance_km = round(float(outbound["distance_km"]) * 2, 1)
        duration_hours = round(float(outbound["estimated_duration_hours"]) * 2, 2)
        if not _is_viable_anchor_route(anchor, distance_km, duration_hours):
            continue
        viable_anchors.append(anchor)
        polyline = outbound.get("polyline") or []
        return_polyline = list(reversed(polyline))
        route_code = f"DYN-{city_code.upper()}-{index:03d}"
        surface_type = _surface_type_for_anchor(anchor)
        candidate = (
            {
                "route_code": route_code,
                "name": f"{start_point_name}-{anchor['name']}休闲往返线",
                "city_code": city_code,
                "start_point_name": start_point_name,
                "start_point_lng": origin["longitude"],
                "start_point_lat": origin["latitude"],
                "end_point_name": anchor["name"],
                "end_point_lng": anchor["longitude"],
                "end_point_lat": anchor["latitude"],
                "loop_type": "out_and_back",
                "district_tags": [anchor.get("district") or constraints.get("origin_region") or city_code],
                "ride_style_tags": _ride_style_tags(constraints),
                "season_tags": [],
                "distance_km": distance_km,
                "elevation_gain_m": 0,
                "estimated_duration_hours": duration_hours,
                "difficulty_level": "easy",
                "best_time_slots": ["当前时段"],
                "avoid_time_slots": [],
                "surface_type": surface_type,
                "traffic_level": "unknown",
                "supply_score": 6,
                "return_difficulty_score": 2,
                "scenic_score": _scenic_score_for_anchor(anchor),
                "training_score": 2,
                "beginner_friendly": True,
                "climb_segments": [],
                "supply_points": [{"name": anchor["name"], "km_mark": round(distance_km / 2, 1), "type": anchor.get("type") or "POI"}],
                "bailout_options": [{"name": "原路折返", "km_mark": round(distance_km / 2, 1), "reason": "近场往返路线，体感不佳可直接返程"}],
                "holiday_penalty_level": "medium",
                "weather_sensitivity": {"heat": "medium", "rain": "medium", "crosswind": "medium"},
                "route_notes": f"基于{start_point_name}周边 POI 和高德骑行路径动态生成，适合先试骑再调整。",
                "route_source": "dynamic_nearby",
                "constraint_warnings": _dynamic_constraint_warnings(
                    distance_km,
                    duration_hours,
                    preferred_distance_km,
                    preferred_duration_hours,
                ),
                "route_context": {
                    "provider_name": "dynamic-nearby-route",
                    "fact_source": "amap-dynamic",
                    "distance_km": distance_km,
                    "estimated_duration_hours": duration_hours,
                    "template_distance_km": distance_km,
                    "template_duration_hours": duration_hours,
                    "total_distance_km": distance_km,
                    "total_duration_hours": duration_hours,
                    "approach_distance_km": 0.0,
                    "approach_duration_hours": 0.0,
                    "user_start_point": origin,
                    "template_start_point": origin,
                    "end_point": anchor,
                    "polyline": [*polyline, *return_polyline[1:]],
                    "surface_type": surface_type,
                    "loop_type": "out_and_back",
                },
            }
        )
        candidate["anchor_quality_score"] = _anchor_quality_score(anchor)
        candidates.append(candidate)
    multi_anchor = _build_multi_anchor_candidate(
        origin=origin,
        anchors=viable_anchors,
        constraints=constraints,
        city_code=city_code,
        route_provider=route_provider,
        preferred_distance_km=preferred_distance_km,
        preferred_duration_hours=preferred_duration_hours,
    )
    if multi_anchor:
        candidates.append(multi_anchor)
    return sorted(candidates, key=lambda route: (route["anchor_quality_score"], route["distance_km"]), reverse=True)[:5]


def _build_multi_anchor_candidate(
    *,
    origin: dict[str, Any],
    anchors: list[dict[str, Any]],
    constraints: dict[str, Any],
    city_code: str,
    route_provider,
    preferred_distance_km: float,
    preferred_duration_hours: float,
) -> dict[str, Any] | None:
    if len(anchors) < 2:
        return None
    ordered_anchors = anchors
    best_candidate = None
    best_gap = None
    for anchor_count in range(2, min(len(ordered_anchors), 4) + 1):
        selected_anchors = ordered_anchors[:anchor_count]
        route_points = [origin, *selected_anchors, origin]
        legs = []
        for start_point, end_point in zip(route_points, route_points[1:]):
            legs.append(route_provider.get_cycling_path(start_point, end_point))
        distance_km = round(sum(float(leg["distance_km"]) for leg in legs), 1)
        duration_hours = round(sum(float(leg["estimated_duration_hours"]) for leg in legs), 2)
        candidate = _format_multi_anchor_candidate(
            origin=origin,
            anchors=selected_anchors,
            legs=legs,
            distance_km=distance_km,
            duration_hours=duration_hours,
            constraints=constraints,
            city_code=city_code,
            preferred_distance_km=preferred_distance_km,
            preferred_duration_hours=preferred_duration_hours,
        )
        gap = abs(distance_km - preferred_distance_km) + abs(duration_hours - preferred_duration_hours) * 8
        if best_gap is None or gap < best_gap:
            best_candidate = candidate
            best_gap = gap
    return best_candidate


def _format_multi_anchor_candidate(
    *,
    origin: dict[str, Any],
    anchors: list[dict[str, Any]],
    legs: list[dict[str, Any]],
    distance_km: float,
    duration_hours: float,
    constraints: dict[str, Any],
    city_code: str,
    preferred_distance_km: float,
    preferred_duration_hours: float,
) -> dict[str, Any]:
    start_point_name = constraints["start_point"]
    anchor_names = [anchor["name"] for anchor in anchors]
    route_name = f"{start_point_name}-{'-'.join(anchor_names)}休闲环线"
    polyline = []
    for leg in legs:
        leg_polyline = leg.get("polyline") or []
        polyline.extend(leg_polyline if not polyline else leg_polyline[1:])
    return {
        "route_code": f"DYN-{city_code.upper()}-LOOP",
        "name": route_name,
        "city_code": city_code,
        "start_point_name": start_point_name,
        "start_point_lng": origin["longitude"],
        "start_point_lat": origin["latitude"],
        "end_point_name": anchor_names[-1],
        "end_point_lng": anchors[-1]["longitude"],
        "end_point_lat": anchors[-1]["latitude"],
        "loop_type": "multi_anchor_loop",
        "district_tags": [constraints.get("origin_region") or city_code],
        "ride_style_tags": _ride_style_tags(constraints),
        "season_tags": [],
        "distance_km": distance_km,
        "elevation_gain_m": 0,
        "estimated_duration_hours": duration_hours,
        "difficulty_level": "easy",
        "best_time_slots": ["当前时段"],
        "avoid_time_slots": [],
        "surface_type": "greenway" if any(_surface_type_for_anchor(anchor) == "greenway" for anchor in anchors) else "urban_road",
        "traffic_level": "unknown",
        "supply_score": 7,
        "return_difficulty_score": 2,
        "scenic_score": max(_scenic_score_for_anchor(anchor) for anchor in anchors),
        "training_score": 2,
        "beginner_friendly": True,
        "climb_segments": [],
        "supply_points": [
            {"name": anchor["name"], "km_mark": round(distance_km * (index + 1) / (len(anchors) + 1), 1), "type": anchor.get("type") or "POI"}
            for index, anchor in enumerate(anchors)
        ],
        "bailout_options": [{"name": "就近折返", "km_mark": round(distance_km / 2, 1), "reason": "多锚点近场路线，可按体感减少后续锚点"}],
        "holiday_penalty_level": "medium",
        "weather_sensitivity": {"heat": "medium", "rain": "medium", "crosswind": "medium"},
        "route_notes": f"基于{start_point_name}周边多个 POI 和骑行路径动态扩张生成，更适合按计划时长休闲骑。",
        "route_source": "dynamic_nearby",
        "constraint_warnings": _dynamic_constraint_warnings(
            distance_km,
            duration_hours,
            preferred_distance_km,
            preferred_duration_hours,
        ),
        "anchor_quality_score": max(_anchor_quality_score(anchor) for anchor in anchors) + 1,
        "route_context": {
            "provider_name": "dynamic-nearby-route",
            "fact_source": "amap-dynamic",
            "distance_km": distance_km,
            "estimated_duration_hours": duration_hours,
            "template_distance_km": distance_km,
            "template_duration_hours": duration_hours,
            "total_distance_km": distance_km,
            "total_duration_hours": duration_hours,
            "approach_distance_km": 0.0,
            "approach_duration_hours": 0.0,
            "user_start_point": origin,
            "template_start_point": origin,
            "end_point": anchors[-1],
            "polyline": polyline,
            "surface_type": "greenway",
            "loop_type": "multi_anchor_loop",
        },
    }


def _ride_style_tags(constraints: dict[str, Any]) -> list[str]:
    if constraints.get("ride_style") == "scenic_relaxed":
        return ["relaxed", "scenic", "nearby"]
    return ["nearby"]


def _preferred_route_size(constraints: dict[str, Any]) -> tuple[float, float]:
    target_distance = constraints.get("target_distance_km")
    if target_distance:
        return max(4.0, float(target_distance) * 0.35), 0.25
    target_hours = float(constraints.get("available_hours") or 2)
    return min(max(target_hours * 8, 6.0), 32.0), min(max(target_hours * 0.45, 0.4), target_hours * 1.25)


def _is_viable_anchor_route(
    anchor: dict[str, Any],
    distance_km: float,
    duration_hours: float,
) -> bool:
    if _anchor_quality_score(anchor) >= 2:
        return distance_km >= 2.0 and duration_hours >= 0.12
    return distance_km >= 4.0 and duration_hours >= 0.25


def _dynamic_constraint_warnings(
    distance_km: float,
    duration_hours: float,
    preferred_distance_km: float,
    preferred_duration_hours: float,
) -> list[str]:
    warnings = []
    if distance_km < preferred_distance_km * 0.75 or duration_hours < preferred_duration_hours * 0.75:
        warnings.append("dynamic-route-shorter-than-plan")
    return warnings


def _anchor_quality_score(anchor: dict[str, Any]) -> int:
    anchor_type = anchor.get("type") or ""
    anchor_text = f"{anchor.get('name', '')}{anchor_type}"
    if any(token in anchor_text for token in ("公园", "绿地", "湖", "河", "运河", "绿道")):
        return 3
    if any(token in anchor_text for token in ("景点", "风景", "广场", "体育", "亚运")):
        return 2
    return 1


def _is_unsupported_anchor(anchor: dict[str, Any]) -> bool:
    anchor_text = f"{anchor.get('name', '')}{anchor.get('type', '')}"
    return any(token in anchor_text for token in ("停车场", "充电", "站点", "地下车库"))


def _surface_type_for_anchor(anchor: dict[str, Any]) -> str:
    anchor_text = f"{anchor.get('name', '')}{anchor.get('type', '')}"
    if any(token in anchor_text for token in ("公园", "绿地", "湖", "河", "运河")):
        return "greenway"
    return "urban_road"


def _scenic_score_for_anchor(anchor: dict[str, Any]) -> int:
    anchor_text = f"{anchor.get('name', '')}{anchor.get('type', '')}"
    if any(token in anchor_text for token in ("公园", "绿地", "湖", "河", "运河")):
        return 8
    return 6
