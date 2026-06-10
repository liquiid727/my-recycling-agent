"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.city_strategy_repository import list_city_strategy_configs
from app.repositories.risk_rule_repository import list_risk_rules


def test_admin_routes_and_city_strategy_are_persisted(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    route_response = client.post(
        "/api/v1/admin/routes",
        json={
            "route_code": "HZ-TEST-006",
            "name": "城西晚风轻松线",
            "city_code": "hangzhou",
            "start_point_name": "城西起点",
            "start_point_lng": 120.08,
            "start_point_lat": 30.28,
            "end_point_name": "城西终点",
            "loop_type": "loop",
            "district_tags": ["城西"],
            "ride_style_tags": ["relaxed", "scenic"],
            "season_tags": ["spring", "autumn"],
            "distance_km": 28,
            "elevation_gain_m": 150,
            "estimated_duration_hours": 2.1,
            "difficulty_level": "easy",
            "best_time_slots": ["06:30-09:00"],
            "avoid_time_slots": ["12:00-15:00"],
            "surface_type": "greenway",
            "traffic_level": "low",
            "supply_score": 7,
            "return_difficulty_score": 2,
            "scenic_score": 7,
            "training_score": 3,
            "beginner_friendly": True,
            "climb_segments": [{"name": "小坡段", "distance_km": 1.2, "elevation_gain_m": 35, "gradient_note": "短缓坡"}],
            "supply_points": [{"name": "城西便利店", "km_mark": 8, "type": "便利店"}],
            "bailout_options": [{"name": "中段折返", "km_mark": 14, "reason": "适合体感不佳时缩短"}],
            "holiday_penalty_level": "low",
            "weather_sensitivity": {"heat": "medium", "rain": "low", "crosswind": "low"},
            "route_notes": "适合下班后放松骑。"
        },
    )
    assert route_response.status_code == 200
    route_payload = route_response.json()
    assert route_payload["id"]
    assert route_payload["route_no"].startswith("RT-")

    recommended_response = client.get(
        "/api/v1/routes/recommended",
        params={"city_code": "hangzhou", "origin_region": "城西", "ride_style": "relaxed"},
    )
    assert recommended_response.status_code == 200
    assert recommended_response.json()[0]["route_code"] == "HZ-TEST-006"

    strategy_response = client.post(
        "/api/v1/admin/city-strategy",
        json={
            "city_code": "hangzhou",
            "config_type": "risk_bias",
            "config_key": "holiday_westlake_penalty",
            "config_value": {"penalty": 0.2},
            "status": "active"
        },
    )
    assert strategy_response.status_code == 200
    strategy_payload = strategy_response.json()
    assert strategy_payload["entity_id"]
    assert strategy_payload["config_no"].startswith("CF-")

    strategy_items = list_city_strategy_configs(f"sqlite:///{tmp_path / 'cycling-agent.db'}", city_code="hangzhou")
    assert strategy_items[0]["config_key"] == "holiday_westlake_penalty"
    assert strategy_items[0]["config_no"].startswith("CF-")

    risk_rule_response = client.post(
        "/api/v1/admin/risk-rules",
        json={
            "city_code": "hangzhou",
            "rule_key": "longjing_heat_penalty",
            "rule_value": {
                "target": "weather",
                "delta": 0.2,
                "conditions": {
                    "district_tags_any": ["龙井"],
                    "temperature_max_gte": 30,
                    "weather_sensitivity_heat_in": ["high"],
                },
            },
            "status": "active",
        },
    )
    assert risk_rule_response.status_code == 200
    risk_rule_payload = risk_rule_response.json()
    assert risk_rule_payload["config_no"].startswith("CF-")

    risk_rule_items = list_risk_rules(f"sqlite:///{tmp_path / 'cycling-agent.db'}", city_code="hangzhou")
    assert risk_rule_items[0]["rule_key"] == "longjing_heat_penalty"
    assert risk_rule_items[0]["config_no"].startswith("CF-")
