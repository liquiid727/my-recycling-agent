"""CN: Phase 2 周边游 API 测试，验证 mvp2 与 mvp1 路线规划隔离后的 trip 输出。
EN: Phase 2 nearby-trip API tests for mvp2 trip output isolated from mvp1 route planning.
"""

from datetime import date

from fastapi.testclient import TestClient

from app.main import create_app


class StubWeatherProvider:
    def get_weather_snapshot(self, *, city_code: str, region_code: str, forecast_date: date) -> dict:
        return {
            "region_code": region_code,
            "forecast_date": str(forecast_date),
            "temperature_min": 23.0,
            "temperature_max": 32.0,
            "precipitation_probability": 0.2,
            "wind_speed": 4.2,
            "wind_direction": "SE",
            "weather_summary": "cloudy",
            "provider_name": "stub",
            "raw_payload": {},
        }


def test_nearby_trip_plan_returns_primary_trip_alternatives_rhythm_and_return_options(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))

    response = client.post(
        "/api/v1/ride/plan",
        json={
            "planning_mode": "nearby_trip",
            "input_mode": "structured",
            "query": "周六从闻涛路滨江段出发，想骑去江边咖啡休息，半天内返回",
            "target_date": "2026-06-06",
            "structured_constraints": {
                "departure_time": "08:00",
                "origin_region": "滨江",
                "start_point": "闻涛路滨江段",
                "available_hours": 5,
                "fitness_level": "medium",
                "ride_style": "scenic_relaxed",
                "slope_tolerance": "avoid",
                "duration_bucket": "half_day",
                "destination_preferences": ["江边", "咖啡"],
                "return_preference": "public_transport",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["planning_mode"] == "nearby_trip"
    assert body["recommended_trip"]["trip_no"].startswith("TRIP-")
    assert body["recommended_trip"]["destination_name"]
    assert body["recommended_trip"]["total_duration_hours"] <= 5
    assert body["recommended_trip"]["stay_suggestion"]
    assert body["recommended_trip"]["return_options"]
    assert len(body["trip_alternatives"]) >= 1
    assert body["trip_rhythm"]["segments"][0]["stage"] == "出发前准备"
    assert any("天气风险" in item for item in body["trip_risks"]["risk_items"])
    assert any("返程风险" in item for item in body["trip_risks"]["risk_items"])
    assert body["trip_risks"]["fallback_plan"]
    assert body["tool_trace"][-1]["stage_name"] == "trip_roadbook_generator"


def test_nearby_trip_preflight_requires_origin_even_when_city_defaults_to_hangzhou() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))

    response = client.post(
        "/api/v1/ride/plan/preflight",
        json={
            "planning_mode": "nearby_trip",
            "query": "周末想找一个半天周边骑行，有目的地和返程方案",
            "target_date": "2026-06-06",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is False
    assert "start_point" in body["missing_core_fields"]
    assert body["parsed_constraints"]["planning_mode"] == "nearby_trip"


def test_weekend_trip_plan_returns_lodging_equipment_and_weather_window(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))

    response = client.post(
        "/api/v1/ride/plan",
        json={
            "planning_mode": "nearby_trip",
            "planning_scene": "weekend_trip",
            "input_mode": "structured",
            "query": "这周末想去千岛湖骑两天",
            "target_date": "2026-06-06",
            "structured_constraints": {
                "departure_time": "08:00",
                "origin_region": "滨江",
                "start_point": "闻涛路滨江段",
                "fitness_level": "medium",
                "ride_style": "scenic_relaxed",
                "slope_tolerance": "neutral",
                "duration_bucket": "two_day",
                "destination_preferences": ["千岛湖"],
                "return_preference": "public_transport",
                "overnight_preference": "required",
                "lodging_preference": "湖边酒店",
                "cross_city_allowed": True,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["parsed_constraints"]["planning_scene"] == "weekend_trip"
    assert body["recommended_trip"]["destination_name"] == "千岛湖周边骑行停留区"
    assert body["recommended_trip"]["duration_bucket"] == "two_day"
    assert body["recommended_trip"]["itinerary_days"]
    assert body["recommended_trip"]["lodging_plan"]
    assert body["recommended_trip"]["equipment_advice"]
    assert body["recommended_trip"]["weather_window_notes"]
    assert body["decision_summary"]["scene"] == "weekend_trip"
    assert any("住宿" in item for item in body["decision_summary"]["confidence_notes"])
