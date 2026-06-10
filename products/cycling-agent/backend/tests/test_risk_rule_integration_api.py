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
            "temperature_min": 24.0,
            "temperature_max": 31.0,
            "precipitation_probability": 0.1,
            "wind_speed": 4.0,
            "wind_direction": "SE",
            "weather_summary": "cloudy",
            "provider_name": "stub",
            "raw_payload": {},
        }


def test_risk_rule_changes_risk_breakdown_in_ride_plan(tmp_path, monkeypatch, dynamic_route_provider, dynamic_poi_provider) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=dynamic_route_provider,
            poi_provider=dynamic_poi_provider,
        )
    )
    query = "周六从闻涛路滨江段出发骑3小时，不想太累，最好风景好一点"

    baseline = client.post(
        "/api/v1/ride/plan",
        json={"query": query, "target_date": "2026-05-30"},
    )
    assert baseline.status_code == 200
    assert baseline.json()["recommended_plan"]["route_code"].startswith("DYN-HANGZHOU-")
    baseline_risk = baseline.json()["roadbook"]["risk_summary"]["weather_risk_score"]

    create_rule = client.post(
        "/api/v1/admin/risk-rules",
        json={
            "city_code": "hangzhou",
            "rule_key": "river_heat_penalty",
            "rule_value": {
                "target": "weather",
                "delta": 0.2,
                "conditions": {
                    "district_tags_any": ["滨江"],
                    "temperature_max_gte": 30,
                    "weather_sensitivity_heat_in": ["medium", "high"],
                },
            },
            "status": "active",
        },
    )
    assert create_rule.status_code == 200

    boosted = client.post(
        "/api/v1/ride/plan",
        json={"query": query, "target_date": "2026-05-30"},
    )
    assert boosted.status_code == 200
    assert boosted.json()["recommended_plan"]["route_code"].startswith("DYN-HANGZHOU-")
    boosted_risk = boosted.json()["roadbook"]["risk_summary"]["weather_risk_score"]

    assert boosted_risk > baseline_risk
