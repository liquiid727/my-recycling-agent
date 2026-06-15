"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from datetime import date

from app.schemas.ride_plan import RidePlanRequestSchema


def test_ride_plan_request_accepts_minimum_payload() -> None:
    payload = RidePlanRequestSchema(
        query="周六从闻涛路滨江段出发骑3小时，不想太累",
        target_date=date(2026, 5, 30),
    )

    assert payload.city_code == "hangzhou"
    assert payload.query.startswith("周六")


def test_ride_plan_request_accepts_scene_location_and_weekend_constraints() -> None:
    payload = RidePlanRequestSchema(
        query="这周末想去千岛湖骑两天",
        target_date=date(2026, 6, 6),
        planning_mode="nearby_trip",
        planning_scene="weekend_trip",
        structured_constraints={
            "origin_location": {
                "name": "闻涛路滨江段",
                "latitude": 30.2064,
                "longitude": 120.2103,
                "source": "browser",
            },
            "start_point": "闻涛路滨江段",
            "duration_bucket": "two_day",
            "overnight_preference": "required",
            "lodging_preference": "湖边酒店",
            "cross_city_allowed": True,
        },
    )

    assert payload.planning_scene == "weekend_trip"
    assert payload.structured_constraints is not None
    assert payload.structured_constraints.origin_location is not None
    assert payload.structured_constraints.origin_location.source == "browser"
    assert payload.structured_constraints.duration_bucket == "two_day"
    assert payload.structured_constraints.overnight_preference == "required"


def test_ride_plan_request_accepts_city_ride_evening_duration() -> None:
    payload = RidePlanRequestSchema(
        query="我今天晚上想出去骑行一下",
        target_date=date(2026, 6, 6),
        planning_scene="city_ride",
        structured_constraints={
            "start_point": "闻涛路滨江段",
            "duration_bucket": "evening",
            "available_hours": 2,
        },
    )

    assert payload.planning_scene == "city_ride"
    assert payload.structured_constraints is not None
    assert payload.structured_constraints.duration_bucket == "evening"


def test_ride_plan_request_accepts_intent_only_weekend_shape() -> None:
    payload = RidePlanRequestSchema(
        query="周末推荐一下",
        target_date=date(2026, 6, 6),
        intent="weekend_recommendation",
        input_mode="structured",
        structured_constraints={
            "start_point": "闻涛路滨江段",
            "duration_bucket": "two_day",
            "overnight_preference": "required",
        },
    )

    assert payload.intent == "weekend_recommendation"
    assert payload.planning_mode is None
    assert payload.planning_scene is None
