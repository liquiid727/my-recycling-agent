"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from datetime import date

from fastapi.testclient import TestClient

from app.main import create_app


class StubWeatherProvider:
    def get_weather_snapshot(self, *, city_code: str, region_code: str, forecast_date: date) -> dict:
        return {
            "region_code": region_code,
            "forecast_date": str(forecast_date),
            "temperature_min": 22.0,
            "temperature_max": 30.0,
            "precipitation_probability": 0.1,
            "wind_speed": 4.2,
            "wind_direction": "SE",
            "weather_summary": "cloudy",
            "provider_name": "stub",
            "raw_payload": {},
        }


class StubLLMProvider:
    provider_name = "stub-llm"

    def parse_query(self, *, query: str, user_profile: dict | None = None) -> dict:
        return {
            "origin_region": "滨江",
            "start_point": "闻涛路滨江段",
            "available_hours": 3,
            "ride_style": "scenic_relaxed",
            "missing_fields": [],
            "confidence": 0.96,
        }

    def generate_roadbook(self, *, route: dict, risk: dict, parsed_constraints: dict) -> dict:
        return {"departure_window": "06:15-08:45", "mitigation_advice": ["用 LLM 润色后的规避建议"]}


def test_ride_plan_uses_llm_provider_when_available(tmp_path, monkeypatch, dynamic_route_provider, dynamic_poi_provider) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    app = create_app(
        weather_provider=StubWeatherProvider(),
        route_provider=dynamic_route_provider,
        poi_provider=dynamic_poi_provider,
    )
    app.state.llm_provider = StubLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert any(item["stage_name"] == "query_parser" and item["status"] == "success" for item in payload["tool_trace"])
    assert any(item["stage_name"] == "roadbook_generator" and item["status"] == "success" for item in payload["tool_trace"])
    assert payload["parsed_constraints"]["origin_region"] == "滨江"
    assert payload["parsed_constraints"]["available_hours"] == 3
    assert payload["parsed_constraints"]["ride_style"] == "scenic_relaxed"
    assert payload["roadbook"]["departure_window"] == "06:15-08:45"
