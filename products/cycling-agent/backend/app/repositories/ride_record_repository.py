"""CN: 骑行记录仓库，保存、读取和列出用户骑行完成记录。
EN: Ride record repository that saves, fetches, and lists completed ride records.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from app.core.storage import connect


def save_ride_record(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_ride_record_payload(payload)

    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO ride_records (
                ride_record_no,
                entry_mode,
                source_request_no,
                ride_date,
                intent,
                plan_kind,
                route_code,
                route_title,
                destination_name,
                start_point,
                origin_region,
                completion_status,
                actual_duration_hours,
                actual_distance_km,
                effort_feeling,
                mood_after,
                notes,
                tags_json,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ride_record_no) DO UPDATE SET
                entry_mode = excluded.entry_mode,
                source_request_no = excluded.source_request_no,
                ride_date = excluded.ride_date,
                intent = excluded.intent,
                plan_kind = excluded.plan_kind,
                route_code = excluded.route_code,
                route_title = excluded.route_title,
                destination_name = excluded.destination_name,
                start_point = excluded.start_point,
                origin_region = excluded.origin_region,
                completion_status = excluded.completion_status,
                actual_duration_hours = excluded.actual_duration_hours,
                actual_distance_km = excluded.actual_distance_km,
                effort_feeling = excluded.effort_feeling,
                mood_after = excluded.mood_after,
                notes = excluded.notes,
                tags_json = excluded.tags_json,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                normalized["ride_record_no"],
                normalized["entry_mode"],
                normalized.get("source_request_no"),
                normalized["ride_date"],
                normalized.get("intent"),
                normalized.get("plan_kind"),
                normalized.get("route_code"),
                normalized.get("route_title"),
                normalized.get("destination_name"),
                normalized.get("start_point"),
                normalized.get("origin_region"),
                normalized["completion_status"],
                normalized.get("actual_duration_hours"),
                normalized.get("actual_distance_km"),
                normalized.get("effort_feeling"),
                normalized.get("mood_after"),
                normalized.get("notes"),
                json.dumps(normalized["tags"], ensure_ascii=False),
                json.dumps(normalized, ensure_ascii=False),
            ),
        )
    return normalized


def get_ride_record(database_url: str, ride_record_no: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            _ride_record_select_sql("WHERE ride_record_no = ?"),
            (ride_record_no,),
        ).fetchone()

    if row is None:
        return None
    return _hydrate_ride_record(row)


def list_ride_records(database_url: str, *, limit: int = 20) -> list[dict[str, Any]]:
    return _list_ride_records(
        database_url,
        where_clause="",
        params=(limit,),
        suffix="ORDER BY ride_date DESC, ride_record_no DESC LIMIT ?",
    )


def list_ride_records_by_date_range(
    database_url: str,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    return _list_ride_records(
        database_url,
        where_clause="WHERE ride_date >= ? AND ride_date < ?",
        params=(_normalize_date_like(start_date), _normalize_date_like(end_date)),
        suffix="ORDER BY ride_date DESC, ride_record_no DESC",
    )


def list_recent_non_cancelled_ride_records(
    database_url: str,
    *,
    before_date: date,
    lookback_days: int,
    limit: int,
) -> list[dict[str, Any]]:
    start_date = before_date - timedelta(days=lookback_days)
    return _list_ride_records(
        database_url,
        where_clause="""
            WHERE ride_date >= ?
              AND ride_date < ?
              AND completion_status != ?
        """,
        params=(
            _normalize_date_like(start_date),
            _normalize_date_like(before_date),
            "cancelled",
            limit,
        ),
        suffix="ORDER BY ride_date DESC, ride_record_no DESC LIMIT ?",
    )


def _list_ride_records(
    database_url: str,
    *,
    where_clause: str,
    params: tuple[Any, ...],
    suffix: str,
) -> list[dict[str, Any]]:
    with connect(database_url) as connection:
        rows = connection.execute(
            _ride_record_select_sql(where_clause, suffix),
            params,
        ).fetchall()

    return [_hydrate_ride_record(row) for row in rows]


def _ride_record_select_sql(where_clause: str, suffix: str = "") -> str:
    return f"""
        SELECT ride_record_no, entry_mode, source_request_no, ride_date, intent, plan_kind, route_code, route_title,
               destination_name, start_point,
               origin_region, completion_status, actual_duration_hours, actual_distance_km, effort_feeling, mood_after,
               notes, tags_json, payload_json, created_at
        FROM ride_records
        {where_clause}
        {suffix}
    """


def _hydrate_ride_record(row: dict[str, Any]) -> dict[str, Any]:
    payload_json = row["payload_json"] if "payload_json" in row.keys() else None
    created_at = row["created_at"] if "created_at" in row.keys() else None
    if payload_json and payload_json != "{}":
        return json.loads(payload_json)
    return {
        "ride_record_no": row["ride_record_no"],
        "entry_mode": _normalize_entry_mode(row["entry_mode"]),
        "source_request_no": row["source_request_no"],
        "ride_date": _normalize_ride_date(row["ride_date"], created_at),
        "intent": row["intent"],
        "plan_kind": row["plan_kind"],
        "route_code": row["route_code"],
        "route_title": row["route_title"],
        "destination_name": row["destination_name"],
        "start_point": row["start_point"],
        "origin_region": row["origin_region"],
        "completion_status": _normalize_completion_status(row["completion_status"]),
        "actual_duration_hours": row["actual_duration_hours"],
        "actual_distance_km": row["actual_distance_km"],
        "effort_feeling": _normalize_effort_feeling(row["effort_feeling"]),
        "mood_after": _normalize_mood_after(row["mood_after"]),
        "notes": row["notes"],
        "tags": _load_tags(row["tags_json"]),
    }


def _normalize_ride_record_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["ride_date"] = _normalize_date_like(normalized.get("ride_date"))
    normalized["tags"] = list(normalized.get("tags", []))
    return normalized


def _normalize_date_like(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _normalize_entry_mode(value: Any) -> str:
    return value if value in {"planned", "manual"} else "manual"


def _normalize_completion_status(value: Any) -> str:
    return value if value in {"completed", "shortened", "cancelled"} else "cancelled"


def _normalize_effort_feeling(value: Any) -> str:
    return value if value in {"easy", "steady", "hard"} else "steady"


def _normalize_mood_after(value: Any) -> str:
    return value if value in {"refreshed", "normal", "tired"} else "normal"


def _normalize_ride_date(ride_date: Any, created_at: Any) -> str:
    normalized = _normalize_date_like(ride_date)
    if isinstance(normalized, str) and normalized.strip():
        return normalized[:10]

    created = _normalize_date_like(created_at)
    if isinstance(created, str) and created.strip():
        return created[:10]

    return date.today().isoformat()


def _load_tags(value: Any) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in parsed if isinstance(item, str)]
