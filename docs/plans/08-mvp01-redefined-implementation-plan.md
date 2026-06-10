# MVP01 Redefined Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Align the live cycling-agent product with the redefined MVP01: a personal pre-ride decision planner for city rides and 2-3 day nearby cycling trips.

**Architecture:** Keep the current `RidePlanningOrchestrator` model and avoid introducing free-form agents. Extend the existing `route` and `nearby_trip` implementation paths with a product-level `planning_scene`, location-first inputs, richer clarification, decision-first output, equipment advice, and weekend-trip planning data.

**Tech Stack:** FastAPI, Pydantic, React, TypeScript, Vite, pytest, Vitest, React Testing Library

---

## Source Documents

- Product source: `docs/product/04-prd-mvp01-redefined.md`
- Legacy MVP reference: `docs/product/02-prd-mvp.md`
- Nearby-trip reference: `docs/product/03-prd-phase2-nearby-trips.md`
- Current implementation guide: `products/cycling-agent/docs/current-implementation-overview.md`
- Backend root: `products/cycling-agent/backend`
- Frontend root: `products/cycling-agent/frontend`

## File Structure

Expected responsibility split:

- `docs/product/02-prd-mvp.md`: mark as legacy MVP draft and point to the new MVP01 definition.
- `docs/product/03-prd-phase2-nearby-trips.md`: clarify that some nearby-trip semantics are now part of MVP01 product scope, while current engineering mode remains `nearby_trip`.
- `products/cycling-agent/backend/app/schemas/ride_plan.py`: request / response schema expansion for scene, location, multi-day duration, lodging, and equipment output.
- `products/cycling-agent/backend/app/agents/query_parser_agent.py`: deterministic parsing for city ride vs weekend trip intent.
- `products/cycling-agent/backend/app/services/ride_planning_orchestrator.py`: scene-aware branching and decision-first response assembly.
- `products/cycling-agent/backend/app/services/nearby_trip_planner.py`: expand from half-day / one-day nearby plans to 2-3 day weekend cycling trips.
- `products/cycling-agent/backend/app/services/roadbook_service.py`: add equipment and decision-summary generation for city rides.
- `products/cycling-agent/data/hangzhou_nearby_destinations.json`: add nearby destinations such as 千岛湖 and 湖州 with lodging and weekend suitability facts.
- `products/cycling-agent/data/hangzhou_trip_templates.json`: add 2-3 day trip templates.
- `products/cycling-agent/frontend/src/features/planner/api.ts`: mirror schema changes in TypeScript.
- `products/cycling-agent/frontend/src/features/planner/hooks.ts`: support location-first input, scene defaults, and clarification flow.
- `products/cycling-agent/frontend/src/pages/HomePage.tsx`: replace MVP labels with user-facing scenarios.
- `products/cycling-agent/frontend/src/components/PlanResultView.tsx`: render decision-first city and weekend-trip results.

## Task 1: Sync Product And Engineering Docs

**Files:**

- Modify: `docs/product/02-prd-mvp.md`
- Modify: `docs/product/03-prd-phase2-nearby-trips.md`
- Modify: `products/cycling-agent/docs/current-implementation-overview.md`

- [x] **Step 1: Mark old MVP doc as legacy**

  Add a short note near the top of `docs/product/02-prd-mvp.md`:

  ```markdown
  > 口径说明：这份文档是旧版 MVP 草稿。新的 MVP01 产品定义以 `docs/product/04-prd-mvp01-redefined.md` 为准；本文保留为早期路线规划闭环参考。
  ```

- [x] **Step 2: Clarify nearby-trip boundary**

  Add a short note near the top of `docs/product/03-prd-phase2-nearby-trips.md`:

  ```markdown
  > 口径说明：新的 MVP01 已经吸收“周末 / 节假日 2 到 3 天附近骑行出行”的产品语义。当前工程里的 `planning_mode=nearby_trip` 仍作为周边出行实现模式保留，但后续需要扩展到多天、住宿、装备和天气窗口。
  ```

- [x] **Step 3: Update current implementation overview**

  In `products/cycling-agent/docs/current-implementation-overview.md`, update the traceability block so `docs/product/04-prd-mvp01-redefined.md` is named as the current product source.

- [x] **Step 4: Verify doc links**

  Run:

  ```bash
  rg -n "04-prd-mvp01-redefined|旧版 MVP|planning_mode=nearby_trip" docs/product products/cycling-agent/docs/current-implementation-overview.md
  ```

  Expected: output shows the new MVP01 doc referenced from the legacy MVP doc, nearby-trip doc, and implementation overview.

## Task 2: Add Scene And Location Request Schema

**Files:**

- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
- Modify: `products/cycling-agent/backend/tests/test_ride_plan_schema.py`
- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
- Modify: `products/cycling-agent/frontend/src/tests/planner-submit.test.tsx`

- [x] **Step 1: Add backend schema tests**

  Add tests that assert:

  - `planning_scene` accepts `city_ride` and `weekend_trip`
  - `origin_location` can carry `name`, `latitude`, `longitude`, and `source`
  - `duration_bucket` accepts `evening`, `half_day`, `one_day`, `two_day`, `three_day`
  - weekend-only preferences can be passed without breaking route-mode requests

- [x] **Step 2: Extend backend schema**

  Add:

  ```python
  class OriginLocationPayload(BaseModel):
      name: str | None = None
      latitude: float | None = None
      longitude: float | None = None
      source: str | None = Field(default=None, pattern="^(browser|manual|saved_place)$")
  ```

  Extend `RidePlanRequestSchema` with:

  ```python
  planning_scene: str | None = Field(default=None, pattern="^(city_ride|weekend_trip)$")
  ```

  Extend `StructuredConstraintsPayload` with:

  ```python
  origin_location: OriginLocationPayload | None = None
  duration_bucket: str | None = Field(default=None, pattern="^(evening|half_day|one_day|two_day|three_day)$")
  overnight_preference: str | None = Field(default=None, pattern="^(avoid|optional|required)$")
  lodging_preference: str | None = None
  cross_city_allowed: bool | None = None
  ```

- [x] **Step 3: Mirror frontend types**

  Update `PlanningMode` only if the implementation still needs old API compatibility. Add a separate `PlanningScene` type:

  ```ts
  export type PlanningScene = "city_ride" | "weekend_trip";
  ```

  Add `origin_location`, expanded `duration_bucket`, `overnight_preference`, `lodging_preference`, and `cross_city_allowed` to `StructuredConstraints`.

- [x] **Step 4: Run schema and frontend request tests**

  Run:

  ```bash
  cd products/cycling-agent/backend && pytest tests/test_ride_plan_schema.py -v
  cd products/cycling-agent/frontend && npm test -- planner-submit.test.tsx
  ```

  Expected: both pass.

## Task 3: Parse City Ride And Weekend Trip Intent

**Files:**

- Modify: `products/cycling-agent/backend/app/agents/query_parser_agent.py`
- Modify: `products/cycling-agent/backend/tests/test_query_parser_agent.py`
- Modify: `products/cycling-agent/backend/tests/test_ride_plan_api.py`

- [x] **Step 1: Add parser tests**

  Cover these examples:

  - `我今天晚上想出去骑行一下` -> `planning_scene=city_ride`, `duration_bucket=evening`, missing `start_point` and time / distance.
  - `周末想出去骑车，附近有什么推荐线路么` -> `planning_scene=weekend_trip`, missing `start_point`, `overnight_preference`, and time / days.
  - `这周末想去千岛湖骑两天` -> `planning_scene=weekend_trip`, `duration_bucket=two_day`, destination preference includes `千岛湖`.
  - `今晚从闻涛路滨江段出发骑2小时，不要爬坡` -> `planning_scene=city_ride`, start point parsed, slope tolerance avoid.

- [x] **Step 2: Extend deterministic parser**

  Add keyword-based detection:

  - city ride keywords: `今晚`, `今天晚上`, `下午`, `下班`, `夜骑`
  - weekend trip keywords: `周末`, `节假日`, `两天`, `三天`, `过夜`, `千岛湖`, `湖州`
  - duration bucket mapping: evening / two_day / three_day
  - lodging preference extraction for `住宿`, `过夜`, `酒店`, `民宿`

- [x] **Step 3: Update clarification rules**

  City ride should clarify start point and time budget first. Weekend trip should clarify start point, trip length, and overnight acceptance first.

- [x] **Step 4: Run parser and API tests**

  Run:

  ```bash
  cd products/cycling-agent/backend && pytest tests/test_query_parser_agent.py tests/test_ride_plan_api.py -v
  ```

  Expected: parser examples pass and preflight returns clarification prompts instead of generating weak plans for vague input.

## Task 4: Add Decision-First Output For City Rides

**Files:**

- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
- Modify: `products/cycling-agent/backend/app/services/ride_planning_orchestrator.py`
- Modify: `products/cycling-agent/backend/app/services/roadbook_service.py`
- Modify: `products/cycling-agent/backend/tests/test_ride_plan_api.py`
- Modify: `products/cycling-agent/backend/tests/test_roadbook_service.py`

- [x] **Step 1: Define decision summary schema**

  Add a response object with:

  - `scene`
  - `go_decision`
  - `decision_title`
  - `decision_reason`
  - `confidence_notes`
  - `equipment_advice`

- [x] **Step 2: Generate city-ride decision summaries**

  For `city_ride`, derive:

  - `go`: low risk and good route match
  - `caution`: medium risk or weather uncertainty
  - `no_go`: high risk or no matching route

  Equipment advice should be deterministic, based on weather and route context:

  - evening ride: lights, reflective gear, light wind layer
  - rain risk: waterproof shell or cancel / shorten
  - climb route: extra water and energy supply

- [x] **Step 3: Keep existing route response compatible**

  Do not remove `recommended_plan`, `alternatives`, `roadbook`, or `route_map`. Add `decision_summary` as an additive field.

- [x] **Step 4: Run backend tests**

  Run:

  ```bash
  cd products/cycling-agent/backend && pytest tests/test_ride_plan_api.py tests/test_roadbook_service.py -v
  ```

  Expected: existing route-mode tests still pass and new `decision_summary` assertions pass.

## Task 5: Expand Weekend Trip Data And Planner

**Files:**

- Modify: `products/cycling-agent/data/hangzhou_nearby_destinations.json`
- Modify: `products/cycling-agent/data/hangzhou_trip_templates.json`
- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
- Modify: `products/cycling-agent/backend/app/services/nearby_trip_planner.py`
- Modify: `products/cycling-agent/backend/tests/test_nearby_trip_api.py`
- Modify: `products/cycling-agent/backend/tests/test_admin_catalog_api.py`

- [x] **Step 1: Add weekend destination fields**

  Extend destination records with:

  - `weekend_duration_options`
  - `lodging_summary`
  - `gear_advice`
  - `weather_window_notes`

  Add seed destinations for `千岛湖` and `湖州`.

- [x] **Step 2: Add 2-3 day trip template fields**

  Extend trip templates with:

  - `duration_bucket`
  - `itinerary_days`
  - `lodging_plan`
  - `equipment_advice`
  - `weather_window_notes`

- [x] **Step 3: Update planner ranking**

  Weekend trip ranking should consider:

  - origin region match
  - duration bucket match
  - destination preference match
  - overnight preference
  - weather risk
  - return / fallback options

- [x] **Step 4: Add weekend-trip card output**

  Extend `NearbyTripCardSchema` or add a dedicated weekend-trip output so results include:

  - recommended destination
  - trip days
  - main route / backup route
  - lodging suggestion
  - equipment advice
  - weather window notes
  - why this destination, not another

- [x] **Step 5: Run backend tests**

  Run:

  ```bash
  cd products/cycling-agent/backend && pytest tests/test_nearby_trip_api.py tests/test_admin_catalog_api.py -v
  ```

  Expected: existing nearby-trip tests pass and new 2-3 day weekend-trip tests pass.

## Task 6: Redesign Planner Input Around Real Scenarios

**Files:**

- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
- Modify: `products/cycling-agent/frontend/src/features/planner/hooks.ts`
- Modify: `products/cycling-agent/frontend/src/pages/HomePage.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/home-page.test.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/clarification-prompt.test.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/planner-input-modes.test.tsx`

- [x] **Step 1: Replace user-facing MVP labels**

  Replace visible `mvp1` / `mvp2` language with:

  - `今晚 / 下午骑一下`
  - `周末骑行出行`

- [x] **Step 2: Add location-first input behavior**

  Use browser geolocation as an optional enhancement. If unavailable or denied, keep manual start point input and saved-place suggestions as the fallback.

- [x] **Step 3: Add scene-specific default examples**

  City ride example:

  ```text
  我今天晚上想出去骑行一下
  ```

  Weekend trip example:

  ```text
  周末想出去骑车，附近有什么推荐线路么
  ```

- [x] **Step 4: Update clarification UI**

  Clarification should ask for the missing high-value fields only:

  - city ride: start point, available time, slope preference
  - weekend trip: start point, trip length, overnight preference

- [x] **Step 5: Run frontend tests**

  Run:

  ```bash
  cd products/cycling-agent/frontend && npm test -- home-page.test.tsx clarification-prompt.test.tsx planner-input-modes.test.tsx
  ```

  Expected: homepage uses scenario labels, location fallback is visible, clarification prompts remain actionable.

## Task 7: Render Decision-First Results

**Files:**

- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
- Modify: `products/cycling-agent/frontend/src/components/PlanResultView.tsx`
- Modify: `products/cycling-agent/frontend/src/components/RecommendationCard.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/result-rendering.test.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/nearby-trip-result.test.tsx`

- [x] **Step 1: Add frontend response types**

  Mirror backend `decision_summary`, weekend-trip lodging, equipment, and weather-window fields.

- [x] **Step 2: Render decision summary first**

  The first result block should show:

  - go / caution / no-go
  - plain-language reason
  - confidence notes
  - equipment advice

- [x] **Step 3: Keep route and trip details below the conclusion**

  City ride: keep route recommendation, alternatives, risk, map, and roadbook below decision summary.

  Weekend trip: render destination, days, lodging, equipment, weather window, route rhythm, alternatives, and fallback plan.

- [x] **Step 4: Run frontend rendering tests**

  Run:

  ```bash
  cd products/cycling-agent/frontend && npm test -- result-rendering.test.tsx nearby-trip-result.test.tsx
  ```

  Expected: result page prioritizes decision summary and still renders existing route / trip detail sections.

## Task 8: Full Verification And Current-State Docs

**Files:**

- Modify: `products/cycling-agent/docs/current-implementation-overview.md`
- Modify: `products/cycling-agent/docs/manual-test-script.md`
- Modify: `docs/plans/05-roadmap.md`

- [x] **Step 1: Update current implementation overview**

  Describe the new product mapping:

  - product scenes: `city_ride`, `weekend_trip`
  - engineering modes: existing `route`, expanded `nearby_trip`
  - new response shape: decision-first output

- [x] **Step 2: Update manual test script**

  Add manual scenarios:

  - vague city ride: `我今天晚上想出去骑行一下`
  - concrete city ride: `今晚从闻涛路滨江段出发骑2小时，不要爬坡`
  - vague weekend trip: `周末想出去骑车，附近有什么推荐线路么`
  - destination weekend trip: `这周末想去千岛湖骑两天`

- [x] **Step 3: Run backend tests**

  Run:

  ```bash
  cd products/cycling-agent/backend && pytest tests -v
  ```

  Expected: all backend tests pass.

- [x] **Step 4: Run frontend tests and build**

  Run:

  ```bash
  cd products/cycling-agent/frontend && npm test && npm run build
  ```

  Expected: all frontend tests pass and production build succeeds.

- [x] **Step 5: Manual browser check**

  Start backend and frontend using non-conflicting ports, then manually verify:

  - city ride vague input triggers clarification
  - concrete city ride returns decision-first route recommendations
  - vague weekend input triggers trip-length / overnight clarification
  - weekend destination input returns lodging, equipment, route, weather, and fallback sections

## Acceptance Criteria

- New product source `docs/product/04-prd-mvp01-redefined.md` is reflected in current docs.
- User-facing UI no longer exposes `mvp1` / `mvp2` as primary labels.
- A vague city ride input clarifies before planning.
- A concrete city ride input returns a decision-first result with 2-4 route options.
- A vague weekend-trip input clarifies before planning.
- A concrete 2-3 day weekend-trip input returns destination, route, lodging, equipment, weather window, and fallback plan.
- Existing route, nearby-trip, admin, audit, weather, and fallback tests continue to pass.
