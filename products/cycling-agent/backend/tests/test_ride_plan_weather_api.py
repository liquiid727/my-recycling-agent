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
            "temperature_max": 31.0,
            "precipitation_probability": 0.15,
            "wind_speed": 4.8,
            "wind_direction": "SE",
            "weather_summary": "cloudy",
            "provider_name": "stub",
        }


def test_post_ride_plan_returns_weather_snapshot_and_no_fallback(tmp_path, monkeypatch, dynamic_route_provider, dynamic_poi_provider) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=dynamic_route_provider,
            poi_provider=dynamic_poi_provider,
        )
    )

    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["weather_snapshot"]["weather_summary"] == "cloudy"
    assert body["fallback_reason"] == []


class FailingWeatherProvider:
    def get_weather_snapshot(self, *, city_code: str, region_code: str, forecast_date: date) -> dict:
        raise RuntimeError("provider-down")


def test_post_ride_plan_falls_back_when_weather_provider_fails(tmp_path, monkeypatch, dynamic_route_provider, dynamic_poi_provider) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=FailingWeatherProvider(),
            route_provider=dynamic_route_provider,
            poi_provider=dynamic_poi_provider,
        )
    )

    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["weather_snapshot"]["provider_name"] == "fallback"
    assert body["fallback_reason"] == ["weather-provider-unavailable"]
