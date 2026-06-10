"""CN: 路线模板仓库，加载种子路线并提供模板增删改查与筛选。
EN: Route template repository that seeds route data and provides template upsert, listing, and lookup.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.ids import generate_business_no, generate_uuid_v7_like
from app.core.storage import connect

def load_route_templates(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def seed_route_templates(database_url: str, path: str | Path) -> None:
    routes = load_route_templates(path)
    with connect(database_url) as connection:
        existing_count = connection.execute("SELECT COUNT(*) AS count FROM route_templates").fetchone()["count"]
    if existing_count:
        for route in list_route_templates(database_url):
            if route.get("id") and route.get("route_no"):
                continue
            save_route_template(database_url, route)
        return
    for route in routes:
        save_route_template(database_url, route)


def save_route_template(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = dict(payload)
    with connect(database_url) as connection:
        existing = connection.execute(
            """
            SELECT id, route_no, status, route_source
            FROM route_templates
            WHERE route_code = ?
            """,
            (payload["route_code"],),
        ).fetchone()
        existing_id = existing["id"] if existing else None
        existing_route_no = existing["route_no"] if existing else None
        existing_status = existing["status"] if existing else None
        existing_route_source = existing["route_source"] if existing else None
        normalized_payload["id"] = normalized_payload.get("id") or existing_id or generate_uuid_v7_like()
        normalized_payload["route_no"] = normalized_payload.get("route_no") or existing_route_no or generate_business_no("RT")
        normalized_payload["status"] = normalized_payload.get("status") or existing_status or "active"
        normalized_payload["route_source"] = normalized_payload.get("route_source") or existing_route_source or "seed"
        connection.execute(
            """
            INSERT INTO route_templates (id, route_no, route_code, city_code, district_tags_json, ride_style_tags_json, payload_json, status, route_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(route_code)
            DO UPDATE SET
                id = excluded.id,
                route_no = excluded.route_no,
                city_code = excluded.city_code,
                district_tags_json = excluded.district_tags_json,
                ride_style_tags_json = excluded.ride_style_tags_json,
                payload_json = excluded.payload_json,
                status = excluded.status,
                route_source = excluded.route_source,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                normalized_payload["id"],
                normalized_payload["route_no"],
                normalized_payload["route_code"],
                normalized_payload["city_code"],
                json.dumps(normalized_payload.get("district_tags", []), ensure_ascii=False),
                json.dumps(normalized_payload.get("ride_style_tags", []), ensure_ascii=False),
                json.dumps(normalized_payload, ensure_ascii=False),
                normalized_payload["status"],
                normalized_payload["route_source"],
            ),
        )
    return normalized_payload


def list_route_templates(
    database_url: str,
    *,
    city_code: str | None = None,
    origin_region: str | None = None,
    ride_style: str | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT payload_json FROM route_templates
        WHERE 1 = 1
    """
    params: list[Any] = []
    if city_code is not None:
        query += " AND city_code = ?"
        params.append(city_code)
    if origin_region:
        query += " AND district_tags_json LIKE ?"
        params.append(f"%{origin_region}%")

    with connect(database_url) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()

    routes = [json.loads(row["payload_json"]) for row in rows]
    if not ride_style:
        return sorted(routes, key=lambda item: item["route_code"])

    requested_tags = set(_normalize_ride_style(ride_style))
    matched_routes = [
        route for route in routes if requested_tags.issubset(set(route.get("ride_style_tags", [])))
    ]
    return sorted(matched_routes, key=lambda item: item["route_code"])


def get_route_template(database_url: str, route_code: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            "SELECT payload_json FROM route_templates WHERE route_code = ?",
            (route_code,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


def _normalize_ride_style(ride_style: str) -> list[str]:
    if ride_style == "scenic_relaxed":
        return ["scenic", "relaxed"]
    if ride_style == "training_loop":
        return ["training", "loop"]
    return [ride_style]
