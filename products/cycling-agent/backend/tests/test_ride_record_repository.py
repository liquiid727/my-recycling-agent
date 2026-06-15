"""CN: 骑行记录仓库测试，覆盖保存、详情读取和列表读取。
EN: Ride record repository tests covering save, detail lookup, and list lookup.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from importlib import import_module

import pytest
from pydantic import ValidationError

from app.core.storage import init_storage
from app.schemas.ride_plan import (
    CreateRideRecordRequestSchema,
    RideRecordDetailResponseSchema,
    RideRecordListResponseSchema,
    RideRecordPayload,
    RideSummarySchema,
)


def test_save_and_list_ride_records(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    repository = _load_repository_module()
    assert repository is not None
    assert hasattr(repository, "save_ride_record")
    assert hasattr(repository, "get_ride_record")
    assert hasattr(repository, "list_ride_records")

    payload = {
        "ride_record_no": "RR-20260615-001",
        "entry_mode": "manual",
        "source_request_no": "RQ-TEST-001",
        "ride_date": "2026-06-15",
        "intent": "ride_today",
        "plan_kind": "route",
        "route_code": "DYN-HANGZHOU-001",
        "route_title": "闻涛路晚风线",
        "destination_name": "钱塘江南岸",
        "start_point": "闻涛路滨江段",
        "origin_region": "滨江",
        "completion_status": "completed",
        "actual_duration_hours": 2.5,
        "actual_distance_km": 48.2,
        "effort_feeling": "steady",
        "mood_after": "refreshed",
        "notes": "风不大，江边体感不错。",
        "tags": ["evening", "riverside"],
    }

    saved_payload = repository.save_ride_record(database_url, payload)

    saved = repository.get_ride_record(database_url, "RR-20260615-001")
    assert saved_payload == payload
    assert saved == payload
    assert "payload" not in saved
    assert RideRecordPayload.model_validate(saved).effort_feeling == "steady"

    with sqlite3.connect(tmp_path / "cycling-agent.db") as connection:
        persisted = connection.execute(
            "SELECT payload_json FROM ride_records WHERE ride_record_no = ?",
            ("RR-20260615-001",),
        ).fetchone()[0]
    assert json.loads(persisted) == payload

    listed = repository.list_ride_records(database_url)
    assert listed == [payload]


def test_init_storage_migrates_legacy_sqlite_ride_records_without_timestamp_default_error(tmp_path) -> None:
    database_path = tmp_path / "legacy-cycling-agent.db"
    database_url = f"sqlite:///{database_path}"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE ride_records (
                ride_record_no TEXT PRIMARY KEY,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute("INSERT INTO ride_records (ride_record_no) VALUES (?)", ("RR-LEGACY-001",))

    init_storage(database_url)

    with sqlite3.connect(database_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(ride_records)").fetchall()}
        migrated = connection.execute(
            "SELECT updated_at, payload_json, tags_json FROM ride_records WHERE ride_record_no = ?",
            ("RR-LEGACY-001",),
        ).fetchone()

    assert {"updated_at", "payload_json", "tags_json"}.issubset(columns)
    assert migrated[0] is not None
    assert migrated[1] == "{}"
    assert migrated[2] == "[]"


def test_legacy_sqlite_ride_record_rows_hydrate_with_safe_defaults(tmp_path) -> None:
    database_path = tmp_path / "legacy-hydrate-cycling-agent.db"
    database_url = f"sqlite:///{database_path}"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE ride_records (
                ride_record_no TEXT PRIMARY KEY,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "INSERT INTO ride_records (ride_record_no, created_at) VALUES (?, ?)",
            ("RR-LEGACY-READ-001", "2026-06-01 08:30:00"),
        )

    init_storage(database_url)

    repository = _load_repository_module()
    hydrated = repository.get_ride_record(database_url, "RR-LEGACY-READ-001")
    listed = repository.list_ride_records(database_url)

    assert hydrated is not None
    assert hydrated["ride_record_no"] == "RR-LEGACY-READ-001"
    assert hydrated["entry_mode"] == "manual"
    assert hydrated["ride_date"] == "2026-06-01"
    assert hydrated["completion_status"] == "cancelled"
    assert hydrated["effort_feeling"] == "steady"
    assert hydrated["mood_after"] == "normal"
    assert hydrated["tags"] == []
    assert RideRecordPayload.model_validate(hydrated).completion_status == "cancelled"
    assert listed == [hydrated]


def test_list_ride_records_by_date_range_returns_only_records_inside_month(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    repository = _load_repository_module()
    assert repository is not None
    assert hasattr(repository, "list_ride_records_by_date_range")

    _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260531-001",
        ride_date="2026-05-31",
        completion_status="completed",
    )
    june_first = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260601-001",
        ride_date="2026-06-01",
        completion_status="completed",
    )
    june_mid = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260615-001",
        ride_date="2026-06-15",
        completion_status="shortened",
    )
    june_last = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260630-001",
        ride_date="2026-06-30",
        completion_status="completed",
    )
    _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260701-001",
        ride_date="2026-07-01",
        completion_status="completed",
    )

    records = repository.list_ride_records_by_date_range(
        database_url,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
    )

    assert records == [june_last, june_mid, june_first]


def test_list_ride_records_by_date_range_includes_record_on_end_date(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    repository = _load_repository_module()
    assert repository is not None

    june_last = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260630-999",
        ride_date="2026-06-30",
        completion_status="completed",
    )

    records = repository.list_ride_records_by_date_range(
        database_url,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
    )

    assert records == [june_last]


def test_list_ride_records_by_date_range_includes_timestamp_like_end_date_rows(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    repository = _load_repository_module()
    assert repository is not None

    june_last = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260630-TS",
        ride_date="2026-06-30T08:00:00",
        completion_status="completed",
    )

    records = repository.list_ride_records_by_date_range(
        database_url,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
    )

    assert records == [{**june_last, "ride_date": "2026-06-30"}]


def test_list_recent_non_cancelled_ride_records_skips_cancelled_records(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    repository = _load_repository_module()
    assert repository is not None
    assert hasattr(repository, "list_recent_non_cancelled_ride_records")

    _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260616-001",
        ride_date="2026-06-16",
        completion_status="completed",
    )
    _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260629-001",
        ride_date="2026-06-29",
        completion_status="cancelled",
    )
    june_thirtieth = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260630-001",
        ride_date="2026-06-30",
        completion_status="shortened",
    )
    june_twenty_eighth = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260628-001",
        ride_date="2026-06-28",
        completion_status="completed",
    )
    _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260701-001",
        ride_date="2026-07-01",
        completion_status="completed",
    )

    records = repository.list_recent_non_cancelled_ride_records(
        database_url,
        before_date=date(2026, 6, 30),
        lookback_days=7,
        limit=10,
    )

    assert records == [june_thirtieth, june_twenty_eighth]


def test_list_recent_non_cancelled_ride_records_includes_same_day_records(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    repository = _load_repository_module()
    assert repository is not None

    same_day = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260630-888",
        ride_date="2026-06-30",
        completion_status="completed",
    )
    previous_day = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260629-888",
        ride_date="2026-06-29",
        completion_status="shortened",
    )

    records = repository.list_recent_non_cancelled_ride_records(
        database_url,
        before_date=date(2026, 6, 30),
        lookback_days=7,
        limit=10,
    )

    assert records == [same_day, previous_day]


def test_list_recent_non_cancelled_ride_records_includes_same_day_timestamp_like_rows(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    repository = _load_repository_module()
    assert repository is not None

    same_day = _save_ride_record(
        repository,
        database_url,
        ride_record_no="RR-20260630-DT",
        ride_date=datetime(2026, 6, 30, 8, 0, 0),
        completion_status="completed",
    )

    records = repository.list_recent_non_cancelled_ride_records(
        database_url,
        before_date=date(2026, 6, 30),
        lookback_days=7,
        limit=10,
    )

    assert records == [{**same_day, "ride_date": "2026-06-30"}]


def test_save_ride_record_rejects_missing_ride_date(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    repository = _load_repository_module()
    assert repository is not None

    with pytest.raises(ValueError, match="ride-date-missing"):
        repository.save_ride_record(
            database_url,
            {
                "ride_record_no": "RR-MISSING-DATE",
                "entry_mode": "manual",
                "completion_status": "completed",
                "effort_feeling": "steady",
                "mood_after": "normal",
                "tags": [],
            },
        )


def test_create_ride_record_request_schema_enforces_flat_contract() -> None:
    payload = CreateRideRecordRequestSchema(
        entry_mode="planned",
        source_request_no="RQ-TEST-001",
        ride_date="2026-06-15",
        route_code="DYN-HANGZHOU-001",
        route_title="闻涛路晚风线",
        destination_name="钱塘江南岸",
        start_point="闻涛路滨江段",
        origin_region="滨江",
        completion_status="completed",
        actual_duration_hours=2.5,
        actual_distance_km=48.2,
        effort_feeling="steady",
        mood_after="normal",
        notes="记录一次按计划完成的骑行。",
        tags=["evening", "riverside"],
    )

    assert payload.entry_mode == "planned"
    assert payload.completion_status == "completed"
    assert payload.effort_feeling == "steady"
    assert payload.mood_after == "normal"

    with pytest.raises(ValidationError):
        CreateRideRecordRequestSchema(
            entry_mode="linked_plan",
            ride_date="2026-06-15",
            completion_status="completed",
            effort_feeling="steady",
            mood_after="normal",
        )

    with pytest.raises(ValidationError):
        CreateRideRecordRequestSchema(
            entry_mode="planned",
            ride_date="2026-06-15",
            completion_status="completed",
            effort_feeling="moderate",
            mood_after="normal",
        )

    with pytest.raises(ValidationError):
        CreateRideRecordRequestSchema(
            entry_mode="planned",
            ride_date="2026-06-15",
            completion_status="partial",
            effort_feeling="steady",
            mood_after="normal",
        )

    with pytest.raises(ValidationError):
        CreateRideRecordRequestSchema(
            entry_mode="planned",
            ride_date="2026-06-15",
            completion_status="completed",
            effort_feeling="steady",
            mood_after="steady",
        )


def test_ride_monthly_summary_response_schema_enforces_contract() -> None:
    ride_plan_module = import_module("app.schemas.ride_plan")
    assert hasattr(ride_plan_module, "RideMonthlySummaryActionSchema")
    assert hasattr(ride_plan_module, "RideMonthlySummaryPayloadSchema")
    assert hasattr(ride_plan_module, "RideMonthlySummaryResponseSchema")

    action_schema = ride_plan_module.RideMonthlySummaryActionSchema
    payload_schema = ride_plan_module.RideMonthlySummaryPayloadSchema
    response_schema = ride_plan_module.RideMonthlySummaryResponseSchema

    response = response_schema.model_validate(
        {
            "ride_monthly_summary": payload_schema.model_validate(
                {
                    "month": "2026-06",
                    "period_start": "2026-06-01",
                    "period_end": "2026-06-30",
                    "ride_count": 4,
                    "ride_day_count": 3,
                    "completed_count": 2,
                    "shortened_count": 1,
                    "cancelled_count": 1,
                    "total_distance_km": 128.5,
                    "total_duration_hours": 8.2,
                    "planned_count": 3,
                    "manual_count": 1,
                    "last_ride_date": "2026-06-30",
                    "days_since_last_ride": 0,
                    "weekly_streak": 2,
                    "habit_status": "steady",
                    "next_action": action_schema.model_validate(
                        {
                            "action_key": "maintain_weekly_rhythm",
                            "title": "保持每周固定一次短骑",
                            "body": "先稳住频率，再逐步加距离。",
                            "suggested_scene": "city_ride",
                            "suggested_entry": "下班后 60 分钟轻松骑",
                        }
                    ),
                    "summary_headline": "六月维持住了每周骑行节奏",
                    "summary_body": "整体频率稳定，月底还有一次按计划完成的短骑。",
                    "top_start_region": "滨江",
                    "top_tag": "evening",
                    "hard_effort_count": 0,
                    "tired_mood_count": 1,
                    "matched_plan_count": 2,
                    "month_to_date": False,
                    "recent_30d_ride_count": 4,
                }
            )
        }
    )

    assert response.ride_monthly_summary.month == "2026-06"
    assert response.ride_monthly_summary.next_action.action_key == "maintain_weekly_rhythm"

    action_json_schema = action_schema.model_json_schema()
    payload_json_schema = payload_schema.model_json_schema()
    response_json_schema = response_schema.model_json_schema()

    assert action_json_schema["properties"]["action_key"]["enum"] == [
        "schedule_easy_city_ride",
        "resume_with_short_ride",
        "maintain_weekly_rhythm",
        "take_recovery_window",
    ]
    assert action_json_schema["properties"]["suggested_scene"]["enum"] == [
        "city_ride",
        "weekend_trip",
    ]
    assert payload_json_schema["properties"]["habit_status"]["enum"] == [
        "starting",
        "rebuilding",
        "steady",
        "overreaching",
    ]
    assert response_json_schema["properties"]["ride_monthly_summary"]["$ref"] == "#/$defs/RideMonthlySummaryPayloadSchema"
    assert action_json_schema["required"] == [
        "action_key",
        "title",
        "body",
        "suggested_scene",
    ]
    assert payload_json_schema["required"] == [
        "month",
        "period_start",
        "period_end",
        "ride_count",
        "ride_day_count",
        "completed_count",
        "shortened_count",
        "cancelled_count",
        "total_distance_km",
        "total_duration_hours",
        "planned_count",
        "manual_count",
        "weekly_streak",
        "habit_status",
        "next_action",
        "summary_headline",
        "summary_body",
    ]

    with pytest.raises(ValidationError):
        payload_schema.model_validate(
            {
                "month": "2026/06",
                "period_start": "2026-06-01",
                "period_end": "2026-06-30",
                "ride_count": -1,
                "ride_day_count": 0,
                "completed_count": 0,
                "shortened_rides": 0,
                "cancelled_count": 0,
                "total_distance_km": 0,
                "total_duration_hours": 0,
                "planned_count": 0,
                "manual_count": 0,
                "weekly_streak": 0,
                "habit_status": "steady",
                "next_action": {
                    "action_key": "maintain_weekly_rhythm",
                    "title": "保持每周固定一次短骑",
                    "body": "先稳住频率，再逐步加距离。",
                    "suggested_scene": "city_ride",
                },
                "summary_headline": "六月维持住了每周骑行节奏",
                "summary_body": "整体频率稳定，月底还有一次按计划完成的短骑。",
            }
        )


def test_ride_record_response_schemas_validate_representative_payloads() -> None:
    ride_record = {
        "ride_record_no": "RR-20260615-001",
        "entry_mode": "planned",
        "source_request_no": "RQ-TEST-001",
        "ride_date": "2026-06-15",
        "intent": "ride_today",
        "plan_kind": "route",
        "route_code": "DYN-HANGZHOU-001",
        "route_title": "闻涛路晚风线",
        "destination_name": "钱塘江南岸",
        "start_point": "闻涛路滨江段",
        "origin_region": "滨江",
        "completion_status": "completed",
        "actual_duration_hours": 2.5,
        "actual_distance_km": 48.2,
        "effort_feeling": "steady",
        "mood_after": "normal",
        "notes": "记录一次按计划完成的骑行。",
        "tags": ["evening", "riverside"],
    }
    ride_summary = {
        "headline": "按计划完成钱塘江晚骑",
        "summary": "整体节奏稳定，路线执行与预期基本一致。",
        "completion_assessment": "完整完成计划路线。",
        "effort_assessment": "体感稳定，没有明显掉速。",
        "recovery_advice": "补水后做轻度拉伸。",
        "next_ride_prompt": "下次可尝试略微增加距离。",
        "plan_alignment": "与计划路线高度一致",
        "confidence_notes": ["基于手动记录整理"],
    }

    validated_record = RideRecordPayload.model_validate(ride_record)
    assert validated_record.entry_mode == "planned"
    assert validated_record.effort_feeling == "steady"

    validated_summary = RideSummarySchema.model_validate(ride_summary)
    assert validated_summary.headline == "按计划完成钱塘江晚骑"
    assert validated_summary.confidence_notes == ["基于手动记录整理"]

    list_response = RideRecordListResponseSchema.model_validate(
        {
            "items": [
                {
                    "ride_record_no": "RR-20260615-001",
                    "ride_date": "2026-06-15",
                    "route_title": "闻涛路晚风线",
                    "destination_name": "钱塘江南岸",
                    "completion_status": "completed",
                    "summary_headline": "按计划完成钱塘江晚骑",
                }
            ]
        }
    )
    assert list_response.items[0].summary_headline == "按计划完成钱塘江晚骑"

    with pytest.raises(ValidationError):
        RideRecordListResponseSchema.model_validate(
            {
                "items": [
                    {
                        "ride_record_no": "RR-20260615-002",
                        "ride_date": "2026-06-15",
                        "completion_status": "partial",
                    }
                ]
            }
        )

    detail_response = RideRecordDetailResponseSchema.model_validate(
        {"ride_record": ride_record, "ride_summary": ride_summary}
    )
    assert detail_response.ride_record.route_title == "闻涛路晚风线"
    assert detail_response.ride_summary.recovery_advice == "补水后做轻度拉伸。"


def _load_repository_module():
    try:
        return import_module("app.repositories.ride_record_repository")
    except ModuleNotFoundError:
        return None


def _save_ride_record(
    repository,
    database_url: str,
    *,
    ride_record_no: str,
    ride_date,
    completion_status: str,
) -> dict:
    payload = {
        "ride_record_no": ride_record_no,
        "entry_mode": "manual",
        "source_request_no": None,
        "ride_date": ride_date,
        "intent": "ride_today",
        "plan_kind": "route",
        "route_code": f"ROUTE-{ride_record_no}",
        "route_title": f"Route {ride_record_no}",
        "destination_name": "钱塘江南岸",
        "start_point": "闻涛路滨江段",
        "origin_region": "滨江",
        "completion_status": completion_status,
        "actual_duration_hours": 2.0,
        "actual_distance_km": 35.0,
        "effort_feeling": "steady",
        "mood_after": "normal",
        "notes": None,
        "tags": ["test"],
    }
    repository.save_ride_record(database_url, payload)
    return payload
