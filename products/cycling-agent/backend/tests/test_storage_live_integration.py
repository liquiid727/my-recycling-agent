"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


pytestmark = pytest.mark.skipif(
    not os.environ.get("CYCLING_AGENT_DATABASE_URL", "").startswith(("postgres://", "postgresql://"))
    or not os.environ.get("CYCLING_AGENT_REDIS_URL"),
    reason="requires live PostgreSQL and Redis configuration",
)


def test_live_postgres_and_redis_support_cached_ride_plans_and_admin_invalidation() -> None:
    client = TestClient(create_app())
    request_body = {
        "query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点",
        "target_date": "2026-05-30",
    }

    first = client.post("/api/v1/ride/plan", json=request_body)
    assert first.status_code == 200

    second = client.post("/api/v1/ride/plan", json=request_body)
    assert second.status_code == 200
    assert second.json()["tool_trace"][0]["stage_name"] == "plan_cache"

    create_rule = client.post(
        "/api/v1/admin/risk-rules",
        json={
            "city_code": "hangzhou",
            "rule_key": "river_heat_penalty_live",
            "rule_value": {
                "target": "weather",
                "delta": 0.2,
                "conditions": {
                    "district_tags_any": ["钱塘江"],
                    "temperature_max_gte": 30,
                    "weather_sensitivity_heat_in": ["medium", "high"],
                },
            },
            "status": "active",
        },
    )
    assert create_rule.status_code == 200

    third = client.post("/api/v1/ride/plan", json=request_body)
    assert third.status_code == 200
    assert third.json()["tool_trace"][0]["stage_name"] != "plan_cache"

    audit = client.get(f"/api/v1/admin/planning-audit/{third.json()['request_no']}")
    assert audit.status_code == 200
    assert audit.json()["decision_result"]["decision_no"].startswith("DC-")
