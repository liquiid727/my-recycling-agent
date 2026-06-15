# Package 1 Planning Chat Result Admin Alignment Design

## Status

Draft approved for implementation planning.

## Scope

This design covers package 1 only:

- planning
- chat
- result
- admin

It aligns the current `products/cycling-agent` experience and backend contract toward the product direction in `docs/design/`.

This design explicitly does not include:

- post-ride summary
- habit tracking
- ride records
- monthly reports
- login or auth

Those belong to package 2.

## Goal

Turn the current MVP from an engineering-shaped cycling planner into a user-facing riding companion product that speaks one consistent language across homepage entry, chat turns, planning execution, result rendering, and admin configuration.

## Product Intent

The product is not a training platform. It helps ordinary riders actually get out and ride.

Package 1 keeps the existing executable planning chain, but changes the primary product contract so that users experience:

- a companion-style entrypoint
- clear intent-based planning
- decision-first results
- admin assets that match what the companion actually says and recommends

## Source Material

- `docs/design/产品设计和定位.md`
- `docs/design/Over-Cycling-Product-Vision-v0.1.md`
- `docs/design/CIM.md`
- `docs/design/DECISION-TREE.md`
- `products/cycling-agent/docs/current-implementation-overview.md`

## Existing System Baseline

The current runnable implementation already provides:

- natural-language planning
- chat turn assembly
- city ride planning
- weekend trip planning
- risk scoring
- decision summary
- route and trip result rendering
- admin maintenance for routes, nearby destinations, trip templates, city strategy, and risk rules

The main gap is not missing infrastructure. The gap is that the visible product language, response structure, and admin mental model still reflect implementation-era concepts such as `planning_mode`, `planning_scene`, route-first output, and engineering-oriented asset maintenance.

## Design Principles

1. Keep the current executable planning chain alive.
2. Make user-facing language intent-first rather than implementation-first.
3. Keep old request fields working during the transition.
4. Do not introduce package 2 domains early.
5. Prefer re-organization and explicit semantics over broad rewrites.

## User-Facing Entry Model

Package 1 changes the primary product entry semantics to three intents:

- `ride_today`
- `ride_plan`
- `weekend_recommendation`

These are product-facing intents.

They replace the current front-end emphasis on:

- `planning_mode=route`
- `planning_mode=nearby_trip`
- `planning_scene=city_ride`
- `planning_scene=weekend_trip`

Those fields remain available internally and on compatibility paths, but they are no longer the main product vocabulary.

## Intent Definitions

### `ride_today`

Used when the user is asking whether it is suitable to ride now or today, with emphasis on weather, time, fatigue, and a conservative go or no-go recommendation.

Typical prompts:

- 今天适合骑吗
- 今晚能不能出去骑一下
- 下午有空，值不值得骑

### `ride_plan`

Used when the user already intends to ride and wants a concrete city ride plan, with emphasis on start point, duration, route style, difficulty, and fallback options.

Typical prompts:

- 帮我安排一次骑行
- 从滨江出发骑两小时
- 不想太累，给我几条稳妥路线

### `weekend_recommendation`

Used when the user is deciding whether and how to arrange a weekend or holiday ride-oriented outing, with emphasis on destination direction, trip duration, overnight preference, weather window, stay advice, and return options.

Typical prompts:

- 周末推荐一下
- 想出去骑两天
- 附近哪里适合轻松骑加过夜

## Chat And Planner Boundary

### Chat responsibilities

Chat becomes the primary user-facing companion layer. It is responsible for:

- understanding user wording
- classifying user intent
- maintaining slot state
- asking for missing constraints
- confirming understanding in companion-style language
- emitting a planner-ready request once information is sufficient

### Planner responsibilities

Planner becomes the execution layer. It is responsible for:

- consuming a structured intent and constraints payload
- producing recommendation candidates
- evaluating risk
- selecting the primary recommendation
- building explanation, equipment, and fallback content

Planner should no longer act as the primary place where user intent is inferred from raw conversation.

## Response Architecture

Package 1 introduces a unified result contract centered on these top-level concepts:

- `intent`
- `decision`
- `plan`
- `alternatives`
- `explanation`
- `risk`
- `equipment`
- `fallback`
- `tool_trace`

The current response fields remain temporarily available for compatibility, but the new contract becomes the canonical shape for package 1 front-end rendering and new tests.

## Decision-First Result Model

The result should always answer in this order:

1. What is the recommendation or decision
2. Why
3. What is the primary plan
4. What risks or caveats matter
5. What equipment or preparation is needed
6. What fallback or alternative options exist

This applies to all three intents.

Weekend results are allowed to add fields for:

- rhythm
- stay guidance
- return options

But weekend results should still be understood as the same result family, not a separate protocol with unrelated semantics.

## Backend Compatibility Strategy

Package 1 does not remove the old execution vocabulary immediately.

Compatibility rules:

1. Existing request payloads using `planning_mode` and `planning_scene` must continue to work.
2. Backend execution may still route using current scene and mode logic.
3. New front-end and chat flows should emit the new `intent` first and rely on backend mapping layers.
4. Old response fields may remain for a transition period, but new rendering and new tests should target the unified intent-based contract.

This keeps the live planning chain stable while shifting the public product semantics.

## Schema Strategy

The schema changes in package 1 should favor layering and normalization over deletion.

Expected schema changes:

- add explicit `intent`
- add a normalized `decision` object
- add a normalized `plan` object that can represent city ride or weekend recommendation payloads
- normalize explanation, risk, equipment, and fallback output
- preserve old route or trip specific fields temporarily

The package 1 schema is successful if the front-end can render all supported experiences from the normalized shape without branching on legacy protocol semantics first.

## Admin Model

Admin becomes a maintenance console for the companion's structured assets rather than a loose collection of engineering forms.

Package 1 admin groups assets into four buckets:

### Decision rules

- clarification rules
- missing-field rules
- recommendation bias rules
- risk and decision adjustment rules

### Route assets

- route templates
- route tags
- POI and supply facts
- bailout facts

### Weekend assets

- nearby destinations
- trip templates
- lodging and return facts
- weekend-specific recommendation structure

### Agent presentation assets

- recommendation wording templates
- equipment guidance templates
- downgrade or fallback wording
- explanation fragments tied to structured facts

This fourth bucket is important because the current product tone is mostly encoded in application logic. Package 1 starts moving that presentation responsibility into explicit assets and configuration boundaries.

## Files Expected To Change

Primary backend files:

- `products/cycling-agent/backend/app/schemas/ride_plan.py`
- `products/cycling-agent/backend/app/agents/chat_turn_agent.py`
- `products/cycling-agent/backend/app/agents/query_parser_agent.py`
- `products/cycling-agent/backend/app/api/routes/ride_chat.py`
- `products/cycling-agent/backend/app/api/routes/ride_plan.py`
- `products/cycling-agent/backend/app/api/routes/admin.py`
- `products/cycling-agent/backend/app/services/ride_planning_orchestrator.py`

Primary frontend files:

- `products/cycling-agent/frontend/src/features/planner/api.ts`
- `products/cycling-agent/frontend/src/features/planner/hooks.ts`
- `products/cycling-agent/frontend/src/pages/HomePage.tsx`
- `products/cycling-agent/frontend/src/components/PlanResultView.tsx`
- `products/cycling-agent/frontend/src/pages/AdminPage.tsx`

Support documentation:

- `products/cycling-agent/docs/current-implementation-overview.md`

## Delivery Order

Package 1 should be delivered in this order:

1. schema and response normalization
2. chat and planner boundary alignment
3. result rendering alignment
4. home entry and interaction alignment
5. admin grouping and naming alignment
6. tests and implementation documentation updates

This order keeps protocol changes ahead of UI changes and avoids coupling admin rework to unsettled response shapes.

## Error Handling And Fallback Rules

Package 1 keeps the current fallback philosophy:

- if the system lacks enough information, chat asks for clarification
- if planning cannot produce a confident recommendation, the result must say so explicitly
- if provider-backed facts degrade, the result must expose fallback status rather than pretending certainty
- if dynamic recommendation fails, the system may show browseable alternatives, but must label them as fallback or reference content

The product should sound companion-like, but never fake confidence.

## Testing Strategy

Package 1 requires three test layers.

### Backend schema and orchestration tests

These must validate:

- `intent` mapping
- chat-to-planner handoff
- normalized result structure
- admin asset grouping behavior
- compatibility for old mode and scene payloads

### Frontend flow tests

These must validate:

- home entry for the three user-facing intents
- chat clarification and slot progression
- decision-first result layout
- admin grouping and labels

### Compatibility tests

These must prove that existing request shapes using legacy fields still execute correctly during the package 1 transition.

## Success Criteria

Package 1 is complete when all of the following are true:

1. The homepage, chat flow, result page, and admin page speak one consistent product language aligned with `docs/design`.
2. The back end exposes a normalized intent-based response model while preserving compatibility for legacy request shapes.
3. Chat clearly owns intent understanding and planner clearly owns execution.
4. Result rendering is decision-first across city ride and weekend recommendation flows.
5. Admin is grouped around companion assets rather than only engineering-era tables.
6. Tests cover the new semantics and legacy compatibility.

## Non-Goals

Package 1 will not:

- add login
- add ride record persistence
- add habit tracking
- add post-ride summary generation
- add monthly reports
- perform a broad database redesign
- move files just to make naming cleaner

## Risks

### Risk: semantic layer drift

If `intent` becomes a front-end label only and does not govern normalized response semantics, package 1 will produce another split vocabulary.

Mitigation:

Use `intent` as the canonical product contract in schema and tests, not just in UI text.

### Risk: over-reliance on compatibility fields

If the front-end continues to read old route and trip shapes first, package 1 will only cosmetically align.

Mitigation:

Shift rendering to the normalized contract and keep old fields as compatibility support only.

### Risk: admin remains data-table-first

If admin only changes labels and not grouping and asset purpose, the companion configuration model remains hidden in code.

Mitigation:

Restructure admin around the four explicit asset buckets and make presentation assets first-class.

## Open Questions Resolved For Package 1

- Package 1 does not include package 2 domains.
- The preferred approach is chain alignment rather than pure surface edits or pure backend-first renaming.
- `intent` is the new primary product semantic layer.
- `planning_mode` and `planning_scene` remain transitional compatibility fields.
