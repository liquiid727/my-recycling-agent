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


def test_planning_audit_returns_normalized_request_weather_risk_and_decision(tmp_path, monkeypatch, dynamic_route_provider, dynamic_poi_provider) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=dynamic_route_provider,
            poi_provider=dynamic_poi_provider,
        )
    )

    create_response = client.post(
        "/api/v1/ride/plan",
        json={
            "query": "周六从闻涛路滨江段出发骑3小时，不想太累，最好风景好一点",
            "target_date": "2026-05-30",
            "user_profile": {"fitness_level": "low", "ride_style_preferences": ["scenic"]},
        },
    )
    assert create_response.status_code == 200

    request_no = create_response.json()["request_no"]
    audit_response = client.get(f"/api/v1/admin/planning-audit/{request_no}")

    assert audit_response.status_code == 200
    audit = audit_response.json()
    assert audit["ride_request"]["request_no"] == request_no
    assert audit["ride_request"]["id"]
    assert audit["ride_request"]["origin_region"] == "滨江"
    assert audit["weather_snapshot"]["id"]
    assert audit["weather_snapshot"]["weather_no"].startswith("WS-")
    assert audit["weather_snapshot"]["provider_name"] == "stub"
    assert audit["risk_assessments"]
    assert audit["risk_assessments"][0]["entity_id"]
    assert audit["risk_assessments"][0]["risk_no"].startswith("RS-")
    assert audit["decision_result"]["id"]
    assert audit["decision_result"]["decision_no"].startswith("DC-")
    assert audit["decision_result"]["recommended_route_code"] == create_response.json()["recommended_plan"]["route_code"]
