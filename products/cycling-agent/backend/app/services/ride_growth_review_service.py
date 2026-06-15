"""CN: 增长回顾服务，按滚动窗口聚合骑行记录并生成低压力的进展反馈。
EN: Rolling-window ride growth review service built from ride records.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from app.services.ride_summary_service import build_ride_summary


SUPPORTED_GROWTH_WINDOWS = {30, 90, 180}
RESETTING_GAP_DAYS = 21
BUILDING_RIDE_DAY_THRESHOLD = 3


def parse_growth_window_days(window_days: int | str) -> int:
    try:
        normalized = int(window_days)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid-window-days") from exc
    if normalized not in SUPPORTED_GROWTH_WINDOWS:
        raise ValueError("invalid-window-days")
    return normalized


def build_ride_growth_review(
    *,
    window_days: int | str,
    window_records: list[dict[str, Any]],
    source_plans_by_request_no: dict[str, dict[str, Any]],
    today: str | date | None = None,
) -> dict[str, Any]:
    normalized_window_days = parse_growth_window_days(window_days)
    current_day = _coerce_date(today) if today is not None else date.today()
    period_end = current_day
    period_start = current_day - timedelta(days=normalized_window_days - 1)
    effective_window_records = [
        record
        for record in window_records
        if record.get("ride_date") and period_start <= _coerce_date(record.get("ride_date")) <= period_end
    ]
    realized_records = [
        record
        for record in effective_window_records
        if record.get("completion_status") != "cancelled"
    ]
    ride_dates = sorted({_coerce_date(record.get("ride_date")) for record in realized_records if record.get("ride_date")})
    last_ride_date = ride_dates[-1] if ride_dates else None
    days_since_last_ride = None if last_ride_date is None else max((period_end - last_ride_date).days, 0)

    recent_slice_start = max(period_start, period_end - timedelta(days=29))
    recent_records = [
        record for record in realized_records if _coerce_date(record.get("ride_date")) >= recent_slice_start
    ]
    previous_records = [
        record for record in realized_records if _coerce_date(record.get("ride_date")) < recent_slice_start
    ]
    recent_ride_count = len(recent_records)
    previous_ride_count = len(previous_records)
    recent_distance = round(sum(_float_or_zero(record.get("actual_distance_km")) for record in recent_records), 1)
    previous_distance = round(sum(_float_or_zero(record.get("actual_distance_km")) for record in previous_records), 1)
    best_weekly_streak = _best_weekly_streak(realized_records)
    growth_status = _growth_status(
        ride_count=len(realized_records),
        ride_day_count=len(ride_dates),
        days_since_last_ride=days_since_last_ride,
        recent_ride_count=recent_ride_count,
        previous_ride_count=previous_ride_count,
        recent_distance=recent_distance,
        previous_distance=previous_distance,
    )
    next_focus = _next_focus(growth_status)

    return {
        "window_days": normalized_window_days,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "ride_count": len(realized_records),
        "ride_day_count": len(ride_dates),
        "completed_count": sum(1 for record in realized_records if record.get("completion_status") == "completed"),
        "total_distance_km": round(sum(_float_or_zero(record.get("actual_distance_km")) for record in realized_records), 1),
        "total_duration_hours": round(sum(_float_or_zero(record.get("actual_duration_hours")) for record in realized_records), 1),
        "longest_distance_km": round(max((_float_or_zero(record.get("actual_distance_km")) for record in realized_records), default=0.0), 1),
        "longest_duration_hours": round(max((_float_or_zero(record.get("actual_duration_hours")) for record in realized_records), default=0.0), 1),
        "active_month_count": len({str(record.get("ride_date"))[:7] for record in realized_records if record.get("ride_date")}),
        "best_weekly_streak": best_weekly_streak,
        "growth_status": growth_status,
        "review_headline": _review_headline(growth_status, ride_count=len(realized_records)),
        "review_body": _review_body(
            growth_status=growth_status,
            recent_ride_count=recent_ride_count,
            previous_ride_count=previous_ride_count,
            recent_distance=recent_distance,
            previous_distance=previous_distance,
        ),
        "next_focus": next_focus,
        "milestones": _build_milestones(realized_records, best_weekly_streak),
        "planned_count": sum(1 for record in realized_records if record.get("entry_mode") == "planned"),
        "manual_count": sum(1 for record in realized_records if record.get("entry_mode") == "manual"),
        "matched_plan_count": _matched_plan_count(realized_records, source_plans_by_request_no),
        "top_start_region": _counter_winner(record.get("origin_region") for record in realized_records),
        "top_tag": _counter_winner(tag for record in realized_records for tag in record.get("tags", [])),
        "recent_vs_previous_ride_delta": recent_ride_count - previous_ride_count,
        "recent_vs_previous_distance_delta_km": round(recent_distance - previous_distance, 1),
    }


def _growth_status(
    *,
    ride_count: int,
    ride_day_count: int,
    days_since_last_ride: int | None,
    recent_ride_count: int,
    previous_ride_count: int,
    recent_distance: float,
    previous_distance: float,
) -> str:
    if ride_count == 0:
        return "building"
    if days_since_last_ride is not None and days_since_last_ride >= RESETTING_GAP_DAYS:
        return "resetting"
    if ride_day_count < BUILDING_RIDE_DAY_THRESHOLD:
        return "building"
    if recent_ride_count >= previous_ride_count + 2 or recent_distance >= previous_distance + 40:
        return "expanding"
    return "steady"


def _next_focus(growth_status: str) -> dict[str, Any]:
    mapping = {
        "building": {
            "action_key": "resume_with_short_ride",
            "title": "先恢复下一次出门",
            "body": "这周先接上一条容易执行的短骑，把频率重新找回来。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周找个傍晚，先安排一趟 1 到 2 小时的轻松骑。",
        },
        "steady": {
            "action_key": "maintain_weekly_rhythm",
            "title": "按现在的节奏继续",
            "body": "现在最重要的是把每周至少一次的出门节奏续住，不需要额外放大强度。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周继续安排一次 2 小时左右的轻松骑。",
        },
        "expanding": {
            "action_key": "maintain_weekly_rhythm",
            "title": "按这个方向继续安排",
            "body": "下一次可以把周末半天骑继续保留住，不用再额外追强度。",
            "suggested_scene": "weekend_trip",
            "suggested_entry": "这个周末安排一次 3 到 4 小时、带一点爬升的半天骑。",
        },
        "resetting": {
            "action_key": "resume_with_short_ride",
            "title": "先把节奏重新接上",
            "body": "前面已经有过输出，现在先恢复一条容易执行的短骑，比直接放大计划更合适。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周先安排一次 1 到 2 小时、不追强度的恢复骑。",
        },
    }
    return mapping[growth_status]


def _review_headline(growth_status: str, *, ride_count: int) -> str:
    if ride_count == 0:
        return "最近这段时间还没有形成新的骑行节奏。"
    return {
        "building": "最近又开始把骑行接回来了。",
        "steady": "这段时间的骑行节奏基本稳住了。",
        "expanding": "最近这段时间，你的骑行范围已经明显打开了。",
        "resetting": "前面有过输出，但最近这段时间需要重新接回节奏。",
    }[growth_status]


def _review_body(
    *,
    growth_status: str,
    recent_ride_count: int,
    previous_ride_count: int,
    recent_distance: float,
    previous_distance: float,
) -> str:
    if growth_status == "building":
        return "先把下一次轻松出门接上，比看更大的统计更重要。"
    if growth_status == "steady":
        return "近 30 天和前一段的骑行次数差不多，说明现在的频率已经比较稳。"
    if growth_status == "expanding":
        return (
            f"近 30 天的骑行次数和距离都比前一段更高，"
            f"最近 {recent_ride_count} 次对比前一段 {previous_ride_count} 次，"
            f"距离多了 {recent_distance - previous_distance:.1f} km。"
        )
    return "最近 21 天没有新的实际骑行，下一步更适合先把低门槛的节奏接回来。"


def _build_milestones(records: list[dict[str, Any]], best_weekly_streak: int) -> list[dict[str, str]]:
    if not records:
        return []

    milestones: list[dict[str, str]] = []
    completed_records = [record for record in records if record.get("completion_status") == "completed"]
    if completed_records:
        first_completed = min(_coerce_date(record.get("ride_date")) for record in completed_records)
        milestones.append(
            {
                "milestone_key": "first_completed_ride",
                "title": f"本窗口最早完成骑行在 {first_completed.isoformat()}",
                "body": "说明这段时间里已经留下了真实完成的骑行落点。",
            }
        )

    longest_distance = max((_float_or_zero(record.get("actual_distance_km")) for record in records), default=0.0)
    if longest_distance > 0:
        milestones.append(
            {
                "milestone_key": "longest_distance",
                "title": f"最长距离刷新到 {longest_distance:.0f} km",
                "body": "说明你已经能把更完整的一次骑行稳定收下来。",
            }
        )

    longest_duration = max((_float_or_zero(record.get("actual_duration_hours")) for record in records), default=0.0)
    if longest_duration > 0:
        milestones.append(
            {
                "milestone_key": "longest_duration",
                "title": f"最长时长来到 {longest_duration:.1f} h",
                "body": "耐受更长时间在路上的能力已经在形成。",
            }
        )

    if best_weekly_streak > 1:
        milestones.append(
            {
                "milestone_key": "best_streak",
                "title": f"连续周骑行来到 {best_weekly_streak} 周",
                "body": "最近几周的骑行频率已经开始稳定。",
            }
        )

    month_counter = Counter(str(record.get("ride_date"))[:7] for record in records if record.get("ride_date"))
    if month_counter:
        most_active_month, ride_count = month_counter.most_common(1)[0]
        milestones.append(
            {
                "milestone_key": "most_active_month",
                "title": f"{most_active_month} 是最近最活跃的月份",
                "body": f"这个月一共留下了 {ride_count} 条实际骑行记录。",
            }
        )
    return milestones


def _matched_plan_count(records: list[dict[str, Any]], source_plans_by_request_no: dict[str, dict[str, Any]]) -> int:
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


def _best_weekly_streak(records: list[dict[str, Any]]) -> int:
    week_starts = sorted({_week_start(_coerce_date(record.get("ride_date"))) for record in records if record.get("ride_date")})
    if not week_starts:
        return 0
    longest = 1
    current = 1
    for index in range(1, len(week_starts)):
        if week_starts[index] - week_starts[index - 1] == timedelta(days=7):
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def _week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _counter_winner(values: Any) -> str | None:
    counter = Counter(str(value) for value in values if value)
    return counter.most_common(1)[0][0] if counter else None


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
