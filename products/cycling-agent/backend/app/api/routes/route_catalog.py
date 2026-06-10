"""CN: 路线目录 API，向前端提供推荐路线列表和单条路线详情。
EN: Route catalog API that serves recommended route lists and route detail pages.
"""

from fastapi import APIRouter, HTTPException, Query, Request

from app.repositories.route_template_repository import get_route_template, list_route_templates
from app.schemas.ride_plan import RecommendedRouteSchema, RouteDetailSchema


router = APIRouter(prefix="/api/v1/routes", tags=["routes"])


@router.get("/recommended", response_model=list[RecommendedRouteSchema])
async def list_recommended_routes(
    request: Request,
    city_code: str = Query(default="hangzhou"),
    origin_region: str | None = Query(default=None),
    ride_style: str | None = Query(default=None),
) -> list[RecommendedRouteSchema]:
    database_url = request.app.state.database_url
    routes = list_route_templates(
        database_url,
        city_code=city_code,
        origin_region=origin_region,
        ride_style=ride_style,
    )
    return [
        RecommendedRouteSchema.model_validate(
            {
                "route_code": route["route_code"],
                "route_name": route["name"],
                "distance_km": route["distance_km"],
                "elevation_gain_m": route["elevation_gain_m"],
                "estimated_duration_hours": route["estimated_duration_hours"],
                "difficulty_level": route["difficulty_level"],
                "ride_style_tags": route.get("ride_style_tags", []),
                "district_tags": route.get("district_tags", []),
            }
        )
        for route in routes
    ]


@router.get("/{route_code}", response_model=RouteDetailSchema)
async def get_route_detail(route_code: str, request: Request) -> RouteDetailSchema:
    route = get_route_template(request.app.state.database_url, route_code)
    if route is None:
        raise HTTPException(status_code=404, detail="route-not-found")
    return RouteDetailSchema.model_validate(
        {
            "route_code": route["route_code"],
            "route_name": route["name"],
            "distance_km": route["distance_km"],
            "elevation_gain_m": route["elevation_gain_m"],
            "estimated_duration_hours": route["estimated_duration_hours"],
            "difficulty_level": route["difficulty_level"],
            "ride_style_tags": route.get("ride_style_tags", []),
            "district_tags": route.get("district_tags", []),
            "city_code": route["city_code"],
            "start_point_name": route.get("start_point_name"),
            "start_point_lng": route.get("start_point_lng"),
            "start_point_lat": route.get("start_point_lat"),
            "end_point_name": route.get("end_point_name"),
            "loop_type": route.get("loop_type"),
            "season_tags": route.get("season_tags", []),
            "best_time_slots": route.get("best_time_slots", []),
            "avoid_time_slots": route.get("avoid_time_slots", []),
            "surface_type": route.get("surface_type"),
            "traffic_level": route["traffic_level"],
            "supply_score": route["supply_score"],
            "return_difficulty_score": route["return_difficulty_score"],
            "scenic_score": route["scenic_score"],
            "training_score": route.get("training_score"),
            "beginner_friendly": route["beginner_friendly"],
            "climb_segments": route.get("climb_segments", []),
            "supply_points": route.get("supply_points", []),
            "bailout_options": route.get("bailout_options", []),
            "holiday_penalty_level": route.get("holiday_penalty_level"),
            "weather_sensitivity": route.get("weather_sensitivity", {}),
            "route_notes": route.get("route_notes"),
        }
    )
