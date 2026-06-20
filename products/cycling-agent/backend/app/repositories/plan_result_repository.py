"""CN: 规划结果仓库，按 request_no 保存和读取完整规划响应。
EN: Plan result repository that saves and loads full planning responses by request_no.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.storage import connect


def save_ride_plan(database_url: str, payload: dict[str, Any]) -> None:
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO ride_plans (request_no, payload_json)
            VALUES (?, ?)
            ON CONFLICT(request_no) DO UPDATE SET payload_json = excluded.payload_json
            """,
            (payload["request_no"], json.dumps(payload, ensure_ascii=False)),
        )


def get_ride_plan(database_url: str, request_no: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            "SELECT payload_json FROM ride_plans WHERE request_no = ?",
            (request_no,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


def find_route_snapshot(database_url: str, route_code: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        rows = connection.execute("SELECT payload_json FROM ride_plans ORDER BY created_at DESC").fetchall()
    for row in rows:
        payload = json.loads(row["payload_json"])
        recommended = payload.get("recommended_plan") or {}
        if recommended.get("route_code") == route_code:
            return {
                "route_code": recommended["route_code"],
                "route_name": recommended["route_name"],
                "distance_km": recommended["distance_km"],
                "estimated_duration_hours": recommended["estimated_duration_hours"],
                "summary": recommended.get("summary_reason") or "来自已生成计划的动态路线。",
                "tags": [recommended.get("risk_level") or "light"],
                "supply_points": (payload.get("route_map") or {}).get("supply_points", []),
                "bailout_options": (payload.get("route_map") or {}).get("bailout_options", []),
            }
    return None
