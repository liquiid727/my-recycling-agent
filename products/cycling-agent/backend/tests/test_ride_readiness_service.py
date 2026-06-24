"""CN: 骑前状态评估测试，验证天气、画像和疲劳输入会落成稳定的 readiness 结论。
EN: Ride-readiness tests for deterministic conclusions from weather, rider profile, and current state.
"""

from app.services.ride_readiness_service import build_ride_readiness


def test_ride_readiness_recommends_light_ride_when_tired_and_hot() -> None:
    readiness = build_ride_readiness(
        planning_scene="city_ride",
        weather_snapshot={
            "temperature_max": 33.0,
            "precipitation_probability": 0.15,
            "wind_speed": 4.2,
            "weather_summary": "cloudy",
        },
        constraints={"available_hours": 2},
        rider_profile={"fitness_level": "medium"},
        rider_state={"fatigue_level": "tired", "last_ride_days_ago": 0},
    )

    assert readiness["status"] in {"light", "rest"}
    assert readiness["recommended_intensity"] in {"light", "rest"}
    assert "heat" in readiness["caution_flags"]
    assert "fatigue" in readiness["caution_flags"]
    assert readiness["summary"]


def test_ride_readiness_allows_regular_weekend_trip_when_conditions_are_stable() -> None:
    readiness = build_ride_readiness(
        planning_scene="weekend_trip",
        weather_snapshot={
            "temperature_max": 27.0,
            "precipitation_probability": 0.1,
            "wind_speed": 3.0,
            "weather_summary": "clear",
        },
        constraints={"duration_bucket": "two_day", "available_hours": 4},
        rider_profile={"fitness_level": "high"},
        rider_state={"fatigue_level": "fresh", "last_ride_days_ago": 3},
    )

    assert readiness["status"] == "go"
    assert readiness["recommended_intensity"] == "steady"
    assert readiness["summary"] == "这个周末整体可以按计划安排。"
