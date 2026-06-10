"""CN: 风险评分服务，用确定性规则计算天气、爬升、交通、补给、返程和人流风险。
EN: Risk scoring service that deterministically scores weather, climb, traffic, supply, return, and crowd risk.
"""

from __future__ import annotations


def score_route_risk(route: dict, weather: dict, user: dict, risk_rules: list[dict] | None = None) -> dict:
    weather_risk = 0.35 if weather.get("temperature_max", 0) >= 33 else 0
    if weather.get("precipitation_probability", 0) >= 0.4:
        weather_risk += 0.2
    if weather.get("wind_speed", 0) >= 6:
        weather_risk += 0.15

    climb_risk = 0.35 if route.get("elevation_gain_m", 0) > 500 and user.get("fitness_level") == "low" else 0
    traffic_level = route.get("traffic_level")
    traffic_risk = 0.15 if traffic_level == "medium" else 0.3 if traffic_level == "high" else 0
    supply_risk = 0.1 if route.get("supply_score", 0) <= 5 else 0
    return_risk = 0.1 if route.get("return_difficulty_score", 0) >= 5 else 0

    risk = {
        "risk_level": "low",
        "weather_risk_score": weather_risk,
        "climb_risk_score": climb_risk,
        "traffic_risk_score": traffic_risk,
        "supply_risk_score": supply_risk,
        "return_risk_score": return_risk,
        "crowd_risk_score": 0.0,
    }
    if risk_rules:
        _apply_custom_risk_rules(risk, route, weather, user, risk_rules)
    overall = round(
        risk["weather_risk_score"]
        + risk["climb_risk_score"]
        + risk["traffic_risk_score"]
        + risk["supply_risk_score"]
        + risk["return_risk_score"]
        + risk["crowd_risk_score"],
        3,
    )
    risk["overall_risk_score"] = overall
    risk["risk_level"] = "high" if overall >= 0.6 else "medium" if overall >= 0.3 else "low"
    return risk


def _apply_custom_risk_rules(
    risk: dict,
    route: dict,
    weather: dict,
    user: dict,
    risk_rules: list[dict],
) -> None:
    for rule in risk_rules:
        rule_value = rule.get("rule_value", {})
        if not _matches_rule_conditions(rule_value.get("conditions", {}), route, weather, user):
            continue
        target = rule_value.get("target", "overall")
        delta = float(rule_value.get("delta", 0.0))
        score_key = _target_to_score_key(target)
        if score_key is None:
            continue
        risk[score_key] = round(max(0.0, risk.get(score_key, 0.0) + delta), 3)


def _target_to_score_key(target: str) -> str | None:
    mapping = {
        "weather": "weather_risk_score",
        "climb": "climb_risk_score",
        "traffic": "traffic_risk_score",
        "supply": "supply_risk_score",
        "return": "return_risk_score",
        "crowd": "crowd_risk_score",
    }
    return mapping.get(target)


def _matches_rule_conditions(conditions: dict, route: dict, weather: dict, user: dict) -> bool:
    route_code_eq = conditions.get("route_code_eq")
    if route_code_eq and route.get("route_code") != route_code_eq:
        return False

    district_tags_any = conditions.get("district_tags_any", [])
    if district_tags_any and not set(district_tags_any).intersection(set(route.get("district_tags", []))):
        return False

    traffic_level_in = conditions.get("traffic_level_in", [])
    if traffic_level_in and route.get("traffic_level") not in traffic_level_in:
        return False

    holiday_penalty_level_in = conditions.get("holiday_penalty_level_in", [])
    if holiday_penalty_level_in and route.get("holiday_penalty_level") not in holiday_penalty_level_in:
        return False

    fitness_level_eq = conditions.get("fitness_level_eq")
    if fitness_level_eq and user.get("fitness_level") != fitness_level_eq:
        return False

    temperature_max_gte = conditions.get("temperature_max_gte")
    if temperature_max_gte is not None and weather.get("temperature_max", 0) < temperature_max_gte:
        return False

    precipitation_probability_gte = conditions.get("precipitation_probability_gte")
    if precipitation_probability_gte is not None and weather.get("precipitation_probability", 0) < precipitation_probability_gte:
        return False

    wind_speed_gte = conditions.get("wind_speed_gte")
    if wind_speed_gte is not None and weather.get("wind_speed", 0) < wind_speed_gte:
        return False

    elevation_gain_m_gte = conditions.get("elevation_gain_m_gte")
    if elevation_gain_m_gte is not None and route.get("elevation_gain_m", 0) < elevation_gain_m_gte:
        return False

    supply_score_lte = conditions.get("supply_score_lte")
    if supply_score_lte is not None and route.get("supply_score", 0) > supply_score_lte:
        return False

    return_difficulty_score_gte = conditions.get("return_difficulty_score_gte")
    if return_difficulty_score_gte is not None and route.get("return_difficulty_score", 0) < return_difficulty_score_gte:
        return False

    weather_sensitivity = route.get("weather_sensitivity", {})
    for field_name, key in (
        ("weather_sensitivity_heat_in", "heat"),
        ("weather_sensitivity_rain_in", "rain"),
        ("weather_sensitivity_crosswind_in", "crosswind"),
    ):
        accepted = conditions.get(field_name, [])
        if accepted and weather_sensitivity.get(key) not in accepted:
            return False

    return True
