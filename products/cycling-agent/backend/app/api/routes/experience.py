"""CN: 新体验层 API，提供首页内容、AI 伙伴规划、编辑化结果页和内容后台接口。
EN: Experience API for homepage content, companion planning, editorialized results, and content-admin payloads.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Request

from app.agents.query_parser_agent import build_clarification_prompt, enrich_parsed_constraints, missing_core_fields, parse_query_fallback
from app.repositories.experience_content_repository import get_experience_content, save_experience_content
from app.repositories.nearby_trip_repository import list_nearby_destinations, list_trip_templates
from app.repositories.plan_result_repository import find_route_snapshot, get_ride_plan, save_ride_plan
from app.repositories.planning_audit_repository import save_planning_audit
from app.repositories.query_log_repository import save_query_log
from app.repositories.route_template_repository import get_route_template
from app.repositories.city_strategy_repository import list_active_city_strategy_configs
from app.repositories.risk_rule_repository import list_active_risk_rules
from app.schemas.experience import (
    CompanionFeaturedPlanSchema,
    CompanionPlanRequestSchema,
    CompanionPlanResponseSchema,
    ExperienceContentSchema,
    ExperienceDecisionSchema,
    ExperienceResultSchema,
    ExperienceRouteDetailSchema,
    ExperienceRouteStorySchema,
)
from app.schemas.ride_plan import RidePlanRequestSchema
from app.services.ride_planning_orchestrator import build_demo_plan


router = APIRouter(prefix="/api/v1/experience", tags=["experience"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin-experience"])


@router.get("/home", response_model=ExperienceContentSchema)
async def get_experience_home(request: Request) -> ExperienceContentSchema:
    return ExperienceContentSchema.model_validate(get_experience_content(request.app.state.database_url))


@admin_router.get("/experience-content", response_model=ExperienceContentSchema)
async def get_admin_experience_content(request: Request) -> ExperienceContentSchema:
    return ExperienceContentSchema.model_validate(get_experience_content(request.app.state.database_url))


@admin_router.put("/experience-content", response_model=ExperienceContentSchema)
async def put_admin_experience_content(payload: ExperienceContentSchema, request: Request) -> ExperienceContentSchema:
    saved = save_experience_content(request.app.state.database_url, payload.model_dump(mode="json"))
    return ExperienceContentSchema.model_validate(saved)


@router.post("/companion/plan", response_model=CompanionPlanResponseSchema)
async def create_companion_plan(payload: CompanionPlanRequestSchema, request: Request) -> CompanionPlanResponseSchema:
    content = get_experience_content(request.app.state.database_url)
    parsed_constraints = enrich_parsed_constraints(parse_query_fallback(payload.message), {})
    target_date = payload.target_date or date.today()
    missing = missing_core_fields(parsed_constraints, target_date=target_date)
    if missing:
        parsed_constraints["missing_fields"] = missing
        return CompanionPlanResponseSchema(
            status="clarification",
            assistant_message=build_clarification_prompt(parsed_constraints) or "告诉我你从哪里出发，想骑多久，我就能给你一页轻计划。",
            suggested_prompts=content["companion_persona"]["quick_prompts"],
        )

    request_schema = RidePlanRequestSchema(
        query=payload.message,
        target_date=target_date,
        planning_mode="nearby_trip" if parsed_constraints.get("planning_scene") == "weekend_trip" else "route",
        planning_scene=parsed_constraints.get("planning_scene") or "city_ride",
        input_mode="natural",
    )
    strategy_rules = list_active_city_strategy_configs(request.app.state.database_url, city_code=request_schema.city_code)
    risk_rules = list_active_risk_rules(request.app.state.database_url, city_code=request_schema.city_code)
    plan_payload = build_demo_plan(
        request_schema,
        llm_provider=request.app.state.llm_provider,
        weather_provider=request.app.state.weather_provider,
        route_provider=request.app.state.route_provider,
        poi_provider=request.app.state.poi_provider,
        strategy_rules=strategy_rules,
        risk_rules=risk_rules,
        nearby_destinations=list_nearby_destinations(request.app.state.database_url, city_code=request_schema.city_code),
        trip_templates=list_trip_templates(request.app.state.database_url, city_code=request_schema.city_code),
    )
    _persist_experience_plan(plan_payload, request_schema, request)
    featured_plan = _select_featured_plan(plan_payload)
    return CompanionPlanResponseSchema(
        status="planned",
        assistant_message=_build_companion_message(plan_payload),
        suggested_prompts=content["companion_persona"]["quick_prompts"],
        editorial_intro=_build_editorial_intro(plan_payload),
        request_no=plan_payload["request_no"],
        featured_plan=CompanionFeaturedPlanSchema.model_validate(featured_plan),
    )


@router.get("/results/{request_no}", response_model=ExperienceResultSchema)
async def get_experience_result(request_no: str, request: Request) -> ExperienceResultSchema:
    payload = get_ride_plan(request.app.state.database_url, request_no)
    if payload is None:
        raise HTTPException(status_code=404, detail="experience-result-not-found")
    return ExperienceResultSchema.model_validate(_build_experience_result_payload(payload))


@router.get("/routes/{route_code}", response_model=ExperienceRouteDetailSchema)
async def get_experience_route_detail(route_code: str, request: Request) -> ExperienceRouteDetailSchema:
    route = get_route_template(request.app.state.database_url, route_code)
    if route is None:
        snapshot = find_route_snapshot(request.app.state.database_url, route_code)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="experience-route-not-found")
        return ExperienceRouteDetailSchema.model_validate(
            {
                "route_code": snapshot["route_code"],
                "route_name": snapshot["route_name"],
                "headline": f"{snapshot['route_name']}：适合今天轻一点地出门",
                "summary": snapshot["summary"],
                "tags": snapshot["tags"],
                "best_time_slots": [],
                "supply_points": snapshot["supply_points"],
                "bailout_options": snapshot["bailout_options"],
            }
        )
    return ExperienceRouteDetailSchema.model_validate(
        {
            "route_code": route["route_code"],
            "route_name": route["name"],
            "headline": f"{route['name']}：给今天留一段顺风和空白",
            "summary": route.get("route_notes") or "适合把城市节奏放慢一点的骑行路线。",
            "tags": route.get("ride_style_tags", []) + route.get("district_tags", []),
            "best_time_slots": route.get("best_time_slots", []),
            "supply_points": route.get("supply_points", []),
            "bailout_options": route.get("bailout_options", []),
        }
    )


def _persist_experience_plan(plan_payload: dict, payload: RidePlanRequestSchema, request: Request) -> None:
    save_ride_plan(request.app.state.database_url, plan_payload)
    save_planning_audit(
        request.app.state.database_url,
        request_payload=payload.model_dump(mode="json"),
        plan_payload=plan_payload,
    )
    featured = _select_featured_plan(plan_payload)
    save_query_log(
        request.app.state.database_url,
        request_no=plan_payload["request_no"],
        query=payload.query,
        target_date=payload.target_date.isoformat(),
        parsed_constraints=plan_payload["parsed_constraints"],
        recommended_route_name=featured["route_name"],
        fallback_reason=plan_payload.get("fallback_reason", []),
    )


def _select_featured_plan(plan_payload: dict) -> dict:
    if plan_payload.get("recommended_trip"):
        trip = plan_payload["recommended_trip"]
        return {
            "route_code": trip["trip_no"],
            "route_name": trip["trip_name"],
            "distance_km": trip["total_distance_km"],
            "estimated_duration_hours": trip["total_duration_hours"],
            "risk_level": trip["risk_level"],
            "summary_reason": trip["why_recommended"],
        }
    recommended = plan_payload["recommended_plan"]
    return {
        "route_code": recommended["route_code"],
        "route_name": recommended["route_name"],
        "distance_km": recommended["distance_km"],
        "estimated_duration_hours": recommended["estimated_duration_hours"],
        "risk_level": recommended["risk_level"],
        "summary_reason": recommended["summary_reason"],
    }


def _build_editorial_intro(plan_payload: dict) -> str:
    decision = plan_payload.get("decision_summary") or {}
    reason = decision.get("decision_reason") or "我先帮你把今天最适合的一页翻出来。"
    return f"{decision.get('decision_title') or '我给你留了一条更轻松的路线。'} {reason}"


def _build_companion_message(plan_payload: dict) -> str:
    decision = plan_payload.get("decision_summary") or {}
    if decision.get("decision_reason"):
        return decision["decision_reason"]
    featured = _select_featured_plan(plan_payload)
    return f"我给你留了一条叫《{featured['route_name']}》的小计划，先按这个方向出门就好。"


def _build_experience_result_payload(plan_payload: dict) -> dict:
    decision = plan_payload.get("decision_summary") or {}
    featured = _select_featured_plan(plan_payload)
    alternatives = [
        ExperienceRouteStorySchema.model_validate(
            {
                "route_code": item["route_code"],
                "route_name": item["route_name"],
                "summary": item["summary_reason"],
                "tags": [item["risk_level"]],
                "distance_km": item["distance_km"],
                "estimated_duration_hours": item["estimated_duration_hours"],
            }
        ).model_dump(mode="json")
        for item in plan_payload.get("alternatives", [])[:2]
    ]
    return {
        "request_no": plan_payload["request_no"],
        "scene": decision.get("scene") or plan_payload.get("planning_mode", "route"),
        "editorial_intro": _build_editorial_intro(plan_payload),
        "decision": {
            "title": decision.get("decision_title") or "今天可以先按主推荐出发",
            "reason": decision.get("decision_reason") or featured["summary_reason"],
            "confidence_notes": decision.get("confidence_notes", []),
        },
        "route_story": {
            "route_code": featured["route_code"],
            "route_name": featured["route_name"],
            "summary": featured["summary_reason"],
            "tags": [featured["risk_level"]],
            "distance_km": featured["distance_km"],
            "estimated_duration_hours": featured["estimated_duration_hours"],
        },
        "support_notes": decision.get("equipment_advice", []),
        "ride_journal_prompt": "如果这趟骑行只留下一个片段，你会想把哪一幕写进今天的日记？",
        "alternative_routes": alternatives,
    }
