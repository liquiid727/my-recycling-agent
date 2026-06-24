"""CN: 新体验层 schema，定义首页内容、AI 伙伴、结果页、路线详情和生活方式偏好。
EN: Experience-layer schemas for home content, companion planning, result payloads, route detail, and lifestyle profile.
"""

from __future__ import annotations

from typing import Any
from datetime import date

from pydantic import BaseModel, Field

from app.schemas.ride_plan import UserProfilePayload


class HeroContentSchema(BaseModel):
    eyebrow: str
    title: str
    lead: str
    primary_cta: str
    secondary_cta: str


class TodayNudgeSchema(BaseModel):
    title: str
    body: str


class CuratedRouteCardSchema(BaseModel):
    route_code: str
    section_label: str
    title: str
    summary: str
    tags: list[str] = Field(default_factory=list)


class CompanionPersonaSchema(BaseModel):
    headline: str
    description: str
    quick_prompts: list[str] = Field(default_factory=list)


class WeekendPlanTemplateSchema(BaseModel):
    slug: str
    title: str
    summary: str


class JournalCardSchema(BaseModel):
    label: str
    title: str


class CtaFooterSchema(BaseModel):
    quote: str
    lead: str
    button_label: str


class ExperienceContentSchema(BaseModel):
    hero: HeroContentSchema
    today_nudges: list[TodayNudgeSchema] = Field(default_factory=list)
    curated_routes: list[CuratedRouteCardSchema] = Field(default_factory=list)
    companion_persona: CompanionPersonaSchema
    weekend_plan_templates: list[WeekendPlanTemplateSchema] = Field(default_factory=list)
    journal_cards: list[JournalCardSchema] = Field(default_factory=list)
    cta_footer: CtaFooterSchema


class LifestyleProfileSchema(BaseModel):
    home_region: str | None = None
    preferred_vibe: str | None = None
    companion_tone: str | None = None
    favorite_motifs: list[str] = Field(default_factory=list)
    avoid_motifs: list[str] = Field(default_factory=list)


class CompanionPlanRequestSchema(BaseModel):
    message: str = Field(min_length=2)
    target_date: date | None = None
    lifestyle_profile: LifestyleProfileSchema | None = None
    user_profile: UserProfilePayload | None = None


class CompanionFeaturedPlanSchema(BaseModel):
    route_code: str
    route_name: str
    distance_km: float
    estimated_duration_hours: float
    risk_level: str
    summary_reason: str


class CompanionPlanResponseSchema(BaseModel):
    status: str = Field(pattern="^(clarification|planned)$")
    assistant_message: str
    suggested_prompts: list[str] = Field(default_factory=list)
    editorial_intro: str | None = None
    request_no: str | None = None
    featured_plan: CompanionFeaturedPlanSchema | None = None


class ExperienceDecisionSchema(BaseModel):
    title: str
    reason: str
    confidence_notes: list[str] = Field(default_factory=list)


class ExperienceRouteStorySchema(BaseModel):
    route_code: str
    route_name: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    distance_km: float
    estimated_duration_hours: float


class ExperienceResultSchema(BaseModel):
    request_no: str
    scene: str
    editorial_intro: str
    decision: ExperienceDecisionSchema
    route_story: ExperienceRouteStorySchema
    support_notes: list[str] = Field(default_factory=list)
    ride_journal_prompt: str
    alternative_routes: list[ExperienceRouteStorySchema] = Field(default_factory=list)


class ExperienceRouteDetailSchema(BaseModel):
    route_code: str
    route_name: str
    headline: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    best_time_slots: list[str] = Field(default_factory=list)
    supply_points: list[dict] = Field(default_factory=list)
    bailout_options: list[dict] = Field(default_factory=list)


class CompletedRideRequestSchema(BaseModel):
    actual_duration_hours: float | None = Field(default=None, ge=0)
    actual_distance_km: float | None = Field(default=None, ge=0)
    selected_route_code: str | None = None
    user_note: str | None = Field(default=None, max_length=280)
    visibility_level: str = Field(pattern="^(private|shareable)$")


class CompletedRideResponseSchema(BaseModel):
    ride_no: str
    request_no: str
    status: str = Field(pattern="^completed$")


class PhotoAssetUploadResponseSchema(BaseModel):
    asset_no: str
    ride_no: str
    status: str = Field(pattern="^uploaded$")
    mime_type: str
    file_size_bytes: int
    original_url: str


class PostRideShareRequestSchema(BaseModel):
    ride_no: str
    asset_no: str
    style_preset: str = Field(pattern="^(anime_sky_glow|warm_journal|sunset_film|city_minimal)$")
    caption_tone: str = Field(pattern="^(gentle|editorial|playful)$")
    channel_targets: list[str] = Field(min_length=1)
    include_route_context: bool = True
    regenerate: bool = False


class PostRideShareResponseSchema(BaseModel):
    share_no: str
    ride_no: str
    asset_no: str
    status: str = Field(pattern="^(queued|processing|succeeded|failed)$")
    stage: str = Field(pattern="^(load_context|generate_style_image|generate_share_copy|done)$")
    poll_url: str | None = None
    styled_image_url: str | None = None
    copy_variants: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
