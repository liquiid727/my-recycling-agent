"""CN: 月度骑行总结服务测试，覆盖稳态月份和空月份规则聚合。
EN: Ride monthly summary service tests covering steady and empty month aggregation.
"""

from __future__ import annotations

from importlib import import_module

from app.schemas.ride_plan import RideMonthlySummaryPayloadSchema


def test_build_ride_monthly_summary_aggregates_steady_month() -> None:
    summary = _build_monthly_summary(
        month="2026-06",
        monthly_records=[
            {
                "ride_record_no": "RR-1",
                "entry_mode": "planned",
                "ride_date": "2026-06-03",
                "completion_status": "completed",
                "actual_duration_hours": 2.0,
                "actual_distance_km": 35.0,
                "effort_feeling": "steady",
                "mood_after": "refreshed",
                "origin_region": "滨江",
                "tags": ["晚骑"],
                "source_request_no": "RQ-1",
                "route_title": "钱塘江晚风线",
            },
            {
                "ride_record_no": "RR-2",
                "entry_mode": "manual",
                "ride_date": "2026-06-10",
                "completion_status": "shortened",
                "actual_duration_hours": 1.5,
                "actual_distance_km": 22.0,
                "effort_feeling": "steady",
                "mood_after": "normal",
                "origin_region": "滨江",
                "tags": ["晚骑"],
                "source_request_no": None,
                "route_title": "西湖轻松骑",
            },
            {
                "ride_record_no": "RR-3",
                "entry_mode": "planned",
                "ride_date": "2026-06-14",
                "completion_status": "completed",
                "actual_duration_hours": 2.0,
                "actual_distance_km": 40.4,
                "effort_feeling": "steady",
                "mood_after": "refreshed",
                "origin_region": "西湖",
                "tags": ["周末"],
                "source_request_no": "RQ-3",
                "route_title": "运河周末线",
            },
            {
                "ride_record_no": "RR-4",
                "entry_mode": "manual",
                "ride_date": "2026-06-14",
                "completion_status": "cancelled",
                "actual_duration_hours": None,
                "actual_distance_km": None,
                "effort_feeling": "easy",
                "mood_after": "normal",
                "origin_region": "滨江",
                "tags": ["通勤"],
                "source_request_no": None,
                "route_title": "工作日通勤骑",
            },
        ],
        recent_non_cancelled_records=[
            {
                "ride_record_no": "RR-3",
                "ride_date": "2026-06-14",
                "completion_status": "completed",
                "effort_feeling": "steady",
                "mood_after": "refreshed",
            },
            {
                "ride_record_no": "RR-2",
                "ride_date": "2026-06-10",
                "completion_status": "shortened",
                "effort_feeling": "steady",
                "mood_after": "normal",
            },
            {
                "ride_record_no": "RR-1",
                "ride_date": "2026-06-03",
                "completion_status": "completed",
                "effort_feeling": "steady",
                "mood_after": "refreshed",
            },
        ],
        source_plans_by_request_no={
            "RQ-1": {"recommended_plan": {"estimated_duration_hours": 2.0}},
            "RQ-3": {"recommended_plan": {"estimated_duration_hours": 2.0}},
        },
        today="2026-06-15",
    )

    validated = RideMonthlySummaryPayloadSchema.model_validate(summary)
    assert validated.ride_count == 4
    assert validated.ride_day_count == 3
    assert validated.completed_count == 2
    assert validated.shortened_count == 1
    assert validated.cancelled_count == 1
    assert validated.total_distance_km == 97.4
    assert validated.total_duration_hours == 5.5
    assert validated.planned_count == 2
    assert validated.manual_count == 2
    assert str(validated.last_ride_date) == "2026-06-14"
    assert validated.days_since_last_ride == 1
    assert validated.weekly_streak == 2
    assert validated.habit_status == "steady"
    assert validated.top_start_region == "滨江"
    assert validated.top_tag == "晚骑"
    assert validated.hard_effort_count == 0
    assert validated.tired_mood_count == 0
    assert validated.matched_plan_count == 2
    assert validated.month_to_date is True
    assert validated.recent_30d_ride_count == 3
    assert validated.next_action.action_key == "maintain_weekly_rhythm"


def test_build_ride_monthly_summary_returns_zeroed_starting_month() -> None:
    summary = _build_monthly_summary(
        month="2026-07",
        monthly_records=[],
        recent_non_cancelled_records=[],
        source_plans_by_request_no={},
        today="2026-07-10",
    )

    validated = RideMonthlySummaryPayloadSchema.model_validate(summary)
    assert validated.ride_count == 0
    assert validated.ride_day_count == 0
    assert validated.completed_count == 0
    assert validated.shortened_count == 0
    assert validated.cancelled_count == 0
    assert validated.total_distance_km == 0
    assert validated.total_duration_hours == 0
    assert validated.planned_count == 0
    assert validated.manual_count == 0
    assert validated.last_ride_date is None
    assert validated.days_since_last_ride is None
    assert validated.weekly_streak == 0
    assert validated.habit_status == "starting"
    assert validated.matched_plan_count == 0
    assert validated.next_action.action_key == "resume_with_short_ride"


def test_build_ride_monthly_summary_marks_starting_after_fourteen_day_gap() -> None:
    summary = _build_monthly_summary(
        month="2026-06",
        monthly_records=[
            {
                "ride_record_no": "RR-1",
                "entry_mode": "manual",
                "ride_date": "2026-06-01",
                "completion_status": "completed",
                "actual_duration_hours": 1.0,
                "actual_distance_km": 18.0,
                "effort_feeling": "easy",
                "mood_after": "refreshed",
                "tags": [],
            }
        ],
        recent_non_cancelled_records=[
            {
                "ride_record_no": "RR-1",
                "ride_date": "2026-06-01",
                "completion_status": "completed",
                "effort_feeling": "easy",
                "mood_after": "refreshed",
            }
        ],
        source_plans_by_request_no={},
        today="2026-06-15",
    )

    validated = RideMonthlySummaryPayloadSchema.model_validate(summary)
    assert validated.days_since_last_ride == 14
    assert validated.habit_status == "starting"
    assert validated.next_action.action_key == "resume_with_short_ride"


def test_build_ride_monthly_summary_marks_overreaching_from_last_two_rides() -> None:
    summary = _build_monthly_summary(
        month="2026-06",
        monthly_records=[
            {
                "ride_record_no": "RR-1",
                "entry_mode": "manual",
                "ride_date": "2026-06-04",
                "completion_status": "completed",
                "actual_duration_hours": 1.5,
                "actual_distance_km": 20.0,
                "effort_feeling": "steady",
                "mood_after": "normal",
                "tags": [],
            },
            {
                "ride_record_no": "RR-2",
                "entry_mode": "manual",
                "ride_date": "2026-06-08",
                "completion_status": "completed",
                "actual_duration_hours": 2.0,
                "actual_distance_km": 35.0,
                "effort_feeling": "hard",
                "mood_after": "normal",
                "tags": [],
            },
            {
                "ride_record_no": "RR-3",
                "entry_mode": "manual",
                "ride_date": "2026-06-10",
                "completion_status": "shortened",
                "actual_duration_hours": 1.0,
                "actual_distance_km": 16.0,
                "effort_feeling": "steady",
                "mood_after": "tired",
                "tags": [],
            },
        ],
        recent_non_cancelled_records=[
            {
                "ride_record_no": "RR-2",
                "ride_date": "2026-06-08",
                "completion_status": "completed",
                "effort_feeling": "hard",
                "mood_after": "normal",
            },
            {
                "ride_record_no": "RR-1",
                "ride_date": "2026-06-04",
                "completion_status": "completed",
                "effort_feeling": "steady",
                "mood_after": "normal",
            },
            {
                "ride_record_no": "RR-3",
                "ride_date": "2026-06-10",
                "completion_status": "shortened",
                "effort_feeling": "steady",
                "mood_after": "tired",
            },
        ],
        source_plans_by_request_no={},
        today="2026-06-11",
    )

    validated = RideMonthlySummaryPayloadSchema.model_validate(summary)
    assert validated.habit_status == "overreaching"
    assert validated.next_action.action_key == "take_recovery_window"


def test_build_ride_monthly_summary_ignores_future_dated_rows_in_current_month() -> None:
    summary = _build_monthly_summary(
        month="2026-06",
        monthly_records=[
            {
                "ride_record_no": "RR-1",
                "entry_mode": "manual",
                "ride_date": "2026-06-10",
                "completion_status": "completed",
                "actual_duration_hours": 1.5,
                "actual_distance_km": 24.0,
                "effort_feeling": "steady",
                "mood_after": "refreshed",
                "tags": ["晚骑"],
            },
            {
                "ride_record_no": "RR-2",
                "entry_mode": "manual",
                "ride_date": "2026-06-20",
                "completion_status": "completed",
                "actual_duration_hours": 2.5,
                "actual_distance_km": 42.0,
                "effort_feeling": "hard",
                "mood_after": "tired",
                "tags": ["周末"],
            },
        ],
        recent_non_cancelled_records=[
            {
                "ride_record_no": "RR-1",
                "ride_date": "2026-06-10",
                "completion_status": "completed",
                "effort_feeling": "steady",
                "mood_after": "refreshed",
            }
        ],
        source_plans_by_request_no={},
        today="2026-06-15",
    )

    validated = RideMonthlySummaryPayloadSchema.model_validate(summary)
    assert validated.ride_count == 1
    assert validated.completed_count == 1
    assert validated.total_distance_km == 24.0
    assert str(validated.last_ride_date) == "2026-06-10"
    assert validated.days_since_last_ride == 5


def _build_monthly_summary(
    *,
    month: str,
    monthly_records: list[dict],
    recent_non_cancelled_records: list[dict],
    streak_non_cancelled_records: list[dict] | None = None,
    source_plans_by_request_no: dict[str, dict],
    today: str,
) -> dict:
    module = _load_service_module()
    assert module is not None
    build_ride_monthly_summary = getattr(module, "build_ride_monthly_summary", None)
    assert callable(build_ride_monthly_summary)
    return build_ride_monthly_summary(
        month=month,
        monthly_records=monthly_records,
        recent_non_cancelled_records=recent_non_cancelled_records,
        streak_non_cancelled_records=streak_non_cancelled_records,
        source_plans_by_request_no=source_plans_by_request_no,
        today=today,
    )


def _load_service_module():
    try:
        return import_module("app.services.ride_monthly_summary_service")
    except ModuleNotFoundError:
        return None
