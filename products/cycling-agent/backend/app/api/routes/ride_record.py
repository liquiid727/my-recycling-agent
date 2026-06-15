"""CN: 骑行记录 API，负责骑后记录的创建、列表和详情读取。
EN: Ride record API for post-ride record create, list, and detail retrieval.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.ids import generate_business_no
from app.repositories.plan_result_repository import get_ride_plan
from app.repositories.ride_record_repository import get_ride_record, list_ride_records, save_ride_record
from app.schemas.ride_plan import (
    CreateRideRecordRequestSchema,
    RideRecordDetailResponseSchema,
    RideRecordListItemSchema,
    RideRecordListResponseSchema,
)
from app.services.ride_summary_service import build_ride_summary


router = APIRouter(prefix="/api/v1/rides", tags=["rides"])


@router.post("/records", response_model=RideRecordDetailResponseSchema)
async def create_ride_record(payload: CreateRideRecordRequestSchema, request: Request) -> RideRecordDetailResponseSchema:
    database_url = _require_database_url(request)
    source_plan = _resolve_source_plan(database_url, payload)
    _validate_create_payload(payload)

    record = _normalize_saved_ride_record(payload, source_plan)
    saved = save_ride_record(database_url, record)

    return RideRecordDetailResponseSchema(
        ride_record=saved,
        ride_summary=build_ride_summary(saved, source_plan=source_plan),
    )


@router.get("/records", response_model=RideRecordListResponseSchema)
async def get_ride_records(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
) -> RideRecordListResponseSchema:
    database_url = _require_database_url(request)
    items = []
    for record in list_ride_records(database_url, limit=limit):
        source_plan = get_ride_plan(database_url, record["source_request_no"]) if record.get("source_request_no") else None
        summary = build_ride_summary(record, source_plan=source_plan)
        items.append(
            RideRecordListItemSchema.model_validate(
                {
                    **record,
                    "summary_headline": summary["headline"],
                }
            )
        )
    return RideRecordListResponseSchema(items=items)


@router.get("/records/{ride_record_no}", response_model=RideRecordDetailResponseSchema)
async def get_one_ride_record(ride_record_no: str, request: Request) -> RideRecordDetailResponseSchema:
    database_url = _require_database_url(request)
    record = get_ride_record(database_url, ride_record_no)
    if record is None:
        raise HTTPException(status_code=404, detail="ride-record-not-found")

    source_plan = get_ride_plan(database_url, record["source_request_no"]) if record.get("source_request_no") else None
    return RideRecordDetailResponseSchema(
        ride_record=record,
        ride_summary=build_ride_summary(record, source_plan=source_plan),
    )


def _require_database_url(request: Request) -> str:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    return database_url


def _resolve_source_plan(database_url: str, payload: CreateRideRecordRequestSchema) -> dict[str, Any] | None:
    if payload.entry_mode != "planned":
        return None
    if not _has_value(payload.source_request_no):
        raise HTTPException(status_code=422, detail="ride-record-source-request-missing")

    source_plan = get_ride_plan(database_url, payload.source_request_no)
    if source_plan is None:
        raise HTTPException(status_code=404, detail="ride-record-source-plan-not-found")
    return source_plan


def _validate_create_payload(payload: CreateRideRecordRequestSchema) -> None:
    if payload.entry_mode == "manual" and not (_has_value(payload.route_title) or _has_value(payload.destination_name)):
        raise HTTPException(status_code=422, detail="ride-record-manual-title-missing")

    if (
        payload.completion_status == "completed"
        and payload.actual_duration_hours is None
        and payload.actual_distance_km is None
    ):
        raise HTTPException(status_code=422, detail="ride-record-completed-metrics-missing")


def _normalize_saved_ride_record(payload: CreateRideRecordRequestSchema, source_plan: dict[str, Any] | None) -> dict[str, Any]:
    base = payload.model_dump(mode="json")
    recommended_plan = (source_plan or {}).get("recommended_plan") or {}
    recommended_trip = (source_plan or {}).get("recommended_trip") or {}
    parsed_constraints = (source_plan or {}).get("parsed_constraints") or {}
    normalized_route_title = _first_value(
        payload.route_title,
        recommended_plan.get("route_name"),
        recommended_plan.get("route_title"),
        recommended_trip.get("trip_name"),
        _nested_value(source_plan, "plan", "title"),
    )
    normalized_destination_name = _first_value(
        payload.destination_name,
        recommended_trip.get("destination_name"),
        recommended_plan.get("destination_name"),
        _nested_value(source_plan, "plan", "destination_name"),
    )
    return {
        "ride_record_no": generate_business_no("RR"),
        "entry_mode": payload.entry_mode,
        "source_request_no": payload.source_request_no,
        "ride_date": base["ride_date"],
        "intent": (source_plan or {}).get("intent"),
        "plan_kind": _nested_value(source_plan, "plan", "kind"),
        "route_code": _first_value(payload.route_code, recommended_plan.get("route_code"), _nested_value(source_plan, "plan", "code")),
        "route_title": normalized_route_title,
        "destination_name": normalized_destination_name,
        "start_point": _first_value(payload.start_point, parsed_constraints.get("start_point")),
        "origin_region": _first_value(payload.origin_region, parsed_constraints.get("origin_region")),
        "completion_status": payload.completion_status,
        "actual_duration_hours": payload.actual_duration_hours,
        "actual_distance_km": payload.actual_distance_km,
        "effort_feeling": payload.effort_feeling,
        "mood_after": payload.mood_after,
        "notes": payload.notes,
        "tags": payload.tags,
    }


def _has_value(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _first_value(*values: Any) -> Any:
    for value in values:
        if _has_value(value):
            return value
    return None


def _nested_value(payload: dict[str, Any] | None, *path: str) -> Any:
    current = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
