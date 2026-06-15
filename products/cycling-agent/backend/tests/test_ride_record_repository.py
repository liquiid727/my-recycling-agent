"""CN: 骑行记录仓库测试，覆盖保存、详情读取和列表读取。
EN: Ride record repository tests covering save, detail lookup, and list lookup.
"""

from __future__ import annotations

import json
import sqlite3
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
