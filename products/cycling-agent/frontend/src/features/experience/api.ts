import type { UserProfile } from "../settings/store";

export type ExperienceContent = {
  hero: {
    eyebrow: string;
    title: string;
    lead: string;
    primary_cta: string;
    secondary_cta: string;
  };
  today_nudges: Array<{ title: string; body: string }>;
  curated_routes: Array<{ route_code: string; section_label: string; title: string; summary: string; tags: string[] }>;
  companion_persona: {
    headline: string;
    description: string;
    quick_prompts: string[];
  };
  weekend_plan_templates: Array<{ slug: string; title: string; summary: string }>;
  journal_cards: Array<{ label: string; title: string }>;
  cta_footer: {
    quote: string;
    lead: string;
    button_label: string;
  };
};

export type CompanionPlanResponse = {
  status: "clarification" | "planned";
  assistant_message: string;
  suggested_prompts: string[];
  editorial_intro: string | null;
  request_no: string | null;
  featured_plan: {
    route_code: string;
    route_name: string;
    distance_km: number;
    estimated_duration_hours: number;
    risk_level: string;
    summary_reason: string;
  } | null;
};

export type ExperienceResult = {
  request_no: string;
  scene: string;
  editorial_intro: string;
  decision: {
    title: string;
    reason: string;
    confidence_notes: string[];
  };
  route_story: {
    route_code: string;
    route_name: string;
    summary: string;
    tags: string[];
    distance_km: number;
    estimated_duration_hours: number;
  };
  support_notes: string[];
  ride_journal_prompt: string;
  alternative_routes: Array<{
    route_code: string;
    route_name: string;
    summary: string;
    tags: string[];
    distance_km: number;
    estimated_duration_hours: number;
  }>;
};

export type ExperienceRouteDetail = {
  route_code: string;
  route_name: string;
  headline: string;
  summary: string;
  tags: string[];
  best_time_slots: string[];
  supply_points: Array<{ name: string; km_mark: number; type: string }>;
  bailout_options: Array<{ name: string; km_mark: number; reason: string }>;
};

export type CompanionPlanRequest = {
  message: string;
  target_date?: string;
  user_profile?: {
    fitness_level?: UserProfile["fitness_level"];
    slope_tolerance?: UserProfile["slope_tolerance"];
    ride_style_preferences?: UserProfile["ride_style_preferences"];
  };
};

export async function getExperienceHome(): Promise<ExperienceContent> {
  return fetchJson("/api/v1/experience/home");
}

export async function createCompanionPlan(payload: CompanionPlanRequest): Promise<CompanionPlanResponse> {
  return fetchJson("/api/v1/experience/companion/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getExperienceResult(requestNo: string): Promise<ExperienceResult> {
  return fetchJson(`/api/v1/experience/results/${requestNo}`);
}

export async function getExperienceRoute(routeCode: string): Promise<ExperienceRouteDetail> {
  return fetchJson(`/api/v1/experience/routes/${routeCode}`);
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`request-failed:${url}`);
  }
  return response.json() as Promise<T>;
}
