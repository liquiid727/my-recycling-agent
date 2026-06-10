"""CN: 高德 live 验证脚本，用真实 key 检查路线和 POI provider 的外部调用质量。
EN: AMap live verification script for checking external route and POI provider quality with a real key.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date

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


def main() -> int:
    api_key = os.environ.get("CYCLING_AGENT_AMAP_WEB_API_KEY")
    if not api_key:
        print("missing AMAP key: set CYCLING_AGENT_AMAP_WEB_API_KEY", file=sys.stderr)
        return 2

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
        json={"query": "周六从滨江出发骑3小时，不想太累，风景好一点", "target_date": date(2026, 5, 30).isoformat()},
    )
    response.raise_for_status()
    payload = response.json()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
