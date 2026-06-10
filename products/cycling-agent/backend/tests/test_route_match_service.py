"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from app.services.route_match_service import rank_route_candidates


def test_rank_route_candidates_prefers_easy_scenic_routes_for_relaxed_query() -> None:
    routes = [
        {
            "name": "钱塘江线",
            "difficulty_level": "easy",
            "scenic_score": 8,
            "estimated_duration_hours": 2.8,
        },
        {
            "name": "龙井线",
            "difficulty_level": "medium",
            "scenic_score": 9,
            "estimated_duration_hours": 3.2,
        },
    ]
    constraints = {"available_hours": 3, "ride_style": "scenic_relaxed"}

    ranked = rank_route_candidates(routes, constraints)

    assert ranked[0]["name"] == "钱塘江线"


def test_rank_route_candidates_prefers_origin_and_style_matching_route() -> None:
    routes = [
        {
            "name": "钱塘江线",
            "district_tags": ["滨江"],
            "ride_style_tags": ["relaxed", "scenic"],
            "difficulty_level": "easy",
            "scenic_score": 8,
            "estimated_duration_hours": 2.8,
        },
        {
            "name": "龙井线",
            "district_tags": ["西湖", "龙井"],
            "ride_style_tags": ["climb", "scenic"],
            "difficulty_level": "medium",
            "scenic_score": 9,
            "estimated_duration_hours": 3.2,
        },
    ]
    constraints = {"origin_region": "西湖", "available_hours": 3, "ride_style": "climb"}

    ranked = rank_route_candidates(routes, constraints)

    assert ranked[0]["name"] == "龙井线"


def test_rank_route_candidates_penalizes_far_approach_from_user_start_point() -> None:
    routes = [
        {
            "name": "远处好看路线",
            "district_tags": ["滨江"],
            "ride_style_tags": ["relaxed", "scenic"],
            "difficulty_level": "easy",
            "scenic_score": 10,
            "estimated_duration_hours": 2.8,
            "distance_km": 42,
            "route_context": {
                "approach_distance_km": 18,
                "approach_duration_hours": 1.2,
                "total_distance_km": 60,
                "total_duration_hours": 4.0,
            },
        },
        {
            "name": "近处普通路线",
            "district_tags": ["滨江"],
            "ride_style_tags": ["relaxed", "scenic"],
            "difficulty_level": "easy",
            "scenic_score": 7,
            "estimated_duration_hours": 2.6,
            "distance_km": 32,
            "route_context": {
                "approach_distance_km": 1.5,
                "approach_duration_hours": 0.12,
                "total_distance_km": 33.5,
                "total_duration_hours": 2.72,
            },
        },
    ]
    constraints = {"origin_region": "滨江", "start_point": "用户小区门口", "available_hours": 3, "target_distance_km": 35, "ride_style": "scenic_relaxed"}

    ranked = rank_route_candidates(routes, constraints)

    assert ranked[0]["name"] == "近处普通路线"
    assert all(route["name"] != "远处好看路线" for route in ranked)


def test_rank_route_candidates_returns_best_soft_match_when_strict_filters_empty() -> None:
    routes = [
        {
            "name": "沈塘桥到滨江休闲线",
            "district_tags": ["滨江"],
            "ride_style_tags": ["relaxed", "scenic"],
            "difficulty_level": "easy",
            "scenic_score": 8,
            "estimated_duration_hours": 2.8,
            "distance_km": 42,
            "route_context": {
                "approach_distance_km": 14.4,
                "approach_duration_hours": 0.96,
                "total_distance_km": 56.4,
                "total_duration_hours": 3.76,
            },
        },
        {
            "name": "沈塘桥到湘湖休闲线",
            "district_tags": ["湘湖"],
            "ride_style_tags": ["relaxed", "scenic"],
            "difficulty_level": "easy",
            "scenic_score": 8,
            "estimated_duration_hours": 2.4,
            "distance_km": 30,
            "route_context": {
                "approach_distance_km": 21.5,
                "approach_duration_hours": 1.43,
                "total_distance_km": 51.5,
                "total_duration_hours": 3.83,
            },
        },
    ]
    constraints = {"origin_region": "杭州", "start_point": "沈塘桥", "available_hours": 3, "ride_style": "scenic_relaxed"}

    ranked = rank_route_candidates(routes, constraints)

    assert ranked
    assert ranked[0]["name"] == "沈塘桥到滨江休闲线"
    assert ranked[0]["constraint_warnings"]
