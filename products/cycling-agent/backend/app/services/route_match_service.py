"""CN: 路线匹配服务，根据用户约束给模板路线打匹配分并排序。
EN: Route matching service that scores and ranks route templates against user constraints.
"""

from __future__ import annotations

from copy import deepcopy

MIN_MATCH_SCORE = 0.75
MAX_APPROACH_DISTANCE_KM = 15.0


def rank_route_candidates(routes: list[dict], constraints: dict) -> list[dict]:
    target_hours = constraints.get("available_hours") or 3
    target_distance = constraints.get("target_distance_km")
    ride_style = constraints.get("ride_style", "general")
    origin_region = constraints.get("origin_region")
    if target_hours > 6:
        return []

    ranked_routes = deepcopy(routes)
    filtered_routes = []
    soft_candidates = []
    for route in ranked_routes:
        route_context = route.get("route_context") or {}
        effective_duration = float(route_context.get("total_duration_hours") or route_context.get("estimated_duration_hours") or route["estimated_duration_hours"])
        effective_distance = float(route_context.get("total_distance_km") or route_context.get("distance_km") or route.get("distance_km", 0))
        approach_distance = route_context.get("approach_distance_km")
        constraint_warnings = list(route.get("constraint_warnings") or [])
        if approach_distance is not None and float(approach_distance) > MAX_APPROACH_DISTANCE_KM:
            constraint_warnings.append("approach-distance-over-limit")
        if target_hours and effective_duration > float(target_hours) + max(0.75, float(target_hours) * 0.25):
            constraint_warnings.append("total-duration-over-target")
        if target_distance:
            allowed_gap = max(12.0, float(target_distance) * 0.4)
            if abs(effective_distance - float(target_distance)) > allowed_gap:
                constraint_warnings.append("target-distance-out-of-range")

        duration_gap = abs(effective_duration - float(target_hours))
        distance_bonus = 0.0
        if target_distance:
            distance_gap = abs(effective_distance - float(target_distance))
            distance_bonus = max(-0.25, 0.18 - distance_gap / max(float(target_distance), 1) * 0.35)
        difficulty_bonus = 0.25 if route["difficulty_level"] == "easy" else 0
        scenic_bonus = route.get("scenic_score", 0) / 100
        style_bonus = 0.0
        route_style_tags = set(route.get("ride_style_tags", []))
        requested_style_tags = set(_normalize_ride_style(ride_style))
        if requested_style_tags and requested_style_tags.issubset(route_style_tags):
            style_bonus += 0.18
        elif ride_style == "scenic_relaxed" and route["difficulty_level"] == "easy":
            style_bonus += 0.1

        origin_bonus = 0.25 if origin_region and origin_region in route.get("district_tags", []) else 0.0
        approach_penalty = min(float(approach_distance or 0) / 30, 0.35)
        source_bonus = 0.25 if route.get("route_source") == "dynamic_nearby" and not target_distance else 0.0
        route["match_score"] = round(
            1
            - duration_gap / 10
            + distance_bonus
            + difficulty_bonus
            + scenic_bonus
            + style_bonus
            + origin_bonus
            + source_bonus
            - approach_penalty,
            3,
        )
        route["constraint_warnings"] = constraint_warnings
        hard_warnings = [warning for warning in constraint_warnings if warning != "dynamic-route-shorter-than-plan"]
        if hard_warnings:
            soft_candidates.append(route)
        else:
            filtered_routes.append(route)

    strict_matches = sorted(
        [item for item in filtered_routes if item["match_score"] >= MIN_MATCH_SCORE],
        key=lambda item: item["match_score"],
        reverse=True,
    )
    if strict_matches:
        return strict_matches
    return sorted(
        [item for item in soft_candidates if item["match_score"] >= MIN_MATCH_SCORE],
        key=lambda item: item["match_score"],
        reverse=True,
    )


def _normalize_ride_style(ride_style: str) -> list[str]:
    if ride_style == "scenic_relaxed":
        return ["scenic", "relaxed"]
    if ride_style == "training_loop":
        return ["training", "loop"]
    if ride_style == "general":
        return []
    return [ride_style]
