# Package 2C Growth Review Design

## Status

Draft for review.

## Workflow Note

This document is draft-only design material.

It is not yet the accepted implementation spec bundle.

Before coding package 2c, this design should be normalized into the repo's spec change chain.

## Scope

This design covers package 2c only:

- growth review across multiple months
- simple ride milestones
- deterministic “what has changed recently” feedback
- one read-only growth-review API
- one growth panel integrated into the existing `/rides` page

This design explicitly does not include:

- training plans
- user-defined goals
- yearly performance dashboards
- device-sync-based fitness analytics
- LLM-written coaching reports
- a second write flow for ride history

## Goal

Add a lightweight growth-review layer to the current cycling-agent product so the app can answer:

- 这段时间有没有在进步
- 最近最稳的骑法是什么
- 哪些变化值得继续保持

using saved `ride_records` as the only fact source.

## Product Intent

The product is still not a training platform.

Package 2c extends package 2a and 2b in a narrow, product-aligned way:

1. help the user go ride
2. record what actually happened
3. summarize one ride
4. review this month
5. let the user see their recent growth in plain language

This stays aligned with the `docs/design/` direction where the product should support:

- “帮助用户骑出去”
- “总结今天的骑行”
- “最近有没有偷懒”
- “记录我的骑行成长”

## Source Material

- `docs/design/Over-Cycling-Product-Vision-v0.1.md`
- `docs/design/OVER-CYCLING-PRD.md`
- `docs/design/产品设计和定位.md`
- `docs/design/CIM.md`
- `docs/design/todo.md`
- `docs/superpowers/specs/2026-06-15-package-2a-post-ride-record-and-summary-design.md`
- `docs/superpowers/specs/2026-06-15-package-2b-habit-monthly-summary-design.md`
- `products/cycling-agent/docs/current-implementation-overview.md`

## Existing System Baseline

The current runnable system already has:

- `ride_records` as the fact layer
- `ride_summary` as a per-ride view
- `ride_monthly_summary` as a month-scoped aggregate
- recent rides list and monthly summary band on `/rides`

The current system does not have:

- any cross-month growth review object
- any milestone extraction over recent ride history
- any deterministic “recently improved / maintained / slipped” review

So package 2c should be built as a read-only layer on top of package 2b, not as a separate analytics product.

## Design Principles

1. `ride_records` remain the only user-history fact source.
2. Package 2c is read-only in v1.
3. Prefer “recent growth you can act on” over broad statistics.
4. Keep the review window explicit and small, such as recent 90 or 180 days.
5. Stay deterministic and rule-first in v1.
6. Do not require heart rate, power, cadence, or external device data.

## Chosen Product Model

Package 2c introduces one derived aggregate object:

### `ride_growth_review`

Read-only response generated from a recent rolling window of saved `ride_records`.

The source of truth remains:

- `ride_records`
- optional linked `ride_plans` only when plan-follow-through facts are useful

`ride_monthly_summary_events` may support observability, but must not become a user-facing fact source.

## Domain Additions

### `ride_growth_review`

Required fields:

- `window_days`
- `period_start`
- `period_end`
- `ride_count`
- `ride_day_count`
- `completed_count`
- `total_distance_km`
- `total_duration_hours`
- `longest_distance_km`
- `longest_duration_hours`
- `active_month_count`
- `best_weekly_streak`
- `growth_status`
- `review_headline`
- `review_body`
- `next_focus`
- `milestones`

Optional but expected fields:

- `planned_count`
- `manual_count`
- `matched_plan_count`
- `top_start_region`
- `top_tag`
- `recent_vs_previous_ride_delta`
- `recent_vs_previous_distance_delta_km`

Rules:

1. `completed` and `shortened` count as rides that happened.
2. `cancelled` rides do not contribute to distance, duration, or milestones.
3. `period_end` is capped at today for rolling-window requests.
4. `best_weekly_streak` means the maximum consecutive calendar-week streak within the review window.
5. `active_month_count` counts distinct months with at least one non-cancelled ride.
6. `milestones` must be a small structured list, not free-form text blobs.
7. `next_focus` must stay low-pressure and directly compatible with the current planner flow.

### `growth_status`

Stable enum:

- `building`
- `steady`
- `expanding`
- `resetting`

Interpretation baseline:

- `building`: riding exists, but cadence and variety are still forming
- `steady`: recent rhythm is stable and maintainable
- `expanding`: recent range or consistency has clearly grown
- `resetting`: recent ride activity has dropped enough that the user is re-starting rhythm

### `milestones`

Structured item fields:

- `milestone_key`
- `title`
- `body`

Stable v1 milestone keys:

- `first_completed_ride`
- `longest_distance`
- `longest_duration`
- `best_streak`
- `most_active_month`

## User Flows

### Flow A: Review recent growth on the rides page

1. User opens `/rides`.
2. Frontend requests:
   - recent ride records
   - current month summary
   - growth review for a default window such as 90 days
3. Page renders a growth panel below the monthly summary band.
4. User sees:
   - recent growth status
   - a short review headline/body
   - simple milestones
   - one next focus suggestion

### Flow B: Switch review window

1. User changes the growth-review window from 90 days to 180 days.
2. Frontend requests a different `window_days`.
3. Backend returns a deterministic rolling-window aggregate.
4. Frontend updates only the growth panel.

### Flow C: Jump back into planning from the next focus

1. User reads `next_focus`.
2. User clicks a CTA such as “按这个方向继续安排”.
3. Frontend routes the user back to `/` with the suggestion text plus structured handoff context such as source window, growth status, streak, and suggested duration when available.

## Aggregation Logic

For a requested rolling window such as `window_days=90`:

1. read all `ride_records` with `ride_date` inside the window
2. exclude `cancelled` rides from realized metrics
3. optionally batch-load linked `ride_plans`
4. compare recent 30 days vs the previous 30 days when deriving simple delta fields

### Derived metrics

- `ride_count`
- `ride_day_count`
- `completed_count`
- `total_distance_km`
- `total_duration_hours`
- `longest_distance_km`
- `longest_duration_hours`
- `active_month_count`
- `best_weekly_streak`
- `top_start_region`
- `top_tag`
- `matched_plan_count`

### Growth-status rules

Suggested v1 thresholds:

1. `resetting`
   - no non-cancelled ride in the last 21 days, or
   - very low activity in the current review window
2. `building`
   - recent activity exists, but cadence is still low or inconsistent
3. `expanding`
   - recent 30-day activity materially exceeds the previous 30-day slice, or
   - a new longest distance / streak milestone appears
4. `steady`
   - otherwise, rhythm is stable without a clear reset or jump

## Backend Contract

### `GET /api/v1/rides/growth-review`

Query params:

- `window_days=90`

Response:

- `ride_growth_review`

Error semantics:

- `422 invalid-window-days`
  - when `window_days` is outside a small supported range
- `200` with zeroed review
  - when the review window has no ride records

## Frontend Surface

Package 2c should continue reusing `/rides`.

Add a growth panel below the monthly summary band showing:

- review-window switcher
- growth headline
- growth body
- key milestones
- one next focus CTA

This panel must explicitly cover:

- loading state while growth review is fetching
- empty state when the window has no rides
- failure state when the review fetch fails

Failure in the growth panel must not block the monthly summary band or the recent-ride list.

## Observability

Package 2c should emit enough evidence to verify use and common failure modes.

Minimum signals:

- count of growth-review requests
- split by `window_days`
- count of zeroed review responses
- count of invalid-window requests
- count of growth CTA clicks on the frontend when tracked

If request-level audit stays lightweight, also capture:

- `growth_status`
- whether a new milestone was present
- `next_focus.action_key`

## Out Of Scope

Package 2c does not include:

- saved annual reports
- social sharing cards for growth stats
- AI-written longform ride retrospectives
- personalized training blocks
- automatic goal adjustment

## Files Expected To Change

Primary backend files:

- `products/cycling-agent/backend/app/schemas/ride_plan.py`
- `products/cycling-agent/backend/app/api/routes/ride_record.py`
- `products/cycling-agent/backend/app/repositories/ride_record_repository.py`
- new `products/cycling-agent/backend/app/services/ride_growth_review_service.py`
- backend tests for the new growth-review behavior

Primary frontend files:

- `products/cycling-agent/frontend/src/features/planner/api.ts`
- `products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx`
- frontend tests for the growth panel and window switching

## Acceptance Criteria

Package 2c is successful when:

1. the backend can return a deterministic rolling-window growth review derived from `ride_records`
2. the review includes a stable `growth_status`, simple milestones, and one structured next focus
3. the `/rides` page shows the growth panel without replacing the existing monthly summary or recent-ride list
4. growth-panel loading or failure does not block the other `/rides` surfaces
5. the next focus can route the user back into the current planner flow
6. package 2c does not introduce a second fact source for ride history
