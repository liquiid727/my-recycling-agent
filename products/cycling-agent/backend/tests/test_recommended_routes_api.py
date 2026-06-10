"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_recommended_routes_filters_by_origin_region_and_style(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/routes/recommended",
        params={"city_code": "hangzhou", "origin_region": "滨江", "ride_style": "scenic_relaxed"},
    )

    assert response.status_code == 200
    routes = response.json()
    assert routes
    assert routes[0]["route_code"] == "HZ-RIVER-001"
