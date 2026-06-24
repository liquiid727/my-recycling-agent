/*
 * CN: 规划前端 API 客户端，封装普通请求、SSE 流式请求、路线详情和历史结果读取。
 * EN: Planner API client wrapping normal requests, SSE streaming, route details, and saved plan reads.
 */

import { type RiderState, type UserProfile } from "../settings/store";

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
  query: string;
  target_date: string;
  planning_mode: PlanningMode;
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
  planning_scene: PlanningScene;
  target_date: string;
  slot_state?: Record<string, unknown>;
};

export type ChatTurnResponse = {
  assistant_name: string;
  assistant_message: string;
  slot_state: Record<string, unknown>;
  missing_slots: string[];
  ready_to_plan: boolean;
  planner_request: PlannerRequest | null;
  rider_state?: RiderState | null;
  ui_hints: {
    quick_replies?: string[];
    show_advanced_controls?: boolean;
    planning_status_label?: string;
  };
};

export type InputSummary = {
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
  template?: {
    fact_source?: string;
    route_code?: string;
    route_name?: string;
    start_point?: { name?: string | null; longitude?: number | null; latitude?: number | null } | null;
    end_point?: { name?: string | null; longitude?: number | null; latitude?: number | null } | null;
    distance_km?: number | null;
    duration_hours?: number | null;
    surface_type?: string | null;
    loop_type?: string | null;
  } | null;
  live?: {
    provider_name?: string;
    fact_source?: string;
    start_region?: string | null;
    user_start_point?: { name?: string | null; longitude?: number | null; latitude?: number | null } | null;
    polyline?: Array<{ longitude: number; latitude: number }>;
    direction_summary?: Array<Record<string, unknown>>;
    road_context?: Record<string, unknown> | null;
    approach_distance_km?: number | null;
    approach_duration_hours?: number | null;
    approach_method?: string | null;
    start_location?: Record<string, unknown> | null;
    approach_polyline?: Array<{ longitude: number; latitude: number }>;
  } | null;
  resolved?: {
    provider_name?: string;
    fact_source?: string;
    metric_source?: string;
    distance_km?: number | null;
    estimated_duration_hours?: number | null;
    average_speed_kmh?: number | null;
    total_distance_km?: number | null;
    total_duration_hours?: number | null;
  } | null;
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
    fact_source?: string;
    source_layer?: string;
    supply_fact_source?: string | null;
    bailout_fact_source?: string | null;
    template?: {
      fact_source?: string;
      supply_items?: SupplyPoint[];
      bailout_items?: BailoutOption[];
    } | null;
    live?: {
      provider_name?: string;
      fact_source?: string;
      supply_items?: Array<Record<string, unknown>>;
      bailout_items?: Array<Record<string, unknown>>;
    } | null;
    resolved?: {
      supply_count?: number;
      bailout_count?: number;
      supply_labels?: string[];
      bailout_labels?: string[];
      fact_source?: string;
      source_layer?: string;
      supply_fact_source?: string | null;
      bailout_fact_source?: string | null;
    } | null;
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
    fact_source?: string;
    template?: RouteMap["template"];
    live?: RouteMap["live"];
    resolved?: RouteMap["resolved"];
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
  planning_mode?: PlanningMode;
  request_no: string;
  parsed_constraints: Record<string, unknown>;
  input_summary?: InputSummary;
  rider_profile?: UserProfile | null;
  rider_state?: RiderState | null;
  ride_readiness?: RideReadiness | null;
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
  decision_summary?: DecisionSummary | null;
  roadbook: Roadbook | null;
  recommended_trip?: NearbyTripCard | null;
  trip_alternatives?: NearbyTripCard[];
  trip_rhythm?: TripRhythm | null;
  trip_risks?: TripRisks | null;
};

export type RideReadiness = {
  status: "go" | "light" | "rest";
  score: number;
  summary: string;
  reasons: string[];
  caution_flags: string[];
  recommended_intensity: "light" | "steady" | "rest";
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
  source_meta?: {
    trip_template?: {
      trip_no?: string;
      route_template_id?: string | null;
      duration_bucket?: string | null;
    } | null;
    destination_template?: {
      destination_no?: string | null;
      destination_type?: string | null;
      region_tags?: string[];
    } | null;
    route_binding?: {
      selected_route_code?: string | null;
      selected_route_name?: string | null;
      selected_route_source?: string | null;
      is_template_route_match?: boolean;
      canonical_route_code?: string | null;
      canonical_route_feasible?: boolean;
      canonical_route_rank?: number | null;
      selected_route_rank?: number | null;
      feasible_route_count?: number | null;
      audit_summary?: string | null;
    } | null;
    resolved_metrics?: {
      distance_km?: number | null;
      ride_duration_hours?: number | null;
      metric_source?: string | null;
    } | null;
  } | null;
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

export async function preflightRidePlan(
  request: PlannerRequest,
  userProfile?: UserProfile,
  riderState?: RiderState
): Promise<RidePlanPreflightResponse> {
  const response = await fetch("/api/v1/ride/plan/preflight", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildRidePlanRequest(request, userProfile, riderState))
  });

  if (!response.ok) {
    throw new Error(`ride-plan-preflight-request-failed:${response.status}`);
  }

  return response.json() as Promise<RidePlanPreflightResponse>;
}

export async function createChatTurn(
  request: ChatTurnRequest,
  userProfile?: UserProfile,
  riderState?: RiderState
): Promise<ChatTurnResponse> {
  const requestBody: Record<string, unknown> = {
    messages: request.messages,
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
  if (hasRiderState(riderState)) {
    requestBody.rider_state = {
      fatigue_level: riderState.fatigue_level || undefined,
      mood: riderState.mood || undefined,
      last_ride_days_ago: typeof riderState.last_ride_days_ago === "number" ? riderState.last_ride_days_ago : undefined
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

export async function createRidePlan(
  request: PlannerRequest,
  userProfile?: UserProfile,
  riderState?: RiderState
): Promise<RidePlanResponse> {
  const requestBody = buildRidePlanRequest(request, userProfile, riderState);
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
  riderState: RiderState | undefined,
  handlers?: StreamHandlers
): Promise<RidePlanResponse> {
  const response = await fetch("/api/v1/ride/plan/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(buildRidePlanRequest(request, userProfile, riderState))
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

function buildRidePlanRequest(
  request: PlannerRequest,
  userProfile?: UserProfile,
  riderState?: RiderState
): Record<string, unknown> {
  const requestBody: Record<string, unknown> = {
    query: request.query,
    target_date: request.target_date,
    planning_mode: request.planning_mode,
    planning_scene: request.planning_scene,
    input_mode: request.input_mode
  };
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
  if (hasRiderState(riderState)) {
    requestBody.rider_state = {
      fatigue_level: riderState.fatigue_level || undefined,
      mood: riderState.mood || undefined,
      last_ride_days_ago: typeof riderState.last_ride_days_ago === "number" ? riderState.last_ride_days_ago : undefined
    };
  }
  return requestBody;
}

function hasRiderState(riderState?: RiderState): riderState is RiderState {
  if (!riderState) {
    return false;
  }
  return Boolean(
    riderState.fatigue_level ||
      riderState.mood ||
      typeof riderState.last_ride_days_ago === "number"
  );
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
