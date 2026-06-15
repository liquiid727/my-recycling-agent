# Package 2A Post-Ride Record And Summary Design

## Status

Draft for review.

## Workflow Note

This document is draft-only design material.

It is not yet the accepted implementation spec bundle.

Before coding package 2a, this design should be normalized into the repo's spec change chain.

## Scope

This design covers package 2a only:

- post-ride record creation
- post-ride summary generation
- recent ride list
- single ride detail review
- planner-to-post-ride entry bridge
- manual backfill for rides without a saved plan

This design explicitly does not include:

- monthly or rolling-window aggregate review
- reminder push or habit notifications
- fitness-device sync
- training load or performance analytics
- social feed or community behavior

## Goal

Add the first real post-ride loop to the current cycling-agent product so the app can answer:

- 今天这次到底骑没骑成
- 这次骑完感觉怎么样
- 下次要不要继续按类似方式出门

using one saved ride fact record plus one deterministic summary, rather than only keeping planning output.

## Product Intent

The product is not a training platform.

Package 2a is the first extension after ride planning:

1. help the user decide and plan
2. save what actually happened
3. summarize one finished or unfinished ride
4. make later cross-ride review possible

This stays aligned with `docs/design/` where the product direction includes:

- “帮助用户骑出去”
- “总结今天的骑行”
- “记录我的骑行成长”

## Source Material

- `docs/design/Over-Cycling-Product-Vision-v0.1.md`
- `docs/design/OVER-CYCLING-PRD.md`
- `docs/design/产品设计和定位.md`
- `docs/design/CIM.md`
- `docs/design/todo.md`
- `products/cycling-agent/docs/current-implementation-overview.md`

## Existing System Baseline

The current runnable system already has:

- saved `ride_plans` keyed by `request_no`
- result pages for city rides and weekend recommendations
- normalized decision / plan / explanation output
- route detail pages and persistent planner history

The current system does not have:

- any saved post-ride fact layer
- any way to tell whether a planned ride really happened
- any single-ride deterministic review object
- any recent-ride history page

So package 2a should be built as an additive fact layer on top of the existing planner, not as a second planning product.

## Design Principles

1. `ride_records` are the only fact source for what actually happened.
2. Package 2a must support both plan-backed entry and manual backfill.
3. The first slice should stay deterministic and rule-first.
4. The post-ride entry path should reuse the current planner/result flow instead of creating a separate app section first.
5. The saved ride summary should be structured and reviewable, not free-form long text.

## Chosen Product Model

Package 2a introduces two new objects:

### `ride_record`

One saved fact record describing what actually happened on a ride.

### `ride_summary`

One deterministic derived object built from a saved `ride_record` plus optional linked `ride_plan`.

`ride_record` is the durable user-history fact source.

`ride_summary` is a derived read model and should not become a second write source.

## Domain Additions

### `ride_record`

Required fields:

- `ride_record_no`
- `entry_mode`
- `ride_date`
- `completion_status`
- `effort_feeling`
- `mood_after`

Optional but expected fields:

- `source_request_no`
- `intent`
- `plan_kind`
- `route_code`
- `route_title`
- `destination_name`
- `start_point`
- `origin_region`
- `actual_duration_hours`
- `actual_distance_km`
- `notes`
- `tags`

Rules:

1. `entry_mode` is `planned` or `manual`.
2. `completion_status` is `completed`, `shortened`, or `cancelled`.
3. `ride_date` must be provided explicitly and must not be silently fabricated on write.
4. Future-dated `ride_date` should be rejected at the API boundary.
5. Manual entry must require enough naming context to identify the ride, such as `route_title` or `destination_name`.

### `ride_summary`

Required fields:

- `headline`
- `summary`
- `completion_assessment`
- `effort_assessment`
- `recovery_advice`
- `next_ride_prompt`

Optional but expected fields:

- `plan_alignment`
- `confidence_notes`

Rules:

1. `ride_summary` must be deterministic and rule-first in v1.
2. It may read a linked `ride_plan` when `source_request_no` exists.
3. It must explain completed, shortened, and cancelled rides differently.
4. It must stay low-pressure and keep the product oriented around going out again.

## User Flows

### Flow A: Save a completed or shortened ride from a saved plan

1. User finishes reading a saved planning result.
2. User clicks `记录这次骑行`.
3. Frontend opens `/rides/new?sourceRequestNo=...`.
4. User fills in actual completion state and body feedback.
5. System saves one `ride_record`.
6. System returns the saved `ride_record` plus `ride_summary`.
7. Frontend routes to `/rides/:rideRecordNo`.

### Flow B: Manually backfill a ride without a source plan

1. User opens `/rides/new`.
2. User enters the minimum route or destination context.
3. User fills in completion state and actual ride facts.
4. System saves one `ride_record`.
5. Frontend routes to the same detail page as plan-backed records.

### Flow C: Review one saved ride

1. User opens `/rides/:rideRecordNo`.
2. System returns the saved facts and one generated summary.
3. User can read what happened, how the ride landed, and the low-pressure next suggestion.

### Flow D: Review recent rides

1. User opens `/rides`.
2. Frontend requests recent saved records.
3. Page shows loading, error, empty, or success.
4. Success state shows short summary headlines and links into ride details.

## Backend Contract

### `POST /api/v1/rides/records`

Returns:

- `ride_record`
- `ride_summary`

Error semantics:

- `422 ride-record-manual-title-missing`
- `422 ride-record-source-request-missing`
- `404 ride-record-source-plan-not-found`
- `422 ride-record-completed-metrics-missing`
- `422 ride-record-date-in-future`

### `GET /api/v1/rides/records`

Returns recent ride-list items with one `summary_headline`.

### `GET /api/v1/rides/records/{ride_record_no}`

Returns one saved `ride_record` plus one `ride_summary`.

## Frontend Surface

Package 2a should add:

- a planner result CTA into the post-ride flow
- one post-ride entry page at `/rides/new`
- one recent-rides page at `/rides`
- one ride detail page at `/rides/:rideRecordNo`

The UI must explicitly cover:

- loading source-plan state
- create validation errors
- recent-list empty state
- recent-list failure state
- detail-page failure state

## Out Of Scope

Package 2a does not include:

- cross-ride consistency analysis
- monthly reports
- rolling growth review
- reminders or habit coaching
- observability events beyond ordinary API/test evidence

## Acceptance Criteria

Package 2a is successful when:

1. the user can save one real ride after planning
2. the user can also manually backfill a ride without a source plan
3. each saved ride returns one deterministic `ride_summary`
4. the app exposes recent rides and single-ride detail review
5. the post-ride loop stays additive and does not replace the existing planner
