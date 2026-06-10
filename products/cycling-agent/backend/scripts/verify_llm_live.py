"""CN: LLM live 验证脚本，用真实 OpenAI-compatible 配置检查解析和路书增强。
EN: LLM live verification script for query parsing and roadbook enhancement with real OpenAI-compatible settings.
"""

from __future__ import annotations

import json
import os
import sys

from fastapi.testclient import TestClient

from app.main import create_app


def main() -> int:
    required = [
        "CYCLING_AGENT_LLM_API_BASE_URL",
        "CYCLING_AGENT_LLM_API_KEY",
        "CYCLING_AGENT_LLM_MODEL",
    ]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        print(f"missing LLM config: {', '.join(missing)}", file=sys.stderr)
        return 2

    client = TestClient(create_app())
    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从滨江出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    )
    response.raise_for_status()
    payload = response.json()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
