"""CN: 新体验层 API 测试，覆盖首页内容、AI 伙伴、结果页、路线详情和生活方式偏好。
EN: Experience API tests covering homepage content, companion planning, result payloads, route detail, and lifestyle profile.
"""

from datetime import date

from fastapi.testclient import TestClient

from app.main import create_app


class StubWeatherProvider:
    def get_weather_snapshot(self, *, city_code: str, region_code: str, forecast_date: date) -> dict:
        return {
            "region_code": region_code,
            "forecast_date": str(forecast_date),
            "temperature_min": 21.0,
            "temperature_max": 27.0,
            "precipitation_probability": 0.08,
            "wind_speed": 3.5,
            "wind_direction": "SE",
            "weather_summary": "cloudy",
            "provider_name": "stub",
            "raw_payload": {},
        }


def test_experience_home_and_admin_content_can_be_loaded_and_saved(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    home_response = client.get("/api/v1/experience/home")
    assert home_response.status_code == 200
    home_payload = home_response.json()
    assert home_payload["hero"]["title"]
    assert home_payload["today_nudges"]
    assert home_payload["curated_routes"]
    assert home_payload["companion_persona"]["headline"]

    admin_response = client.get("/api/v1/admin/experience-content")
    assert admin_response.status_code == 200
    admin_payload = admin_response.json()
    assert admin_payload["hero"]["title"] == home_payload["hero"]["title"]

    updated = dict(admin_payload)
    updated["hero"]["title"] = "今天不训练，只是在城市里收集一点晚风。"
    updated["cta_footer"]["button_label"] = "从一句心情开始"

    save_response = client.put("/api/v1/admin/experience-content", json=updated)
    assert save_response.status_code == 200
    assert save_response.json()["hero"]["title"] == "今天不训练，只是在城市里收集一点晚风。"

    refreshed_home = client.get("/api/v1/experience/home")
    assert refreshed_home.status_code == 200
    refreshed_payload = refreshed_home.json()
    assert refreshed_payload["hero"]["title"] == "今天不训练，只是在城市里收集一点晚风。"
    assert refreshed_payload["cta_footer"]["button_label"] == "从一句心情开始"


def test_companion_plan_returns_clarification_for_vague_message(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))

    response = client.post(
        "/api/v1/experience/companion/plan",
        json={"message": "今天想出去骑一下"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "clarification"
    assert payload["assistant_message"]
    assert payload["suggested_prompts"]


def test_companion_plan_persists_editorial_result_and_route_detail(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))

    response = client.post(
        "/api/v1/experience/companion/plan",
        json={"message": "我在闻涛路滨江段，想轻松骑2小时，最好有江边和咖啡"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "planned"
    assert payload["request_no"].startswith("RQ-")
    assert payload["featured_plan"]["route_code"]
    assert payload["editorial_intro"]

    result_response = client.get(f"/api/v1/experience/results/{payload['request_no']}")
    assert result_response.status_code == 200
    result_payload = result_response.json()
    assert result_payload["request_no"] == payload["request_no"]
    assert result_payload["decision"]["title"]
    assert result_payload["route_story"]["route_code"] == payload["featured_plan"]["route_code"]
    assert result_payload["ride_journal_prompt"]

    detail_response = client.get(f"/api/v1/experience/routes/{payload['featured_plan']['route_code']}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["route_code"] == payload["featured_plan"]["route_code"]
    assert detail_payload["headline"]
    assert detail_payload["tags"]


def test_companion_plan_forwards_target_date_and_user_profile_to_planner(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))

    response = client.post(
        "/api/v1/experience/companion/plan",
        json={
            "message": "我在闻涛路滨江段，想骑10公里",
            "target_date": "2026-06-08",
            "user_profile": {"fitness_level": "medium", "slope_tolerance": "avoid"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    result_response = client.get(f"/api/v1/experience/results/{payload['request_no']}")
    assert result_response.status_code == 200

    plan_response = client.get(f"/api/v1/ride/plan/{payload['request_no']}")
    assert plan_response.status_code == 200
    plan_payload = plan_response.json()
    assert plan_payload["parsed_constraints"]["fitness_level"] == "medium"
    assert plan_payload["parsed_constraints"]["slope_tolerance"] == "avoid"
    assert plan_payload["weather_snapshot"]["forecast_date"] == "2026-06-08"


def test_lifestyle_profile_can_be_saved_and_loaded(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    initial = client.get("/api/v1/profile/lifestyle")
    assert initial.status_code == 200
    assert initial.json()["preferred_vibe"] is None

    save_response = client.put(
        "/api/v1/profile/lifestyle",
        json={
            "home_region": "滨江",
            "preferred_vibe": "tree_shade",
            "companion_tone": "gentle",
            "favorite_motifs": ["树荫", "咖啡", "日落"],
            "avoid_motifs": ["刷圈", "成绩", "配速"],
        },
    )
    assert save_response.status_code == 200
    saved_payload = save_response.json()
    assert saved_payload["home_region"] == "滨江"
    assert saved_payload["preferred_vibe"] == "tree_shade"

    loaded = client.get("/api/v1/profile/lifestyle")
    assert loaded.status_code == 200
    loaded_payload = loaded.json()
    assert loaded_payload["companion_tone"] == "gentle"
    assert loaded_payload["favorite_motifs"] == ["树荫", "咖啡", "日落"]
