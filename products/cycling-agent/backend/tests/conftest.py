"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

import os

import pytest

from app.core.storage import connect, init_storage


LIVE_ENV_KEYS = [
    "CYCLING_AGENT_AMAP_WEB_API_KEY",
    "CYCLING_AGENT_LLM_API_BASE_URL",
    "CYCLING_AGENT_LLM_API_KEY",
    "CYCLING_AGENT_LLM_MODEL",
    "CYCLING_AGENT_DATABASE_URL",
    "CYCLING_AGENT_REDIS_URL",
    "CYCLING_AGENT_ROUTE_PROVIDER_MODE",
    "CYCLING_AGENT_POI_PROVIDER_MODE",
]

TEST_DATABASE_URL = os.environ.get(
    "CYCLING_AGENT_TEST_DATABASE_URL",
    "postgresql://cycling:cycling@127.0.0.1:54329/cycling_agent",
)

TRUNCATE_TABLES = [
    "post_ride_shares",
    "media_assets",
    "completed_rides",
    "risk_assessments",
    "decision_results",
    "weather_snapshots",
    "ride_requests",
    "query_logs",
    "ride_plans",
    "nearby_destinations",
    "trip_templates",
    "route_templates",
    "city_strategy_configs",
    "experience_contents",
    "lifestyle_profiles",
    "user_profiles",
]


class DynamicRouteProvider:
    provider_name = "dynamic-route"

    def resolve_point(self, address: str, *, city_code: str) -> dict:
        return {"name": address, "longitude": 120.2103, "latitude": 30.2064, "source": "stub-geocode"}

    def get_cycling_path(self, start_point: dict, end_point: dict) -> dict:
        return {
            "distance_km": 5.0,
            "estimated_duration_hours": 0.35,
            "polyline": [
                {"longitude": start_point["longitude"], "latitude": start_point["latitude"]},
                {"longitude": end_point["longitude"], "latitude": end_point["latitude"]},
            ],
        }

    def get_route_context(self, route: dict, constraints: dict) -> dict:
        return route["route_context"]


class DynamicPoiProvider:
    provider_name = "dynamic-poi"

    def search_route_anchors(self, *, longitude: float, latitude: float, city_code: str, ride_style: str | None = None) -> list[dict]:
        return [{"name": "运河亚运公园", "type": "公园", "longitude": 120.145, "latitude": 30.31}]

    def get_poi_context(self, route: dict) -> dict:
        return {
            "provider_name": self.provider_name,
            "poi_summary": {
                "supply_count": len(route.get("supply_points", [])),
                "bailout_count": len(route.get("bailout_options", [])),
                "supply_labels": [point["name"] for point in route.get("supply_points", [])],
                "bailout_labels": [option["name"] for option in route.get("bailout_options", [])],
                "fact_source": "dynamic",
            },
        }


@pytest.fixture
def dynamic_route_provider() -> DynamicRouteProvider:
    return DynamicRouteProvider()


@pytest.fixture
def dynamic_poi_provider() -> DynamicPoiProvider:
    return DynamicPoiProvider()


@pytest.fixture(autouse=True)
def isolate_live_env(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    nodeid = request.node.nodeid
    if "live_integration" in nodeid:
        if "test_storage_live_integration.py" not in nodeid:
            monkeypatch.delenv("CYCLING_AGENT_REDIS_URL", raising=False)
        return
    for key in LIVE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def set_test_database_url(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", TEST_DATABASE_URL)
    init_storage(TEST_DATABASE_URL)
    with connect(TEST_DATABASE_URL) as connection:
        connection.execute(f"TRUNCATE TABLE {', '.join(TRUNCATE_TABLES)} RESTART IDENTITY CASCADE")
    return TEST_DATABASE_URL
