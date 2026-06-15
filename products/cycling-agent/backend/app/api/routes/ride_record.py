"""CN: 骑行记录 API，负责骑后记录的创建、列表和详情读取。
EN: Ride record API for post-ride record create, list, and detail retrieval.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.ids import generate_business_no
from app.repositories.plan_result_repository import get_ride_plan, get_ride_plans
from app.repositories.ride_monthly_summary_event_repository import save_ride_monthly_summary_event
from app.repositories.ride_record_repository import (
    get_ride_record,
    list_non_cancelled_ride_records_before_date,
    list_recent_non_cancelled_ride_records,
    list_ride_records,
    list_ride_records_by_date_range,
    save_ride_record,
)
from app.schemas.ride_plan import (
    CreateRideRecordRequestSchema,
    RideGrowthReviewResponseSchema,
    RideRecordDetailResponseSchema,
    RideRecordListItemSchema,
    RideRecordListResponseSchema,
    RideMonthlySummaryEventSchema,
    RideMonthlySummaryResponseSchema,
    TrackRideGrowthReviewCtaClickRequestSchema,
    TrackRideMonthlySummaryCtaClickRequestSchema,
)
from app.services.ride_growth_review_service import build_ride_growth_review, parse_growth_window_days
from app.services.ride_monthly_summary_service import build_ride_monthly_summary, parse_ride_month
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
    records = list_ride_records(database_url, limit=limit)
    source_plans = get_ride_plans(
        database_url,
        [record["source_request_no"] for record in records if record.get("source_request_no")],
    )
    items = []
    for record in records:
        source_plan = source_plans.get(record["source_request_no"]) if record.get("source_request_no") else None
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


@router.get("/monthly-summary", response_model=RideMonthlySummaryResponseSchema)
async def get_ride_monthly_summary(request: Request, month: str = Query(...)) -> RideMonthlySummaryResponseSchema:
    database_url = getattr(request.app.state, "database_url", None)
    try:
        period_start = parse_ride_month(month)
    except ValueError:
        if database_url:
            _save_monthly_summary_event(
                database_url,
                event_type="invalid_month",
                requested_month=month,
                source="backend",
            )
        raise HTTPException(status_code=422, detail="invalid-month-format")

    database_url = _require_database_url(request)
    period_end = _month_end(period_start)
    reference_day = min(date.today(), period_end)
    monthly_records = list_ride_records_by_date_range(database_url, period_start, period_end)
    recent_non_cancelled_records = list_recent_non_cancelled_ride_records(
        database_url,
        before_date=reference_day,
        lookback_days=30,
        limit=1000,
    )
    streak_non_cancelled_records = list_non_cancelled_ride_records_before_date(
        database_url,
        before_date=reference_day,
        limit=1000,
    )
    source_plans = get_ride_plans(
        database_url,
        [record["source_request_no"] for record in monthly_records if record.get("source_request_no")],
    )
    summary = build_ride_monthly_summary(
        month=month,
        monthly_records=monthly_records,
        recent_non_cancelled_records=recent_non_cancelled_records,
        streak_non_cancelled_records=streak_non_cancelled_records,
        source_plans_by_request_no=source_plans,
        today=reference_day,
    )
    _save_monthly_summary_event(
        database_url,
        event_type="summary_request",
        requested_month=month,
        is_empty_summary=summary["ride_count"] == 0,
        has_planned_rides=summary["planned_count"] > 0,
        habit_status=summary["habit_status"],
        next_action_key=summary["next_action"]["action_key"],
        source="backend",
    )
    return RideMonthlySummaryResponseSchema(ride_monthly_summary=summary)


@router.get("/growth-review", response_model=RideGrowthReviewResponseSchema)
async def get_ride_growth_review(
    request: Request,
    window_days: int = Query(default=90),
) -> RideGrowthReviewResponseSchema:
    database_url = getattr(request.app.state, "database_url", None)
    try:
        normalized_window_days = parse_growth_window_days(window_days)
    except ValueError:
        if database_url:
            _save_monthly_summary_event(
                database_url,
                event_type="growth_review_invalid_window",
                requested_window_days=window_days,
                source="backend",
            )
        raise HTTPException(status_code=422, detail="invalid-window-days")

    database_url = _require_database_url(request)
    reference_day = date.today()
    period_start = reference_day - timedelta(days=normalized_window_days - 1)
    window_records = list_ride_records_by_date_range(database_url, period_start, reference_day)
    source_plans = get_ride_plans(
        database_url,
        [record["source_request_no"] for record in window_records if record.get("source_request_no")],
    )
    summary = build_ride_growth_review(
        window_days=normalized_window_days,
        window_records=window_records,
        source_plans_by_request_no=source_plans,
        today=reference_day,
    )
    _save_monthly_summary_event(
        database_url,
        event_type="growth_review_request",
        requested_window_days=normalized_window_days,
        suggested_scene=summary["next_focus"]["suggested_scene"],
        is_zero_growth_review=summary["ride_count"] == 0,
        growth_status=summary["growth_status"],
        has_milestones=bool(summary["milestones"]),
        next_action_key=summary["next_focus"]["action_key"],
        source="backend",
    )
    return RideGrowthReviewResponseSchema(ride_growth_review=summary)


@router.post("/monthly-summary-events", response_model=RideMonthlySummaryEventSchema)
async def track_ride_monthly_summary_cta_click(
    payload: TrackRideMonthlySummaryCtaClickRequestSchema,
    request: Request,
) -> RideMonthlySummaryEventSchema:
    database_url = _require_database_url(request)
    saved = _save_monthly_summary_event(
        database_url,
        event_type="cta_click",
        requested_month=payload.month,
        suggested_scene=payload.suggested_scene,
        next_action_key=payload.action_key,
        source="frontend",
    )
    return RideMonthlySummaryEventSchema.model_validate(
        {
            **saved,
            "created_at": date.today().isoformat(),
        }
    )


@router.post("/growth-review-events", response_model=RideMonthlySummaryEventSchema)
async def track_ride_growth_review_cta_click(
    payload: TrackRideGrowthReviewCtaClickRequestSchema,
    request: Request,
) -> RideMonthlySummaryEventSchema:
    database_url = _require_database_url(request)
    saved = _save_monthly_summary_event(
        database_url,
        event_type="growth_review_cta_click",
        requested_window_days=payload.window_days,
        suggested_scene=payload.suggested_scene,
        growth_status=payload.growth_status,
        next_action_key=payload.action_key,
        source="frontend",
    )
    return RideMonthlySummaryEventSchema.model_validate(
        {
            **saved,
            "created_at": date.today().isoformat(),
        }
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

    if payload.ride_date > date.today():
        raise HTTPException(status_code=422, detail="ride-record-date-in-future")

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
        "source_request_no": payload.source_request_no if payload.entry_mode == "planned" else None,
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


def _month_end(period_start: date) -> date:
    if period_start.month == 12:
        next_month = date(period_start.year + 1, 1, 1)
    else:
        next_month = date(period_start.year, period_start.month + 1, 1)
    return next_month - timedelta(days=1)


def _save_monthly_summary_event(
    database_url: str,
    *,
    event_type: str,
    requested_month: str | None = None,
    requested_window_days: int | None = None,
    source: str,
    suggested_scene: str | None = None,
    is_empty_summary: bool | None = None,
    is_zero_growth_review: bool | None = None,
    has_planned_rides: bool | None = None,
    habit_status: str | None = None,
    growth_status: str | None = None,
    has_milestones: bool | None = None,
    next_action_key: str | None = None,
) -> dict[str, Any]:
    return save_ride_monthly_summary_event(
        database_url,
        {
            "event_no": generate_business_no("RME"),
            "event_type": event_type,
            "requested_month": requested_month,
            "requested_window_days": requested_window_days,
            "suggested_scene": suggested_scene,
            "is_empty_summary": is_empty_summary,
            "is_zero_growth_review": is_zero_growth_review,
            "has_planned_rides": has_planned_rides,
            "habit_status": habit_status,
            "growth_status": growth_status,
            "has_milestones": has_milestones,
            "next_action_key": next_action_key,
            "source": source,
        },
    )
