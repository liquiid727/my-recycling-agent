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
            "raw_payload": {},
        }


def test_city_strategy_bonus_keeps_city_ride_on_dynamic_route_source(tmp_path, monkeypatch, dynamic_route_provider, dynamic_poi_provider) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=dynamic_route_provider,
            poi_provider=dynamic_poi_provider,
        )
    )

    baseline = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，最好风景好一点", "target_date": "2026-05-30"},
    )
    assert baseline.status_code == 200
    assert baseline.json()["recommended_plan"]["route_code"].startswith("DYN-HANGZHOU-")

    strategy_response = client.post(
        "/api/v1/admin/city-strategy",
        json={
                "city_code": "hangzhou",
                "config_type": "risk_bias",
                "config_key": "xianghu_bonus",
                "config_value": {"district_tags": ["湘湖"], "city_bonus": 0.8},
                "status": "active",
            },
        )
    assert strategy_response.status_code == 200

    boosted = client.post(
        "/api/v1/ride/plan",
        json={"query": "周日从闻涛路滨江段出发骑3小时，不想太累，最好风景好一点", "target_date": "2026-05-31"},
    )
    assert boosted.status_code == 200
    assert boosted.json()["recommended_plan"]["route_code"].startswith("DYN-HANGZHOU-")
