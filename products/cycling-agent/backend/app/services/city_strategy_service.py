"""CN: 城市策略服务，把杭州本地规则应用到风险评分和最终推荐分。
EN: City strategy service that applies Hangzhou-local rules to risk scores and final recommendation scores.
"""

from __future__ import annotations

from typing import Any


def apply_city_strategy_to_risk(
    route: dict[str, Any],
    weather_snapshot: dict[str, Any],
    risk: dict[str, Any],
    strategy_rules: list[dict[str, Any]],
) -> dict[str, Any]:
    adjusted = dict(risk)
    original_weather_risk = float(adjusted.get("weather_risk_score", 0.0))
    original_crowd_risk = float(adjusted.get("crowd_risk_score", 0.0))
    adjusted.setdefault("crowd_risk_score", 0.0)

    for rule in _active_risk_bias_rules(strategy_rules):
        if not _rule_matches_route(route, rule):
            continue

        value = rule["config_value"]
        adjusted["crowd_risk_score"] = round(
            adjusted.get("crowd_risk_score", 0.0) + float(value.get("crowd_risk_delta", 0.0)),
            3,
        )

        if weather_snapshot.get("temperature_max", 0) >= 33:
            adjusted["weather_risk_score"] = round(
                adjusted.get("weather_risk_score", 0.0) + float(value.get("heat_weather_risk_delta", 0.0)),
                3,
            )

        if weather_snapshot.get("wind_speed", 0) >= 8:
            adjusted["weather_risk_score"] = round(
                adjusted.get("weather_risk_score", 0.0) + float(value.get("crosswind_weather_risk_delta", 0.0)),
                3,
            )

    adjusted["overall_risk_score"] = _recalculate_overall(
        base_overall=float(risk.get("overall_risk_score", 0.0)),
        weather_risk_delta=float(adjusted.get("weather_risk_score", 0.0)) - original_weather_risk,
        crowd_risk_delta=float(adjusted.get("crowd_risk_score", 0.0)) - original_crowd_risk,
    )
    adjusted["risk_level"] = _risk_level_from_score(adjusted["overall_risk_score"])
    return adjusted


def apply_city_strategy_to_recommendation_score(
    route: dict[str, Any],
    recommendation_score: float,
    strategy_rules: list[dict[str, Any]],
) -> float:
    city_bonus = 0.0
    for rule in _active_risk_bias_rules(strategy_rules):
        if _rule_matches_route(route, rule):
            city_bonus += float(rule["config_value"].get("city_bonus", 0.0))

    return round(recommendation_score + city_bonus, 3)


def _active_risk_bias_rules(strategy_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        rule
        for rule in strategy_rules
        if rule.get("config_type") == "risk_bias" and rule.get("status", "active") == "active"
    ]


def _rule_matches_route(route: dict[str, Any], rule: dict[str, Any]) -> bool:
    config_value = rule.get("config_value", {})
    rule_districts = set(config_value.get("district_tags", []))
    route_districts = set(route.get("district_tags", []))
    if rule_districts and rule_districts.intersection(route_districts):
        return True

    route_code = config_value.get("route_code")
    return bool(route_code and route_code == route.get("route_code"))


def _recalculate_overall(*, base_overall: float, weather_risk_delta: float, crowd_risk_delta: float) -> float:
    total = base_overall + weather_risk_delta + crowd_risk_delta
    return round(min(total, 1.0), 3)


def _risk_level_from_score(score: float) -> str:
    if score >= 0.6:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"
