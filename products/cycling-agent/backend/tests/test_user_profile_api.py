"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_default_user_profile_can_be_saved_and_loaded(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    initial = client.get("/api/v1/profile/default")
    assert initial.status_code == 200
    assert initial.json()["uid"] is None

    saved = client.put(
        "/api/v1/profile/default",
        json={
            "home_region": "滨江",
            "fitness_level": "medium",
            "ride_style_preferences": ["scenic", "relaxed"],
            "slope_tolerance": "avoid",
        },
    )
    assert saved.status_code == 200
    saved_payload = saved.json()
    assert saved_payload["id"]
    assert saved_payload["uid"] == "00000001"
    assert saved_payload["home_region"] == "滨江"

    loaded = client.get("/api/v1/profile/default")
    assert loaded.status_code == 200
    loaded_payload = loaded.json()
    assert loaded_payload["uid"] == "00000001"
    assert loaded_payload["ride_style_preferences"] == ["scenic", "relaxed"]
