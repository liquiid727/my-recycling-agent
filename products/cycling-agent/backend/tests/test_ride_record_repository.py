"""CN: 骑行记录仓库测试，覆盖保存、详情读取和列表读取。
EN: Ride record repository tests covering save, detail lookup, and list lookup.
"""

from __future__ import annotations

from importlib import import_module

import pytest
from pydantic import ValidationError

from app.core.storage import init_storage
from app.schemas.ride_plan import CreateRideRecordRequestSchema


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
        "effort_feeling": "moderate",
        "mood_after": "refreshed",
        "notes": "风不大，江边体感不错。",
        "tags": ["evening", "riverside"],
        "payload": {
            "ride_summary": {
                "destination_name": "钱塘江南岸",
                "start_point": "闻涛路滨江段",
                "completion_status": "completed",
            },
            "route_snapshot": {
                "route_code": "DYN-HANGZHOU-001",
                "route_title": "闻涛路晚风线",
            },
            "extra_notes": ["补给正常", "路面顺"],
        },
    }

    repository.save_ride_record(database_url, payload)

    saved = repository.get_ride_record(database_url, "RR-20260615-001")
    assert saved == payload
    assert saved["payload"]["route_snapshot"]["route_title"] == "闻涛路晚风线"

    listed = repository.list_ride_records(database_url)
    assert listed == [payload]


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


def _load_repository_module():
    try:
        return import_module("app.repositories.ride_record_repository")
    except ModuleNotFoundError:
        return None
