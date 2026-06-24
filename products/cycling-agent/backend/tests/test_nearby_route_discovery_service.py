"""CN: 近场路线发现测试，验证基于出发点和周边 POI 生成动态骑行候选。
EN: Nearby route discovery tests for generating dynamic candidates from origin and nearby POIs.
"""

from app.services.nearby_route_discovery_service import discover_nearby_route_candidates


class StubRouteProvider:
    provider_name = "stub-route"

    def resolve_point(self, address: str, *, city_code: str) -> dict:
        assert address == "沈塘桥"
        return {"name": address, "longitude": 120.1518, "latitude": 30.2895, "source": "stub-geocode"}

    def get_cycling_path(self, start_point: dict, end_point: dict) -> dict:
        if end_point["name"] == "街角咖啡":
            distance_km = 0.5
            duration_hours = 0.04
        else:
            distance_km = 6.2
            duration_hours = 0.42
        return {
            "distance_km": distance_km,
            "estimated_duration_hours": duration_hours,
            "polyline": [
                {"longitude": start_point["longitude"], "latitude": start_point["latitude"]},
                {"longitude": end_point["longitude"], "latitude": end_point["latitude"]},
            ],
        }


class ExpansionRouteProvider(StubRouteProvider):
    def get_cycling_path(self, start_point: dict, end_point: dict) -> dict:
        distance_by_pair = {
            ("沈塘桥", "市民公园"): (2.8, 0.18),
            ("沈塘桥", "运河文化公园"): (2.6, 0.16),
            ("沈塘桥", "朝晖文化公园"): (5.6, 0.36),
            ("市民公园", "运河文化公园"): (2.4, 0.15),
            ("运河文化公园", "朝晖文化公园"): (4.0, 0.25),
            ("朝晖文化公园", "沈塘桥"): (5.6, 0.36),
        }
        distance_km, duration_hours = distance_by_pair.get(
            (start_point["name"], end_point["name"]),
            distance_by_pair.get((end_point["name"], start_point["name"]), (1.0, 0.06)),
        )
        return {
            "distance_km": distance_km,
            "estimated_duration_hours": duration_hours,
            "polyline": [
                {"longitude": start_point["longitude"], "latitude": start_point["latitude"]},
                {"longitude": end_point["longitude"], "latitude": end_point["latitude"]},
            ],
        }


class StubPoiProvider:
    provider_name = "stub-poi"

    def search_route_anchors(self, *, longitude: float, latitude: float, city_code: str, ride_style: str | None = None) -> list[dict]:
        return [
            {
                "name": "街角咖啡",
                "type": "咖啡店",
                "address": "拱墅区",
                "longitude": 120.150,
                "latitude": 30.290,
            },
            {
                "name": "市民公园地下停车场",
                "type": "交通设施服务",
                "address": "拱墅区",
                "longitude": 120.146,
                "latitude": 30.309,
            },
            {
                "name": "运河亚运公园",
                "type": "公园",
                "address": "拱墅区",
                "longitude": 120.145,
                "latitude": 30.31,
            }
        ]


class ExpansionPoiProvider:
    provider_name = "expansion-poi"

    def search_route_anchors(self, *, longitude: float, latitude: float, city_code: str, ride_style: str | None = None) -> list[dict]:
        return [
            {"name": "市民公园", "type": "公园", "address": "拱墅区", "longitude": 120.156, "latitude": 30.274},
            {"name": "运河文化公园", "type": "公园", "address": "拱墅区", "longitude": 120.157, "latitude": 30.284},
            {"name": "朝晖文化公园", "type": "公园", "address": "拱墅区", "longitude": 120.165, "latitude": 30.287},
        ]


def test_discover_nearby_route_candidates_builds_dynamic_out_and_back_route() -> None:
    routes = discover_nearby_route_candidates(
        constraints={"start_point": "沈塘桥", "available_hours": 2, "ride_style": "scenic_relaxed"},
        city_code="hangzhou",
        route_provider=StubRouteProvider(),
        poi_provider=StubPoiProvider(),
    )

    assert len(routes) == 1
    route = routes[0]
    assert route["route_source"] == "dynamic_nearby"
    assert route["route_code"].startswith("DYN-HANGZHOU-")
    assert route["name"] == "沈塘桥-运河亚运公园休闲往返线"
    assert route["start_point_name"] == "沈塘桥"
    assert route["end_point_name"] == "运河亚运公园"
    assert route["distance_km"] == 12.4
    assert route["estimated_duration_hours"] == 0.84
    assert route["route_context"]["provider_name"] == "dynamic-nearby-route"
    assert route["route_context"]["fact_source"] == "amap-dynamic"
    assert route["route_context"]["total_distance_km"] == 12.4
    assert route["route_context"]["total_duration_hours"] == 0.84
    assert route["route_context"]["template"] is None
    assert route["route_context"]["live"]["fact_source"] == "amap-dynamic"
    assert route["route_context"]["resolved"]["metric_source"] == "dynamic-live"


def test_discover_nearby_route_candidates_expands_short_anchors_into_multi_anchor_loop() -> None:
    routes = discover_nearby_route_candidates(
        constraints={"start_point": "沈塘桥", "available_hours": 2, "ride_style": "scenic_relaxed"},
        city_code="hangzhou",
        route_provider=ExpansionRouteProvider(),
        poi_provider=ExpansionPoiProvider(),
    )

    assert routes[0]["loop_type"] == "multi_anchor_loop"
    assert routes[0]["name"] == "沈塘桥-市民公园-运河文化公园-朝晖文化公园休闲环线"
    assert routes[0]["distance_km"] == 14.8
    assert routes[0]["estimated_duration_hours"] == 0.94
    assert routes[0]["route_context"]["loop_type"] == "multi_anchor_loop"
    assert routes[0]["route_context"]["total_distance_km"] == 14.8
    assert routes[0]["route_context"]["template"] is None
    assert routes[0]["route_context"]["resolved"]["total_distance_km"] == 14.8
    assert "dynamic-route-shorter-than-plan" not in routes[0]["constraint_warnings"]
