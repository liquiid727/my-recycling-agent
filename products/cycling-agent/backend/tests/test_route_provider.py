"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from app.providers.route_provider import AMapRouteProvider, LocalRouteProvider


def test_local_route_provider_estimates_known_user_start_approach() -> None:
    provider = LocalRouteProvider()

    context = provider.get_route_context(
        {
            "route_code": "HZ-RIVER-001",
            "city_code": "hangzhou",
            "start_point_name": "闻涛路滨江段",
            "start_point_lng": 120.2103,
            "start_point_lat": 30.2064,
            "end_point_name": "钱塘江南岸观景折返点",
            "loop_type": "out_and_back",
            "distance_km": 42,
            "estimated_duration_hours": 2.8,
            "surface_type": "greenway",
        },
        {"origin_region": "拱墅", "start_point": "沈塘桥"},
    )

    assert context["fact_source"] == "template+local-approach"
    assert context["user_start_point"]["name"] == "沈塘桥"
    assert context["user_start_point"]["longitude"] is not None
    assert context["template_start_point"]["name"] == "闻涛路滨江段"
    assert context["approach_distance_km"] is not None
    assert context["approach_distance_km"] > 0
    assert context["approach_duration_hours"] is not None
    assert context["total_distance_km"] > context["template_distance_km"]
    assert context["total_duration_hours"] > context["template_duration_hours"]
    assert "fallback_reason" not in context


class MockResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


def test_amap_route_provider_normalizes_reverse_geocode_and_direction() -> None:
    calls: list[str] = []

    def fake_get(url: str, *, params: dict, timeout: float):
        calls.append(url)
        if url.endswith("/v3/geocode/regeo"):
            return MockResponse(
                {
                    "status": "1",
                    "regeocode": {
                        "addressComponent": {"district": "滨江区", "city": "杭州市", "province": "浙江省"},
                        "roads": [{"name": "闻涛路"}],
                    },
                }
            )
        if url.endswith("/v3/geocode/geo"):
            return MockResponse({"status": "1", "geocodes": [{"location": "120.2200,30.2200"}]})
        if url.endswith("/v4/direction/bicycling"):
            return MockResponse(
                {
                    "errcode": 0,
                    "data": {
                        "paths": [
                            {
                                "distance": "12000",
                                "duration": "2400",
                                "rides": [
                                    {
                                        "instruction": "沿江直行",
                                        "polyline": "120.2103,30.2064;120.2200,30.2200",
                                    }
                                ],
                            }
                        ]
                    },
                }
            )
        raise AssertionError(f"unexpected-url:{url}")

    provider = AMapRouteProvider(
        base_url="https://restapi.amap.com",
        api_key="test-key",
        timeout_seconds=5,
        http_get=fake_get,
    )

    context = provider.get_route_context(
        {
            "route_code": "HZ-RIVER-001",
            "city_code": "hangzhou",
            "start_point_name": "闻涛路滨江段",
            "start_point_lng": 120.2103,
            "start_point_lat": 30.2064,
            "end_point_name": "钱塘江南岸观景折返点",
            "loop_type": "out_and_back",
            "distance_km": 42,
            "estimated_duration_hours": 2.8,
            "surface_type": "greenway",
        },
        {"origin_region": "滨江"},
    )

    assert context["provider_name"] == "amap-route"
    assert context["start_region"] == "滨江区"
    assert context["road_context"]["road_name"] == "闻涛路"
    assert context["distance_km"] == 42.0
    assert context["total_distance_km"] == 42.0
    assert context["polyline"] == [
        {"longitude": 120.2103, "latitude": 30.2064},
        {"longitude": 120.22, "latitude": 30.22},
    ]
    assert calls


def test_amap_route_provider_adds_user_start_approach_to_template_route() -> None:
    def fake_get(url: str, *, params: dict, timeout: float):
        if url.endswith("/v3/geocode/geo"):
            return MockResponse({"status": "1", "geocodes": [{"location": "120.3000,30.3000"}]})
        if url.endswith("/v3/geocode/regeo"):
            return MockResponse(
                {
                    "status": "1",
                    "regeocode": {
                        "addressComponent": {"district": "滨江区", "city": "杭州市", "province": "浙江省"},
                        "roads": [{"name": "用户起点路"}],
                    },
                }
            )
        if url.endswith("/v4/direction/bicycling"):
            if params["origin"].startswith("120.3,30.3"):
                return MockResponse(
                    {
                        "errcode": 0,
                        "data": {
                            "paths": [
                                {
                                    "distance": "8000",
                                    "duration": "1800",
                                    "rides": [{"instruction": "去模板起点", "polyline": "120.3000,30.3000;120.2103,30.2064"}],
                                }
                            ]
                        },
                    }
                )
            return MockResponse(
                {
                    "errcode": 0,
                    "data": {
                        "paths": [
                            {
                                "distance": "12000",
                                "duration": "2400",
                                "rides": [{"instruction": "主路线", "polyline": "120.2103,30.2064;120.2200,30.2200"}],
                            }
                        ]
                    },
                }
            )
        raise AssertionError(f"unexpected-url:{url}")

    provider = AMapRouteProvider(
        base_url="https://restapi.amap.com",
        api_key="test-key",
        timeout_seconds=5,
        http_get=fake_get,
    )

    context = provider.get_route_context(
        {
            "route_code": "HZ-RIVER-001",
            "city_code": "hangzhou",
            "start_point_name": "闻涛路滨江段",
            "start_point_lng": 120.2103,
            "start_point_lat": 30.2064,
            "end_point_name": "钱塘江南岸观景折返点",
            "loop_type": "out_and_back",
            "distance_km": 42,
            "estimated_duration_hours": 2.8,
            "surface_type": "greenway",
        },
        {"origin_region": "滨江", "start_point": "用户小区门口"},
    )

    assert context["user_start_point"]["name"] == "用户小区门口"
    assert context["template_start_point"]["name"] == "闻涛路滨江段"
    assert context["approach_distance_km"] == 8.0
    assert context["approach_duration_hours"] == 0.5
    assert context["template_distance_km"] == 42.0
    assert context["template_duration_hours"] == 2.8
    assert context["total_distance_km"] == 50.0
    assert context["total_duration_hours"] == 3.3


def test_amap_route_provider_get_cycling_path_falls_back_to_endpoint_polyline_when_rides_empty() -> None:
    def fake_get(url: str, *, params: dict, timeout: float):
        assert url.endswith("/v4/direction/bicycling")
        return MockResponse(
            {
                "errcode": 0,
                "data": {
                    "paths": [
                        {
                            "distance": "2800",
                            "duration": "650",
                            "rides": [],
                        }
                    ]
                },
            }
        )

    provider = AMapRouteProvider(
        base_url="https://restapi.amap.com",
        api_key="test-key",
        timeout_seconds=5,
        http_get=fake_get,
    )

    path = provider.get_cycling_path(
        {"name": "起点", "longitude": 120.1, "latitude": 30.1},
        {"name": "终点", "longitude": 120.2, "latitude": 30.2},
    )

    assert path["distance_km"] == 2.8
    assert path["polyline"] == [
        {"longitude": 120.1, "latitude": 30.1},
        {"longitude": 120.2, "latitude": 30.2},
    ]
