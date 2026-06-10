"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from app.agents.query_parser_agent import build_clarification_prompt, enrich_parsed_constraints, parse_query_fallback


def test_parse_query_extracts_origin_hours_and_style() -> None:
    parsed = parse_query_fallback("周六从闻涛路滨江段出发骑3小时，不想太累，风景好一点")

    assert parsed["origin_region"] == "滨江"
    assert parsed["start_point"] == "闻涛路滨江段"
    assert parsed["available_hours"] == 3
    assert parsed["target_distance_km"] is None
    assert parsed["ride_style"] == "scenic_relaxed"
    assert parsed["missing_fields"] == []


def test_parse_query_marks_missing_fields_and_generates_clarification_prompt() -> None:
    parsed = parse_query_fallback("周六想骑轻松一点，最好风景好")

    assert parsed["origin_region"] is None
    assert "available_hours_or_target_distance_km" in parsed["missing_fields"]
    assert build_clarification_prompt(parsed) is not None


def test_parse_query_extracts_distance_and_enriches_profile_fields() -> None:
    parsed = enrich_parsed_constraints(
        parse_query_fallback("周六从闻涛路滨江段出发骑40公里，最好轻松一点"),
        {"fitness_level": "medium", "slope_tolerance": "avoid"},
    )

    assert parsed["target_distance_km"] == 40
    assert parsed["fitness_level"] == "medium"
    assert parsed["slope_tolerance"] == "avoid"


def test_parse_query_detects_vague_evening_city_ride() -> None:
    parsed = parse_query_fallback("我今天晚上想出去骑行一下")

    assert parsed["planning_scene"] == "city_ride"
    assert parsed["duration_bucket"] == "evening"
    assert parsed["missing_fields"] == ["start_point", "available_hours_or_target_distance_km"]


def test_parse_query_detects_weekend_trip_and_destination_duration() -> None:
    parsed = parse_query_fallback("这周末想去千岛湖骑两天")

    assert parsed["planning_scene"] == "weekend_trip"
    assert parsed["duration_bucket"] == "two_day"
    assert "千岛湖" in parsed["destination_preferences"]
    assert "overnight_preference" not in parsed["missing_fields"]


def test_parse_query_detects_weekend_trip_missing_overnight_preference() -> None:
    parsed = parse_query_fallback("周末想出去骑车，附近有什么推荐线路么")

    assert parsed["planning_scene"] == "weekend_trip"
    assert "start_point" in parsed["missing_fields"]
    assert "duration_bucket" in parsed["missing_fields"]
    assert "overnight_preference" in parsed["missing_fields"]


def test_parse_query_detects_evening_start_point_and_slope_preference() -> None:
    parsed = parse_query_fallback("今晚从闻涛路滨江段出发骑2小时，不要爬坡")

    assert parsed["planning_scene"] == "city_ride"
    assert parsed["duration_bucket"] == "evening"
    assert parsed["start_point"] == "闻涛路滨江段"
    assert parsed["available_hours"] == 2
    assert parsed["slope_tolerance"] == "avoid"


def test_parse_query_accepts_chat_follow_up_location_and_hour_range() -> None:
    parsed = parse_query_fallback("我今天晚上想出去骑行一下；我在沈塘桥，就这里骑行2-4h吧 轻松点 现在出发")

    assert parsed["planning_scene"] == "city_ride"
    assert parsed["duration_bucket"] == "evening"
    assert parsed["start_point"] == "沈塘桥"
    assert parsed["available_hours"] == 4
    assert parsed["ride_style"] == "scenic_relaxed"
    assert parsed["slope_tolerance"] == "avoid"
    assert parsed["missing_fields"] == []


def test_parse_query_accepts_bare_nearby_location_without_treating_intent_as_place() -> None:
    parsed = parse_query_fallback("杭州东附近，骑两个小时")

    assert parsed["start_point"] == "杭州东"
    assert parsed["available_hours"] == 2
    assert parsed["missing_fields"] == []
