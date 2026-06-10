"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from app.services.risk_scoring_service import score_route_risk


def test_score_route_risk_marks_hot_climb_route_as_medium_or_higher() -> None:
    route = {"elevation_gain_m": 520, "traffic_level": "medium", "supply_score": 6}
    weather = {"temperature_max": 34, "precipitation_probability": 0.1, "wind_speed": 3}
    user = {"fitness_level": "low"}

    result = score_route_risk(route, weather, user)

    assert result["risk_level"] in {"medium", "high"}
    assert result["weather_risk_score"] > 0


def test_score_route_risk_applies_custom_risk_rules() -> None:
    route = {
        "route_code": "HZ-HILL-002",
        "district_tags": ["西湖", "龙井"],
        "elevation_gain_m": 520,
        "traffic_level": "medium",
        "supply_score": 6,
        "weather_sensitivity": {"heat": "high", "rain": "high", "crosswind": "low"},
        "holiday_penalty_level": "high",
    }
    weather = {"temperature_max": 31, "precipitation_probability": 0.1, "wind_speed": 4}
    user = {"fitness_level": "medium"}
    risk_rules = [
        {
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
        },
        {
            "rule_key": "holiday_crowd_penalty",
            "rule_value": {
                "target": "crowd",
                "delta": 0.15,
                "conditions": {"holiday_penalty_level_in": ["high"]},
            },
        },
    ]

    result = score_route_risk(route, weather, user, risk_rules)

    assert result["weather_risk_score"] >= 0.2
    assert result["crowd_risk_score"] == 0.15
    assert result["risk_level"] in {"medium", "high"}
