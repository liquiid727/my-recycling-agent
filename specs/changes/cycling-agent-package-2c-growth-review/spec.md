# Cycling Agent Package 2C Growth Review

## Meta

- Domain: `cycling-agent`
- Feature: `package-2c-growth-review`
- Source Draft:
  - `docs/superpowers/specs/2026-06-15-package-2c-growth-review-design.md`
  - `docs/superpowers/plans/2026-06-15-package-2c-growth-review.md`
- Status: proposed

## Goal

Add a lightweight growth-review layer so the current cycling-agent product can show recent progress in plain language without turning into a training platform.

The product should be able to answer:

1. 这段时间有没有在进步
2. 最近最稳的骑法是什么
3. 哪些变化值得继续保持

## Non-Goals

- No training-plan domain.
- No user-defined goals.
- No annual analytics dashboard.
- No device-sync-based fitness model.
- No new write flow for ride history.

## Scope

This change package covers:

- one rolling-window `ride_growth_review`
- one read-only `GET /api/v1/rides/growth-review`
- simple deterministic milestones
- one growth panel integrated into `/rides`
- one next-focus CTA that routes back into the current planner flow

## Accepted Baseline

This package is layered on top of:

- `specs/changes/cycling-agent-package-2-ride-review-loop/spec.md`
- the current `/rides` recent-list and monthly-summary behavior

Package 2c must remain additive and must not replace package 2a or 2b surfaces.

## User Flows

### Flow A: Review recent growth on `/rides`

1. User opens `/rides`.
2. Frontend requests:
   - recent ride records
   - current month summary
   - growth review for a default rolling window such as 90 days
3. Page renders a growth panel below the monthly summary band.
4. User sees:
   - growth status
   - review headline and body
   - a small milestone list
   - one next-focus CTA

### Flow B: Switch the growth-review window

1. User switches from 90 days to 180 days.
2. Frontend requests a different `window_days`.
3. Backend returns a deterministic rolling-window aggregate.
4. Only the growth panel updates.

### Flow C: Return to planning from the next focus

1. User reads the growth review.
2. User clicks the next-focus CTA.
3. Frontend routes back to `/` with a seeded planner suggestion plus structured handoff context such as source window, growth status, streak, and suggested duration.
4. Planner remains the current main flow.

## Data Model

### `ride_growth_review`

Derived rolling-window object generated only from `ride_records` plus optional linked `ride_plans`.

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

Optional fields:

- `planned_count`
- `manual_count`
- `matched_plan_count`
- `top_start_region`
- `top_tag`
- `recent_vs_previous_ride_delta`
- `recent_vs_previous_distance_delta_km`

Rules:

1. `completed` and `shortened` count as rides that happened.
2. `cancelled` rides do not contribute to distance, duration, streaks, or milestones.
3. `period_end` is capped at today.
4. `best_weekly_streak` means the maximum consecutive calendar-week streak within the window.
5. `milestones` must stay structured and deterministic.
6. `next_focus` must stay planner-compatible and low-pressure.

### `growth_status`

Stable enum:

- `building`
- `steady`
- `expanding`
- `resetting`

Interpretation baseline:

- `building`: cadence exists but is still forming
- `steady`: rhythm is stable and maintainable
- `expanding`: recent range or consistency has clearly grown
- `resetting`: recent activity has dropped enough that the user is effectively re-starting

### `milestones`

Stable milestone keys:

- `first_completed_ride`
- `longest_distance`
- `longest_duration`
- `best_streak`
- `most_active_month`

## API Contract

### `GET /api/v1/rides/growth-review`

Query:

- `window_days=30|90|180`

Response:

- `ride_growth_review`

Error semantics:

- `422 invalid-window-days`
- `200` zeroed review when no rides exist in the requested window

## UI States

### `/rides` growth panel

Must cover:

- loading
- failure
- zeroed/empty review
- success

Rules:

- growth-panel failure must not block the monthly summary band
- growth-panel failure must not block the recent-ride list
- monthly summary and recent list remain independent existing surfaces

## Exceptions

- Window validation must reject unsupported values rather than silently clamping.
- Growth review must not use `ride_monthly_summary_events` as user-history input.
- Growth CTA must reuse current planner handoff style rather than introducing a new route.

## Tests

Required verification assets:

- service tests for:
  - zeroed review
  - stable growth
  - expanding review
  - resetting review
  - milestone extraction
- API tests for:
  - valid growth-review response
  - invalid `window_days`
  - zeroed review behavior
- frontend tests for:
  - growth-panel success
  - growth-panel failure independence
  - window switching
  - planner CTA handoff
- frontend build validation

## Observability

Minimum signals:

- count of growth-review requests
- split by `window_days`
- count of zeroed-review responses
- count of invalid-window requests
- count of growth CTA clicks if tracked

Optional payload tags:

- `growth_status`
- `next_focus.action_key`
- whether a milestone list was non-empty

## Open Questions

- Should `/rides` show both 90-day and 180-day quick switches in v1, or only one alternate window?

## Implementation Note

- Growth-review observability reuses `ride_monthly_summary_events` with extra event types and growth-specific fields such as `requested_window_days`, `growth_status`, `has_milestones`, and `is_zero_growth_review`.
