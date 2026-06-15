"""CN: 骑行记录仓库，保存、读取和列出用户骑行完成记录。
EN: Ride record repository that saves, fetches, and lists completed ride records.
"""

from __future__ import annotations

import json
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
            """
            SELECT ride_record_no, entry_mode, source_request_no, ride_date, intent, plan_kind, route_code, route_title,
                   destination_name, start_point,
                   origin_region, completion_status, actual_duration_hours, actual_distance_km, effort_feeling, mood_after,
                   notes, tags_json, payload_json
            FROM ride_records
            WHERE ride_record_no = ?
            """,
            (ride_record_no,),
        ).fetchone()

    if row is None:
        return None
    return _hydrate_ride_record(row)


def list_ride_records(database_url: str, *, limit: int = 20) -> list[dict[str, Any]]:
    with connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT ride_record_no, entry_mode, source_request_no, ride_date, intent, plan_kind, route_code, route_title,
                   destination_name, start_point,
                   origin_region, completion_status, actual_duration_hours, actual_distance_km, effort_feeling, mood_after,
                   notes, tags_json, payload_json
            FROM ride_records
            ORDER BY ride_date DESC, ride_record_no DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [_hydrate_ride_record(row) for row in rows]


def _hydrate_ride_record(row: dict[str, Any]) -> dict[str, Any]:
    payload_json = row["payload_json"] if "payload_json" in row.keys() else None
    if payload_json and payload_json != "{}":
        return json.loads(payload_json)
    return {
        "ride_record_no": row["ride_record_no"],
        "entry_mode": row["entry_mode"],
        "source_request_no": row["source_request_no"],
        "ride_date": row["ride_date"],
        "intent": row["intent"],
        "plan_kind": row["plan_kind"],
        "route_code": row["route_code"],
        "route_title": row["route_title"],
        "destination_name": row["destination_name"],
        "start_point": row["start_point"],
        "origin_region": row["origin_region"],
        "completion_status": row["completion_status"],
        "actual_duration_hours": row["actual_duration_hours"],
        "actual_distance_km": row["actual_distance_km"],
        "effort_feeling": row["effort_feeling"],
        "mood_after": row["mood_after"],
        "notes": row["notes"],
        "tags": json.loads(row["tags_json"]),
        "payload": {},
    }


def _normalize_ride_record_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["ride_date"] = _normalize_date_like(normalized.get("ride_date"))
    normalized["tags"] = list(normalized.get("tags", []))
    normalized["payload"] = dict(normalized.get("payload", {}))
    return normalized


def _normalize_date_like(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
