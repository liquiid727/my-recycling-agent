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


def get_ride_plans(database_url: str, request_nos: list[str]) -> dict[str, dict[str, Any]]:
    unique_request_nos = list(dict.fromkeys(request_nos))
    if not unique_request_nos:
        return {}

    placeholders = ",".join("?" for _ in unique_request_nos)
    with connect(database_url) as connection:
        rows = connection.execute(
            f"SELECT request_no, payload_json FROM ride_plans WHERE request_no IN ({placeholders})",
            unique_request_nos,
        ).fetchall()
    return {row["request_no"]: json.loads(row["payload_json"]) for row in rows}
