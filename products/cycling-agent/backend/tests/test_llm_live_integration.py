"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


pytestmark = pytest.mark.skipif(
    not (
        os.environ.get("CYCLING_AGENT_LLM_API_BASE_URL")
        and os.environ.get("CYCLING_AGENT_LLM_API_KEY")
        and os.environ.get("CYCLING_AGENT_LLM_MODEL")
    ),
    reason="LLM live integration requires CYCLING_AGENT_LLM_API_BASE_URL, CYCLING_AGENT_LLM_API_KEY, CYCLING_AGENT_LLM_MODEL",
)


def test_live_llm_query_parser_and_roadbook_generator_enrich_ride_plan(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    payload = response.json()
    query_trace = next(item for item in payload["tool_trace"] if item["stage_name"] == "query_parser")
    roadbook_trace = next(item for item in payload["tool_trace"] if item["stage_name"] == "roadbook_generator")
    assert query_trace["status"] == "success"
    assert roadbook_trace["status"] == "success"
    assert payload["recommended_plan"]["route_name"]
    assert payload["roadbook"] is not None
