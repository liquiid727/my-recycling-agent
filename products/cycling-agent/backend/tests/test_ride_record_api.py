"""CN: 骑行记录 API 测试，覆盖创建、列表、详情和关键校验错误。
EN: Ride record API tests covering create, list, detail, and key validation errors.
"""

from __future__ import annotations

from importlib import import_module
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


class FixedDate(date):
    @classmethod
    def today(cls) -> "FixedDate":
        return cls(2026, 6, 15)


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
    assert body["ride_record"]["route_code"] == planned_payload["recommended_plan"]["route_code"]
    assert body["ride_record"]["route_title"] == planned_payload["recommended_plan"]["route_name"]
    assert body["ride_record"]["destination_name"] == planned_payload["plan"]["destination_name"]
    assert body["ride_record"]["start_point"] == planned_payload["parsed_constraints"]["start_point"]
    assert body["ride_record"]["origin_region"] == planned_payload["parsed_constraints"]["origin_region"]
    assert body["ride_record"]["intent"] == planned_payload["intent"]
    assert body["ride_record"]["plan_kind"] == planned_payload["plan"]["kind"]
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


def test_create_ride_record_rejects_negative_duration_metric(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": "2026-06-15",
            "route_title": "湘湖绕湖骑",
            "completion_status": "completed",
            "actual_duration_hours": -1.0,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 422
    assert "greater than or equal to 0" in str(response.json())


def test_create_ride_record_rejects_negative_distance_metric(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": "2026-06-15",
            "route_title": "湘湖绕湖骑",
            "completion_status": "completed",
            "actual_distance_km": -5.0,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 422
    assert "greater than or equal to 0" in str(response.json())


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


def test_create_manual_ride_record_normalizes_source_request_no_to_none(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "source_request_no": "RQ-BOGUS-MANUAL",
            "ride_date": "2026-06-15",
            "route_title": "湘湖绕湖骑",
            "completion_status": "completed",
            "actual_duration_hours": 1.5,
            "actual_distance_km": 24.0,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 200
    assert response.json()["ride_record"]["source_request_no"] is None


def test_create_ride_record_rejects_future_ride_date(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    route_module = import_module("app.api.routes.ride_record")
    monkeypatch.setattr(route_module, "date", FixedDate)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": "2026-06-16",
            "route_title": "明天的骑行先记上",
            "completion_status": "completed",
            "actual_duration_hours": 1.0,
            "actual_distance_km": 18.0,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "ride-record-date-in-future"


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


def test_list_ride_records_uses_batch_plan_lookup_for_summary_headlines(
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

    first_plan = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，最好风景好一点", "target_date": "2026-05-30"},
    ).json()
    second_plan = client.post(
        "/api/v1/ride/plan",
        json={"query": "周日从闻涛路滨江段出发骑2小时，想轻松看江景", "target_date": "2026-05-31"},
    ).json()

    for plan in (first_plan, second_plan):
        create_response = client.post(
            "/api/v1/rides/records",
            json={
                "entry_mode": "planned",
                "source_request_no": plan["request_no"],
                "ride_date": plan["input_summary"]["target_date"],
                "completion_status": "completed",
                "actual_duration_hours": plan["recommended_plan"]["estimated_duration_hours"],
                "actual_distance_km": plan["recommended_plan"]["distance_km"],
                "effort_feeling": "steady",
                "mood_after": "refreshed",
            },
        )
        assert create_response.status_code == 200

    ride_record_route = import_module("app.api.routes.ride_record")
    plan_repository = import_module("app.repositories.plan_result_repository")

    def fail_on_single_plan_lookup(database_url: str, request_no: str) -> dict:
        raise AssertionError(f"unexpected single get_ride_plan lookup for {request_no}")

    def batch_lookup(database_url: str, request_nos: list[str]) -> dict[str, dict]:
        return plan_repository.get_ride_plans(database_url, request_nos)

    monkeypatch.setattr(ride_record_route, "get_ride_plan", fail_on_single_plan_lookup)
    monkeypatch.setattr(ride_record_route, "get_ride_plans", batch_lookup, raising=False)

    listed = client.get("/api/v1/rides/records?limit=5")

    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 2
    assert listed.json()["items"][0]["summary_headline"]


def test_get_ride_record_returns_not_found_for_missing_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.get("/api/v1/rides/records/RR-NOT-FOUND")

    assert response.status_code == 404
    assert response.json()["detail"] == "ride-record-not-found"
