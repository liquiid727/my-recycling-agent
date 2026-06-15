"""CN: 月度骑行总结服务，按规则聚合骑行记录并生成结构化习惯反馈。
EN: Rule-first monthly ride summary service built from ride records and linked plans.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from app.schemas.ride_plan import RIDE_MONTHLY_SUMMARY_MONTH_PATTERN
from app.services.ride_summary_service import build_ride_summary


STARTING_GAP_DAYS = 14
REBUILDING_RIDE_DAY_THRESHOLD = 3


def build_ride_monthly_summary(
    *,
    month: str,
    monthly_records: list[dict[str, Any]],
    recent_non_cancelled_records: list[dict[str, Any]],
    streak_non_cancelled_records: list[dict[str, Any]] | None = None,
    source_plans_by_request_no: dict[str, dict[str, Any]],
    today: str | date | None = None,
) -> dict[str, Any]:
    period_start = parse_ride_month(month)
    period_end = _month_end(period_start)
    current_day = _coerce_date(today) if today is not None else date.today()
    reference_day = min(current_day, period_end)
    effective_monthly_records = [
        record
        for record in monthly_records
        if record.get("ride_date") and _coerce_date(record.get("ride_date")) <= reference_day
    ]
    recent_window_records = [
        record
        for record in recent_non_cancelled_records
        if record.get("completion_status") != "cancelled"
        and record.get("ride_date")
        and _coerce_date(record.get("ride_date")) <= reference_day
    ]
    streak_records_source = streak_non_cancelled_records if streak_non_cancelled_records is not None else recent_window_records
    streak_records = [
        record
        for record in streak_records_source
        if record.get("completion_status") != "cancelled"
        and record.get("ride_date")
        and _coerce_date(record.get("ride_date")) <= reference_day
    ]

    non_cancelled_records = [record for record in effective_monthly_records if record.get("completion_status") != "cancelled"]
    ride_dates = {_coerce_date(record.get("ride_date")) for record in non_cancelled_records if record.get("ride_date")}
    completed_count = sum(1 for record in effective_monthly_records if record.get("completion_status") == "completed")
    shortened_count = sum(1 for record in effective_monthly_records if record.get("completion_status") == "shortened")
    cancelled_count = sum(1 for record in effective_monthly_records if record.get("completion_status") == "cancelled")
    last_ride_date = _latest_ride_date(non_cancelled_records)
    days_since_last_ride = None if last_ride_date is None else max((reference_day - last_ride_date).days, 0)
    hard_effort_count = sum(1 for record in non_cancelled_records if record.get("effort_feeling") == "hard")
    tired_mood_count = sum(1 for record in non_cancelled_records if record.get("mood_after") == "tired")
    matched_plan_count = _matched_plan_count(non_cancelled_records, source_plans_by_request_no)
    ride_day_count = len(ride_dates)
    habit_status = _habit_status(
        ride_day_count=ride_day_count,
        days_since_last_ride=days_since_last_ride,
        recent_non_cancelled_records=recent_window_records,
    )

    return {
        "month": month,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "ride_count": len(effective_monthly_records),
        "ride_day_count": ride_day_count,
        "completed_count": completed_count,
        "shortened_count": shortened_count,
        "cancelled_count": cancelled_count,
        "total_distance_km": round(
            sum(_float_or_zero(record.get("actual_distance_km")) for record in non_cancelled_records),
            1,
        ),
        "total_duration_hours": round(
            sum(_float_or_zero(record.get("actual_duration_hours")) for record in non_cancelled_records),
            1,
        ),
        "planned_count": sum(1 for record in effective_monthly_records if record.get("entry_mode") == "planned"),
        "manual_count": sum(1 for record in effective_monthly_records if record.get("entry_mode") == "manual"),
        "last_ride_date": None if last_ride_date is None else last_ride_date.isoformat(),
        "days_since_last_ride": days_since_last_ride,
        "weekly_streak": _weekly_streak(streak_records, reference_day),
        "habit_status": habit_status,
        "next_action": _next_action(habit_status),
        "summary_headline": _summary_headline(habit_status, ride_day_count),
        "summary_body": _summary_body(
            ride_count=len(effective_monthly_records),
            days_since_last_ride=days_since_last_ride,
            habit_status=habit_status,
            total_distance_km=round(
                sum(_float_or_zero(record.get("actual_distance_km")) for record in non_cancelled_records),
                1,
            ),
        ),
        "top_start_region": _counter_winner(record.get("origin_region") for record in non_cancelled_records),
        "top_tag": _counter_winner(tag for record in non_cancelled_records for tag in record.get("tags", [])),
        "hard_effort_count": hard_effort_count,
        "tired_mood_count": tired_mood_count,
        "matched_plan_count": matched_plan_count,
        "month_to_date": period_start <= current_day <= period_end,
        "recent_30d_ride_count": len(recent_window_records),
    }


def parse_ride_month(month: str) -> date:
    if not re.fullmatch(RIDE_MONTHLY_SUMMARY_MONTH_PATTERN, month):
        raise ValueError("invalid-month-format")
    try:
        return date.fromisoformat(f"{month}-01")
    except ValueError as exc:
        raise ValueError("invalid-month-format") from exc


def _month_end(period_start: date) -> date:
    if period_start.month == 12:
        next_month = date(period_start.year + 1, 1, 1)
    else:
        next_month = date(period_start.year, period_start.month + 1, 1)
    return next_month - timedelta(days=1)


def _coerce_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        raise ValueError("ride-date-missing")
    return date.fromisoformat(str(value)[:10])


def _float_or_zero(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def _latest_ride_date(records: list[dict[str, Any]]) -> date | None:
    if not records:
        return None
    return max(_coerce_date(record.get("ride_date")) for record in records if record.get("ride_date"))


def _matched_plan_count(
    records: list[dict[str, Any]],
    source_plans_by_request_no: dict[str, dict[str, Any]],
) -> int:
    matched_count = 0
    for record in records:
        request_no = record.get("source_request_no")
        if not request_no:
            continue
        source_plan = source_plans_by_request_no.get(str(request_no))
        if not source_plan:
            continue
        summary = build_ride_summary(record, source_plan=source_plan)
        if summary.get("plan_alignment") == "matched-core-plan":
            matched_count += 1
    return matched_count


def _habit_status(
    *,
    ride_day_count: int,
    days_since_last_ride: int | None,
    recent_non_cancelled_records: list[dict[str, Any]],
) -> str:
    if ride_day_count == 0 or days_since_last_ride is None or days_since_last_ride >= STARTING_GAP_DAYS:
        return "starting"
    last_two = sorted(
        (
            record
            for record in recent_non_cancelled_records
            if record.get("ride_date")
        ),
        key=lambda record: _coerce_date(record.get("ride_date")),
        reverse=True,
    )[:2]
    if len(last_two) == 2 and all(
        record.get("effort_feeling") == "hard" or record.get("mood_after") == "tired"
        for record in last_two
    ):
        return "overreaching"
    if ride_day_count < REBUILDING_RIDE_DAY_THRESHOLD:
        return "rebuilding"
    return "steady"


def _next_action(habit_status: str) -> dict[str, Any]:
    mapping = {
        "starting": {
            "action_key": "resume_with_short_ride",
            "title": "先把下一次出门门槛降下来。",
            "body": "先安排一次短而轻松的城市骑，把节奏重新接上。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。",
        },
        "rebuilding": {
            "action_key": "schedule_easy_city_ride",
            "title": "这周再补一趟轻松骑会更稳。",
            "body": "你已经在恢复节奏了，再补一次低压力短骑最合适。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周再安排一次 2 小时内、不追强度的轻松骑。",
        },
        "steady": {
            "action_key": "maintain_weekly_rhythm",
            "title": "这周再补一趟轻松骑就能把节奏续上。",
            "body": "你最近的骑行频率比较稳，下一次继续安排一趟不追强度的城市骑就够了。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。",
        },
        "overreaching": {
            "action_key": "take_recovery_window",
            "title": "先把恢复放在前面。",
            "body": "最近两次骑行的体感偏顶，下一次更适合恢复骑或直接休息。",
            "suggested_scene": "city_ride",
            "suggested_entry": "明天不追强度，只安排一次轻松恢复骑，或者直接休息。",
        },
    }
    return mapping[habit_status]


def _summary_headline(habit_status: str, ride_day_count: int) -> str:
    if ride_day_count == 0:
        return "这个月还没把骑行重新接起来。"
    return {
        "starting": "现在最重要的是把下一次轻松出门接上。",
        "rebuilding": "你已经在把骑行节奏慢慢找回来了。",
        "steady": "这个月你已经把骑行节奏续起来了。",
        "overreaching": "这个月有输出，但恢复要跟上。",
    }[habit_status]


def _summary_body(
    *,
    ride_count: int,
    days_since_last_ride: int | None,
    habit_status: str,
    total_distance_km: float,
) -> str:
    if ride_count == 0:
        return "这个月还没有实际骑行记录，下一次先安排一趟容易出门的短骑就够了。"
    recency_text = "最近还没有实际完成的骑行" if days_since_last_ride is None else f"最近一次距离参考日 {days_since_last_ride} 天"
    habit_copy = {
        "starting": "当前节奏还没稳定下来",
        "rebuilding": "说明你已经在恢复骑行习惯",
        "steady": "整体节奏比较稳定",
        "overreaching": "不过最近输出偏顶，恢复要更主动",
    }[habit_status]
    return f"本月累计 {ride_count} 条记录、{total_distance_km:.1f} km，{habit_copy}，{recency_text}。"


def _counter_winner(values: Any) -> str | None:
    counter = Counter(str(value) for value in values if value)
    return counter.most_common(1)[0][0] if counter else None


def _weekly_streak(records: list[dict[str, Any]], reference_day: date) -> int:
    if not records:
        return 0
    record_dates = sorted(
        (_coerce_date(record.get("ride_date")) for record in records if record.get("ride_date")),
        reverse=True,
    )
    anchor_day = next((record_date for record_date in record_dates if record_date <= reference_day), None)
    if anchor_day is None:
        return 0
    year_weeks = {record_date.isocalendar()[:2] for record_date in record_dates}
    streak = 0
    cursor = anchor_day
    while True:
        if cursor.isocalendar()[:2] not in year_weeks:
            return streak
        streak += 1
        cursor -= timedelta(days=7)
