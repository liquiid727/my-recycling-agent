"""CN: MVP 主编排器，按解析、天气、路线、POI、风险、决策、路书的顺序组织规划链路。
EN: Main MVP orchestrator that runs parsing, weather, route, POI, risk, decision, and roadbook stages in order.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from datetime import date
from typing import Callable, Any
import json

from app.agents.query_parser_agent import (
    build_clarification_prompt,
    build_structured_constraints,
    enrich_parsed_constraints,
    parse_query_fallback,
    resolve_planning_context,
)
from app.core.ids import generate_business_no
from app.providers.weather_provider import build_fallback_weather_snapshot, normalize_region_code
from app.repositories.city_strategy_repository import list_active_city_strategy_configs
from app.repositories.route_template_repository import load_route_templates
from app.schemas.ride_plan import RidePlanRequestSchema
from app.services.city_strategy_service import (
    apply_city_strategy_to_recommendation_score,
    apply_city_strategy_to_risk,
)
from app.services.roadbook_service import build_equipment_advice, build_roadbook
from app.services.nearby_trip_planner import (
    build_nearby_trip_card,
    build_trip_rhythm,
    build_trip_risks,
    rank_nearby_trip_candidates,
)
from app.services.nearby_route_discovery_service import discover_nearby_route_candidates
from app.services.risk_scoring_service import score_route_risk
from app.services.route_match_service import rank_route_candidates


SEED_PATH = Path(__file__).resolve().parents[3] / "data" / "hangzhou_routes.json"
NEARBY_DESTINATIONS_SEED_PATH = Path(__file__).resolve().parents[3] / "data" / "hangzhou_nearby_destinations.json"
TRIP_TEMPLATES_SEED_PATH = Path(__file__).resolve().parents[3] / "data" / "hangzhou_trip_templates.json"
LLM_STAGE_TIMEOUT_SECONDS = 8.0
StageTracer = Callable[[dict], None]


def _build_route_card(route: dict, risk: dict, summary_reason: str) -> dict:
    route_context = route.get("route_context") or {}
    distance_km = route_context.get("total_distance_km") or route_context.get("distance_km") or route["distance_km"]
    estimated_duration_hours = (
        route_context.get("total_duration_hours")
        or route_context.get("estimated_duration_hours")
        or route["estimated_duration_hours"]
    )
    if route_context.get("fallback_reason") == "route-provider-template-only":
        summary_reason = f"{summary_reason} 当前未按准确出发点重算接驳距离和总时长，仅展示样板路线估算。"
    constraint_warnings = route.get("constraint_warnings") or []
    warning_summary = _format_constraint_warnings(constraint_warnings)
    if warning_summary:
        summary_reason = f"{summary_reason} {warning_summary}"
    go_decision = "go" if risk["risk_level"] == "low" else "caution" if risk["risk_level"] == "medium" else "no_go"
    if constraint_warnings and go_decision == "go":
        go_decision = "caution"
    return {
        "go_decision": go_decision,
        "route_name": route["name"],
        "route_code": route["route_code"],
        "distance_km": distance_km,
        "elevation_gain_m": route["elevation_gain_m"],
        "estimated_duration_hours": estimated_duration_hours,
        "risk_level": risk["risk_level"],
        "summary_reason": summary_reason,
    }


def _format_constraint_warnings(warnings: list[str]) -> str | None:
    labels = []
    if "total-duration-over-target" in warnings:
        labels.append("总时长略超出原计划")
    if "approach-distance-over-limit" in warnings:
        labels.append("从当前出发点接驳偏远")
    if "target-distance-out-of-range" in warnings:
        labels.append("总距离和目标距离有偏差")
    if "dynamic-route-shorter-than-plan" in warnings:
        labels.append("周边动态线短于原计划")
    if not labels:
        return None
    return "注意：" + "，".join(labels) + "，这是放宽硬约束后的最接近路线。"


def _build_normalized_decision(intent: str, summary: dict) -> dict:
    return {
        "intent": intent,
        "scene": summary.get("scene"),
        "go_decision": summary.get("go_decision", "caution"),
        "title": summary.get("decision_title", "先看结论"),
        "summary": summary.get("decision_reason", ""),
    }


def _build_normalized_route_plan(card: dict) -> dict:
    return {
        "kind": "route",
        "code": card["route_code"],
        "title": card["route_name"],
        "summary": card["summary_reason"],
        "distance_km": card["distance_km"],
        "elevation_gain_m": card["elevation_gain_m"],
        "estimated_duration_hours": card["estimated_duration_hours"],
        "risk_level": card["risk_level"],
    }


def _build_normalized_weekend_plan(card: dict) -> dict:
    return {
        "kind": "weekend_recommendation",
        "code": card["trip_no"],
        "title": card["trip_name"],
        "summary": card["why_recommended"],
        "distance_km": card["total_distance_km"],
        "estimated_duration_hours": card["ride_duration_hours"],
        "total_duration_hours": card["total_duration_hours"],
        "risk_level": card["risk_level"],
        "destination_name": card["destination_name"],
        "stay_suggestion": card["stay_suggestion"],
        "return_options": card.get("return_options", []),
    }


def _build_normalized_explanation(summary: dict, clarification_prompt: str | None = None) -> dict:
    explanation = {
        "headline": summary.get("decision_title", "先看结论"),
        "summary": summary.get("decision_reason", ""),
        "confidence_notes": summary.get("confidence_notes", []),
    }
    if clarification_prompt:
        explanation["confidence_notes"] = [*explanation["confidence_notes"], clarification_prompt]
    return explanation


def _build_normalized_risk(*, risk_level: str | None, items: list[str], fallback_plan: str | None, scores: dict | None = None) -> dict:
    return {
        "level": risk_level,
        "items": items,
        "fallback_plan": fallback_plan,
        "scores": scores,
    }


def _build_normalized_equipment(items: list[str]) -> dict:
    return {"items": items}


def _build_normalized_fallback(*, status: str, fallback_reason: list[str], message: str | None) -> dict:
    fallback_status = "stable"
    if status == "no_match":
        fallback_status = "no_match"
    elif fallback_reason:
        fallback_status = "degraded"
    return {
        "status": fallback_status,
        "reasons": fallback_reason,
        "message": message,
    }


def build_demo_plan(
    payload: RidePlanRequestSchema,
    *,
    llm_provider=None,
    weather_provider=None,
    route_provider=None,
    poi_provider=None,
    strategy_rules: list[dict] | None = None,
    risk_rules: list[dict] | None = None,
    nearby_destinations: list[dict] | None = None,
    trip_templates: list[dict] | None = None,
    stage_tracer: StageTracer | None = None,
) -> dict:
    request_no = generate_business_no("RQ")
    user_profile = payload.user_profile.model_dump() if payload.user_profile else {}
    fallback_reason: list[str] = []
    tool_trace: list[dict] = []
    constraints = _resolve_parsed_constraints(payload.query, user_profile, llm_provider, fallback_reason, tool_trace, stage_tracer)
    constraints = _merge_structured_constraints(payload, constraints, user_profile)
    planning_context = resolve_planning_context(
        intent=payload.intent,
        planning_mode=payload.planning_mode,
        planning_scene=payload.planning_scene,
        query=payload.query,
        parsed_constraints=constraints,
    )
    constraints.update(planning_context)
    planning_mode = planning_context["planning_mode"]
    intent = planning_context["intent"]
    clarification_prompt = build_clarification_prompt(constraints)
    region_code = normalize_region_code(constraints.get("origin_region"), payload.city_code)
    strategy_rules = strategy_rules or []
    risk_rules = risk_rules or []
    weather_snapshot = _resolve_weather_snapshot(
        city_code=payload.city_code,
        region_code=region_code,
        forecast_date=payload.target_date,
        weather_provider=weather_provider,
        fallback_reason=fallback_reason,
        tool_trace=tool_trace,
        stage_tracer=stage_tracer,
    )
    if planning_mode == "nearby_trip":
        return _build_nearby_trip_plan(
            payload=payload,
            request_no=request_no,
            constraints=constraints,
            intent=intent,
            user_profile=user_profile,
            clarification_prompt=clarification_prompt,
            weather_snapshot=weather_snapshot,
            fallback_reason=fallback_reason,
            tool_trace=tool_trace,
            risk_rules=risk_rules,
            nearby_destinations=nearby_destinations,
            trip_templates=trip_templates,
            route_provider=route_provider,
            stage_tracer=stage_tracer,
        )

    routes = _resolve_city_ride_candidates(
        payload=payload,
        constraints=constraints,
        route_provider=route_provider,
        poi_provider=poi_provider,
        fallback_reason=fallback_reason,
        tool_trace=tool_trace,
        stage_tracer=stage_tracer,
    )
    ranked_routes = rank_route_candidates(routes, constraints)
    _record_stage(
        tool_trace,
        stage_tracer,
        {
            "stage_name": "route_planner",
            "status": "success" if ranked_routes else "fallback",
            "provider_name": "dynamic-nearby-route",
            "summary": f"Matched {len(ranked_routes)} route candidates from dynamic nearby route discovery.",
            "fallback_reason": None if ranked_routes else "route-candidate-empty",
        },
    )
    if not ranked_routes:
        return _build_no_match_response(
            payload,
            request_no,
            constraints,
            clarification_prompt,
            weather_snapshot,
            fallback_reason,
            tool_trace,
        )

    enriched_routes = []
    for route in ranked_routes:
        poi_context = _resolve_poi_context(route, poi_provider, fallback_reason, tool_trace, stage_tracer)
        route["poi_summary"] = poi_context["poi_summary"]
        risk = score_route_risk(route, weather_snapshot, user_profile, risk_rules)
        risk = apply_city_strategy_to_risk(route, weather_snapshot, risk, strategy_rules)
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "risk_evaluator",
                "status": "success",
                "provider_name": "rule-engine",
                "summary": f"Calculated risk scores for {route['route_code']}.",
                "fallback_reason": None,
            }
        )
        recommendation_score = apply_city_strategy_to_recommendation_score(
            route,
            route.get("match_score", 0.0) - risk["overall_risk_score"],
            strategy_rules,
        )
        enriched_routes.append(
            {
                "route": route,
                "risk": risk,
                "recommendation_score": recommendation_score,
                "card": _build_route_card(
                    route,
                    risk,
                    summary_reason=route.get("route_notes", "结合时长、风格和风险后的推荐结果。"),
                ),
            }
        )

    enriched_routes.sort(key=lambda item: item["recommendation_score"], reverse=True)
    _record_stage(
        tool_trace,
        stage_tracer,
        {
            "stage_name": "decision_engine",
            "status": "success",
            "provider_name": "rule-engine",
            "summary": f"Ranked {len(enriched_routes)} route candidates and selected primary recommendation.",
            "fallback_reason": None,
        }
    )
    recommended = enriched_routes[0]
    alternatives = [item["card"] for item in enriched_routes[1:4]]
    roadbook = {
        **_resolve_roadbook(
            recommended["route"],
            recommended["risk"],
            constraints,
            llm_provider,
            fallback_reason,
            tool_trace,
            stage_tracer,
        ),
        "route_notes": recommended["route"].get("route_notes"),
        "risk_summary": recommended["risk"],
        "backup_plan": "如天气转差，优先缩短到江边往返或改为湘湖轻松线。",
    }
    decision_summary = _build_decision_summary(
        scene=constraints.get("planning_scene", "city_ride"),
        primary_card=recommended["card"],
        route=recommended["route"],
        risk=recommended["risk"],
        weather_snapshot=weather_snapshot,
        constraints=constraints,
        status="success",
    )

    return {
        "request_no": request_no,
        "status": "success",
        "intent": intent,
        "planning_mode": planning_mode,
        "parsed_constraints": constraints,
        "input_summary": _build_input_summary(payload, constraints),
        "clarification_prompt": clarification_prompt,
        "no_match_reason": None,
        "recommended_plan": recommended["card"],
        "alternatives": alternatives,
        "weather_snapshot": weather_snapshot,
        "fallback_reason": fallback_reason,
        "tool_trace": tool_trace,
        "decision": _build_normalized_decision(intent, decision_summary),
        "plan": _build_normalized_route_plan(recommended["card"]),
        "alternative_plans": [_build_normalized_route_plan(item["card"]) for item in enriched_routes[1:4]],
        "explanation": _build_normalized_explanation(decision_summary, clarification_prompt),
        "risk": _build_normalized_risk(
            risk_level=recommended["risk"].get("risk_level"),
            items=recommended["risk"].get("risk_items", []),
            fallback_plan=roadbook["backup_plan"],
            scores=recommended["risk"],
        ),
        "equipment": _build_normalized_equipment(decision_summary.get("equipment_advice", [])),
        "fallback": _build_normalized_fallback(
            status="success",
            fallback_reason=fallback_reason,
            message=roadbook["backup_plan"],
        ),
        "decision_summary": decision_summary,
        "route_map": _build_route_map(recommended["route"]),
        "roadbook": roadbook,
        "_audit": {
            "candidate_assessments": [
                {
                    "route_code": item["route"]["route_code"],
                    "route_name": item["route"]["name"],
                    "recommendation_score": item["recommendation_score"],
                    "risk": item["risk"],
                    "card": item["card"],
                }
                for item in enriched_routes
            ],
        },
    }


def _build_no_match_response(
    payload: RidePlanRequestSchema,
    request_no: str,
    constraints: dict,
    clarification_prompt: str | None,
    weather_snapshot: dict,
    fallback_reason: list[str],
    tool_trace: list[dict],
) -> dict:
    decision_summary = _build_decision_summary(
        scene=constraints.get("planning_scene", "city_ride"),
        primary_card={
            "go_decision": "no_go",
            "route_name": "当前没有合适路线",
            "risk_level": "unknown",
            "summary_reason": "动态路线暂时没有可用候选，未使用固定模板生成本次推荐。",
        },
        route={},
        risk={"risk_level": "high"},
        weather_snapshot=weather_snapshot,
        constraints=constraints,
        status="no_match",
    )
    return {
        "status": "no_match",
        "intent": constraints.get("intent", "ride_plan"),
        "planning_mode": constraints.get("planning_mode", "route"),
        "request_no": request_no,
        "parsed_constraints": constraints,
        "input_summary": _build_input_summary(payload, constraints),
        "clarification_prompt": clarification_prompt,
        "no_match_reason": "动态路线暂时没有可执行候选，未使用固定模板生成本次推荐。",
        "recommended_plan": {
            "go_decision": "no_go",
            "route_name": "当前没有合适路线",
            "route_code": "NO-MATCH",
            "distance_km": 0.0,
            "elevation_gain_m": 0.0,
            "estimated_duration_hours": 0.0,
            "risk_level": "unknown",
            "summary_reason": "动态路线暂时没有可用候选，未使用固定模板生成本次推荐。",
        },
        "alternatives": [],
        "weather_snapshot": weather_snapshot,
        "fallback_reason": fallback_reason,
        "tool_trace": tool_trace,
        "decision": _build_normalized_decision(constraints.get("intent", "ride_plan"), decision_summary),
        "plan": _build_normalized_route_plan(
            {
                "route_code": "NO-MATCH",
                "route_name": "当前没有合适路线",
                "distance_km": 0.0,
                "elevation_gain_m": 0.0,
                "estimated_duration_hours": 0.0,
                "risk_level": "unknown",
                "summary_reason": "动态路线暂时没有可用候选，未使用固定模板生成本次推荐。",
            }
        ),
        "alternative_plans": [],
        "explanation": _build_normalized_explanation(decision_summary, clarification_prompt),
        "risk": _build_normalized_risk(
            risk_level="unknown",
            items=[],
            fallback_plan="请调整时长、出发点或换个时段再试。",
            scores=None,
        ),
        "equipment": _build_normalized_equipment([]),
        "fallback": _build_normalized_fallback(
            status="no_match",
            fallback_reason=fallback_reason,
            message="请调整时长、出发点或换个时段再试。",
        ),
        "decision_summary": decision_summary,
        "route_map": None,
        "roadbook": None,
        "_audit": {
            "candidate_assessments": [],
        },
    }


def _resolve_city_ride_candidates(
    *,
    payload: RidePlanRequestSchema,
    constraints: dict,
    route_provider,
    poi_provider,
    fallback_reason: list[str],
    tool_trace: list[dict],
    stage_tracer: StageTracer | None,
) -> list[dict]:
    return _discover_dynamic_city_routes(
        payload=payload,
        constraints=constraints,
        route_provider=route_provider,
        poi_provider=poi_provider,
        fallback_reason=fallback_reason,
        tool_trace=tool_trace,
        stage_tracer=stage_tracer,
    )


def _discover_dynamic_city_routes(
    *,
    payload: RidePlanRequestSchema,
    constraints: dict,
    route_provider,
    poi_provider,
    fallback_reason: list[str],
    tool_trace: list[dict],
    stage_tracer: StageTracer | None,
) -> list[dict]:
    missing_reasons = []
    if not constraints.get("start_point"):
        missing_reasons.append("start-point-missing")
    if route_provider is None or not hasattr(route_provider, "resolve_point") or not hasattr(route_provider, "get_cycling_path"):
        missing_reasons.append("route-provider-unavailable")
    if poi_provider is None or not hasattr(poi_provider, "search_route_anchors"):
        missing_reasons.append("poi-provider-unavailable")
    if missing_reasons:
        reason = "nearby-route-discovery-unavailable" if any("provider" in item for item in missing_reasons) else "nearby-route-discovery-start-point-missing"
        if reason == "nearby-route-discovery-unavailable":
            _append_unique(fallback_reason, reason)
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "nearby_route_discovery",
                "status": "fallback",
                "provider_name": "dynamic-nearby-route",
                "summary": f"Dynamic route discovery unavailable ({', '.join(missing_reasons)}).",
                "fallback_reason": reason,
            },
        )
        return []

    try:
        routes = discover_nearby_route_candidates(
            constraints=constraints,
            city_code=payload.city_code,
            route_provider=route_provider,
            poi_provider=poi_provider,
        )
    except Exception as exc:
        _append_unique(fallback_reason, "nearby-route-discovery-unavailable")
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "nearby_route_discovery",
                "status": "fallback",
                "provider_name": "dynamic-nearby-route",
                "summary": f"Nearby route discovery failed ({type(exc).__name__}: {exc}), falling back to route templates.",
                "fallback_reason": "nearby-route-discovery-unavailable",
            },
        )
        return []

    _record_stage(
        tool_trace,
        stage_tracer,
        {
            "stage_name": "nearby_route_discovery",
            "status": "success" if routes else "fallback",
            "provider_name": "dynamic-nearby-route",
            "summary": f"Generated {len(routes)} nearby dynamic route candidates.",
            "fallback_reason": None if routes else "nearby-route-discovery-empty",
        },
    )
    return routes


def _merge_structured_constraints(payload: RidePlanRequestSchema, parsed_constraints: dict, user_profile: dict) -> dict:
    if payload.input_mode != "structured" or payload.structured_constraints is None:
        if payload.planning_scene:
            parsed_constraints = {**parsed_constraints, "planning_scene": payload.planning_scene}
        return parsed_constraints
    structured = build_structured_constraints(payload.structured_constraints.model_dump(), user_profile)
    merged = dict(parsed_constraints)
    for key, value in structured.items():
        if key in {"missing_fields", "confidence", "defaults_applied"}:
            continue
        if value not in (None, "", []):
            merged[key] = value
    merged["missing_fields"] = structured["missing_fields"]
    merged["confidence"] = structured["confidence"]
    merged["defaults_applied"] = structured["defaults_applied"]
    return merged


def _build_input_summary(payload: RidePlanRequestSchema, constraints: dict) -> dict:
    summary = {
        "intent": constraints.get("intent"),
        "input_mode": payload.input_mode,
        "target_date": payload.target_date.isoformat(),
        "departure_time": constraints.get("departure_time"),
        "city_code": payload.city_code,
        "origin_region": constraints.get("origin_region"),
        "start_point": constraints.get("start_point"),
        "available_hours": constraints.get("available_hours"),
        "target_distance_km": constraints.get("target_distance_km"),
        "fitness_level": constraints.get("fitness_level"),
        "ride_style": constraints.get("ride_style"),
        "slope_tolerance": constraints.get("slope_tolerance"),
        "priority": constraints.get("priority"),
        "defaults_applied": constraints.get("defaults_applied", []),
    }
    if constraints.get("planning_scene"):
        summary["planning_scene"] = constraints.get("planning_scene")
    if constraints.get("planning_mode") == "nearby_trip":
        summary.update(
            {
                "planning_mode": constraints.get("planning_mode"),
                "duration_bucket": constraints.get("duration_bucket"),
                "destination_preferences": constraints.get("destination_preferences", []),
                "return_preference": constraints.get("return_preference"),
            }
        )
    return summary


def _build_decision_summary(
    *,
    scene: str | None,
    primary_card: dict,
    route: dict,
    risk: dict,
    weather_snapshot: dict,
    constraints: dict,
    status: str,
) -> dict:
    go_decision = primary_card.get("go_decision") or ("no_go" if status == "no_match" else "go")
    if status == "no_match":
        return {
            "scene": scene,
            "go_decision": "no_go",
            "decision_title": "当前不建议按这些条件直接出发",
            "decision_reason": "动态路线没有返回可执行候选，系统没有使用固定模板冒充本次推荐。",
            "confidence_notes": ["没有可用候选路线，系统没有强行推荐。"],
            "equipment_advice": ["先不要准备完整装备，等路线和天气窗口明确后再决定。"],
        }

    title_map = {
        "go": "这次可以骑，优先按主推荐执行",
        "caution": "这次可以谨慎骑，建议保留缩短方案",
        "no_go": "这次不建议按原计划骑",
    }
    decision_reason = primary_card.get("summary_reason") or "结合路线匹配、天气和风险后的推荐结论。"
    confidence_notes = [
        f"风险等级：{risk.get('risk_level', primary_card.get('risk_level', 'unknown'))}",
        f"天气：{weather_snapshot.get('weather_summary', 'unknown')}",
    ]
    if constraints.get("start_point"):
        confidence_notes.append(f"出发点：{constraints['start_point']}")
    return {
        "scene": scene,
        "go_decision": go_decision,
        "decision_title": title_map.get(go_decision, "本次建议已生成"),
        "decision_reason": decision_reason,
        "confidence_notes": confidence_notes,
        "equipment_advice": build_equipment_advice(route, risk, weather_snapshot, constraints),
    }


def _build_route_map(route: dict) -> dict:
    route_context = route.get("route_context") or {}
    template_start_point = route_context.get("template_start_point") or {
        "name": route.get("start_point_name"),
        "longitude": route.get("start_point_lng"),
        "latitude": route.get("start_point_lat"),
    }
    user_start_point = route_context.get("user_start_point") or template_start_point
    end_point = {
        "name": route.get("end_point_name") or route.get("start_point_name"),
        "longitude": route.get("end_point_lng") or route.get("start_point_lng"),
        "latitude": route.get("end_point_lat") or route.get("start_point_lat"),
    }
    polyline = route_context.get("polyline") or []
    return {
        "route_code": route["route_code"],
        "route_name": route["name"],
        "provider_name": route_context.get("provider_name", "template-only"),
        "fact_source": route_context.get("fact_source", "template"),
        "polyline": polyline,
        "polyline_available": bool(polyline),
        "fallback_reason": None if polyline else "route-polyline-unavailable",
        "start_point": user_start_point,
        "user_start_point": user_start_point,
        "template_start_point": template_start_point,
        "end_point": end_point,
        "approach_distance_km": route_context.get("approach_distance_km"),
        "approach_duration_hours": route_context.get("approach_duration_hours"),
        "template_distance_km": route_context.get("template_distance_km") or route.get("distance_km"),
        "template_duration_hours": route_context.get("template_duration_hours") or route.get("estimated_duration_hours"),
        "total_distance_km": route_context.get("total_distance_km") or route_context.get("distance_km") or route.get("distance_km"),
        "total_duration_hours": route_context.get("total_duration_hours") or route_context.get("estimated_duration_hours") or route.get("estimated_duration_hours"),
        "supply_points": route.get("supply_points", []),
        "bailout_options": route.get("bailout_options", []),
        "climb_segments": route.get("climb_segments", []),
    }


def _build_nearby_trip_plan(
    *,
    payload: RidePlanRequestSchema,
    request_no: str,
    constraints: dict,
    intent: str,
    user_profile: dict,
    clarification_prompt: str | None,
    weather_snapshot: dict,
    fallback_reason: list[str],
    tool_trace: list[dict],
    risk_rules: list[dict],
    nearby_destinations: list[dict] | None,
    trip_templates: list[dict] | None,
    route_provider,
    stage_tracer: StageTracer | None,
) -> dict:
    routes = _enrich_routes_with_route_context(
        load_route_templates(SEED_PATH),
        constraints,
        route_provider,
        fallback_reason,
        tool_trace,
        stage_tracer,
    )
    destinations = nearby_destinations or _load_json_list(NEARBY_DESTINATIONS_SEED_PATH)
    trips = trip_templates or _load_json_list(TRIP_TEMPLATES_SEED_PATH)
    ranked_trips = rank_nearby_trip_candidates(
        trips=trips,
        destinations=destinations,
        routes=routes,
        constraints=constraints,
        weather_snapshot=weather_snapshot,
        user_profile=user_profile,
        risk_rules=risk_rules,
    )
    _record_stage(
        tool_trace,
        stage_tracer,
        {
            "stage_name": "trip_planner",
            "status": "success" if ranked_trips else "fallback",
            "provider_name": "trip-template-library",
            "summary": f"Matched {len(ranked_trips)} nearby trip candidates from Hangzhou templates.",
            "fallback_reason": None if ranked_trips else "nearby-trip-candidate-empty",
        },
    )
    if not ranked_trips:
        return _build_no_match_response(
            payload,
            request_no,
            constraints,
            clarification_prompt,
            weather_snapshot,
            fallback_reason,
            tool_trace,
        )

    recommended = ranked_trips[0]
    alternatives = ranked_trips[1:3]
    recommended_card = build_nearby_trip_card(recommended)
    route_card = _build_route_card(
        recommended["route"],
        recommended["risk"],
        summary_reason=recommended_card["why_recommended"],
    )
    trip_rhythm = build_trip_rhythm(recommended, departure_time=constraints.get("departure_time"))
    trip_risks = build_trip_risks(recommended, weather_snapshot)
    _record_stage(
        tool_trace,
        stage_tracer,
        {
            "stage_name": "decision_engine",
            "status": "success",
            "provider_name": "rule-engine",
            "summary": f"Ranked {len(ranked_trips)} nearby trip candidates and selected primary trip.",
            "fallback_reason": None,
        },
    )
    _record_stage(
        tool_trace,
        stage_tracer,
        {
            "stage_name": "trip_roadbook_generator",
            "status": "success",
            "provider_name": "template-trip-roadbook",
            "summary": "Generated nearby trip rhythm, stay advice, risks, return, and fallback plan.",
            "fallback_reason": None,
        },
    )
    decision_summary = _build_trip_decision_summary(recommended_card, recommended, trip_risks, constraints, weather_snapshot)
    return {
        "request_no": request_no,
        "status": "success",
        "intent": intent,
        "planning_mode": "nearby_trip",
        "parsed_constraints": constraints,
        "input_summary": _build_input_summary(payload, constraints),
        "clarification_prompt": clarification_prompt,
        "no_match_reason": None,
        "recommended_plan": route_card,
        "alternatives": [_build_route_card(item["route"], item["risk"], build_nearby_trip_card(item)["why_recommended"]) for item in alternatives],
        "recommended_trip": recommended_card,
        "trip_alternatives": [build_nearby_trip_card(item) for item in alternatives],
        "trip_rhythm": trip_rhythm,
        "trip_risks": trip_risks,
        "weather_snapshot": weather_snapshot,
        "fallback_reason": fallback_reason,
        "tool_trace": tool_trace,
        "decision": _build_normalized_decision(intent, decision_summary),
        "plan": _build_normalized_weekend_plan(recommended_card),
        "alternative_plans": [_build_normalized_weekend_plan(build_nearby_trip_card(item)) for item in alternatives],
        "explanation": _build_normalized_explanation(decision_summary, clarification_prompt),
        "risk": _build_normalized_risk(
            risk_level=recommended["risk"].get("risk_level"),
            items=trip_risks.get("risk_items", []),
            fallback_plan=trip_risks.get("fallback_plan"),
            scores=recommended["risk"],
        ),
        "equipment": _build_normalized_equipment(recommended_card.get("equipment_advice", [])),
        "fallback": _build_normalized_fallback(
            status="success",
            fallback_reason=fallback_reason,
            message=trip_risks.get("fallback_plan"),
        ),
        "decision_summary": decision_summary,
        "route_map": _build_route_map(recommended["route"]),
        "roadbook": {
            "departure_window": recommended_card["recommended_departure_time"],
            "key_segments": [segment["description"] for segment in trip_rhythm["segments"]],
            "supply_advice": [recommended["destination"]["supply_summary"]],
            "mitigation_advice": trip_risks["risk_items"],
            "shorten_options": [trip_risks["fallback_plan"]],
            "route_notes": recommended["route"].get("route_notes"),
            "risk_summary": recommended["risk"],
            "backup_plan": trip_risks["fallback_plan"],
        },
        "_audit": {
            "candidate_assessments": [
                {
                    "route_code": item["route"]["route_code"],
                    "route_name": item["trip"]["name"],
                    "recommendation_score": item["score"],
                    "risk": item["risk"],
                    "card": _build_route_card(item["route"], item["risk"], build_nearby_trip_card(item)["why_recommended"]),
                }
                for item in ranked_trips
            ],
        },
    }


def _build_trip_decision_summary(recommended_card: dict, candidate: dict, trip_risks: dict, constraints: dict, weather_snapshot: dict) -> dict:
    lodging_plan = recommended_card.get("lodging_plan")
    confidence_notes = [
        f"目的地：{recommended_card['destination_name']}",
        f"出行时长：{recommended_card.get('duration_bucket') or constraints.get('duration_bucket')}",
        f"天气：{weather_snapshot.get('weather_summary', 'unknown')}",
    ]
    if lodging_plan:
        confidence_notes.append(f"住宿：{lodging_plan}")
    if recommended_card.get("weather_window_notes"):
        confidence_notes.append(f"天气窗口：{recommended_card['weather_window_notes']}")
    return {
        "scene": constraints.get("planning_scene", "weekend_trip"),
        "go_decision": "caution" if candidate["risk"].get("risk_level") == "medium" else "go" if candidate["risk"].get("risk_level") == "low" else "no_go",
        "decision_title": f"优先考虑{recommended_card['destination_name']}方向",
        "decision_reason": recommended_card["why_recommended"],
        "confidence_notes": confidence_notes,
        "equipment_advice": recommended_card.get("equipment_advice", []),
    }


def _load_json_list(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_weather_snapshot(
    *,
    city_code: str,
    region_code: str,
    forecast_date: date,
    weather_provider,
    fallback_reason: list[str],
    tool_trace: list[dict],
    stage_tracer: StageTracer | None,
) -> dict:
    if weather_provider is None:
        _append_unique(fallback_reason, "weather-provider-missing")
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "weather_provider",
                "status": "fallback",
                "provider_name": "fallback",
                "summary": f"Weather provider missing for {region_code}, using fallback snapshot.",
                "fallback_reason": "weather-provider-missing",
            }
        )
        return build_fallback_weather_snapshot(region_code, forecast_date)

    try:
        snapshot = weather_provider.get_weather_snapshot(
            city_code=city_code,
            region_code=region_code,
            forecast_date=forecast_date,
        )
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "weather_provider",
                "status": "success",
                "provider_name": snapshot.get("provider_name", "unknown"),
                "summary": f"Loaded weather snapshot for {region_code}.",
                "fallback_reason": None,
            }
        )
        return snapshot
    except Exception:
        _append_unique(fallback_reason, "weather-provider-unavailable")
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "weather_provider",
                "status": "fallback",
                "provider_name": getattr(weather_provider, "provider_name", "unknown"),
                "summary": f"Weather provider unavailable for {region_code}, using fallback snapshot.",
                "fallback_reason": "weather-provider-unavailable",
            }
        )
        return build_fallback_weather_snapshot(region_code, forecast_date)


def _resolve_route_context(
    route: dict,
    constraints: dict,
    route_provider,
    fallback_reason: list[str],
    tool_trace: list[dict],
    stage_tracer: StageTracer | None,
) -> dict:
    if route_provider is None:
        _append_unique(fallback_reason, "route-provider-missing")
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "route_provider",
                "status": "fallback",
                "provider_name": "none",
                "summary": "Route provider missing, using route template facts only.",
                "fallback_reason": "route-provider-missing",
            }
        )
        return _build_template_only_route_context(route, constraints)
    try:
        context = route_provider.get_route_context(route, constraints)
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "route_provider",
                "status": "success",
                "provider_name": context.get("provider_name", "unknown"),
                "summary": f"Loaded route context for {route['route_code']}.",
                "fallback_reason": None,
            }
        )
        return context
    except Exception:
        _append_unique(fallback_reason, "route-provider-unavailable")
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "route_provider",
                "status": "fallback",
                "provider_name": getattr(route_provider, "provider_name", "unknown"),
                "summary": f"Route context unavailable for {route['route_code']}, using route template facts only.",
                "fallback_reason": "route-provider-unavailable",
            }
        )
        return _build_template_only_route_context(route, constraints)


def _enrich_routes_with_route_context(
    routes: list[dict],
    constraints: dict,
    route_provider,
    fallback_reason: list[str],
    tool_trace: list[dict],
    stage_tracer: StageTracer | None,
) -> list[dict]:
    enriched_routes = []
    for route in routes:
        enriched = dict(route)
        enriched["route_context"] = _resolve_route_context(enriched, constraints, route_provider, fallback_reason, tool_trace, stage_tracer)
        enriched_routes.append(enriched)
    return enriched_routes


def _build_template_only_route_context(route: dict, constraints: dict) -> dict:
    distance_km = float(route.get("distance_km", 0))
    estimated_duration_hours = float(route.get("estimated_duration_hours", 0))
    return {
        "provider_name": "template-only",
        "fact_source": "template",
        "fallback_reason": "route-provider-template-only",
        "start_region": constraints.get("origin_region") or route.get("district_tags", ["杭州"])[0],
        "distance_km": distance_km,
        "estimated_duration_hours": estimated_duration_hours,
        "template_distance_km": distance_km,
        "template_duration_hours": estimated_duration_hours,
        "total_distance_km": distance_km,
        "total_duration_hours": estimated_duration_hours,
        "approach_distance_km": None,
        "approach_duration_hours": None,
        "user_start_point": {"name": constraints.get("start_point"), "longitude": None, "latitude": None},
        "template_start_point": {
            "name": route.get("start_point_name"),
            "longitude": route.get("start_point_lng"),
            "latitude": route.get("start_point_lat"),
        },
    }


def _resolve_poi_context(
    route: dict,
    poi_provider,
    fallback_reason: list[str],
    tool_trace: list[dict],
    stage_tracer: StageTracer | None,
) -> dict:
    if poi_provider is None:
        _append_unique(fallback_reason, "poi-provider-missing")
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "poi_provider",
                "status": "fallback",
                "provider_name": "none",
                "summary": "POI provider missing, using route template POI only.",
                "fallback_reason": "poi-provider-missing",
            }
        )
        return {"poi_summary": None, "provider_name": "template-only"}
    try:
        context = poi_provider.get_poi_context(route)
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "poi_provider",
                "status": "success",
                "provider_name": context.get("provider_name", "unknown"),
                "summary": f"Loaded POI context for {route['route_code']}.",
                "fallback_reason": None,
            }
        )
        return context
    except Exception:
        _append_unique(fallback_reason, "poi-provider-unavailable")
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "poi_provider",
                "status": "fallback",
                "provider_name": getattr(poi_provider, "provider_name", "unknown"),
                "summary": f"POI context unavailable for {route['route_code']}, using route template POI only.",
                "fallback_reason": "poi-provider-unavailable",
            }
        )
        return {"poi_summary": None, "provider_name": "template-only"}


def _append_unique(target: list[str], value: str) -> None:
    if value not in target:
        target.append(value)


def _resolve_parsed_constraints(
    query: str,
    user_profile: dict,
    llm_provider,
    fallback_reason: list[str],
    tool_trace: list[dict],
    stage_tracer: StageTracer | None,
) -> dict:
    fallback_constraints = enrich_parsed_constraints(parse_query_fallback(query), user_profile)
    if llm_provider is None:
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "query_parser",
                "status": "fallback",
                "provider_name": "rule-fallback",
                "summary": "LLM query parser unavailable, using deterministic fallback parser.",
                "fallback_reason": "llm-query-parser-missing",
            }
        )
        return fallback_constraints
    try:
        parsed = enrich_parsed_constraints(
            _call_llm_stage_with_timeout(
                lambda: llm_provider.parse_query(query=query, user_profile=user_profile),
                llm_provider=llm_provider,
            ),
            user_profile,
        )
        if not parsed.get("start_point") and fallback_constraints.get("start_point"):
            parsed["start_point"] = fallback_constraints["start_point"]
            parsed["missing_fields"] = [item for item in parsed.get("missing_fields", []) if item != "start_point"]
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "query_parser",
                "status": "success",
                "provider_name": getattr(llm_provider, "provider_name", "llm"),
                "summary": "Parsed query with LLM provider.",
                "fallback_reason": None,
            }
        )
        return parsed
    except Exception:
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "query_parser",
                "status": "fallback",
                "provider_name": getattr(llm_provider, "provider_name", "llm"),
                "summary": "LLM query parser failed, using deterministic fallback parser.",
                "fallback_reason": "llm-query-parser-unavailable",
            }
        )
        return fallback_constraints


def _resolve_roadbook(
    route: dict,
    risk: dict,
    parsed_constraints: dict,
    llm_provider,
    fallback_reason: list[str],
    tool_trace: list[dict],
    stage_tracer: StageTracer | None,
) -> dict:
    fallback_roadbook = build_roadbook(route, risk)
    if llm_provider is None:
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "roadbook_generator",
                "status": "fallback",
                "provider_name": "template-roadbook",
                "summary": "LLM roadbook generator unavailable, using deterministic template roadbook.",
                "fallback_reason": "llm-roadbook-missing",
            }
        )
        return fallback_roadbook
    try:
        generated = _call_llm_stage_with_timeout(
            lambda: llm_provider.generate_roadbook(route=route, risk=risk, parsed_constraints=parsed_constraints),
            llm_provider=llm_provider,
        )
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "roadbook_generator",
                "status": "success",
                "provider_name": getattr(llm_provider, "provider_name", "llm"),
                "summary": "Generated roadbook with LLM provider.",
                "fallback_reason": None,
            }
        )
        return {**fallback_roadbook, **generated}
    except Exception:
        _record_stage(
            tool_trace,
            stage_tracer,
            {
                "stage_name": "roadbook_generator",
                "status": "fallback",
                "provider_name": getattr(llm_provider, "provider_name", "llm"),
                "summary": "LLM roadbook generator failed, using deterministic template roadbook.",
                "fallback_reason": "llm-roadbook-unavailable",
            }
        )
        return fallback_roadbook


def _call_llm_stage_with_timeout(call: Callable[[], Any], *, llm_provider) -> Any:
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        timeout_seconds = min(float(getattr(llm_provider, "timeout_seconds", LLM_STAGE_TIMEOUT_SECONDS)), LLM_STAGE_TIMEOUT_SECONDS)
        future = executor.submit(call)
        return future.result(timeout=timeout_seconds)
    except TimeoutError as exc:
        executor.shutdown(wait=False, cancel_futures=True)
        raise RuntimeError("llm-stage-timeout") from exc
    except Exception:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        executor.shutdown(wait=False)


def _record_stage(tool_trace: list[dict], stage_tracer: StageTracer | None, event: dict) -> None:
    tool_trace.append(event)
    if stage_tracer is not None:
        stage_tracer(event)
