"""CN: 城市策略仓库，持久化杭州本地风险偏置和推荐排序偏置规则。
EN: City strategy repository for Hangzhou-specific risk bias and ranking bonus rules.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.ids import generate_business_no, generate_uuid_v7_like
from app.core.storage import connect


def save_city_strategy_config(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = dict(payload)
    with connect(database_url) as connection:
        existing = connection.execute(
            """
            SELECT entity_id, config_no
            FROM city_strategy_configs
            WHERE city_code = ? AND config_type = ? AND config_key = ?
            """,
            (
                payload["city_code"],
                payload["config_type"],
                payload["config_key"],
            ),
        ).fetchone()
        existing_entity_id = existing["entity_id"] if existing else None
        existing_config_no = existing["config_no"] if existing else None
        normalized_payload["entity_id"] = (
            normalized_payload.get("entity_id") or existing_entity_id or generate_uuid_v7_like()
        )
        normalized_payload["config_no"] = (
            normalized_payload.get("config_no") or existing_config_no or generate_business_no("CF")
        )
        connection.execute(
            """
            INSERT INTO city_strategy_configs (entity_id, config_no, city_code, config_type, config_key, config_value_json, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city_code, config_type, config_key)
            DO UPDATE SET
                entity_id = excluded.entity_id,
                config_no = excluded.config_no,
                config_value_json = excluded.config_value_json,
                status = excluded.status
            """,
            (
                normalized_payload["entity_id"],
                normalized_payload["config_no"],
                normalized_payload["city_code"],
                normalized_payload["config_type"],
                normalized_payload["config_key"],
                json.dumps(normalized_payload["config_value"], ensure_ascii=False),
                normalized_payload["status"],
            ),
        )
    return normalized_payload


def list_city_strategy_configs(database_url: str, city_code: str | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT entity_id, config_no, city_code, config_type, config_key, config_value_json, status
        FROM city_strategy_configs
    """
    params: tuple[Any, ...] = ()
    if city_code:
        query += " WHERE city_code = ?"
        params = (city_code,)
    query += " ORDER BY city_code, config_type, config_key"

    with connect(database_url) as connection:
        rows = connection.execute(query, params).fetchall()

    items = [
        {
            "entity_id": row["entity_id"],
            "config_no": row["config_no"],
            "city_code": row["city_code"],
            "config_type": row["config_type"],
            "config_key": row["config_key"],
            "config_value": json.loads(row["config_value_json"]),
            "status": row["status"],
        }
        for row in rows
    ]
    normalized_items: list[dict[str, Any]] = []
    for item in items:
        if item.get("entity_id") and item.get("config_no"):
            normalized_items.append(item)
            continue
        normalized_items.append(save_city_strategy_config(database_url, item))
    return normalized_items


def list_active_city_strategy_configs(database_url: str, city_code: str) -> list[dict[str, Any]]:
    return [
        item
        for item in list_city_strategy_configs(database_url, city_code=city_code)
        if item["status"] == "active" and item["config_type"] != "risk_rule"
    ]
