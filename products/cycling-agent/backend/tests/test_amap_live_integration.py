"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from __future__ import annotations

import os
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.providers.poi_provider import AMapPoiProvider
from app.providers.route_provider import AMapRouteProvider


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


pytestmark = pytest.mark.skipif(
    not os.environ.get("CYCLING_AGENT_AMAP_WEB_API_KEY"),
    reason="AMap live integration requires CYCLING_AGENT_AMAP_WEB_API_KEY",
)


def test_live_amap_route_and_poi_provider_enrich_ride_plan(tmp_path, monkeypatch) -> None:
    api_key = os.environ.get("CYCLING_AGENT_AMAP_WEB_API_KEY")
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")

    route_provider = AMapRouteProvider(
        base_url=os.environ.get("CYCLING_AGENT_AMAP_BASE_URL", "https://restapi.amap.com"),
        api_key=api_key,
        timeout_seconds=float(os.environ.get("CYCLING_AGENT_AMAP_TIMEOUT_SECONDS", "10")),
    )
    poi_provider = AMapPoiProvider(
        base_url=os.environ.get("CYCLING_AGENT_AMAP_BASE_URL", "https://restapi.amap.com"),
        api_key=api_key,
        timeout_seconds=float(os.environ.get("CYCLING_AGENT_AMAP_TIMEOUT_SECONDS", "10")),
    )
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=route_provider,
            poi_provider=poi_provider,
        )
    )

    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    route_trace = next(item for item in payload["tool_trace"] if item["stage_name"] == "route_provider")
    poi_trace = next(item for item in payload["tool_trace"] if item["stage_name"] == "poi_provider")
    assert route_trace["status"] == "success"
    assert poi_trace["status"] == "success"
    assert payload["roadbook"]["route_context"]["provider_name"] == "amap-route"
    assert payload["roadbook"]["poi_summary"]["fact_source"] == "amap"
