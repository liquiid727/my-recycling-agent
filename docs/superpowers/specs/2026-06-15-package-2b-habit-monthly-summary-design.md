# Package 2B Habit And Monthly Summary Design

## Status

Draft for review.

## Workflow Note

This document is draft-only design material.

It is not yet the accepted implementation spec bundle.

Before coding package 2b, this design should be normalized into the repo's spec change chain.

## Scope

This design covers package 2b only:

- habit coach lite
- monthly ride summary
- consistency feedback across multiple rides
- one read-only monthly aggregate API
- one summary band integrated into the existing `/rides` page

This design explicitly does not include:

- ride-record creation or single-ride summary generation
- reminder push or habit notifications
- training load or power analysis
- device sync with Strava, Garmin, Apple Health, or bike computers
- login, identity merge, or multi-user ride history
- long-term yearly analytics dashboards

## Goal

Add a real cross-ride consistency layer to the current cycling-agent product so the app can answer:

- 最近有没有偷懒
- 本月骑得怎么样
- 下一次适合怎么接着骑

using saved `ride_records` rather than reinterpreting planning logs.

## Product Intent

The product is not a training platform.

Package 2b extends package 2a in the most direct way:

1. help the user go ride
2. record what actually happened
3. summarize one ride
4. reflect on riding rhythm across multiple rides
5. suggest the next low-pressure action that helps the user keep riding

This stays aligned with `docs/design/` where the product direction includes:

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
- `products/cycling-agent/docs/current-implementation-overview.md`

## Existing System Baseline

The current runnable system already has:

- `ride_records` as the fact layer for actual rides
- `ride_summary` as a per-ride derived response
- saved `ride_plans` by `request_no`
- ride record entry from a planned result
- manual ride backfill
- recent rides list at `/rides`
- ride record detail page at `/rides/:rideRecordNo`

The current system does not have:

- any aggregate ride summary across multiple rides
- any month-scoped or date-range ride query API
- any consistency or habit interpretation layer
- any next-step guidance derived from multiple ride records
- any dedicated monthly report surface

So package 2b should be built as an addition on top of the package 2a ride-history entry point, not as a separate product branch.

## Design Principles

1. `ride_records` are the only fact source for package 2b aggregation.
2. Package 2b is read-only in v1. No new write flow is introduced.
3. Extend the existing `/rides` page before creating a new standalone dashboard.
4. Keep interpretation rule-first and deterministic in v1.
5. Prefer low-pressure habit feedback over training-style performance coaching.
6. Do not require user-defined monthly goals in the first slice.

## Chosen Product Model

Package 2b introduces one derived aggregate object:

### `ride_monthly_summary`

Read-only response object generated from saved `ride_records` inside a requested month, optionally enriched by linked `ride_plans`.

The source of truth remains:

- `ride_records`
- optional `ride_plans` lookup for planned-vs-manual interpretation

No new table is required in v1.

## Domain Additions

### `ride_monthly_summary`

Required fields:

- `month`: `YYYY-MM`
- `period_start`
- `period_end`
- `ride_count`
- `ride_day_count`
- `completed_count`
- `shortened_count`
- `cancelled_count`
- `total_distance_km`
- `total_duration_hours`
- `planned_count`
- `manual_count`
- `last_ride_date`
- `days_since_last_ride`
- `weekly_streak`
- `habit_status`
- `next_action`
- `summary_headline`
- `summary_body`

Optional but expected fields:

- `top_start_region`
- `top_tag`
- `hard_effort_count`
- `tired_mood_count`
- `matched_plan_count`
- `month_to_date`
- `recent_30d_ride_count`

Rules:

1. Aggregation should treat `completed` and `shortened` as rides that actually happened.
2. `cancelled` records count toward outcome distribution but not distance or duration totals.
3. `ride_day_count` counts unique `ride_date` values among non-cancelled rides.
4. `total_distance_km` and `total_duration_hours` sum only non-null values from non-cancelled rides.
5. `planned_count` and `manual_count` are based on `entry_mode`.
6. `days_since_last_ride` uses the latest non-cancelled `ride_date`; if none exists, return `null`.
7. `weekly_streak` means consecutive calendar weeks, ending at the requested month or current week, that contain at least one non-cancelled ride.
8. `habit_status` must be a small stable vocabulary, not free-form prose.
9. `next_action` is a structured, user-facing recommendation derived by rule, not by LLM in v1.

### `habit_status`

Stable enum:

- `starting`
- `rebuilding`
- `steady`
- `overreaching`

Interpretation baseline:

- `starting`: very low recent ride count or no recent non-cancelled ride
- `rebuilding`: the user is riding again but cadence is not yet stable
- `steady`: the user shows consistent recent ride rhythm without clear overload signs
- `overreaching`: recent rides skew hard/tired enough that the next action should back off

### `next_action`

Structured object:

- `action_key`
- `title`
- `body`
- `suggested_scene`
- `suggested_entry`

Stable `action_key` values for v1:

- `schedule_easy_city_ride`
- `resume_with_short_ride`
- `maintain_weekly_rhythm`
- `take_recovery_window`

`suggested_scene` should map back to current planning capability:

- `city_ride`
- `weekend_trip`

`suggested_entry` is optional helper copy or query text for reopening the planner.

## User Flows

### Flow A: Review this month from the existing rides page

1. User opens `/rides`.
2. Frontend requests both:
   - recent ride records
   - monthly summary for the current month
3. Page renders a summary band above the recent-ride list.
4. User sees:
   - this month ride count
   - total distance and duration
   - last ride recency
   - current consistency status
   - one next step recommendation
5. User can still scroll straight into the existing recent-ride list.

### Flow B: Switch month and review prior rhythm

1. User opens `/rides`.
2. User switches from current month to the previous month.
3. Frontend requests a different `month=YYYY-MM`.
4. Backend returns the matching aggregate.
5. Frontend updates the summary band without changing the recent-ride list contract.

### Flow C: Jump back into planning from habit feedback

1. User reads `next_action`.
2. User clicks a CTA such as “按这个建议去规划”.
3. Frontend routes the user back to `/` with the suggestion text plus structured handoff context such as source month, habit status, streak, and suggested duration when available.
4. The existing planning chain handles the ride planning request.

## Aggregation Logic

Package 2b v1 should stay rule-first.

### Base record set

For a requested `month=YYYY-MM`:

1. read all `ride_records` with `ride_date` inside that month
2. separately read recent non-cancelled rides in the prior 30 days when needed for recency and status heuristics
3. optionally batch-load linked `ride_plans` for records with `source_request_no`

### Derived metrics

- `ride_count`: all records in the month
- `ride_day_count`: unique non-cancelled ride dates
- `completed_count`: monthly records with `completion_status=completed`
- `shortened_count`: monthly records with `completion_status=shortened`
- `cancelled_count`: monthly records with `completion_status=cancelled`
- `total_distance_km`: sum of non-cancelled `actual_distance_km`
- `total_duration_hours`: sum of non-cancelled `actual_duration_hours`
- `planned_count`: monthly records with `entry_mode=planned`
- `manual_count`: monthly records with `entry_mode=manual`
- `hard_effort_count`: non-cancelled rides with `effort_feeling=hard`
- `tired_mood_count`: non-cancelled rides with `mood_after=tired`
- `top_start_region`: most frequent non-empty `origin_region`
- `top_tag`: most frequent tag
- `matched_plan_count`: planned rides whose per-ride summary aligns as `matched-core-plan`

### Habit status rules

Suggested v1 thresholds:

1. `starting`
   - no non-cancelled ride in the requested month, or
   - `days_since_last_ride >= 14`
2. `rebuilding`
   - at least one non-cancelled ride in the month, but
   - low frequency such as `ride_day_count < 3`
3. `overreaching`
   - recent monthly rides exist, and
   - the last two non-cancelled rides both show `effort_feeling=hard` or `mood_after=tired`
4. `steady`
   - otherwise, if monthly riding cadence is active and not overloaded

These thresholds should remain explicit constants in code, not hidden in copy.

### Next action rules

1. If `days_since_last_ride >= 14`
   - `action_key = resume_with_short_ride`
   - guide the user back into a short easy city ride
2. If recent effort and mood indicate overload
   - `action_key = take_recovery_window`
   - suggest waiting or planning a recovery ride
3. If the user is active but below a stable cadence
   - `action_key = schedule_easy_city_ride`
   - suggest fitting in one short weekday ride
4. If the user already has a stable monthly rhythm
   - `action_key = maintain_weekly_rhythm`
   - suggest continuing the current cadence

## Backend Contract

### `GET /api/v1/rides/monthly-summary`

Query params:

- `month=YYYY-MM`

Response:

- `ride_monthly_summary`

Error semantics:

- `422 invalid-month-format`
  - when `month` is not `YYYY-MM`
- `200` with zeroed summary
  - when the month has no ride records

### Example response

```json
{
  "ride_monthly_summary": {
    "month": "2026-06",
    "period_start": "2026-06-01",
    "period_end": "2026-06-30",
    "ride_count": 4,
    "ride_day_count": 4,
    "completed_count": 3,
    "shortened_count": 1,
    "cancelled_count": 0,
    "total_distance_km": 112.4,
    "total_duration_hours": 7.1,
    "planned_count": 3,
    "manual_count": 1,
    "last_ride_date": "2026-06-14",
    "days_since_last_ride": 1,
    "weekly_streak": 3,
    "habit_status": "steady",
    "next_action": {
      "action_key": "maintain_weekly_rhythm",
      "title": "这周再补一趟轻松骑就能把节奏续上。",
      "body": "你最近的骑行频率比较稳，下一次继续安排一趟不追强度的城市骑就够了。",
      "suggested_scene": "city_ride",
      "suggested_entry": "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。"
    },
    "summary_headline": "这个月你已经把骑行节奏续起来了。",
    "summary_body": "本月累计 4 次骑行、112.4 km，最近一次距离现在 1 天，整体节奏稳定，没有明显过载信号。",
    "top_start_region": "滨江",
    "top_tag": "晚骑",
    "hard_effort_count": 1,
    "tired_mood_count": 1,
    "matched_plan_count": 2,
    "month_to_date": true,
    "recent_30d_ride_count": 5
  }
}
```

## Frontend Changes

Package 2b should reuse the current `/rides` route.

### Page behavior

Add a summary band above the existing recent-ride list showing:

- selected month
- monthly totals
- ride outcome split
- consistency status
- next action
- CTA back to planner

Keep the current recent-ride list below it.

### Loading and failure states

The summary band must explicitly cover:

- loading state while monthly summary is fetching
- empty state when the month has no rides
- failure state when monthly summary fetch fails

Failure in the summary band must not block the existing recent-ride list from rendering.

### Interaction

The page should support:

- current month by default
- at least one prior-month switch, or a simple previous/next month control
- a CTA that reopens the planner from the next action guidance

## Backend Impact

Expected new backend areas:

- new monthly summary response schemas
- one aggregation service over `ride_records`
- repository read helpers for month/date-range querying
- new ride monthly summary API route under the existing `rides` router

The existing ride record create/list/detail endpoints should stay unchanged.

## Observability

Package 2b should emit enough evidence to verify actual use and common failure modes.

Minimum signals:

- count of monthly summary requests
- split by month requested
- count of empty-summary responses
- count of invalid-month requests
- count of summary CTA clicks on the frontend when tracked

If request-level audit is kept lightweight, also capture:

- whether the summary contained any planned rides
- whether `habit_status` was `starting`, `rebuilding`, `steady`, or `overreaching`
- which `next_action.action_key` was returned

## Out Of Scope

Package 2b does not include:

- reminder scheduling
- streak goals configured by the user
- chat-history-based habit coaching
- saved monthly snapshots
- fatigue models across power, heart rate, or elevation load
- social comparison or rankings
- coach-style intervention flows

## Files Expected To Change

Primary backend files:

- `products/cycling-agent/backend/app/schemas/ride_plan.py`
- `products/cycling-agent/backend/app/api/routes/ride_record.py`
- `products/cycling-agent/backend/app/repositories/ride_record_repository.py`
- new `products/cycling-agent/backend/app/services/ride_monthly_summary_service.py`
- backend tests for the new monthly summary behavior

Primary frontend files:

- `products/cycling-agent/frontend/src/features/planner/api.ts`
- `products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx`
- `products/cycling-agent/frontend/src/app/router.tsx` only if route/query behavior needs extension
- frontend tests for the summary band and month switching

## Acceptance Criteria

Package 2b is successful when:

1. the backend can return a deterministic monthly aggregate derived from `ride_records`
2. the aggregate includes consistency feedback and one structured next action
3. the `/rides` page shows the monthly summary without replacing the existing recent-ride list
4. summary loading or failure does not block recent-ride rendering
5. the next action can route the user back into the current planner flow
6. package 2b does not introduce a second fact source for ride history
