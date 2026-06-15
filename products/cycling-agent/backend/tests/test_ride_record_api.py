"""CN: 骑行记录 API 测试，覆盖创建、列表、详情和关键校验错误。
EN: Ride record API tests covering create, list, detail, and key validation errors.
"""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.main import create_app


class StubWeatherProvider:
    def get_weather_snapshot(self, *, city_code: str, region_code: str, forecast_date: date) -> dict:
        return {
            "region_code": region_code,
            "forecast_date": str(forecast_date),
            "temperature_min": 22.0,
            "temperature_max": 31.0,
            "precipitation_probability": 0.15,
            "wind_speed": 4.8,
            "wind_direction": "SE",
            "weather_summary": "cloudy",
            "provider_name": "stub",
            "raw_payload": {},
        }


def test_create_ride_record_from_saved_plan_returns_summary(
    tmp_path,
    monkeypatch,
    dynamic_route_provider,
    dynamic_poi_provider,
) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=dynamic_route_provider,
            poi_provider=dynamic_poi_provider,
        )
    )

    plan_response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，最好风景好一点", "target_date": "2026-05-30"},
    )

    assert plan_response.status_code == 200
    planned_payload = plan_response.json()
    request_no = planned_payload["request_no"]

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "planned",
            "source_request_no": request_no,
            "ride_date": "2026-05-30",
            "completion_status": "completed",
            "actual_duration_hours": planned_payload["recommended_plan"]["estimated_duration_hours"],
            "actual_distance_km": 35.0,
            "effort_feeling": "steady",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ride_record"]["ride_record_no"].startswith("RR-")
    assert body["ride_record"]["source_request_no"] == request_no
    assert body["ride_record"]["route_title"]
    assert body["ride_summary"]["completion_assessment"] == "completed-as-planned"
    assert body["ride_summary"]["plan_alignment"] == "matched-core-plan"


def test_create_manual_ride_record_requires_title_or_destination(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": "2026-06-15",
            "completion_status": "completed",
            "actual_duration_hours": 1.5,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "ride-record-manual-title-missing"


def test_create_planned_ride_record_requires_source_request_no(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "planned",
            "ride_date": "2026-06-15",
            "completion_status": "completed",
            "actual_duration_hours": 1.5,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "ride-record-source-request-missing"


def test_create_completed_ride_record_requires_duration_or_distance(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": "2026-06-15",
            "route_title": "湘湖绕湖骑",
            "completion_status": "completed",
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "ride-record-completed-metrics-missing"


def test_create_planned_ride_record_rejects_missing_source_plan(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "planned",
            "source_request_no": "RQ-NOT-FOUND",
            "ride_date": "2026-06-15",
            "completion_status": "completed",
            "actual_distance_km": 20.0,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "ride-record-source-plan-not-found"


def test_list_and_get_ride_records_return_saved_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": "2026-06-15",
            "route_title": "湘湖绕湖骑",
            "destination_name": "湘湖",
            "completion_status": "completed",
            "actual_duration_hours": 1.5,
            "actual_distance_km": 24.0,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert created.status_code == 200
    ride_record_no = created.json()["ride_record"]["ride_record_no"]

    listed = client.get("/api/v1/rides/records?limit=5")
    loaded = client.get(f"/api/v1/rides/records/{ride_record_no}")

    assert listed.status_code == 200
    assert listed.json()["items"][0]["ride_record_no"] == ride_record_no
    assert loaded.status_code == 200
    assert loaded.json()["ride_record"]["ride_record_no"] == ride_record_no
    assert loaded.json()["ride_summary"]["headline"]


def test_get_ride_record_returns_not_found_for_missing_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.get("/api/v1/rides/records/RR-NOT-FOUND")

    assert response.status_code == 404
    assert response.json()["detail"] == "ride-record-not-found"
