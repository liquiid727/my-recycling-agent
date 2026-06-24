"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from app.providers.poi_provider import AMapPoiProvider


class MockResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


def test_amap_poi_provider_normalizes_supply_labels() -> None:
    def fake_get(url: str, *, params: dict, timeout: float):
        assert url.endswith("/v5/place/around")
        return MockResponse(
            {
                "status": "1",
                "pois": [
                    {"name": "江边便利店", "type": "购物服务;便民商店/便利店", "address": "闻涛路", "location": "120.21,30.20"},
                    {"name": "湖畔咖啡", "type": "餐饮服务;咖啡厅", "address": "江边", "location": "120.22,30.21"},
                ],
            }
        )

    provider = AMapPoiProvider(
        base_url="https://restapi.amap.com",
        api_key="test-key",
        timeout_seconds=5,
        http_get=fake_get,
    )

    context = provider.get_poi_context(
        {
            "start_point_lng": 120.2103,
            "start_point_lat": 30.2064,
            "bailout_options": [{"name": "奥体中途折返"}],
        }
    )

    assert context["provider_name"] == "amap-poi"
    assert context["poi_summary"]["supply_count"] == 2
    assert context["poi_summary"]["supply_labels"][0] == "江边便利店(便利店)"
    assert context["poi_summary"]["source_layer"] == "mixed"
    assert context["poi_summary"]["template"]["bailout_items"][0]["name"] == "奥体中途折返"
    assert context["poi_summary"]["live"]["supply_items"][0]["name"] == "江边便利店"
