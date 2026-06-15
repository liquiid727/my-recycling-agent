"""CN: 增长回顾 API 测试，覆盖成功响应、非法窗口和空窗口。
EN: Ride growth review API tests covering success, invalid window, and zero window results.
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


def test_get_growth_review_returns_aggregate_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    _freeze_growth_review_today(monkeypatch)
    client = TestClient(create_app())

    _seed_ride_record(client, ride_date="2026-04-24", completion_status="completed", route_title="通勤轻骑", actual_duration_hours=1.0, actual_distance_km=18.0)
    _seed_ride_record(client, ride_date="2026-05-20", completion_status="completed", route_title="周中拉开", actual_duration_hours=1.8, actual_distance_km=32.0)
    _seed_ride_record(client, ride_date="2026-06-02", completion_status="completed", route_title="周末出门", actual_duration_hours=2.6, actual_distance_km=46.0)
    _seed_ride_record(client, ride_date="2026-06-12", completion_status="shortened", route_title="拉长一点", actual_duration_hours=3.2, actual_distance_km=58.0)

    response = client.get("/api/v1/rides/growth-review?window_days=90")

    assert response.status_code == 200
    body = response.json()["ride_growth_review"]
    assert body["window_days"] == 90
    assert body["ride_count"] == 4
    assert body["growth_status"] == "expanding"
    assert body["longest_distance_km"] == 58.0
    assert body["next_focus"]["suggested_scene"] == "weekend_trip"

    events = client.get("/api/v1/admin/ride-monthly-summary-events")
    assert events.status_code == 200
    assert events.json()[0]["event_type"] == "growth_review_request"
    assert events.json()[0]["requested_window_days"] == 90
    assert events.json()[0]["growth_status"] == "expanding"
    assert events.json()[0]["has_milestones"] is True
    assert events.json()[0]["is_zero_growth_review"] is False


def test_get_growth_review_rejects_invalid_window_days(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.get("/api/v1/rides/growth-review?window_days=45")

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid-window-days"

    events = client.get("/api/v1/admin/ride-monthly-summary-events")
    assert events.status_code == 200
    assert events.json()[0]["event_type"] == "growth_review_invalid_window"
    assert events.json()[0]["requested_window_days"] == 45


def test_get_growth_review_returns_zeroed_payload_when_window_has_no_rides(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    _freeze_growth_review_today(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/api/v1/rides/growth-review?window_days=90")

    assert response.status_code == 200
    body = response.json()["ride_growth_review"]
    assert body["ride_count"] == 0
    assert body["growth_status"] == "building"
    assert body["milestones"] == []

    events = client.get("/api/v1/admin/ride-monthly-summary-events")
    assert events.status_code == 200
    assert events.json()[0]["event_type"] == "growth_review_request"
    assert events.json()[0]["requested_window_days"] == 90
    assert events.json()[0]["growth_status"] == "building"
    assert events.json()[0]["has_milestones"] is False
    assert events.json()[0]["is_zero_growth_review"] is True


def test_track_growth_review_cta_click_records_frontend_event(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/growth-review-events",
        json={
            "window_days": 90,
            "action_key": "maintain_weekly_rhythm",
            "suggested_scene": "weekend_trip",
            "growth_status": "expanding",
        },
    )

    assert response.status_code == 200
    assert response.json()["event_type"] == "growth_review_cta_click"
    assert response.json()["requested_window_days"] == 90
    assert response.json()["growth_status"] == "expanding"
    assert response.json()["next_action_key"] == "maintain_weekly_rhythm"
    assert response.json()["source"] == "frontend"


def _freeze_growth_review_today(monkeypatch) -> None:
    route_module = import_module("app.api.routes.ride_record")
    service_module = import_module("app.services.ride_growth_review_service")
    monkeypatch.setattr(route_module, "date", FixedDate)
    monkeypatch.setattr(service_module, "date", FixedDate)


def _seed_ride_record(
    client: TestClient,
    *,
    ride_date: str,
    completion_status: str,
    route_title: str,
    actual_duration_hours: float | None,
    actual_distance_km: float | None,
) -> None:
    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
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
