"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from datetime import date

from fastapi.testclient import TestClient

from app.core.cache import InMemoryCacheBackend
from app.main import create_app
from app.providers.weather_provider import CachedWeatherProvider


class CountingWeatherProvider:
    def __init__(self) -> None:
        self.calls = 0

    def get_weather_snapshot(self, *, city_code: str, region_code: str, forecast_date: date) -> dict:
        self.calls += 1
        return {
            "region_code": region_code,
            "forecast_date": str(forecast_date),
            "temperature_min": 22.0,
            "temperature_max": 31.0,
            "precipitation_probability": 0.15,
            "wind_speed": 4.8,
            "wind_direction": "SE",
            "weather_summary": "cloudy",
            "provider_name": "counting",
            "raw_payload": {},
        }


class FailingRouteProvider:
    provider_name = "failing-route"

    def get_route_context(self, route: dict, constraints: dict) -> dict:
        raise RuntimeError("route-provider-down")


def test_cached_weather_provider_reuses_snapshot_for_same_region_and_date() -> None:
    backend = InMemoryCacheBackend()
    provider = CountingWeatherProvider()
    cached_provider = CachedWeatherProvider(provider, backend, ttl_seconds=600)

    first = cached_provider.get_weather_snapshot(
        city_code="hangzhou",
        region_code="binjiang",
        forecast_date=date(2026, 5, 30),
    )
    second = cached_provider.get_weather_snapshot(
        city_code="hangzhou",
        region_code="binjiang",
        forecast_date=date(2026, 5, 30),
    )

    assert provider.calls == 1
    assert first == second


def test_ride_plan_reuses_hot_query_cache_and_stamps_new_request_no(tmp_path, monkeypatch, dynamic_route_provider, dynamic_poi_provider) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=CountingWeatherProvider(),
            route_provider=dynamic_route_provider,
            poi_provider=dynamic_poi_provider,
        )
    )

    first = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )
    second = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["request_no"] != second_payload["request_no"]
    assert second_payload["tool_trace"][0]["stage_name"] == "plan_cache"


def test_ride_plan_does_not_cache_provider_fallback_results(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app(weather_provider=CountingWeatherProvider(), route_provider=FailingRouteProvider()))

    first = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )
    second = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert "nearby-route-discovery-unavailable" in first.json()["fallback_reason"]
    assert "nearby-route-discovery-unavailable" in second.json()["fallback_reason"]
    assert second.json()["tool_trace"][0]["stage_name"] != "plan_cache"
