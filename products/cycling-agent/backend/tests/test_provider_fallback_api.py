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


class FailingRouteProvider:
    provider_name = "failing-route"

    def get_route_context(self, route: dict, constraints: dict) -> dict:
        raise RuntimeError("route-provider-down")


class FailingPoiProvider:
    provider_name = "failing-poi"

    def get_poi_context(self, route: dict) -> dict:
        raise RuntimeError("poi-provider-down")


def test_ride_plan_marks_provider_fallback_when_route_or_poi_provider_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=FailingRouteProvider(),
            poi_provider=FailingPoiProvider(),
        )
    )

    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "nearby-route-discovery-unavailable" in payload["fallback_reason"]
    assert {item["status"] for item in payload["tool_trace"]} >= {"fallback"}
    fallback_stages = {
        item["stage_name"] for item in payload["tool_trace"] if item["status"] == "fallback"
    }
    assert fallback_stages >= {"nearby_route_discovery"}
    assert payload["status"] == "no_match"
    assert payload["recommended_plan"]["route_code"] == "NO-MATCH"
