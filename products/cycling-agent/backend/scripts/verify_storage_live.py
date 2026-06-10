"""CN: 存储 live 验证脚本，用 PostgreSQL 和 Redis 配置检查基础设施适配。
EN: Storage live verification script for PostgreSQL and Redis infrastructure adapters.
"""

from __future__ import annotations

import json
import os
import sys

from fastapi.testclient import TestClient

from app.main import create_app


def main() -> int:
    database_url = os.environ.get("CYCLING_AGENT_DATABASE_URL")
    redis_url = os.environ.get("CYCLING_AGENT_REDIS_URL")
    if not database_url or not database_url.startswith(("postgres://", "postgresql://")):
        print("missing PostgreSQL database url: set CYCLING_AGENT_DATABASE_URL to a postgres url", file=sys.stderr)
        return 2
    if not redis_url:
        print("missing Redis url: set CYCLING_AGENT_REDIS_URL", file=sys.stderr)
        return 2

    client = TestClient(create_app())
    request_body = {
        "query": "周六从滨江出发骑3小时，不想太累，风景好一点",
        "target_date": "2026-05-30",
    }

    first = client.post("/api/v1/ride/plan", json=request_body)
    first.raise_for_status()
    first_payload = first.json()

    second = client.post("/api/v1/ride/plan", json=request_body)
    second.raise_for_status()
    second_payload = second.json()

    if second_payload["tool_trace"][0]["stage_name"] != "plan_cache":
        print("expected second request to hit plan_cache", file=sys.stderr)
        return 1

    strategy = client.post(
        "/api/v1/admin/city-strategy",
        json={
            "city_code": "hangzhou",
            "config_type": "risk_bias",
            "config_key": "xianghu_bonus",
            "config_value": {"district_tags": ["湘湖"], "city_bonus": 0.5},
            "status": "active",
        },
    )
    strategy.raise_for_status()

    third = client.post("/api/v1/ride/plan", json=request_body)
    third.raise_for_status()
    third_payload = third.json()
    if third_payload["tool_trace"][0]["stage_name"] == "plan_cache":
        print("expected admin update to invalidate ride-plan cache", file=sys.stderr)
        return 1

    audit = client.get(f"/api/v1/admin/planning-audit/{third_payload['request_no']}")
    audit.raise_for_status()

    output = {
        "first_request_no": first_payload["request_no"],
        "second_request_no": second_payload["request_no"],
        "third_request_no": third_payload["request_no"],
        "second_first_stage": second_payload["tool_trace"][0],
        "third_first_stage": third_payload["tool_trace"][0],
        "audit_summary": {
            "decision_no": audit.json()["decision_result"]["decision_no"],
            "risk_count": len(audit.json()["risk_assessments"]),
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
