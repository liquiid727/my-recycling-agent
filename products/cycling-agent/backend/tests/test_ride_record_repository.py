"""CN: 骑行记录仓库测试，覆盖保存、详情读取和列表读取。
EN: Ride record repository tests covering save, detail lookup, and list lookup.
"""

from __future__ import annotations

from importlib import import_module

from app.core.storage import init_storage


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
        "origin_region": "滨江",
        "completion_status": "completed",
        "actual_duration_hours": 2.5,
        "actual_distance_km": 48.2,
        "effort_feeling": "moderate",
        "mood_after": "refreshed",
        "notes": "风不大，江边体感不错。",
        "tags": ["evening", "riverside"],
    }

    repository.save_ride_record(database_url, payload)

    saved = repository.get_ride_record(database_url, "RR-20260615-001")
    assert saved == payload

    listed = repository.list_ride_records(database_url)
    assert listed == [payload]


def _load_repository_module():
    try:
        return import_module("app.repositories.ride_record_repository")
    except ModuleNotFoundError:
        return None
