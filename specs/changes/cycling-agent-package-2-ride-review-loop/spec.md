# Cycling Agent Package 2 Ride Review Loop

## Meta

- Domain: `cycling-agent`
- Feature: `package-2-ride-review-loop`
- Source Draft:
  - `docs/superpowers/specs/2026-06-15-package-2a-post-ride-record-and-summary-design.md`
  - `docs/superpowers/specs/2026-06-15-package-2b-habit-monthly-summary-design.md`
- Status: proposed

## Goal

Extend the current ride-planning product with a real post-ride review loop so the product can:

1. save what actually happened after a ride
2. summarize one ride deterministically
3. review the current month without introducing a second history source
4. route the user back into the planner from post-ride feedback

## Non-Goals

- No training-plan or performance-coaching domain.
- No external fitness-device sync.
- No second write flow for ride history.
- No saved annual analytics dashboard.
- No user-defined habit goals.

## Scope

This change package covers:

- package 2a post-ride record creation
- package 2a per-ride summary generation
- package 2a recent-ride list and detail view
- package 2b month-scoped ride summary
- package 2b low-pressure habit feedback
- package 2b summary-to-planner handoff
- package 2b lightweight observability events

## Accepted Baseline

The accepted baseline remains the package 1 planning product documented in:

- `products/cycling-agent/docs/current-implementation-overview.md`
- `specs/current/`

This change is additive on top of the existing planning flow and must not replace it.

## User Flows

### Flow A: Save a ride after planning

1. User completes or shortens a ride from a saved plan result.
2. User opens the post-ride entry flow.
3. System saves one `ride_record`.
4. System returns the saved record plus a deterministic `ride_summary`.

### Flow B: Manually backfill a ride

1. User opens `/rides/new` without a source plan.
2. User enters the minimum manual fields.
3. System saves one `ride_record`.
4. User can review the record and its generated summary like any planned ride.

### Flow C: Review recent rides

1. User opens `/rides`.
2. Frontend requests recent ride records.
3. Page renders loading, error, empty, or success states.
4. Success state shows recent ride items with summary headline and detail links.

### Flow D: Review this month

1. User opens `/rides`.
2. Frontend also requests `GET /api/v1/rides/monthly-summary?month=YYYY-MM`.
3. Page renders a summary band above the recent-ride list.
4. Failure in the summary band must not block the recent-ride list.

### Flow E: Return to planning from monthly feedback

1. User reads the monthly `next_action`.
2. User clicks the CTA.
3. Frontend routes back to `/` with a seeded planner suggestion plus structured handoff context such as source month, habit status, streak, and suggested duration.
4. Planner remains the same current main flow.

## Data Model

### `ride_records`

Fact source for post-ride history.

Rules:

- `planned` and `manual` are the only entry modes.
- `completed`, `shortened`, and `cancelled` are the only completion statuses.
- `ride_date` must not be silently fabricated on write.
- future-dated `ride_date` must be rejected at the API boundary.

### `ride_summary`

Per-ride derived object generated from one `ride_record` plus optional linked `ride_plan`.

Rules:

- deterministic, rule-first generation
- no LLM dependency
- stable fields for completion, effort, recovery, next ride, and plan alignment

### `ride_monthly_summary`

Month-scoped derived object generated from `ride_records`.

Rules:

- `completed` and `shortened` count as rides that happened
- `cancelled` contributes to outcome distribution but not realized totals
- `weekly_streak` means consecutive calendar weeks ending at the requested month or current week
- current-month summary must ignore future-dated rows beyond the reference day
- `next_action` must remain planner-compatible

### `ride_monthly_summary_events`

Lightweight observability event stream for package 2b.

Event types:

- `summary_request`
- `invalid_month`
- `cta_click`

Rules:

- this table is observability only, never the user-history fact source
- backend should emit summary requests and invalid-month events
- frontend should emit CTA-click events when tracked

## API Contract

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

Returns recent ride list items with `summary_headline`.

### `GET /api/v1/rides/records/{ride_record_no}`

Returns one saved `ride_record` plus `ride_summary`.

### `GET /api/v1/rides/monthly-summary`

Query:

- `month=YYYY-MM`

Returns:

- `ride_monthly_summary`

Error semantics:

- `422 invalid-month-format`
- `200` zeroed summary when no ride records exist in the month

### `POST /api/v1/rides/monthly-summary-events`

Tracks frontend summary CTA clicks.

### `GET /api/v1/admin/ride-monthly-summary-events`

Returns recent observability events for package 2b.

## UI States

### `/rides`

Must cover:

- monthly-summary loading
- monthly-summary failure
- monthly-summary success
- recent-list loading
- recent-list failure
- recent-list empty
- recent-list success

Rule:

- summary-band failure must not block recent-list rendering

### `/rides/new`

Must support:

- source-plan-backed entry
- manual backfill
- validation error display

### `/rides/:rideRecordNo`

Must show:

- saved ride facts
- generated per-ride summary

## Exceptions

- Timestamp-shaped `ride_date` inputs should normalize to day precision.
- Regex-valid but invalid ISO months such as `0000-01` must still map to `422 invalid-month-format`.
- Weekly-streak logic must not truncate true streaks merely because recent recency heuristics use a 30-day slice.
- Repository writes must fail fast on missing `ride_date` instead of writing today’s date.

## Tests

Required verification assets:

- repository tests for month-range reads and same-day inclusivity
- service tests for per-ride summary rules
- service tests for monthly summary rules
- API tests for post-ride record creation/list/detail
- API tests for invalid month, future ride dates, and monthly summary event tracking
- frontend tests for:
  - recent-ride list success / empty / error
  - monthly summary band success / failure independence
  - planner seed handoff from the summary CTA
- frontend build validation

## Observability

Minimum signals:

- count of monthly summary requests
- split by requested month
- count of invalid-month requests
- count of empty-summary responses
- count of summary CTA clicks
- optional payload tags:
  - `habit_status`
  - `next_action_key`
  - `has_planned_rides`

## Open Questions

- Should package 2 observability also surface in an admin UI panel, or is the admin API enough for now?
- Should package 2a and 2b stay one combined change package through promotion, or split into separate archive entries after git is unblocked?
