"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from datetime import date

from fastapi.testclient import TestClient

from app.main import create_app


class StubWeatherProvider:
    def get_weather_snapshot(self, *, city_code: str, region_code: str, forecast_date: date) -> dict:
        return {
            "region_code": region_code,
            "forecast_date": str(forecast_date),
            "temperature_min": 22.0,
            "temperature_max": 31.0,
            "precipitation_probability": 0.15,
            "wind_speed": 4.8,
            "wind_direction": "SE",
            "weather_summary": "cloudy",
            "provider_name": "stub",
            "raw_payload": {},
        }


class StubRouteProvider:
    provider_name = "stub-route"

    def get_route_context(self, route: dict, constraints: dict) -> dict:
        return {
            "provider_name": self.provider_name,
            "fact_source": "template+stub-approach",
            "start_region": constraints["origin_region"],
            "user_start_point": {
                "name": constraints["start_point"],
                "longitude": 120.3000,
                "latitude": 30.3000,
            },
            "template_start_point": {
                "name": route["start_point_name"],
                "longitude": route["start_point_lng"],
                "latitude": route["start_point_lat"],
            },
            "approach_distance_km": 8.0,
            "approach_duration_hours": 0.5,
            "template_distance_km": route["distance_km"],
            "template_duration_hours": route["estimated_duration_hours"],
            "total_distance_km": route["distance_km"] + 8.0,
            "total_duration_hours": route["estimated_duration_hours"] + 0.5,
            "distance_km": route["distance_km"] + 8.0,
            "estimated_duration_hours": route["estimated_duration_hours"] + 0.5,
        }


class SoftMatchRouteProvider:
    provider_name = "soft-match-route"

    def get_route_context(self, route: dict, constraints: dict) -> dict:
        duration_by_code = {
            "HZ-RIVER-001": (14.4, 0.96),
            "HZ-HILL-002": (8.4, 0.56),
            "HZ-LEISURE-003": (21.5, 1.43),
            "HZ-LOOP-004": (17.0, 1.13),
            "HZ-SUBURB-005": (15.4, 1.02),
        }
        approach_distance_km, approach_duration_hours = duration_by_code[route["route_code"]]
        return {
            "provider_name": self.provider_name,
            "fact_source": "template+stub-approach",
            "user_start_point": {"name": constraints["start_point"], "longitude": 120.1518, "latitude": 30.2895},
            "template_start_point": {
                "name": route["start_point_name"],
                "longitude": route["start_point_lng"],
                "latitude": route["start_point_lat"],
            },
            "approach_distance_km": approach_distance_km,
            "approach_duration_hours": approach_duration_hours,
            "template_distance_km": route["distance_km"],
            "template_duration_hours": route["estimated_duration_hours"],
            "total_distance_km": round(route["distance_km"] + approach_distance_km, 1),
            "total_duration_hours": round(route["estimated_duration_hours"] + approach_duration_hours, 2),
            "distance_km": round(route["distance_km"] + approach_distance_km, 1),
            "estimated_duration_hours": round(route["estimated_duration_hours"] + approach_duration_hours, 2),
        }


class DynamicRouteProvider:
    provider_name = "dynamic-route"

    def resolve_point(self, address: str, *, city_code: str) -> dict:
        return {"name": address, "longitude": 120.1518, "latitude": 30.2895, "source": "stub-geocode"}

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


class EmptyDynamicPoiProvider(DynamicPoiProvider):
    def search_route_anchors(self, *, longitude: float, latitude: float, city_code: str, ride_style: str | None = None) -> list[dict]:
        return []


def test_post_ride_plan_returns_recommendation_payload() -> None:
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=DynamicRouteProvider(),
            poi_provider=DynamicPoiProvider(),
        )
    )
    response = client.post(
        "/api/v1/ride/plan",
        json={
            "query": "周六从闻涛路滨江段出发骑10公里，不想太累，风景好一点",
            "target_date": "2026-05-30",
            "user_profile": {"fitness_level": "medium", "slope_tolerance": "avoid"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["parsed_constraints"]["target_distance_km"] == 10
    assert body["parsed_constraints"]["fitness_level"] == "medium"
    assert body["parsed_constraints"]["slope_tolerance"] == "avoid"
    assert body["recommended_plan"]["route_code"].startswith("DYN-HANGZHOU-")
    assert body["alternatives"] == []
    assert body["decision"]["intent"] == "ride_plan"
    assert body["plan"]["kind"] == "route"
    assert body["plan"]["code"] == body["recommended_plan"]["route_code"]
    assert body["equipment"]["items"]
    assert body["fallback"]["status"] in {"stable", "degraded"}
    assert body["decision_summary"]["go_decision"] in {"go", "caution", "no_go"}
    assert body["decision_summary"]["decision_title"]
    assert body["decision_summary"]["equipment_advice"]


def test_post_ride_plan_returns_clarification_prompt_when_query_missing_key_fields() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))
    response = client.post(
        "/api/v1/ride/plan/preflight",
        json={"query": "周六想骑轻松一点，最好风景好", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["clarification_prompt"] is not None


def test_preflight_requires_exact_start_point_before_planning() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))
    response = client.post(
        "/api/v1/ride/plan/preflight",
        json={"query": "周六从滨江出发骑3小时，不想太累，最好风景好", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is False
    assert body["missing_core_fields"] == ["start_point"]
    assert "准确出发地点" in body["clarification_prompt"]


def test_preflight_returns_missing_core_fields_without_planning() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))
    response = client.post(
        "/api/v1/ride/plan/preflight",
        json={"query": "周六想骑轻松一点，最好风景好", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is False
    assert body["parsed_constraints"]["origin_region"] is None
    assert body["missing_core_fields"] == ["start_point", "available_hours_or_target_distance_km"]
    assert body["clarification_prompt"] is not None


def test_preflight_accepts_intent_only_weekend_payload_and_maps_execution_fields() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))
    response = client.post(
        "/api/v1/ride/plan/preflight",
        json={
            "query": "周末推荐一下",
            "target_date": "2026-05-30",
            "intent": "weekend_recommendation",
            "input_mode": "structured",
            "structured_constraints": {
                "start_point": "闻涛路滨江段",
                "duration_bucket": "two_day",
                "overnight_preference": "required",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["parsed_constraints"]["intent"] == "weekend_recommendation"
    assert body["parsed_constraints"]["planning_mode"] == "nearby_trip"
    assert body["parsed_constraints"]["planning_scene"] == "weekend_trip"


def test_post_ride_plan_rejects_missing_core_fields_before_planning() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))
    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六想骑轻松一点，最好风景好", "target_date": "2026-05-30"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "ride-plan-core-fields-missing"


def test_post_ride_plan_accepts_structured_constraints_and_returns_dynamic_input_summary_and_route_map() -> None:
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=DynamicRouteProvider(),
            poi_provider=DynamicPoiProvider(),
        )
    )
    response = client.post(
        "/api/v1/ride/plan",
        json={
            "input_mode": "structured",
            "query": "表单规划：周六滨江轻松风景骑",
            "target_date": "2026-05-30",
            "structured_constraints": {
                "departure_time": "07:00",
                "origin_region": "滨江",
                "start_point": "闻涛路滨江段",
                "available_hours": 3,
                "target_distance_km": 10,
                "fitness_level": "medium",
                "ride_style": "scenic_relaxed",
                "slope_tolerance": "avoid",
                "priority": "风景",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "ride_plan"
    assert body["parsed_constraints"]["origin_region"] == "滨江"
    assert body["parsed_constraints"]["start_point"] == "闻涛路滨江段"
    assert body["input_summary"] == {
        "intent": "ride_plan",
        "input_mode": "structured",
        "target_date": "2026-05-30",
        "departure_time": "07:00",
        "city_code": "hangzhou",
        "origin_region": "滨江",
        "start_point": "闻涛路滨江段",
        "available_hours": 3.0,
            "target_distance_km": 10.0,
        "fitness_level": "medium",
        "ride_style": "scenic_relaxed",
        "slope_tolerance": "avoid",
        "priority": "风景",
        "planning_scene": "city_ride",
        "defaults_applied": [],
    }
    route_map = body["route_map"]
    assert route_map["route_code"] == body["recommended_plan"]["route_code"]
    assert route_map["provider_name"] == "dynamic-nearby-route"
    assert route_map["fact_source"] == "amap-dynamic"
    assert route_map["polyline_available"] is True
    assert body["recommended_plan"]["distance_km"] == 10.0
    assert body["recommended_plan"]["estimated_duration_hours"] == 0.7
    assert body["decision_summary"]["scene"] == "city_ride"
    assert any("车灯" in item for item in body["decision_summary"]["equipment_advice"]) is False
    assert route_map["user_start_point"]["name"] == "闻涛路滨江段"
    assert route_map["template_start_point"]["name"] == "闻涛路滨江段"
    assert route_map["approach_distance_km"] == 0.0
    assert route_map["total_distance_km"] == 10.0
    assert route_map["start_point"]["name"] == "闻涛路滨江段"
    assert route_map["supply_points"]
    assert route_map["bailout_options"]


def test_post_ride_plan_prefers_dynamic_nearby_route_candidates() -> None:
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=DynamicRouteProvider(),
            poi_provider=DynamicPoiProvider(),
        )
    )
    response = client.post(
        "/api/v1/ride/plan",
        json={
            "query": "我在沈塘桥，骑2小时，轻松点",
            "target_date": "2026-06-06",
            "planning_scene": "city_ride",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["recommended_plan"]["route_code"].startswith("DYN-HANGZHOU-")
    assert body["recommended_plan"]["route_name"] == "沈塘桥-运河亚运公园休闲往返线"
    assert body["route_map"]["provider_name"] == "dynamic-nearby-route"
    assert body["route_map"]["fact_source"] == "amap-dynamic"
    assert any(item["stage_name"] == "nearby_route_discovery" and item["status"] == "success" for item in body["tool_trace"])


def test_post_ride_plan_does_not_promote_template_routes_when_dynamic_routes_are_empty() -> None:
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=DynamicRouteProvider(),
            poi_provider=EmptyDynamicPoiProvider(),
        )
    )
    response = client.post(
        "/api/v1/ride/plan",
        json={
            "query": "我在沈塘桥，骑2小时，轻松点",
            "target_date": "2026-06-06",
            "planning_scene": "city_ride",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_match"
    assert body["recommended_plan"]["route_code"] == "NO-MATCH"
    assert body["alternatives"] == []
    assert any(item["stage_name"] == "nearby_route_discovery" and item["status"] == "fallback" for item in body["tool_trace"])
    assert all(not item.get("route_code", "").startswith("HZ-") for item in [body["recommended_plan"], *body["alternatives"]])


def test_post_ride_plan_returns_no_match_for_extreme_duration_constraint() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))
    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从闻涛路滨江段出发骑12小时，不想太累，最好风景好一点", "target_date": "2026-05-30"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_match"
    assert body["recommended_plan"]["route_code"] == "NO-MATCH"
    assert body["decision_summary"]["go_decision"] == "no_go"


def test_post_ride_plan_returns_no_match_when_dynamic_route_provider_capability_is_missing() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider(), route_provider=SoftMatchRouteProvider()))
    response = client.post(
        "/api/v1/ride/plan",
        json={
            "input_mode": "structured",
            "query": "结构化规划：沈塘桥轻松骑 3 小时",
            "target_date": "2026-06-06",
            "planning_scene": "city_ride",
            "structured_constraints": {
                "origin_region": "杭州",
                "start_point": "沈塘桥",
                "available_hours": 3,
                "ride_style": "scenic_relaxed",
                "slope_tolerance": "avoid",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_match"
    assert body["recommended_plan"]["route_code"] == "NO-MATCH"
    assert "nearby-route-discovery-unavailable" in body["fallback_reason"]
    assert body["decision_summary"]["go_decision"] == "no_go"


def test_post_city_ride_evening_plan_returns_decision_first_equipment_advice() -> None:
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=DynamicRouteProvider(),
            poi_provider=DynamicPoiProvider(),
        )
    )
    response = client.post(
        "/api/v1/ride/plan",
        json={
            "query": "今晚从闻涛路滨江段出发骑2小时，不要爬坡",
            "target_date": "2026-06-06",
            "planning_scene": "city_ride",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["parsed_constraints"]["planning_scene"] == "city_ride"
    assert body["parsed_constraints"]["duration_bucket"] == "evening"
    assert body["decision_summary"]["scene"] == "city_ride"
    assert body["decision_summary"]["go_decision"] in {"go", "caution", "no_go"}
    assert any("车灯" in item for item in body["decision_summary"]["equipment_advice"])


def test_preflight_accepts_chat_follow_up_location_and_hour_range() -> None:
    client = TestClient(create_app(weather_provider=StubWeatherProvider()))
    response = client.post(
        "/api/v1/ride/plan/preflight",
        json={
            "query": "我今天晚上想出去骑行一下；我在沈塘桥，就这里骑行2-4h吧 轻松点 现在出发",
            "target_date": "2026-06-06",
            "planning_scene": "city_ride",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["missing_core_fields"] == []
    assert body["parsed_constraints"]["start_point"] == "沈塘桥"
    assert body["parsed_constraints"]["available_hours"] == 4
    assert body["clarification_prompt"] is None


def test_post_ride_plan_uses_dynamic_route_for_chat_follow_up() -> None:
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=DynamicRouteProvider(),
            poi_provider=DynamicPoiProvider(),
        )
    )
    response = client.post(
        "/api/v1/ride/plan",
        json={
            "query": "我今天晚上想出去骑行一下；我在沈塘桥，就这里骑行2-4h吧 轻松点 现在出发",
            "target_date": "2026-06-06",
            "planning_scene": "city_ride",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["parsed_constraints"]["start_point"] == "沈塘桥"
    assert "当前未按准确出发点重算接驳距离和总时长" not in body["recommended_plan"]["summary_reason"]
    assert "当前未按准确出发点重算接驳距离和总时长" not in body["decision_summary"]["decision_reason"]
    route_map = body["route_map"]
    assert route_map["user_start_point"]["name"] == "沈塘桥"
    assert route_map["provider_name"] == "dynamic-nearby-route"
    assert route_map["fact_source"] == "amap-dynamic"
    assert route_map["approach_distance_km"] == 0.0
    assert route_map["total_distance_km"] == body["recommended_plan"]["distance_km"]
    assert route_map["total_duration_hours"] == body["recommended_plan"]["estimated_duration_hours"]


def test_post_ride_plan_stream_returns_stage_updates_and_final_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(
        create_app(
            weather_provider=StubWeatherProvider(),
            route_provider=DynamicRouteProvider(),
            poi_provider=DynamicPoiProvider(),
        )
    )

    with client.stream(
        "POST",
        "/api/v1/ride/plan/stream",
            json={"query": "周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点", "target_date": "2026-05-30"},
    ) as response:
        payload = response.read().decode("utf-8")

    assert response.status_code == 200
    assert "event: planning_started" in payload
    assert "event: stage_update" in payload
    assert "event: plan_ready" in payload
    assert '"stage_name": "query_parser"' in payload
    assert '"stage_name": "decision_engine"' in payload
    assert '"request_no": "RQ-' in payload
