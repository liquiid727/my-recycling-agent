"""CN: 骑行总结服务测试，验证基于规则的总结生成分支。
EN: Ride summary service tests covering rule-first post-ride summary generation.
"""

from __future__ import annotations

from importlib import import_module

from app.schemas.ride_plan import RideSummarySchema


def test_build_ride_summary_marks_completed_steady_ride_as_stable() -> None:
    summary = _build_summary(
        {
            "entry_mode": "planned",
            "completion_status": "completed",
            "effort_feeling": "steady",
            "mood_after": "refreshed",
            "actual_duration_hours": 2.1,
            "actual_distance_km": 38.5,
            "route_title": "钱塘江晚风线",
        },
        source_plan={"recommended_plan": {"estimated_duration_hours": 2.0, "distance_km": 36.0}},
    )

    validated = RideSummarySchema.model_validate(summary)
    assert validated.completion_assessment == "completed-as-planned"
    assert validated.effort_assessment == "matched-expected-effort"
    assert validated.plan_alignment == "matched-core-plan"
    assert "很稳" in validated.headline
    assert "按计划" in validated.summary
    assert validated.confidence_notes


def test_build_ride_summary_marks_completed_hard_ride_as_slightly_harder_than_expected() -> None:
    summary = _build_summary(
        {
            "entry_mode": "planned",
            "completion_status": "completed",
            "effort_feeling": "hard",
            "mood_after": "tired",
            "actual_duration_hours": 3.0,
            "actual_distance_km": 52.0,
            "route_title": "富春江耐力线",
        },
        source_plan={"recommended_plan": {"estimated_duration_hours": 2.1, "distance_km": 45.0}},
    )

    validated = RideSummarySchema.model_validate(summary)
    assert validated.completion_assessment == "completed-as-planned"
    assert validated.effort_assessment == "slightly-harder-than-expected"
    assert validated.plan_alignment == "duration-ran-long"
    assert "比预期更吃力" in validated.summary
    assert "恢复" in validated.recovery_advice


def test_build_ride_summary_frames_shortened_ride_as_partial_completion() -> None:
    summary = _build_summary(
        {
            "entry_mode": "planned",
            "completion_status": "shortened",
            "effort_feeling": "steady",
            "mood_after": "normal",
            "actual_duration_hours": 1.3,
            "actual_distance_km": 24.0,
            "route_title": "西湖晨骑线",
        },
        source_plan={"recommended_plan": {"estimated_duration_hours": 2.0, "distance_km": 32.0}},
    )

    validated = RideSummarySchema.model_validate(summary)
    assert validated.completion_assessment == "partially-completed"
    assert validated.plan_alignment == "shortened-from-plan"
    assert "部分完成" in validated.headline
    assert "主段" in validated.summary
    assert "下次" in validated.next_ride_prompt


def test_build_ride_summary_treats_cancelled_ride_as_low_friction_restart() -> None:
    summary = _build_summary(
        {
            "entry_mode": "manual",
            "completion_status": "cancelled",
            "effort_feeling": "easy",
            "mood_after": "normal",
            "route_title": "滨江夜骑",
        },
        source_plan=None,
    )

    validated = RideSummarySchema.model_validate(summary)
    assert validated.completion_assessment == "cancelled"
    assert validated.effort_assessment == "not-started"
    assert validated.plan_alignment == "not-ridden"
    assert "不要有负担" in validated.summary
    assert "轻松" in validated.next_ride_prompt


def _build_summary(record: dict, *, source_plan: dict | None) -> dict:
    module = _load_service_module()
    assert module is not None
    build_ride_summary = getattr(module, "build_ride_summary", None)
    assert callable(build_ride_summary)
    return build_ride_summary(record, source_plan=source_plan)


def _load_service_module():
    try:
        return import_module("app.services.ride_summary_service")
    except ModuleNotFoundError:
        return None
