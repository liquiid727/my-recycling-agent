"""CN: 月度骑行总结事件仓库，记录请求、非法月份和 CTA 点击等轻量观测事件。
EN: Ride monthly summary event repository for lightweight observability signals.
"""

from __future__ import annotations

from typing import Any

from app.core.storage import connect


def save_ride_monthly_summary_event(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_event_payload(payload)
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO ride_monthly_summary_events (
                event_no,
                event_type,
                requested_month,
                requested_window_days,
                suggested_scene,
                is_empty_summary,
                is_zero_growth_review,
                has_planned_rides,
                habit_status,
                growth_status,
                has_milestones,
                next_action_key,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_no) DO UPDATE SET
                event_type = excluded.event_type,
                requested_month = excluded.requested_month,
                requested_window_days = excluded.requested_window_days,
                suggested_scene = excluded.suggested_scene,
                is_empty_summary = excluded.is_empty_summary,
                is_zero_growth_review = excluded.is_zero_growth_review,
                has_planned_rides = excluded.has_planned_rides,
                habit_status = excluded.habit_status,
                growth_status = excluded.growth_status,
                has_milestones = excluded.has_milestones,
                next_action_key = excluded.next_action_key,
                source = excluded.source
            """,
            (
                normalized["event_no"],
                normalized["event_type"],
                normalized.get("requested_month"),
                normalized.get("requested_window_days"),
                normalized.get("suggested_scene"),
                normalized.get("is_empty_summary"),
                normalized.get("is_zero_growth_review"),
                normalized.get("has_planned_rides"),
                normalized.get("habit_status"),
                normalized.get("growth_status"),
                normalized.get("has_milestones"),
                normalized.get("next_action_key"),
                normalized["source"],
            ),
        )
    return normalized


def list_ride_monthly_summary_events(database_url: str, *, limit: int = 50) -> list[dict[str, Any]]:
    with connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT event_no, event_type, requested_month, requested_window_days, suggested_scene,
                   is_empty_summary, is_zero_growth_review, has_planned_rides, habit_status,
                   growth_status, has_milestones, next_action_key, source, created_at
            FROM ride_monthly_summary_events
            ORDER BY created_at DESC, event_no DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "event_no": row["event_no"],
            "event_type": row["event_type"],
            "requested_month": row["requested_month"],
            "requested_window_days": row["requested_window_days"],
            "suggested_scene": row["suggested_scene"],
            "is_empty_summary": _normalize_optional_bool(row["is_empty_summary"]),
            "is_zero_growth_review": _normalize_optional_bool(row["is_zero_growth_review"]),
            "has_planned_rides": _normalize_optional_bool(row["has_planned_rides"]),
            "habit_status": row["habit_status"],
            "growth_status": row["growth_status"],
            "has_milestones": _normalize_optional_bool(row["has_milestones"]),
            "next_action_key": row["next_action_key"],
            "source": row["source"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _normalize_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_no": str(payload["event_no"]),
        "event_type": str(payload["event_type"]),
        "requested_month": _normalize_optional_str(payload.get("requested_month")),
        "requested_window_days": _normalize_optional_int(payload.get("requested_window_days")),
        "suggested_scene": _normalize_optional_str(payload.get("suggested_scene")),
        "is_empty_summary": _normalize_optional_bool(payload.get("is_empty_summary")),
        "is_zero_growth_review": _normalize_optional_bool(payload.get("is_zero_growth_review")),
        "has_planned_rides": _normalize_optional_bool(payload.get("has_planned_rides")),
        "habit_status": _normalize_optional_str(payload.get("habit_status")),
        "growth_status": _normalize_optional_str(payload.get("growth_status")),
        "has_milestones": _normalize_optional_bool(payload.get("has_milestones")),
        "next_action_key": _normalize_optional_str(payload.get("next_action_key")),
        "source": str(payload["source"]),
    }


def _normalize_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _normalize_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def _normalize_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None
