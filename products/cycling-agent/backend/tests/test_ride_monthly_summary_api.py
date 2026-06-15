"""CN: 月度骑行总结 API 测试，覆盖成功响应和非法月份校验。
EN: Ride monthly summary API tests covering success and invalid month input.
"""

from __future__ import annotations

from datetime import date
from importlib import import_module

from fastapi.testclient import TestClient

from app.main import create_app


class FixedDate(date):
    @classmethod
    def today(cls) -> "FixedDate":
        return cls(2026, 6, 15)


def test_get_monthly_summary_returns_aggregate_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    _freeze_monthly_summary_today(monkeypatch)
    client = TestClient(create_app())

    _seed_ride_record(
        client,
        ride_date="2026-06-03",
        completion_status="completed",
        entry_mode="manual",
        route_title="滨江晚骑",
        actual_duration_hours=1.5,
        actual_distance_km=24.0,
    )
    _seed_ride_record(
        client,
        ride_date="2026-06-14",
        completion_status="shortened",
        entry_mode="manual",
        route_title="西湖轻松骑",
        actual_duration_hours=1.2,
        actual_distance_km=18.0,
    )
    _seed_ride_record(
        client,
        ride_date="2026-06-14",
        completion_status="cancelled",
        entry_mode="manual",
        route_title="雨天取消骑",
        actual_duration_hours=None,
        actual_distance_km=None,
    )

    response = client.get("/api/v1/rides/monthly-summary?month=2026-06")

    assert response.status_code == 200
    body = response.json()["ride_monthly_summary"]
    assert body["month"] == "2026-06"
    assert body["ride_count"] == 3
    assert body["ride_day_count"] == 2
    assert body["completed_count"] == 1
    assert body["shortened_count"] == 1
    assert body["cancelled_count"] == 1
    assert body["total_duration_hours"] == 2.7
    assert body["total_distance_km"] == 42.0
    assert body["last_ride_date"] == "2026-06-14"
    assert body["days_since_last_ride"] == 1
    assert body["habit_status"] == "rebuilding"
    assert body["next_action"]["action_key"] == "schedule_easy_city_ride"

    events = client.get("/api/v1/admin/ride-monthly-summary-events")
    assert events.status_code == 200
    assert events.json()[0]["event_type"] == "summary_request"
    assert events.json()[0]["requested_month"] == "2026-06"
    assert events.json()[0]["habit_status"] == "rebuilding"


def test_get_monthly_summary_rejects_invalid_month_format(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.get("/api/v1/rides/monthly-summary?month=2026-6")

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid-month-format"

    events = client.get("/api/v1/admin/ride-monthly-summary-events")
    assert events.status_code == 200
    assert events.json()[0]["event_type"] == "invalid_month"
    assert events.json()[0]["requested_month"] == "2026-6"


def test_get_monthly_summary_rejects_invalid_iso_month_value(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.get("/api/v1/rides/monthly-summary?month=0000-01")

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid-month-format"


def test_get_monthly_summary_keeps_full_weekly_streak_beyond_thirty_days(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    _freeze_monthly_summary_today(monkeypatch)
    client = TestClient(create_app())

    for ride_date in ["2026-05-11", "2026-05-18", "2026-05-25", "2026-06-01", "2026-06-08", "2026-06-15"]:
        _seed_ride_record(
            client,
            ride_date=ride_date,
            completion_status="completed",
            entry_mode="manual",
            route_title=f"{ride_date} 连续周骑行",
            actual_duration_hours=1.0,
            actual_distance_km=20.0,
        )

    response = client.get("/api/v1/rides/monthly-summary?month=2026-06")

    assert response.status_code == 200
    assert response.json()["ride_monthly_summary"]["weekly_streak"] == 6


def test_track_monthly_summary_cta_click_records_frontend_event(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/monthly-summary-events",
        json={
            "month": "2026-06",
            "action_key": "maintain_weekly_rhythm",
            "suggested_scene": "city_ride",
        },
    )

    assert response.status_code == 200
    assert response.json()["event_type"] == "cta_click"
    assert response.json()["requested_month"] == "2026-06"
    assert response.json()["next_action_key"] == "maintain_weekly_rhythm"
    assert response.json()["source"] == "frontend"


def _freeze_monthly_summary_today(monkeypatch) -> None:
    route_module = import_module("app.api.routes.ride_record")
    service_module = import_module("app.services.ride_monthly_summary_service")
    monkeypatch.setattr(route_module, "date", FixedDate)
    monkeypatch.setattr(service_module, "date", FixedDate)


def _seed_ride_record(
    client: TestClient,
    *,
    ride_date: str,
    completion_status: str,
    route_title: str,
    entry_mode: str,
    actual_duration_hours: float | None,
    actual_distance_km: float | None,
    source_request_no: str | None = None,
) -> None:
    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": entry_mode,
            "source_request_no": source_request_no,
            "ride_date": ride_date,
            "route_title": route_title,
            "completion_status": completion_status,
            "actual_duration_hours": actual_duration_hours,
            "actual_distance_km": actual_distance_km,
            "effort_feeling": "steady",
            "mood_after": "refreshed",
            "tags": [],
        },
    )
    assert response.status_code == 200
