"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from app.services.city_strategy_service import (
    apply_city_strategy_to_recommendation_score,
    apply_city_strategy_to_risk,
)


def test_apply_city_strategy_to_risk_adds_crowd_and_weather_bias_for_matching_route() -> None:
    route = {
        "district_tags": ["西湖", "龙井"],
        "weather_sensitivity": {"heat": "high"},
    }
    weather = {"temperature_max": 34, "wind_speed": 3}
    risk = {
        "overall_risk_score": 0.35,
        "weather_risk_score": 0.25,
        "climb_risk_score": 0.0,
        "traffic_risk_score": 0.0,
        "supply_risk_score": 0.0,
        "return_risk_score": 0.0,
        "crowd_risk_score": 0.0,
        "risk_level": "medium",
    }
    strategy_rules = [
        {
            "config_type": "risk_bias",
            "config_value": {
                "district_tags": ["西湖", "龙井"],
                "crowd_risk_delta": 0.2,
                "heat_weather_risk_delta": 0.1,
            },
        }
    ]

    adjusted = apply_city_strategy_to_risk(route, weather, risk, strategy_rules)

    assert adjusted["crowd_risk_score"] == 0.2
    assert adjusted["weather_risk_score"] == 0.35
    assert adjusted["overall_risk_score"] == 0.65
    assert adjusted["risk_level"] == "high"


def test_apply_city_strategy_to_recommendation_score_adds_city_bonus() -> None:
    route = {"district_tags": ["湘湖"], "route_code": "HZ-LEISURE-003"}
    strategy_rules = [
        {
            "config_type": "risk_bias",
            "config_value": {
                "district_tags": ["湘湖"],
                "city_bonus": 0.12,
            },
        }
    ]

    score = apply_city_strategy_to_recommendation_score(route, 0.78, strategy_rules)

    assert score == 0.9
