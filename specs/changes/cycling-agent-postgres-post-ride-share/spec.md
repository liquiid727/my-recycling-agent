# cycling-agent/postgres-post-ride-share Spec

## Meta

- Domain: `cycling-agent`
- Feature: `postgres-post-ride-share`
- Source Draft: `spec-draft/over-cycling-product-upgrade.md`
- Source Thread: current Codex thread on PostgreSQL-only storage and post-ride share generation
- Status: proposed

## Goal

Move the accepted backend storage baseline from dual SQLite/PostgreSQL compatibility to PostgreSQL-only storage, and add a new experience-layer post-ride sharing capability that turns a completed ride photo into a stylized riding postcard plus share-ready copy for Xiaohongshu and WeChat Moments.

## Non-Goals

- This change does not add a general social feed, comments, likes, or follower graph.
- This change does not add live ride tracking, navigation, or hardware sync.
- This change does not make image generation part of the pre-ride planner critical path.
- This change does not promise artist-name style presets in public API contracts.
- This change does not introduce a distributed job queue in the first backend slice.

## Product Scope

This change extends the accepted product from a pure pre-ride planning system toward the documented post-ride loop:

- preserve current `city_ride` and `weekend_trip` planning flows
- add a persisted completed-ride fact
- add user photo asset upload tied to a completed ride
- add stylized postcard generation and share-copy generation as an experience-layer capability
- switch accepted backend storage and local validation baseline to PostgreSQL

## System Flow

1. User completes a ride that originated from an existing planning result or from a future manual ride entry.
2. Frontend calls a new experience endpoint to persist a completed-ride record.
3. User uploads one ride photo tied to that completed ride.
4. Backend stores the uploaded photo in media storage and persists a metadata record in PostgreSQL.
5. User requests share generation with a constrained style preset and channel targets.
6. Backend loads ride context from the completed ride and linked plan result when available.
7. Backend calls an OpenAI-compatible image-edit capability to stylize the uploaded photo.
8. Backend calls an OpenAI-compatible text-generation capability to produce share copy candidates.
9. Backend persists generation status, prompt audit payloads, and result payloads.
10. Frontend polls the share result endpoint until generation succeeds or fails.

## Core Entities

- `CompletedRide`
- `MediaAsset`
- `PostRideShare`
- existing `RidePlan` result payload
- existing `UserProfile` and `LifestyleProfile`

## Domain Rules

- A post-ride share must be anchored to a completed-ride fact, not directly to a plan result alone.
- Image generation is optional experience enhancement and must not block route planning, route detail, or profile flows.
- Public API contracts must use backend-owned style preset ids rather than open-ended artist-name strings.
- Generated copy must stay grounded in known ride facts; it must not invent distance, elevation, route completion, or weather details that were not persisted.
- Exact home-like start points and other sensitive location details must not be echoed into public-facing share copy by default.
- The same completed ride may have multiple regenerated shares, but idempotent retries with the same key must return the same share record.

## Storage Baseline Change

- Accepted local and live backend storage baseline becomes PostgreSQL-only.
- SQLite runtime support, SQLite docs, and SQLite test assumptions are removed from the accepted baseline.
- Repository SQL may continue to use shared placeholder syntax if the PostgreSQL adapter remains the only execution target.
- Backend configuration must fail fast when `CYCLING_AGENT_DATABASE_URL` is absent or not PostgreSQL.

## API Contract

### Existing APIs preserved

- Existing planning, route catalog, profile, admin, chat-turn, and audit APIs remain available.

### New APIs

- `POST /api/v1/experience/rides/{request_no}/complete`
- `POST /api/v1/experience/photo-assets`
- `POST /api/v1/experience/post-ride-shares`
- `GET /api/v1/experience/post-ride-shares/{share_no}`

### `POST /api/v1/experience/rides/{request_no}/complete`

Create a completed-ride record anchored to an existing planning result.

Request fields:

- `actual_duration_hours: float | null`
- `actual_distance_km: float | null`
- `selected_route_code: str | null`
- `user_note: str | null`
- `visibility_level: "private" | "shareable"`

Response fields:

- `ride_no: str`
- `request_no: str`
- `status: "completed"`

### `POST /api/v1/experience/photo-assets`

Upload one photo for a completed ride.

Request shape:

- `multipart/form-data`
- `ride_no: str`
- `photo: UploadFile`

Response fields:

- `asset_no: str`
- `ride_no: str`
- `status: "uploaded"`
- `mime_type: str`
- `file_size_bytes: int`
- `original_url: str`

### `POST /api/v1/experience/post-ride-shares`

Create a post-ride share generation job or inline generation record.

Request fields:

- `ride_no: str`
- `asset_no: str`
- `style_preset: "anime_sky_glow" | "warm_journal" | "sunset_film" | "city_minimal"`
- `caption_tone: "gentle" | "editorial" | "playful"`
- `channel_targets: list["xiaohongshu" | "moments"]`
- `include_route_context: bool`
- `regenerate: bool = false`

Response fields:

- `share_no: str`
- `ride_no: str`
- `asset_no: str`
- `status: "queued" | "processing" | "succeeded" | "failed"`
- `stage: "load_context" | "generate_style_image" | "generate_share_copy" | "done"`
- `poll_url: str`

### `GET /api/v1/experience/post-ride-shares/{share_no}`

Response fields:

- `share_no: str`
- `ride_no: str`
- `asset_no: str`
- `status: "queued" | "processing" | "succeeded" | "failed"`
- `stage: "load_context" | "generate_style_image" | "generate_share_copy" | "done"`
- `styled_image_url: str | null`
- `copy_variants: dict`
- `error_code: str | null`

## Data Model

### `completed_rides`

- `ride_no TEXT PRIMARY KEY`
- `request_no TEXT NOT NULL`
- `user_uid TEXT NOT NULL`
- `selected_route_code TEXT`
- `actual_duration_hours DOUBLE PRECISION`
- `actual_distance_km DOUBLE PRECISION`
- `user_note TEXT`
- `visibility_level TEXT NOT NULL`
- `created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`

### `media_assets`

- `asset_no TEXT PRIMARY KEY`
- `owner_type TEXT NOT NULL`
- `owner_no TEXT NOT NULL`
- `storage_key TEXT NOT NULL`
- `mime_type TEXT NOT NULL`
- `file_size_bytes BIGINT NOT NULL`
- `status TEXT NOT NULL`
- `created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`

### `post_ride_shares`

- `share_no TEXT PRIMARY KEY`
- `ride_no TEXT NOT NULL`
- `asset_no TEXT NOT NULL`
- `styled_asset_no TEXT`
- `style_preset TEXT NOT NULL`
- `caption_tone TEXT NOT NULL`
- `channel_targets_json TEXT NOT NULL`
- `status TEXT NOT NULL`
- `stage TEXT NOT NULL`
- `provider_name TEXT`
- `idempotency_key TEXT NOT NULL UNIQUE`
- `context_json TEXT`
- `prompt_json TEXT`
- `result_payload_json TEXT`
- `error_code TEXT`
- `created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`

## Media And Provider Rules

- Uploaded photos and generated photos must be stored outside core plan payload tables.
- Database rows store references and audit metadata only; image bytes must not be embedded in `ride_plans.payload_json`.
- The image provider contract must support image-edit semantics using an uploaded source image plus a backend-constructed prompt.
- The text provider contract may reuse the existing OpenAI-compatible provider shape, but image generation must not be forced through chat-completion JSON output.

## Style Preset Rules

- Public API style presets are repository-owned ids.
- Backend prompt composition maps preset ids to safe descriptive prompt fragments.
- Prompts must avoid explicit artist-name branding in stable API contracts.
- Default copy targets are short-form lifestyle sharing surfaces, not training summaries.

## Error Semantics

- `experience-completed-ride-plan-not-found`
- `experience-completed-ride-save-failed`
- `experience-photo-ride-not-found`
- `experience-photo-empty-upload`
- `experience-photo-unsupported-media-type`
- `experience-photo-store-failed`
- `experience-share-ride-not-found`
- `experience-share-asset-not-found`
- `experience-share-generation-failed`
- `experience-share-not-found`
- `cycling-agent-postgres-required`

## Exceptions And Fallbacks

- If a completed ride exists without a linked recommended route, share copy falls back to user note plus generic ride context.
- If the image provider fails after the share record is created, status becomes `failed` and `error_code` is persisted.
- If share-copy generation fails after a styled image succeeds, the share remains `failed`; partial image output may still be retained for operator debugging but is not returned as a successful share.
- If `regenerate=false` and the same idempotency key already exists, the existing share record is returned.

## Observability

- Record completed-ride creation events with `request_no` and `ride_no`.
- Record asset upload success and failure with `ride_no`, `asset_no`, mime type, and size.
- Record share generation transitions by `share_no`, `status`, `stage`, provider name, and error code.
- Preserve compact prompt/context audit payloads for generated images and generated copy.

## Security And Privacy

- Only accepted image mime types are allowed.
- Backend must cap upload size.
- Share-copy generation must avoid exposing exact start addresses or other precise personal-location hints by default.
- Admin or operator-only debug payloads must stay out of user-facing response shapes.

## Verification

Backend verification must cover:

- PostgreSQL-only config acceptance and fail-fast rejection of SQLite urls
- completed-ride creation success and 404 behavior
- photo upload validation and metadata persistence
- share generation success path with provider stubs
- share generation failure path with persisted `failed` status
- idempotent retry behavior

Documentation verification must cover:

- root README and product README no longer describe SQLite as accepted runtime
- current architecture context reflects PostgreSQL-only baseline after acceptance

## Open Questions

- Whether completed rides without `request_no` should be accepted in the first slice or deferred
- Whether generated share records should expose multiple stylized image variants in the first slice
- Whether the first slice should process generation inline or via a later background worker
