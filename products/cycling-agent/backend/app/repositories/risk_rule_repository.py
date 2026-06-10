"""CN: 风险规则仓库，维护可配置的天气、爬升、交通、补给、返程和人流风险规则。
EN: Risk rule repository for configurable weather, climb, traffic, supply, return, and crowd rules.
"""

from __future__ import annotations

from typing import Any

from app.repositories.city_strategy_repository import (
    list_city_strategy_configs,
    save_city_strategy_config,
)


RISK_RULE_CONFIG_TYPE = "risk_rule"


def save_risk_rule(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    saved = save_city_strategy_config(
        database_url,
        {
            "city_code": payload["city_code"],
            "config_type": RISK_RULE_CONFIG_TYPE,
            "config_key": payload["rule_key"],
            "config_value": payload["rule_value"],
            "status": payload["status"],
        },
    )
    return {
        **payload,
        "entity_id": saved.get("entity_id"),
        "config_no": saved.get("config_no"),
    }


def list_risk_rules(database_url: str, city_code: str | None = None) -> list[dict[str, Any]]:
    return [
        {
            "entity_id": item.get("entity_id"),
            "config_no": item.get("config_no"),
            "city_code": item["city_code"],
            "rule_key": item["config_key"],
            "rule_value": item["config_value"],
            "status": item["status"],
        }
        for item in list_city_strategy_configs(database_url, city_code=city_code)
        if item["config_type"] == RISK_RULE_CONFIG_TYPE
    ]


def list_active_risk_rules(database_url: str, city_code: str) -> list[dict[str, Any]]:
    return [item for item in list_risk_rules(database_url, city_code=city_code) if item["status"] == "active"]
