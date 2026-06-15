/*
 * CN: 规划前端 API 客户端，封装普通请求、SSE 流式请求、路线详情和历史结果读取。
 * EN: Planner API client wrapping normal requests, SSE streaming, route details, and saved plan reads.
 */

export type RoutePlanCard = {
  go_decision?: string;
  route_name: string;
  route_code: string;
  distance_km: number;
  elevation_gain_m: number;
  estimated_duration_hours: number;
  risk_level: string;
  summary_reason: string;
};

export type InputMode = "natural" | "structured";
export type RideIntent = "ride_today" | "ride_plan" | "weekend_recommendation";
export type PlanningMode = "route" | "nearby_trip";
export type PlanningScene = "city_ride" | "weekend_trip";

export type OriginLocation = {
  name?: string;
  latitude?: number;
  longitude?: number;
  source?: "browser" | "manual" | "saved_place";
};

export type StructuredConstraints = {
  departure_time?: string;
  origin_region?: string;
  start_point?: string;
  origin_location?: OriginLocation;
  available_hours?: number;
  target_distance_km?: number;
  fitness_level?: string;
  ride_style?: string;
  slope_tolerance?: string;
  priority?: string;
  duration_bucket?: "evening" | "half_day" | "one_day" | "two_day" | "three_day";
  destination_preferences?: string[];
  return_preference?: "ride_back" | "public_transport" | "shorten_route";
  overnight_preference?: "avoid" | "optional" | "required";
  lodging_preference?: string;
  cross_city_allowed?: boolean;
};

export type PlannerRequest = {
  intent?: RideIntent;
  query: string;
  target_date: string;
  planning_mode?: PlanningMode;
  planning_scene?: PlanningScene;
  input_mode: InputMode;
  structured_constraints?: StructuredConstraints;
};

export type RidePlanPreflightResponse = {
  ready_to_plan: boolean;
  parsed_constraints: Record<string, unknown>;
  missing_core_fields: string[];
  clarification_prompt: string | null;
};

export type ChatTurnMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatTurnRequest = {
  messages: ChatTurnMessage[];
  intent?: RideIntent;
  planning_scene?: PlanningScene;
  target_date: string;
  slot_state?: Record<string, unknown>;
};

export type ChatTurnResponse = {
  assistant_name: string;
  intent: RideIntent;
  assistant_message: string;
  slot_state: Record<string, unknown>;
  missing_slots: string[];
  ready_to_plan: boolean;
  planner_request: PlannerRequest | null;
  ui_hints: {
    quick_replies?: string[];
    show_advanced_controls?: boolean;
    planning_status_label?: string;
  };
};

export type InputSummary = {
  intent?: RideIntent;
  planning_mode?: PlanningMode;
  planning_scene?: PlanningScene;
  input_mode: InputMode;
  target_date: string;
  departure_time?: string | null;
  city_code: string;
  origin_region?: string | null;
  start_point?: string | null;
  available_hours?: number | null;
  target_distance_km?: number | null;
  fitness_level?: string | null;
  ride_style?: string | null;
  slope_tolerance?: string | null;
  priority?: string | null;
  duration_bucket?: "evening" | "half_day" | "one_day" | "two_day" | "three_day" | null;
  destination_preferences?: string[];
  return_preference?: "ride_back" | "public_transport" | "shorten_route" | null;
  overnight_preference?: "avoid" | "optional" | "required" | null;
  lodging_preference?: string | null;
  cross_city_allowed?: boolean | null;
  defaults_applied: string[];
};

export type RouteMap = {
  route_code: string;
  route_name: string;
  provider_name: string;
  fact_source: string;
  polyline: Array<{ longitude: number; latitude: number }>;
  polyline_available: boolean;
  fallback_reason: string | null;
  start_point: { name?: string | null; longitude?: number | null; latitude?: number | null };
  user_start_point?: { name?: string | null; longitude?: number | null; latitude?: number | null };
  template_start_point?: { name?: string | null; longitude?: number | null; latitude?: number | null };
  end_point: { name?: string | null; longitude?: number | null; latitude?: number | null };
  approach_distance_km?: number | null;
  approach_duration_hours?: number | null;
  template_distance_km?: number | null;
  template_duration_hours?: number | null;
  total_distance_km?: number | null;
  total_duration_hours?: number | null;
  supply_points: SupplyPoint[];
  bailout_options: BailoutOption[];
  climb_segments: ClimbSegment[];
};

export type RiskSummary = {
  overall_risk_score?: number;
  weather_risk_score?: number;
  climb_risk_score?: number;
  traffic_risk_score?: number;
  supply_risk_score?: number;
  return_risk_score?: number;
  risk_level?: string;
};

export type SupplyPoint = {
  name: string;
  km_mark: number;
  type: string;
};

export type BailoutOption = {
  name: string;
  km_mark: number;
  reason: string;
};

export type ClimbSegment = {
  name: string;
  distance_km: number;
  elevation_gain_m: number;
  gradient_note: string;
};

export type Roadbook = {
  departure_window?: string;
  key_segments?: string[];
  supply_advice?: string[];
  mitigation_advice?: string[];
  shorten_options?: string[];
  route_notes?: string;
  risk_summary?: RiskSummary;
  backup_plan?: string;
  poi_summary?: {
    supply_count?: number;
    bailout_count?: number;
    supply_labels?: string[];
    bailout_labels?: string[];
  } | null;
  route_context?: {
    provider_name?: string;
    start_region?: string;
    distance_km?: number;
    estimated_duration_hours?: number;
    approach_distance_km?: number | null;
    approach_duration_hours?: number | null;
    total_distance_km?: number | null;
    total_duration_hours?: number | null;
    average_speed_kmh?: number | null;
    surface_type?: string | null;
    loop_type?: string | null;
  } | null;
};

export type WeatherSnapshot = {
  region_code: string;
  forecast_date: string;
  temperature_min: number | null;
  temperature_max: number | null;
  precipitation_probability: number | null;
  wind_speed: number | null;
  wind_direction: string | null;
  weather_summary: string;
  provider_name: string;
  raw_payload: Record<string, unknown> | null;
};

export type RouteDetail = {
  route_code: string;
  route_name: string;
  city_code: string;
  distance_km: number;
  elevation_gain_m: number;
  estimated_duration_hours: number;
  difficulty_level: string;
  ride_style_tags: string[];
  district_tags: string[];
  start_point_name: string | null;
  start_point_lng: number | null;
  start_point_lat: number | null;
  end_point_name: string | null;
  loop_type: string | null;
  season_tags: string[];
  best_time_slots: string[];
  avoid_time_slots: string[];
  surface_type: string | null;
  traffic_level: string;
  supply_score: number;
  return_difficulty_score: number;
  scenic_score: number;
  training_score: number | null;
  beginner_friendly: boolean;
  climb_segments: ClimbSegment[];
  supply_points: SupplyPoint[];
  bailout_options: BailoutOption[];
  holiday_penalty_level: string | null;
  weather_sensitivity: Record<string, unknown>;
  route_notes: string | null;
};

export type RecommendedRoute = {
  route_code: string;
  route_name: string;
  distance_km: number;
  elevation_gain_m: number;
  estimated_duration_hours: number;
  difficulty_level: string;
  ride_style_tags: string[];
  district_tags: string[];
};

export type RidePlanResponse = {
  status: string;
  intent?: RideIntent;
  planning_mode?: PlanningMode;
  request_no: string;
  parsed_constraints: Record<string, unknown>;
  input_summary?: InputSummary;
  route_map?: RouteMap | null;
  clarification_prompt: string | null;
  no_match_reason: string | null;
  recommended_plan: RoutePlanCard;
  alternatives: RoutePlanCard[];
  weather_snapshot: WeatherSnapshot;
  fallback_reason: string[];
  tool_trace: Array<{
    stage_name: string;
    status: string;
    provider_name: string;
    summary: string;
    fallback_reason: string | null;
  }>;
  decision?: {
    intent: RideIntent;
    scene?: PlanningScene | null;
    go_decision: string;
    title: string;
    summary: string;
  } | null;
  plan?: {
    kind: "route" | "weekend_recommendation";
    code: string;
    title: string;
    summary: string;
    distance_km?: number | null;
    elevation_gain_m?: number | null;
    estimated_duration_hours?: number | null;
    total_duration_hours?: number | null;
    risk_level?: string | null;
    destination_name?: string | null;
    stay_suggestion?: string | null;
    return_options?: string[];
  } | null;
  alternative_plans?: Array<{
    kind: "route" | "weekend_recommendation";
    code: string;
    title: string;
    summary: string;
    distance_km?: number | null;
    elevation_gain_m?: number | null;
    estimated_duration_hours?: number | null;
    total_duration_hours?: number | null;
    risk_level?: string | null;
    destination_name?: string | null;
    stay_suggestion?: string | null;
    return_options?: string[];
  }>;
  explanation?: {
    headline: string;
    summary: string;
    confidence_notes: string[];
  } | null;
  risk?: {
    level?: string | null;
    items: string[];
    fallback_plan?: string | null;
    scores?: Record<string, unknown> | null;
  } | null;
  equipment?: {
    items: string[];
  } | null;
  fallback?: {
    status: string;
    reasons: string[];
    message?: string | null;
  } | null;
  decision_summary?: DecisionSummary | null;
  roadbook: Roadbook | null;
  recommended_trip?: NearbyTripCard | null;
  trip_alternatives?: NearbyTripCard[];
  trip_rhythm?: TripRhythm | null;
  trip_risks?: TripRisks | null;
};

export type DecisionSummary = {
  scene?: PlanningScene | null;
  go_decision: string;
  decision_title: string;
  decision_reason: string;
  confidence_notes: string[];
  equipment_advice: string[];
};

export type NearbyTripCard = {
  trip_no: string;
  trip_name: string;
  destination_name: string;
  suitable_for: string;
  total_distance_km: number;
  ride_duration_hours: number;
  total_duration_hours: number;
  recommended_departure_time: string;
  stay_suggestion: string;
  why_recommended: string;
  risk_level: string;
  return_options: string[];
  duration_bucket?: string | null;
  itinerary_days?: Array<Record<string, unknown>>;
  lodging_plan?: string | null;
  equipment_advice?: string[];
  weather_window_notes?: string | null;
};

export type TripRhythm = {
  segments: Array<{
    stage: string;
    time_window: string;
    description: string;
  }>;
};

export type TripRisks = {
  risk_items: string[];
  fallback_plan: string;
};

export type RideRecordEntryMode = "planned" | "manual";
export type RideRecordCompletionStatus = "completed" | "shortened" | "cancelled";
export type RideRecordEffortFeeling = "easy" | "steady" | "hard";
export type RideRecordMoodAfter = "refreshed" | "normal" | "tired";

export type CreateRideRecordRequest = {
  entry_mode: RideRecordEntryMode;
  source_request_no?: string;
  ride_date: string;
  route_code?: string;
  route_title?: string;
  destination_name?: string;
  start_point?: string;
  origin_region?: string;
  completion_status: RideRecordCompletionStatus;
  actual_duration_hours?: number;
  actual_distance_km?: number;
  effort_feeling: RideRecordEffortFeeling;
  mood_after: RideRecordMoodAfter;
  notes?: string;
  tags: string[];
};

export type RideSummary = {
  headline: string;
  summary: string;
  completion_assessment: string;
  effort_assessment: string;
  recovery_advice: string;
  next_ride_prompt: string;
  plan_alignment?: string | null;
  confidence_notes: string[];
};

export type RideRecordPayload = {
  ride_record_no: string;
  entry_mode: RideRecordEntryMode;
  source_request_no?: string | null;
  ride_date: string;
  intent?: RideIntent;
  plan_kind?: "route" | "weekend_recommendation" | null;
  route_code?: string | null;
  route_title?: string | null;
  destination_name?: string | null;
  start_point?: string | null;
  origin_region?: string | null;
  completion_status: RideRecordCompletionStatus;
  actual_duration_hours?: number | null;
  actual_distance_km?: number | null;
  effort_feeling: RideRecordEffortFeeling;
  mood_after: RideRecordMoodAfter;
  notes?: string | null;
  tags: string[];
};

export type RideRecordDetailResponse = {
  ride_record: RideRecordPayload;
  ride_summary: RideSummary;
};

export class ApiRequestError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.detail = detail;
  }
}

export type RideRecordListItem = {
  ride_record_no: string;
  ride_date: string;
  route_title?: string | null;
  destination_name?: string | null;
  completion_status: RideRecordCompletionStatus;
  summary_headline?: string | null;
};

export type RideRecordListResponse = {
  items: RideRecordListItem[];
};

export type PlannerStageUpdate = {
  stage_name: string;
  status: string;
  provider_name: string;
  summary: string;
  fallback_reason: string | null;
};

type StreamHandlers = {
  onStage?: (stage: PlannerStageUpdate) => void;
};

export async function preflightRidePlan(request: PlannerRequest, userProfile?: UserProfile): Promise<RidePlanPreflightResponse> {
  const response = await fetch("/api/v1/ride/plan/preflight", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildRidePlanRequest(request, userProfile))
  });

  if (!response.ok) {
    throw new Error(`ride-plan-preflight-request-failed:${response.status}`);
  }

  return response.json() as Promise<RidePlanPreflightResponse>;
}

export async function createChatTurn(request: ChatTurnRequest, userProfile?: UserProfile): Promise<ChatTurnResponse> {
  const requestBody: Record<string, unknown> = {
    messages: request.messages,
    intent: request.intent,
    planning_scene: request.planning_scene,
    target_date: request.target_date,
    slot_state: request.slot_state ?? {}
  };
  if (userProfile && (userProfile.fitness_level || userProfile.slope_tolerance || userProfile.ride_style_preferences.length > 0)) {
    requestBody.user_profile = {
      fitness_level: userProfile.fitness_level || undefined,
      slope_tolerance: userProfile.slope_tolerance || undefined,
      ride_style_preferences: userProfile.ride_style_preferences
    };
  }
  const response = await fetch("/api/v1/ride/chat/turn", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    throw new Error(`ride-chat-turn-request-failed:${response.status}`);
  }

  return response.json() as Promise<ChatTurnResponse>;
}

export async function createRidePlan(request: PlannerRequest, userProfile?: UserProfile): Promise<RidePlanResponse> {
  const requestBody = buildRidePlanRequest(request, userProfile);
  const response = await fetch("/api/v1/ride/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    throw new Error(`ride-plan-request-failed:${response.status}`);
  }

  return response.json() as Promise<RidePlanResponse>;
}

export async function createRidePlanStream(
  request: PlannerRequest,
  userProfile: UserProfile | undefined,
  handlers?: StreamHandlers
): Promise<RidePlanResponse> {
  const response = await fetch("/api/v1/ride/plan/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(buildRidePlanRequest(request, userProfile))
  });

  if (!response.ok || !response.body) {
    throw new Error(`ride-plan-stream-request-failed:${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: RidePlanResponse | null = null;

  while (finalResult === null) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const eventBlocks = buffer.split("\n\n");
    buffer = eventBlocks.pop() ?? "";

    for (const block of eventBlocks) {
      const parsed = parseSseEvent(block);
      if (!parsed) {
        continue;
      }
      if (parsed.event === "stage_update") {
        handlers?.onStage?.(parsed.data as PlannerStageUpdate);
      }
      if (parsed.event === "plan_ready") {
        finalResult = parsed.data as RidePlanResponse;
        break;
      }
      if (parsed.event === "error") {
        throw new Error("ride-plan-stream-server-error");
      }
    }

    if (done) {
      break;
    }
  }

  if (finalResult === null) {
    throw new Error("ride-plan-stream-incomplete");
  }

  return finalResult;
}

export async function getRouteDetail(routeCode: string): Promise<RouteDetail> {
  const response = await fetch(`/api/v1/routes/${routeCode}`);

  if (!response.ok) {
    throw new Error(`route-detail-request-failed:${response.status}`);
  }

  return response.json() as Promise<RouteDetail>;
}

export async function getRecommendedRoutes(params?: {
  cityCode?: string;
  originRegion?: string | null;
  rideStyle?: string | null;
}): Promise<RecommendedRoute[]> {
  const searchParams = new URLSearchParams();
  if (params?.cityCode) {
    searchParams.set("city_code", params.cityCode);
  }
  if (params?.originRegion) {
    searchParams.set("origin_region", params.originRegion);
  }
  if (params?.rideStyle) {
    searchParams.set("ride_style", params.rideStyle);
  }
  const query = searchParams.toString();
  const response = await fetch(`/api/v1/routes/recommended${query ? `?${query}` : ""}`);

  if (!response.ok) {
    throw new Error(`recommended-routes-request-failed:${response.status}`);
  }

  return response.json() as Promise<RecommendedRoute[]>;
}

export async function getRidePlan(requestNo: string): Promise<RidePlanResponse> {
  const response = await fetch(`/api/v1/ride/plan/${requestNo}`);

  if (!response.ok) {
    throw new Error(`ride-plan-detail-request-failed:${response.status}`);
  }

  return response.json() as Promise<RidePlanResponse>;
}

export async function createRideRecord(payload: CreateRideRecordRequest): Promise<RideRecordDetailResponse> {
  const response = await fetch("/api/v1/rides/records", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw await buildApiRequestError("ride-record-create-request-failed", response);
  }

  return response.json() as Promise<RideRecordDetailResponse>;
}

export async function getRideRecord(rideRecordNo: string): Promise<RideRecordDetailResponse> {
  const response = await fetch(`/api/v1/rides/records/${rideRecordNo}`);

  if (!response.ok) {
    throw new Error(`ride-record-detail-request-failed:${response.status}`);
  }

  return response.json() as Promise<RideRecordDetailResponse>;
}

export async function listRideRecords(limit = 20): Promise<RideRecordListResponse> {
  const searchParams = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(`/api/v1/rides/records?${searchParams.toString()}`);

  if (!response.ok) {
    throw new Error(`ride-record-list-request-failed:${response.status}`);
  }

  return response.json() as Promise<RideRecordListResponse>;
}

function buildRidePlanRequest(request: PlannerRequest, userProfile?: UserProfile): Record<string, unknown> {
  const requestBody: Record<string, unknown> = {
    intent: request.intent,
    query: request.query,
    target_date: request.target_date,
    input_mode: request.input_mode
  };
  if (request.planning_mode) {
    requestBody.planning_mode = request.planning_mode;
  }
  if (request.planning_scene) {
    requestBody.planning_scene = request.planning_scene;
  }
  if (request.structured_constraints) {
    requestBody.structured_constraints = request.structured_constraints;
  }
  if (userProfile && (userProfile.fitness_level || userProfile.slope_tolerance || userProfile.ride_style_preferences.length > 0)) {
    requestBody.user_profile = {
      fitness_level: userProfile.fitness_level || undefined,
      slope_tolerance: userProfile.slope_tolerance || undefined,
      ride_style_preferences: userProfile.ride_style_preferences
    };
  }
  return requestBody;
}

function parseSseEvent(block: string): { event: string; data: unknown } | null {
  const lines = block.split("\n");
  const eventLine = lines.find((line) => line.startsWith("event: "));
  const dataLines = lines.filter((line) => line.startsWith("data: "));

  if (!eventLine || dataLines.length === 0) {
    return null;
  }

  return {
    event: eventLine.replace("event: ", "").trim(),
    data: JSON.parse(dataLines.map((line) => line.replace("data: ", "")).join("\n"))
  };
}

async function buildApiRequestError(prefix: string, response: Response): Promise<ApiRequestError> {
  const detail = await readErrorDetail(response);
  return new ApiRequestError(`${prefix}:${response.status}${detail ? `:${detail}` : ""}`, response.status, detail);
}

async function readErrorDetail(response: Response): Promise<string | undefined> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : undefined;
  } catch {
    return undefined;
  }
}

import type { UserProfile } from "../settings/store";
