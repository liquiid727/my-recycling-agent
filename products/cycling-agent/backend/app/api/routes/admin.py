"""CN: 后台管理 API，维护路线模板、城市策略、风险规则、查询日志和规划审计。
EN: Admin API for route templates, city strategies, risk rules, query logs, and planning audits.
"""

from fastapi import APIRouter, HTTPException, Request

from app.repositories.city_strategy_repository import list_city_strategy_configs, save_city_strategy_config
from app.repositories.planning_audit_repository import get_planning_audit
from app.repositories.query_log_repository import list_query_logs
from app.repositories.risk_rule_repository import list_risk_rules, save_risk_rule
from app.repositories.route_template_repository import list_route_templates, save_route_template
from app.repositories.nearby_trip_repository import (
    list_nearby_destinations,
    list_trip_templates,
    save_nearby_destination,
    save_trip_template,
)
from app.schemas.ride_plan import (
    CityStrategyConfigSchema,
    NearbyDestinationAdminSchema,
    PlanningAuditBundleSchema,
    QueryLogEntrySchema,
    RiskRuleSchema,
    RouteTemplateAdminSchema,
    TripTemplateAdminSchema,
)


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/routes", response_model=RouteTemplateAdminSchema)
async def create_or_update_route_template(
    payload: RouteTemplateAdminSchema,
    request: Request,
) -> RouteTemplateAdminSchema:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    saved = save_route_template(database_url, payload.model_dump())
    _invalidate_ride_plan_cache(request)
    return RouteTemplateAdminSchema.model_validate(saved)


@router.get("/routes", response_model=list[RouteTemplateAdminSchema])
async def get_route_templates(request: Request) -> list[RouteTemplateAdminSchema]:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    routes = list_route_templates(database_url, city_code="hangzhou")
    return [RouteTemplateAdminSchema.model_validate(route) for route in routes]


@router.post("/city-strategy", response_model=CityStrategyConfigSchema)
async def create_or_update_city_strategy(
    payload: CityStrategyConfigSchema,
    request: Request,
) -> CityStrategyConfigSchema:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    saved = save_city_strategy_config(database_url, payload.model_dump())
    _invalidate_ride_plan_cache(request)
    return CityStrategyConfigSchema.model_validate(saved)


@router.get("/city-strategy", response_model=list[CityStrategyConfigSchema])
async def get_city_strategy_configs(request: Request) -> list[CityStrategyConfigSchema]:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    return [
        CityStrategyConfigSchema.model_validate(item)
        for item in list_city_strategy_configs(database_url, city_code="hangzhou")
        if item["config_type"] != "risk_rule"
    ]


@router.post("/risk-rules", response_model=RiskRuleSchema)
async def create_or_update_risk_rule(
    payload: RiskRuleSchema,
    request: Request,
) -> RiskRuleSchema:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    saved = save_risk_rule(database_url, payload.model_dump())
    _invalidate_ride_plan_cache(request)
    return RiskRuleSchema.model_validate(saved)


@router.get("/risk-rules", response_model=list[RiskRuleSchema])
async def get_risk_rules(request: Request) -> list[RiskRuleSchema]:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    return [RiskRuleSchema.model_validate(item) for item in list_risk_rules(database_url, city_code="hangzhou")]


@router.post("/nearby-destinations", response_model=NearbyDestinationAdminSchema)
async def create_or_update_nearby_destination(
    payload: NearbyDestinationAdminSchema,
    request: Request,
) -> NearbyDestinationAdminSchema:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    saved = save_nearby_destination(database_url, payload.model_dump())
    _invalidate_ride_plan_cache(request)
    return NearbyDestinationAdminSchema.model_validate(saved)


@router.get("/nearby-destinations", response_model=list[NearbyDestinationAdminSchema])
async def get_nearby_destinations(request: Request) -> list[NearbyDestinationAdminSchema]:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    return [NearbyDestinationAdminSchema.model_validate(item) for item in list_nearby_destinations(database_url, city_code="hangzhou")]


@router.post("/trip-templates", response_model=TripTemplateAdminSchema)
async def create_or_update_trip_template(
    payload: TripTemplateAdminSchema,
    request: Request,
) -> TripTemplateAdminSchema:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    saved = save_trip_template(database_url, payload.model_dump())
    _invalidate_ride_plan_cache(request)
    return TripTemplateAdminSchema.model_validate(saved)


@router.get("/trip-templates", response_model=list[TripTemplateAdminSchema])
async def get_trip_templates(request: Request) -> list[TripTemplateAdminSchema]:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    return [TripTemplateAdminSchema.model_validate(item) for item in list_trip_templates(database_url, city_code="hangzhou")]


@router.get("/query-logs", response_model=list[QueryLogEntrySchema])
async def get_query_logs(request: Request) -> list[QueryLogEntrySchema]:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    return [QueryLogEntrySchema.model_validate(item) for item in list_query_logs(database_url)]


@router.get("/planning-audit/{request_no}", response_model=PlanningAuditBundleSchema)
async def get_planning_audit_bundle(request_no: str, request: Request) -> PlanningAuditBundleSchema:
    database_url = getattr(request.app.state, "database_url", None)
    if not database_url:
        raise HTTPException(status_code=500, detail="database-url-missing")
    payload = get_planning_audit(database_url, request_no)
    if payload is None:
        raise HTTPException(status_code=404, detail="planning-audit-not-found")
    return PlanningAuditBundleSchema.model_validate(payload)


def _invalidate_ride_plan_cache(request: Request) -> None:
    cache_backend = getattr(request.app.state, "cache_backend", None)
    if cache_backend is None:
        return
    cache_backend.clear_prefix("ride-plan:")
