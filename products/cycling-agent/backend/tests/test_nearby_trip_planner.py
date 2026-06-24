from app.services.nearby_trip_planner import rank_nearby_trip_candidates, rank_nearby_trip_route_candidates


def test_rank_nearby_trip_route_candidates_filters_hard_climb_for_avoid_slope() -> None:
    routes = [
        {
            "route_code": "HZ-RIVER-001",
            "name": "滨江江边线",
            "district_tags": ["滨江", "江边"],
            "ride_style_tags": ["relaxed", "scenic"],
            "difficulty_level": "easy",
            "scenic_score": 8,
            "distance_km": 42,
            "elevation_gain_m": 180,
            "estimated_duration_hours": 2.8,
            "route_context": {"total_distance_km": 42, "total_duration_hours": 2.8, "approach_distance_km": 1.0},
        },
        {
            "route_code": "HZ-HILL-002",
            "name": "龙井爬坡线",
            "district_tags": ["西湖", "龙井"],
            "ride_style_tags": ["climb", "scenic"],
            "difficulty_level": "medium",
            "scenic_score": 9,
            "distance_km": 36,
            "elevation_gain_m": 520,
            "estimated_duration_hours": 3.2,
            "route_context": {"total_distance_km": 36, "total_duration_hours": 3.2, "approach_distance_km": 2.0},
        },
    ]

    ranked = rank_nearby_trip_route_candidates(
        routes=routes,
        constraints={
            "duration_bucket": "half_day",
            "available_hours": 5,
            "origin_region": "滨江",
            "ride_style": "scenic_relaxed",
            "slope_tolerance": "avoid",
            "destination_preferences": ["江边"],
        },
    )

    assert ranked
    assert ranked[0]["route_code"] == "HZ-RIVER-001"
    assert all(route["route_code"] != "HZ-HILL-002" for route in ranked)


def test_rank_nearby_trip_candidates_can_use_feasible_alternative_route_when_canonical_route_missing() -> None:
    route_candidates = [
        {
            "route_code": "HZ-RIVER-001",
            "name": "滨江江边线",
            "district_tags": ["滨江", "江边"],
            "ride_style_tags": ["relaxed", "scenic"],
            "difficulty_level": "easy",
            "scenic_score": 8,
            "distance_km": 42,
            "elevation_gain_m": 180,
            "estimated_duration_hours": 2.8,
            "weekend_route_score": 0.92,
            "route_context": {"total_distance_km": 42, "total_duration_hours": 2.8, "approach_distance_km": 1.0},
        }
    ]
    trips = [
        {
            "trip_no": "TRIP-HZ-RIVER-CAFE",
            "route_template_id": "HZ-SOME-OTHER-ROUTE",
            "destination_no": "DST-HZ-RIVER-CAFE",
            "name": "钱塘江沿线亲水骑 + 江边咖啡",
            "origin_region_tags": ["滨江"],
            "total_duration_hours": 4.5,
            "ride_duration_hours": 2.8,
            "trip_style_tags": ["half_day", "江边", "咖啡", "relaxed", "scenic"],
            "return_mode_options": ["地铁 6 号线公共交通返程"],
            "fallback_plan": "天气转差就提前返程。",
        }
    ]
    destinations = [
        {
            "destination_no": "DST-HZ-RIVER-CAFE",
            "name": "钱塘江滨江咖啡休息带",
            "destination_type": "咖啡",
            "region_tags": ["滨江", "江边", "咖啡"],
            "suitable_duration": ["half_day"],
            "stay_duration_minutes": 60,
            "crowd_level": {"weekend": "medium", "holiday": "high"},
            "stay_suggestion": "喝杯咖啡再返程。",
            "supply_summary": "江边补给稳定。",
        }
    ]

    ranked = rank_nearby_trip_candidates(
        trips=trips,
        destinations=destinations,
        route_candidates=route_candidates,
        constraints={
            "duration_bucket": "half_day",
            "available_hours": 5,
            "origin_region": "滨江",
            "ride_style": "scenic_relaxed",
            "destination_preferences": ["江边", "咖啡"],
            "return_preference": "public_transport",
        },
        weather_snapshot={"weather_summary": "cloudy", "temperature_max": 28, "precipitation_probability": 0.1},
        user_profile={},
        risk_rules=[],
    )

    assert ranked
    assert ranked[0]["trip"]["trip_no"] == "TRIP-HZ-RIVER-CAFE"
    assert ranked[0]["route"]["route_code"] == "HZ-RIVER-001"
    assert ranked[0]["route_compatibility_score"] >= 0.25
