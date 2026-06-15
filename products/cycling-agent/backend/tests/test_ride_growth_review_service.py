"""CN: 增长回顾服务测试，覆盖空窗口、稳态、增长和重启节奏判断。
EN: Ride growth review service tests covering zero, steady, expanding, and resetting windows.
"""

from __future__ import annotations

from importlib import import_module

from app.schemas.ride_plan import RideGrowthReviewPayloadSchema


def test_build_ride_growth_review_returns_zeroed_building_window() -> None:
    summary = _build_growth_review(
        window_days=90,
        window_records=[],
        source_plans_by_request_no={},
        today="2026-06-15",
    )

    validated = RideGrowthReviewPayloadSchema.model_validate(summary)
    assert validated.window_days == 90
    assert validated.ride_count == 0
    assert validated.ride_day_count == 0
    assert validated.completed_count == 0
    assert validated.total_distance_km == 0
    assert validated.total_duration_hours == 0
    assert validated.longest_distance_km == 0
    assert validated.longest_duration_hours == 0
    assert validated.active_month_count == 0
    assert validated.best_weekly_streak == 0
    assert validated.growth_status == "building"
    assert validated.milestones == []
    assert validated.next_focus.action_key == "resume_with_short_ride"


def test_build_ride_growth_review_marks_steady_when_recent_rhythm_is_stable() -> None:
    summary = _build_growth_review(
        window_days=90,
        window_records=[
            _record("RR-1", "2026-04-26", 24.0, 1.4, origin_region="滨江", tags=["晚骑"]),
            _record("RR-2", "2026-05-14", 28.0, 1.6, origin_region="滨江", tags=["晚骑"]),
            _record("RR-3", "2026-05-29", 26.0, 1.5, origin_region="西湖", tags=["通勤"]),
            _record("RR-4", "2026-06-10", 30.0, 1.8, origin_region="西湖", tags=["晚骑"]),
        ],
        source_plans_by_request_no={},
        today="2026-06-15",
    )

    validated = RideGrowthReviewPayloadSchema.model_validate(summary)
    assert validated.ride_count == 4
    assert validated.ride_day_count == 4
    assert validated.total_distance_km == 108.0
    assert validated.growth_status == "steady"
    assert validated.recent_vs_previous_ride_delta == 0
    assert validated.active_month_count == 3
    assert validated.top_tag == "晚骑"
    assert validated.next_focus.action_key == "maintain_weekly_rhythm"


def test_build_ride_growth_review_marks_expanding_when_recent_thirty_days_jump() -> None:
    summary = _build_growth_review(
        window_days=90,
        window_records=[
            _record("RR-1", "2026-04-24", 18.0, 1.0, entry_mode="manual", tags=["通勤"]),
            _record("RR-2", "2026-05-20", 32.0, 1.8, entry_mode="planned", source_request_no="RQ-2", tags=["爬坡"]),
            _record("RR-3", "2026-06-02", 46.0, 2.6, entry_mode="planned", source_request_no="RQ-3", tags=["周末"]),
            _record("RR-4", "2026-06-12", 58.0, 3.2, entry_mode="planned", source_request_no="RQ-4", tags=["周末"]),
        ],
        source_plans_by_request_no={
            "RQ-2": {"recommended_plan": {"estimated_duration_hours": 1.8}},
            "RQ-3": {"recommended_plan": {"estimated_duration_hours": 2.6}},
            "RQ-4": {"recommended_plan": {"estimated_duration_hours": 3.2}},
        },
        today="2026-06-15",
    )

    validated = RideGrowthReviewPayloadSchema.model_validate(summary)
    assert validated.growth_status == "expanding"
    assert validated.recent_vs_previous_ride_delta == 2
    assert validated.recent_vs_previous_distance_delta_km == 118.0
    assert validated.longest_distance_km == 58.0
    assert validated.matched_plan_count == 3
    assert {milestone.milestone_key for milestone in validated.milestones} >= {
        "longest_distance",
        "best_streak",
        "most_active_month",
    }


def test_build_ride_growth_review_marks_resetting_after_twenty_one_day_gap() -> None:
    summary = _build_growth_review(
        window_days=90,
        window_records=[
            _record("RR-1", "2026-04-05", 36.0, 2.0),
            _record("RR-2", "2026-04-20", 42.0, 2.3),
            _record("RR-3", "2026-05-01", None, None, completion_status="cancelled"),
        ],
        source_plans_by_request_no={},
        today="2026-06-15",
    )

    validated = RideGrowthReviewPayloadSchema.model_validate(summary)
    assert validated.ride_count == 2
    assert validated.growth_status == "resetting"
    assert validated.next_focus.action_key == "resume_with_short_ride"


def _build_growth_review(**kwargs):
    module = import_module("app.services.ride_growth_review_service")
    return module.build_ride_growth_review(**kwargs)


def _record(
    ride_record_no: str,
    ride_date: str,
    actual_distance_km: float | None,
    actual_duration_hours: float | None,
    *,
    entry_mode: str = "manual",
    completion_status: str = "completed",
    source_request_no: str | None = None,
    origin_region: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, object]:
    return {
        "ride_record_no": ride_record_no,
        "entry_mode": entry_mode,
        "ride_date": ride_date,
        "completion_status": completion_status,
        "actual_distance_km": actual_distance_km,
        "actual_duration_hours": actual_duration_hours,
        "source_request_no": source_request_no,
        "origin_region": origin_region,
        "tags": tags or [],
        "effort_feeling": "steady",
        "mood_after": "refreshed",
        "route_title": ride_record_no,
    }
