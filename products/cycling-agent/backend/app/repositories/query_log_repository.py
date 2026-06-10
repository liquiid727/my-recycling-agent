"""CN: 查询日志仓库，记录最近规划输入、解析约束和命中状态供后台查看。
EN: Query log repository for recent planning inputs, parsed constraints, and match status in admin views.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.storage import connect


def save_query_log(
    database_url: str,
    *,
    request_no: str,
    query: str,
    target_date: str,
    parsed_constraints: dict[str, Any],
    recommended_route_name: str,
    fallback_reason: list[str],
) -> None:
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO query_logs (
                request_no,
                query,
                target_date,
                parsed_constraints_json,
                recommended_route_name,
                fallback_reason_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_no) DO UPDATE SET
                query = excluded.query,
                target_date = excluded.target_date,
                parsed_constraints_json = excluded.parsed_constraints_json,
                recommended_route_name = excluded.recommended_route_name,
                fallback_reason_json = excluded.fallback_reason_json
            """,
            (
                request_no,
                query,
                target_date,
                json.dumps(parsed_constraints, ensure_ascii=False),
                recommended_route_name,
                json.dumps(fallback_reason, ensure_ascii=False),
            ),
        )


def list_query_logs(database_url: str, *, limit: int = 20) -> list[dict[str, Any]]:
    with connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT request_no, query, target_date, parsed_constraints_json, recommended_route_name, fallback_reason_json, created_at
            FROM query_logs
            ORDER BY created_at DESC, request_no DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "request_no": row["request_no"],
            "query": row["query"],
            "target_date": row["target_date"],
            "parsed_constraints": json.loads(row["parsed_constraints_json"]),
            "recommended_route_name": row["recommended_route_name"],
            "fallback_reason": json.loads(row["fallback_reason_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
