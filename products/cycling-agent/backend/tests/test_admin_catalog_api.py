"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_admin_catalog_endpoints_return_routes_city_strategies_and_risk_rules(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    route_response = client.get("/api/v1/admin/routes")
    assert route_response.status_code == 200
    routes = route_response.json()
    assert routes
    assert routes[0]["route_no"].startswith("RT-")
    assert routes[0]["route_code"]

    create_strategy = client.post(
        "/api/v1/admin/city-strategy",
        json={
            "city_code": "hangzhou",
            "config_type": "risk_bias",
            "config_key": "westlake_holiday_penalty",
            "config_value": {"district_tags": ["西湖"], "crowd_risk_delta": 0.2},
            "status": "active",
        },
    )
    assert create_strategy.status_code == 200

    strategy_response = client.get("/api/v1/admin/city-strategy")
    assert strategy_response.status_code == 200
    strategies = strategy_response.json()
    assert strategies[0]["config_no"].startswith("CF-")
    assert strategies[0]["config_key"] == "westlake_holiday_penalty"

    create_risk_rule = client.post(
        "/api/v1/admin/risk-rules",
        json={
            "city_code": "hangzhou",
            "rule_key": "qiantang_crosswind_penalty",
            "rule_value": {
                "target": "weather",
                "delta": 0.15,
                "conditions": {
                    "district_tags_any": ["钱塘江"],
                    "wind_speed_gte": 6,
                    "weather_sensitivity_crosswind_in": ["medium", "high"],
                },
            },
            "status": "active",
        },
    )
    assert create_risk_rule.status_code == 200

    risk_rule_response = client.get("/api/v1/admin/risk-rules")
    assert risk_rule_response.status_code == 200
    risk_rules = risk_rule_response.json()
    assert risk_rules[0]["config_no"].startswith("CF-")
    assert risk_rules[0]["rule_key"] == "qiantang_crosswind_penalty"


def test_admin_catalog_endpoints_maintain_nearby_destinations_and_trip_templates(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    destinations_response = client.get("/api/v1/admin/nearby-destinations")
    assert destinations_response.status_code == 200
    destinations = destinations_response.json()
    assert destinations
    assert destinations[0]["destination_no"].startswith("DST-")

    create_destination = client.post(
        "/api/v1/admin/nearby-destinations",
        json={
            "destination_no": "DST-ADMIN-001",
            "city_code": "hangzhou",
            "name": "后台江边咖啡点",
            "destination_type": "咖啡",
            "region_tags": ["滨江", "钱塘江"],
            "suitable_duration": ["half_day"],
            "stay_duration_minutes": 60,
            "crowd_level": {"weekday": "low", "weekend": "medium", "holiday": "high"},
            "supply_summary": "江边咖啡与便利店充足。",
            "public_transport_options": ["地铁 6 号线返程"],
            "stay_suggestion": "到达后补水，停留 45 到 60 分钟。"
        },
    )
    assert create_destination.status_code == 200

    create_trip = client.post(
        "/api/v1/admin/trip-templates",
        json={
            "trip_no": "TRIP-ADMIN-001",
            "city_code": "hangzhou",
            "route_template_id": "HZ-RIVER-001",
            "destination_no": "DST-ADMIN-001",
            "name": "后台江边咖啡半日骑",
            "origin_region_tags": ["滨江"],
            "total_duration_hours": 4.5,
            "ride_duration_hours": 2.8,
            "trip_style_tags": ["江边", "咖啡", "half_day"],
            "return_mode_options": ["骑回", "公共交通"],
            "fallback_plan": "天气转差时缩短到奥体折返。",
            "status": "active",
        },
    )
    assert create_trip.status_code == 200

    trips_response = client.get("/api/v1/admin/trip-templates")
    assert trips_response.status_code == 200
    trips = trips_response.json()
    assert any(item["trip_no"] == "TRIP-ADMIN-001" for item in trips)
