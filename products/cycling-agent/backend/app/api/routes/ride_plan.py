"""CN: 骑行规划 API，负责同步和流式规划入口、缓存命中、持久化与 SSE 输出。
EN: Ride-planning API for sync and streaming entrypoints, cache hits, persistence, and SSE output.
"""

import json
import queue
import threading
from copy import deepcopy
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.cache import ride_plan_cache_key
from app.core.ids import generate_business_no
from app.repositories.city_strategy_repository import list_active_city_strategy_configs
from app.repositories.plan_result_repository import get_ride_plan, save_ride_plan
from app.repositories.planning_audit_repository import save_planning_audit
from app.repositories.query_log_repository import save_query_log
from app.repositories.risk_rule_repository import list_active_risk_rules
from app.repositories.nearby_trip_repository import list_nearby_destinations, list_trip_templates
from app.agents.query_parser_agent import (
    build_clarification_prompt,
    build_structured_constraints,
    enrich_parsed_constraints,
    missing_core_fields,
    parse_query_fallback,
    resolve_planning_context,
)
from app.schemas.ride_plan import RidePlanPreflightResponseSchema, RidePlanRequestSchema, RidePlanResponseSchema
from app.services.ride_planning_orchestrator import build_demo_plan


router = APIRouter(prefix="/api/v1/ride", tags=["ride"])


@router.post("/plan", response_model=RidePlanResponseSchema)
async def create_ride_plan(payload: RidePlanRequestSchema, request: Request) -> RidePlanResponseSchema:
    _raise_if_core_fields_missing(payload)
    cached = _resolve_cached_plan(payload, request)
    if cached is not None:
        return RidePlanResponseSchema.model_validate(cached)

    strategy_rules = list_active_city_strategy_configs(request.app.state.database_url, city_code=payload.city_code)
    risk_rules = list_active_risk_rules(request.app.state.database_url, city_code=payload.city_code)
    plan_payload = build_demo_plan(
        payload,
        llm_provider=request.app.state.llm_provider,
        weather_provider=request.app.state.weather_provider,
        route_provider=request.app.state.route_provider,
        poi_provider=request.app.state.poi_provider,
        strategy_rules=strategy_rules,
        risk_rules=risk_rules,
        nearby_destinations=list_nearby_destinations(request.app.state.database_url, city_code=payload.city_code),
        trip_templates=list_trip_templates(request.app.state.database_url, city_code=payload.city_code),
    )
    _persist_plan_payload(plan_payload, payload, request)
    return RidePlanResponseSchema.model_validate(plan_payload)


@router.post("/plan/stream")
async def create_ride_plan_stream(payload: RidePlanRequestSchema, request: Request) -> StreamingResponse:
    _raise_if_core_fields_missing(payload)
    cached = _resolve_cached_plan(payload, request)
    if cached is not None:
        def stream_cached_events():
            yield _format_sse(
                "planning_started",
                {
                    "summary": "RidePlanningOrchestrator accepted the request and started staged execution.",
                },
            )
            for stage in cached["tool_trace"]:
                yield _format_sse("stage_update", stage)
            yield _format_sse("plan_ready", cached)

        return StreamingResponse(
            stream_cached_events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    strategy_rules = list_active_city_strategy_configs(request.app.state.database_url, city_code=payload.city_code)
    risk_rules = list_active_risk_rules(request.app.state.database_url, city_code=payload.city_code)
    event_queue: queue.Queue[tuple[str, dict]] = queue.Queue()
    done = threading.Event()

    def stage_tracer(stage_event: dict) -> None:
        event_queue.put(("stage_update", stage_event))

    def worker() -> None:
        try:
            plan_payload = build_demo_plan(
                payload,
                llm_provider=request.app.state.llm_provider,
                weather_provider=request.app.state.weather_provider,
                route_provider=request.app.state.route_provider,
                poi_provider=request.app.state.poi_provider,
                strategy_rules=strategy_rules,
                risk_rules=risk_rules,
                nearby_destinations=list_nearby_destinations(request.app.state.database_url, city_code=payload.city_code),
                trip_templates=list_trip_templates(request.app.state.database_url, city_code=payload.city_code),
                stage_tracer=stage_tracer,
            )
            _persist_plan_payload(plan_payload, payload, request)
            event_queue.put(("plan_ready", plan_payload))
        except Exception:
            event_queue.put(
                (
                    "error",
                    {
                        "message": "ride-plan-stream-failed",
                    },
                )
            )
        finally:
            done.set()

    threading.Thread(target=worker, daemon=True).start()

    def stream_events():
        yield _format_sse(
            "planning_started",
            {
                "summary": "RidePlanningOrchestrator accepted the request and started staged execution.",
            },
        )
        while not (done.is_set() and event_queue.empty()):
            try:
                event_name, event_payload = event_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            yield _format_sse(event_name, event_payload)

    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/plan/preflight", response_model=RidePlanPreflightResponseSchema)
async def preflight_ride_plan(payload: RidePlanRequestSchema) -> RidePlanPreflightResponseSchema:
    parsed = _parse_payload_constraints(payload)
    missing = missing_core_fields(parsed, target_date=payload.target_date)
    parsed["missing_fields"] = missing
    return RidePlanPreflightResponseSchema(
        ready_to_plan=not missing,
        parsed_constraints=parsed,
        missing_core_fields=missing,
        clarification_prompt=build_clarification_prompt(parsed),
    )


@router.get("/plan/{request_no}", response_model=RidePlanResponseSchema)
async def get_saved_ride_plan(request_no: str, request: Request) -> RidePlanResponseSchema:
    payload = get_ride_plan(request.app.state.database_url, request_no)
    if payload is None:
        raise HTTPException(status_code=404, detail="ride-plan-not-found")
    return RidePlanResponseSchema.model_validate(payload)


def _raise_if_core_fields_missing(payload: RidePlanRequestSchema) -> None:
    parsed = _parse_payload_constraints(payload)
    if missing_core_fields(parsed, target_date=payload.target_date):
        raise HTTPException(status_code=422, detail="ride-plan-core-fields-missing")


def _parse_payload_constraints(payload: RidePlanRequestSchema) -> dict:
    user_profile = payload.user_profile.model_dump() if payload.user_profile else {}
    if payload.input_mode == "structured":
        parsed = build_structured_constraints(
            payload.structured_constraints.model_dump() if payload.structured_constraints else {},
            user_profile,
        )
    else:
        parsed = enrich_parsed_constraints(parse_query_fallback(payload.query), user_profile)
    parsed.update(
        resolve_planning_context(
            intent=payload.intent,
            planning_mode=payload.planning_mode,
            planning_scene=payload.planning_scene,
            query=payload.query,
            parsed_constraints=parsed,
        )
    )
    return _merge_handoff_context(payload, parsed)


def _merge_handoff_context(payload: RidePlanRequestSchema, parsed_constraints: dict) -> dict:
    if payload.handoff_context is None:
        return parsed_constraints

    handoff = payload.handoff_context
    merged = dict(parsed_constraints)
    if handoff.origin_region and not merged.get("origin_region"):
        merged["origin_region"] = handoff.origin_region
    if handoff.suggested_duration_hours and not merged.get("available_hours"):
        merged["available_hours"] = handoff.suggested_duration_hours
    if handoff.suggested_scene == "weekend_trip" and not merged.get("duration_bucket"):
        merged["duration_bucket"] = "half_day"
    return merged


def _format_sse(event_name: str, payload: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _resolve_cached_plan(payload: RidePlanRequestSchema, request: Request) -> dict | None:
    cache_backend = getattr(request.app.state, "cache_backend", None)
    if cache_backend is None:
        return None
    request_payload = payload.model_dump(mode="json")
    cached_plan = cache_backend.get_json(ride_plan_cache_key(request_payload))
    if cached_plan is None:
        return None

    cloned = deepcopy(cached_plan)
    cached_request_no = cloned["request_no"]
    cloned["request_no"] = _new_request_no()
    cloned["tool_trace"] = [
        {
            "stage_name": "plan_cache",
            "status": "success",
            "provider_name": "cache-backend",
            "summary": f"Served cached ride plan generated from {cached_request_no}.",
            "fallback_reason": None,
        },
        *cloned.get("tool_trace", []),
    ]
    _persist_plan_payload(cloned, payload, request)
    return cloned


def _persist_plan_payload(plan_payload: dict, payload: RidePlanRequestSchema, request: Request) -> None:
    save_ride_plan(request.app.state.database_url, plan_payload)
    save_planning_audit(
        request.app.state.database_url,
        request_payload=payload.model_dump(mode="json"),
        plan_payload=plan_payload,
    )
    save_query_log(
        request.app.state.database_url,
        request_no=plan_payload["request_no"],
        query=payload.query,
        target_date=payload.target_date.isoformat(),
        parsed_constraints=plan_payload["parsed_constraints"],
        recommended_route_name=(plan_payload.get("recommended_trip") or {}).get("trip_name", plan_payload["recommended_plan"]["route_name"]),
        fallback_reason=plan_payload["fallback_reason"],
    )
    cache_backend = getattr(request.app.state, "cache_backend", None)
    if cache_backend is not None and _is_cacheable_plan(plan_payload):
        cache_backend.set_json(
            ride_plan_cache_key(payload.model_dump(mode="json")),
            plan_payload,
            ttl_seconds=getattr(request.app.state, "ride_plan_cache_ttl_seconds", 1800),
        )


def _is_cacheable_plan(plan_payload: dict) -> bool:
    if plan_payload.get("status") != "success":
        return False
    non_cacheable_reasons = {
        "route-provider-missing",
        "route-provider-unavailable",
        "poi-provider-missing",
        "poi-provider-unavailable",
        "route-candidate-empty",
    }
    return not any(reason in non_cacheable_reasons for reason in plan_payload.get("fallback_reason", []))


def _new_request_no() -> str:
    return generate_business_no("RQ")
