"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from pathlib import Path

from app.repositories.route_template_repository import load_route_templates, save_route_template


def test_load_route_templates_returns_seeded_hangzhou_routes() -> None:
    routes = load_route_templates(
        Path(__file__).resolve().parents[2] / "data" / "hangzhou_routes.json"
    )

    assert len(routes) >= 3
    assert routes[0]["city_code"] == "hangzhou"


def test_save_route_template_assigns_route_no_and_internal_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")

    payload = {
        "route_code": "HZ-TEST-900",
        "name": "测试线",
        "city_code": "hangzhou",
        "district_tags": ["滨江"],
        "ride_style_tags": ["relaxed"],
        "distance_km": 20,
        "elevation_gain_m": 100,
        "estimated_duration_hours": 1.5,
        "difficulty_level": "easy",
        "traffic_level": "low",
        "supply_score": 6,
        "return_difficulty_score": 2,
        "scenic_score": 7,
        "beginner_friendly": True,
        "route_notes": "测试录入。",
    }

    from app.core.storage import init_storage

    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)
    saved = save_route_template(database_url, payload)

    assert saved["id"]
    assert saved["route_no"].startswith("RT-")
    assert saved["status"] == "active"
