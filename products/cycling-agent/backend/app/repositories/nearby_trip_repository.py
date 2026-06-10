"""CN: Phase 2 周边目的地和周边游模板仓库，负责种子加载、后台维护和查询。
EN: Phase 2 nearby destination and trip-template repository for seeding, admin maintenance, and lookup.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.storage import connect


def load_nearby_destinations(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_trip_templates(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def seed_nearby_trip_catalog(database_url: str, destinations_path: str | Path, trips_path: str | Path) -> None:
    with connect(database_url) as connection:
        destination_count = connection.execute("SELECT COUNT(*) AS count FROM nearby_destinations").fetchone()["count"]
        trip_count = connection.execute("SELECT COUNT(*) AS count FROM trip_templates").fetchone()["count"]
    if not destination_count:
        for destination in load_nearby_destinations(destinations_path):
            save_nearby_destination(database_url, destination)
    if not trip_count:
        for trip in load_trip_templates(trips_path):
            save_trip_template(database_url, trip)


def save_nearby_destination(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["destination_no"] = normalized.get("destination_no") or f"DST-{normalized['name']}"
    normalized["status"] = normalized.get("status") or "active"
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO nearby_destinations (destination_no, city_code, region_tags_json, payload_json, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(destination_no)
            DO UPDATE SET
                city_code = excluded.city_code,
                region_tags_json = excluded.region_tags_json,
                payload_json = excluded.payload_json,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                normalized["destination_no"],
                normalized["city_code"],
                json.dumps(normalized.get("region_tags", []), ensure_ascii=False),
                json.dumps(normalized, ensure_ascii=False),
                normalized["status"],
            ),
        )
    return normalized


def save_trip_template(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["trip_no"] = normalized.get("trip_no") or f"TRIP-{normalized['route_template_id']}-{normalized['destination_no']}"
    normalized["status"] = normalized.get("status") or "active"
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO trip_templates (
                trip_no,
                city_code,
                route_template_id,
                destination_no,
                origin_region_tags_json,
                trip_style_tags_json,
                payload_json,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trip_no)
            DO UPDATE SET
                city_code = excluded.city_code,
                route_template_id = excluded.route_template_id,
                destination_no = excluded.destination_no,
                origin_region_tags_json = excluded.origin_region_tags_json,
                trip_style_tags_json = excluded.trip_style_tags_json,
                payload_json = excluded.payload_json,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                normalized["trip_no"],
                normalized["city_code"],
                normalized["route_template_id"],
                normalized["destination_no"],
                json.dumps(normalized.get("origin_region_tags", []), ensure_ascii=False),
                json.dumps(normalized.get("trip_style_tags", []), ensure_ascii=False),
                json.dumps(normalized, ensure_ascii=False),
                normalized["status"],
            ),
        )
    return normalized


def list_nearby_destinations(database_url: str, *, city_code: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT payload_json FROM nearby_destinations WHERE status = 'active'"
    params: list[Any] = []
    if city_code:
        query += " AND city_code = ?"
        params.append(city_code)
    with connect(database_url) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    return sorted([json.loads(row["payload_json"]) for row in rows], key=lambda item: item["destination_no"])


def list_trip_templates(database_url: str, *, city_code: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT payload_json FROM trip_templates WHERE status = 'active'"
    params: list[Any] = []
    if city_code:
        query += " AND city_code = ?"
        params.append(city_code)
    with connect(database_url) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    return sorted([json.loads(row["payload_json"]) for row in rows], key=lambda item: item["trip_no"])

