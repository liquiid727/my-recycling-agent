"""CN: API schema 定义，固定规划请求、响应、路线详情、后台维护和审计载荷结构。
EN: API schema definitions for planning requests/responses, route details, admin payloads, and audit bundles.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


INTENT_PATTERN = "^(ride_today|ride_plan|weekend_recommendation)$"
PLAN_KIND_PATTERN = "^(route|weekend_recommendation)$"
RIDE_RECORD_ENTRY_MODE_PATTERN = "^(planned|manual)$"
RIDE_RECORD_COMPLETION_STATUS_PATTERN = "^(completed|shortened|cancelled)$"
RIDE_RECORD_EFFORT_FEELING_PATTERN = "^(easy|steady|hard)$"
RIDE_RECORD_MOOD_AFTER_PATTERN = "^(refreshed|normal|tired)$"


class UserProfilePayload(BaseModel):
    id: str | None = None
    uid: str | None = None
    nickname: str | None = None
    home_region: str | None = None
    fitness_level: str | None = Field(default=None, pattern="^(low|medium|high)$")
    ride_style_preferences: list[str] = Field(default_factory=list)
    slope_tolerance: str | None = Field(default=None, pattern="^(avoid|neutral|prefer)$")


class RidePlanRequestSchema(BaseModel):
    query: str = Field(min_length=3)
    target_date: date
    city_code: str = "hangzhou"
    intent: str | None = Field(default=None, pattern=INTENT_PATTERN)
    planning_mode: str | None = Field(default=None, pattern="^(route|nearby_trip)$")
    planning_scene: str | None = Field(default=None, pattern="^(city_ride|weekend_trip)$")
    input_mode: str = Field(default="natural", pattern="^(natural|structured)$")
    structured_constraints: "StructuredConstraintsPayload | None" = None
    user_profile: UserProfilePayload | None = None


class OriginLocationPayload(BaseModel):
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source: str | None = Field(default=None, pattern="^(browser|manual|saved_place)$")


class StructuredConstraintsPayload(BaseModel):
    departure_time: str | None = None
    origin_region: str | None = None
    start_point: str | None = None
    origin_location: OriginLocationPayload | None = None
    available_hours: float | None = None
    target_distance_km: float | None = None
    fitness_level: str | None = Field(default=None, pattern="^(low|medium|high)$")
    ride_style: str | None = None
    slope_tolerance: str | None = Field(default=None, pattern="^(avoid|neutral|prefer)$")
    priority: str | None = None
    duration_bucket: str | None = Field(default=None, pattern="^(evening|half_day|one_day|two_day|three_day)$")
    destination_preferences: list[str] = Field(default_factory=list)
    return_preference: str | None = Field(default=None, pattern="^(ride_back|public_transport|shorten_route)$")
    overnight_preference: str | None = Field(default=None, pattern="^(avoid|optional|required)$")
    lodging_preference: str | None = None
    cross_city_allowed: bool | None = None


class RidePlanPreflightResponseSchema(BaseModel):
    ready_to_plan: bool
    parsed_constraints: dict
    missing_core_fields: list[str] = Field(default_factory=list)
    clarification_prompt: str | None = None


class ChatMessageSchema(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1)


class ChatTurnRequestSchema(BaseModel):
    messages: list[ChatMessageSchema] = Field(min_length=1)
    intent: str | None = Field(default=None, pattern=INTENT_PATTERN)
    planning_scene: str | None = Field(default=None, pattern="^(city_ride|weekend_trip)$")
    target_date: date
    slot_state: dict = Field(default_factory=dict)
    user_profile: UserProfilePayload | None = None


class ChatTurnResponseSchema(BaseModel):
    assistant_name: str = "AAA骑车帮帮"
    intent: str = Field(default="ride_plan", pattern=INTENT_PATTERN)
    assistant_message: str
    slot_state: dict = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    ready_to_plan: bool
    planner_request: dict | None = None
    ui_hints: dict = Field(default_factory=dict)


class RoutePlanCardSchema(BaseModel):
    go_decision: str = "go"
    route_name: str
    route_code: str
    distance_km: float
    elevation_gain_m: float
    estimated_duration_hours: float
    risk_level: str
    summary_reason: str


class NearbyTripCardSchema(BaseModel):
    trip_no: str
    trip_name: str
    destination_name: str
    suitable_for: str
    total_distance_km: float
    ride_duration_hours: float
    total_duration_hours: float
    recommended_departure_time: str
    stay_suggestion: str
    why_recommended: str
    risk_level: str
    return_options: list[str] = Field(default_factory=list)
    duration_bucket: str | None = None
    itinerary_days: list[dict] = Field(default_factory=list)
    lodging_plan: str | None = None
    equipment_advice: list[str] = Field(default_factory=list)
    weather_window_notes: str | None = None


class DecisionSummarySchema(BaseModel):
    scene: str | None = None
    go_decision: str
    decision_title: str
    decision_reason: str
    confidence_notes: list[str] = Field(default_factory=list)
    equipment_advice: list[str] = Field(default_factory=list)


class TripRhythmSegmentSchema(BaseModel):
    stage: str
    time_window: str
    description: str


class TripRhythmSchema(BaseModel):
    segments: list[TripRhythmSegmentSchema] = Field(default_factory=list)


class TripRisksSchema(BaseModel):
    risk_items: list[str] = Field(default_factory=list)
    fallback_plan: str


class WeatherSnapshotSchema(BaseModel):
    region_code: str
    forecast_date: str
    temperature_min: float | None = None
    temperature_max: float | None = None
    precipitation_probability: float | None = None
    wind_speed: float | None = None
    wind_direction: str | None = None
    weather_summary: str
    provider_name: str
    raw_payload: dict | None = None


class ToolTraceItemSchema(BaseModel):
    stage_name: str
    status: str
    provider_name: str
    summary: str
    fallback_reason: str | None = None


class NormalizedDecisionSchema(BaseModel):
    intent: str = Field(pattern=INTENT_PATTERN)
    scene: str | None = Field(default=None, pattern="^(city_ride|weekend_trip)$")
    go_decision: str
    title: str
    summary: str


class NormalizedPlanSchema(BaseModel):
    kind: str = Field(pattern="^(route|weekend_recommendation)$")
    code: str
    title: str
    summary: str
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    estimated_duration_hours: float | None = None
    total_duration_hours: float | None = None
    risk_level: str | None = None
    destination_name: str | None = None
    stay_suggestion: str | None = None
    return_options: list[str] = Field(default_factory=list)


class NormalizedExplanationSchema(BaseModel):
    headline: str
    summary: str
    confidence_notes: list[str] = Field(default_factory=list)


class NormalizedRiskSchema(BaseModel):
    level: str | None = None
    items: list[str] = Field(default_factory=list)
    fallback_plan: str | None = None
    scores: dict | None = None


class NormalizedEquipmentSchema(BaseModel):
    items: list[str] = Field(default_factory=list)


class NormalizedFallbackSchema(BaseModel):
    status: str
    reasons: list[str] = Field(default_factory=list)
    message: str | None = None


class RidePlanResponseSchema(BaseModel):
    status: str = "success"
    intent: str = Field(default="ride_plan", pattern=INTENT_PATTERN)
    planning_mode: str = "route"
    request_no: str
    parsed_constraints: dict
    input_summary: dict
    route_map: dict | None = None
    clarification_prompt: str | None = None
    no_match_reason: str | None = None
    recommended_plan: RoutePlanCardSchema
    alternatives: list[RoutePlanCardSchema]
    weather_snapshot: WeatherSnapshotSchema
    fallback_reason: list[str] = Field(default_factory=list)
    tool_trace: list[ToolTraceItemSchema] = Field(default_factory=list)
    decision: NormalizedDecisionSchema | None = None
    plan: NormalizedPlanSchema | None = None
    alternative_plans: list[NormalizedPlanSchema] = Field(default_factory=list)
    explanation: NormalizedExplanationSchema | None = None
    risk: NormalizedRiskSchema | None = None
    equipment: NormalizedEquipmentSchema | None = None
    fallback: NormalizedFallbackSchema | None = None
    decision_summary: DecisionSummarySchema | None = None
    roadbook: dict | None = None
    recommended_trip: NearbyTripCardSchema | None = None
    trip_alternatives: list[NearbyTripCardSchema] = Field(default_factory=list)
    trip_rhythm: TripRhythmSchema | None = None
    trip_risks: TripRisksSchema | None = None


class RecommendedRouteSchema(BaseModel):
    route_code: str
    route_name: str
    distance_km: float
    elevation_gain_m: float
    estimated_duration_hours: float
    difficulty_level: str
    ride_style_tags: list[str]
    district_tags: list[str]


class SupplyPointSchema(BaseModel):
    name: str
    km_mark: float
    type: str


class BailoutOptionSchema(BaseModel):
    name: str
    km_mark: float
    reason: str


class ClimbSegmentSchema(BaseModel):
    name: str
    distance_km: float
    elevation_gain_m: float
    gradient_note: str


class RouteDetailSchema(RecommendedRouteSchema):
    city_code: str
    start_point_name: str | None = None
    start_point_lng: float | None = None
    start_point_lat: float | None = None
    end_point_name: str | None = None
    loop_type: str | None = None
    season_tags: list[str] = Field(default_factory=list)
    best_time_slots: list[str] = Field(default_factory=list)
    avoid_time_slots: list[str] = Field(default_factory=list)
    surface_type: str | None = None
    traffic_level: str
    supply_score: int
    return_difficulty_score: int
    scenic_score: int
    training_score: int | None = None
    beginner_friendly: bool
    climb_segments: list[ClimbSegmentSchema] = Field(default_factory=list)
    supply_points: list[SupplyPointSchema] = Field(default_factory=list)
    bailout_options: list[BailoutOptionSchema] = Field(default_factory=list)
    holiday_penalty_level: str | None = None
    weather_sensitivity: dict = Field(default_factory=dict)
    route_notes: str | None = None


class RouteTemplateAdminSchema(BaseModel):
    id: str | None = None
    route_no: str | None = None
    route_code: str
    name: str
    city_code: str
    start_point_name: str | None = None
    start_point_lng: float | None = None
    start_point_lat: float | None = None
    end_point_name: str | None = None
    loop_type: str | None = None
    district_tags: list[str]
    ride_style_tags: list[str]
    season_tags: list[str] = Field(default_factory=list)
    distance_km: float
    elevation_gain_m: float
    estimated_duration_hours: float
    difficulty_level: str
    best_time_slots: list[str] = Field(default_factory=list)
    avoid_time_slots: list[str] = Field(default_factory=list)
    surface_type: str | None = None
    traffic_level: str
    supply_score: int
    return_difficulty_score: int
    scenic_score: int
    training_score: int | None = None
    beginner_friendly: bool
    climb_segments: list[ClimbSegmentSchema] = Field(default_factory=list)
    supply_points: list[SupplyPointSchema] = Field(default_factory=list)
    bailout_options: list[BailoutOptionSchema] = Field(default_factory=list)
    holiday_penalty_level: str | None = None
    weather_sensitivity: dict = Field(default_factory=dict)
    route_notes: str
    status: str | None = None
    route_source: str | None = None


class CityStrategyConfigSchema(BaseModel):
    entity_id: str | None = None
    config_no: str | None = None
    city_code: str
    config_type: str
    config_key: str
    config_value: dict
    status: str


class RiskRuleSchema(BaseModel):
    entity_id: str | None = None
    config_no: str | None = None
    city_code: str
    rule_key: str
    rule_value: dict
    status: str


class NearbyDestinationAdminSchema(BaseModel):
    destination_no: str | None = None
    city_code: str
    name: str
    destination_type: str
    region_tags: list[str]
    suitable_duration: list[str]
    stay_duration_minutes: int
    crowd_level: dict
    supply_summary: str
    public_transport_options: list[str] = Field(default_factory=list)
    stay_suggestion: str
    status: str | None = None


class TripTemplateAdminSchema(BaseModel):
    trip_no: str | None = None
    city_code: str
    route_template_id: str
    destination_no: str
    name: str
    origin_region_tags: list[str]
    total_duration_hours: float
    ride_duration_hours: float
    trip_style_tags: list[str]
    return_mode_options: list[str]
    fallback_plan: str
    status: str | None = None


class QueryLogEntrySchema(BaseModel):
    request_no: str
    query: str
    target_date: str
    parsed_constraints: dict
    recommended_route_name: str
    fallback_reason: list[str]
    created_at: str


class RideSummarySchema(BaseModel):
    headline: str
    summary: str
    completion_assessment: str
    effort_assessment: str
    recovery_advice: str
    next_ride_prompt: str
    plan_alignment: str | None = None
    confidence_notes: list[str] = Field(default_factory=list)


class RideRecordPayload(BaseModel):
    ride_record_no: str
    entry_mode: str = Field(pattern=RIDE_RECORD_ENTRY_MODE_PATTERN)
    source_request_no: str | None = None
    ride_date: date
    intent: str | None = Field(default=None, pattern=INTENT_PATTERN)
    plan_kind: str | None = Field(default=None, pattern=PLAN_KIND_PATTERN)
    route_code: str | None = None
    route_title: str | None = None
    destination_name: str | None = None
    start_point: str | None = None
    origin_region: str | None = None
    completion_status: str = Field(pattern=RIDE_RECORD_COMPLETION_STATUS_PATTERN)
    actual_duration_hours: float | None = None
    actual_distance_km: float | None = None
    effort_feeling: str = Field(pattern=RIDE_RECORD_EFFORT_FEELING_PATTERN)
    mood_after: str = Field(pattern=RIDE_RECORD_MOOD_AFTER_PATTERN)
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)


class CreateRideRecordRequestSchema(BaseModel):
    entry_mode: str = Field(pattern=RIDE_RECORD_ENTRY_MODE_PATTERN)
    source_request_no: str | None = None
    ride_date: date
    route_code: str | None = None
    route_title: str | None = None
    destination_name: str | None = None
    start_point: str | None = None
    origin_region: str | None = None
    completion_status: str = Field(pattern=RIDE_RECORD_COMPLETION_STATUS_PATTERN)
    actual_duration_hours: float | None = None
    actual_distance_km: float | None = None
    effort_feeling: str = Field(pattern=RIDE_RECORD_EFFORT_FEELING_PATTERN)
    mood_after: str = Field(pattern=RIDE_RECORD_MOOD_AFTER_PATTERN)
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)


class RideRecordListItemSchema(BaseModel):
    ride_record_no: str
    ride_date: date
    route_title: str | None = None
    destination_name: str | None = None
    completion_status: str = Field(pattern=RIDE_RECORD_COMPLETION_STATUS_PATTERN)
    summary_headline: str | None = None


class RideRecordListResponseSchema(BaseModel):
    items: list[RideRecordListItemSchema] = Field(default_factory=list)


class RideRecordDetailResponseSchema(BaseModel):
    ride_record: RideRecordPayload
    ride_summary: RideSummarySchema


class RideRequestAuditSchema(BaseModel):
    id: str | None = None
    request_no: str
    city_code: str
    raw_query: str
    target_date: str
    origin_region: str | None = None
    available_hours: float | None = None
    target_distance_km: float | None = None
    fitness_level: str | None = None
    ride_style: str | None = None
    parsed_constraints: dict
    user_profile: dict | None = None
    created_at: str


class WeatherSnapshotAuditSchema(BaseModel):
    id: str | None = None
    weather_no: str
    city_code: str
    region_code: str
    forecast_date: str
    temperature_min: float | None = None
    temperature_max: float | None = None
    precipitation_probability: float | None = None
    wind_speed: float | None = None
    wind_direction: str | None = None
    weather_summary: str
    provider_name: str
    raw_payload: dict | None = None
    fetched_at: str


class RiskAssessmentAuditSchema(BaseModel):
    entity_id: str | None = None
    risk_no: str
    route_code: str
    route_name: str
    recommendation_score: float
    overall_risk_score: float
    risk_level: str
    weather_risk_score: float
    climb_risk_score: float
    traffic_risk_score: float
    supply_risk_score: float
    return_risk_score: float
    crowd_risk_score: float
    reasons: list[str]
    mitigation_advice: list[str]
    created_at: str


class DecisionResultAuditSchema(BaseModel):
    id: str | None = None
    decision_no: str
    recommended_route_code: str
    backup_route_codes: list[str]
    go_decision: str
    explanation: str
    roadbook: dict | None = None
    status: str
    created_at: str


class PlanningAuditBundleSchema(BaseModel):
    ride_request: RideRequestAuditSchema
    weather_snapshot: WeatherSnapshotAuditSchema | None = None
    risk_assessments: list[RiskAssessmentAuditSchema] = Field(default_factory=list)
    decision_result: DecisionResultAuditSchema | None = None
