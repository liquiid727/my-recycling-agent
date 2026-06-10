"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_route_detail_returns_supply_points_and_time_slots(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.get("/api/v1/routes/HZ-RIVER-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["route_code"] == "HZ-RIVER-001"
    assert payload["start_point_name"] == "闻涛路滨江段"
    assert payload["best_time_slots"]
    assert payload["supply_points"][0]["name"]
    assert payload["bailout_options"][0]["reason"]
