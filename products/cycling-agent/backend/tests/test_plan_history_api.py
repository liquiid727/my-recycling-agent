"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_get_ride_plan_returns_persisted_payload(tmp_path, monkeypatch, dynamic_route_provider, dynamic_poi_provider) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app(route_provider=dynamic_route_provider, poi_provider=dynamic_poi_provider))

    create_response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，最好风景好一点", "target_date": "2026-05-30"},
    )
    assert create_response.status_code == 200

    request_no = create_response.json()["request_no"]
    detail_response = client.get(f"/api/v1/ride/plan/{request_no}")

    assert detail_response.status_code == 200
    assert detail_response.json()["recommended_plan"]["route_code"].startswith("DYN-HANGZHOU-")
