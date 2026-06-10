"""CN: Provider 配置测试，验证显式 provider 模式缺配置时 fail fast。
EN: Provider config tests for fail-fast behavior when explicit provider modes miss required config.
"""

import pytest

from app.main import create_app


def test_create_app_requires_amap_key_when_route_provider_mode_is_amap(monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_ROUTE_PROVIDER_MODE", "amap")
    monkeypatch.delenv("CYCLING_AGENT_AMAP_WEB_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="cycling-agent-amap-key-missing"):
        create_app()


def test_create_app_requires_amap_key_when_poi_provider_mode_is_amap(monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_POI_PROVIDER_MODE", "amap")
    monkeypatch.delenv("CYCLING_AGENT_AMAP_WEB_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="cycling-agent-amap-key-missing"):
        create_app()
