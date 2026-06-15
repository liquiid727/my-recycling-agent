# Package 2B Habit And Monthly Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a rule-first monthly ride summary and habit-feedback layer on top of package 2a, exposed on the existing `/rides` page and backed only by `ride_records`.

**Architecture:** Keep package 2b additive and read-only. Extend the current `rides` router with one monthly-summary endpoint, add repository range-query helpers plus a dedicated aggregation service, then layer a summary band onto the existing `/rides` page without breaking the recent-rides list. Route the “next action” CTA back into the current planner flow instead of introducing a new write path or a second history source.

**Tech Stack:** FastAPI, Pydantic, SQLite/PostgreSQL compatibility layer, React, React Router, TypeScript, Vitest, Testing Library, pytest.

---

## File Structure

### Backend

- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
  - add monthly-summary response models and stable enums
- Modify: `products/cycling-agent/backend/app/repositories/ride_record_repository.py`
  - add month/date-range query helpers and recent non-cancelled lookup helpers
- Modify: `products/cycling-agent/backend/app/api/routes/ride_record.py`
  - add `GET /api/v1/rides/monthly-summary`
- Create: `products/cycling-agent/backend/app/services/ride_monthly_summary_service.py`
  - compute deterministic monthly aggregates and next-action guidance

### Frontend

- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
  - add monthly-summary types and fetch helper
- Modify: `products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx`
  - add month state, summary fetch, summary band, and planner CTA
- Modify: `products/cycling-agent/frontend/src/pages/HomePage.tsx`
  - accept optional query-param seed for planner suggestion handoff

### Tests

- Create: `products/cycling-agent/backend/tests/test_ride_monthly_summary_service.py`
- Create: `products/cycling-agent/backend/tests/test_ride_monthly_summary_api.py`
- Modify: `products/cycling-agent/backend/tests/test_ride_record_repository.py`
- Modify: `products/cycling-agent/frontend/src/tests/ride-record-list-page.test.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/home-page.test.tsx`

### Docs

- Modify: `products/cycling-agent/docs/current-implementation-overview.md`
- Modify: `products/cycling-agent/docs/manual-test-script.md`

---

## Task 1: Add Monthly Summary Schemas And Ride-Record Range Queries

**Files:**
- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
- Modify: `products/cycling-agent/backend/app/repositories/ride_record_repository.py`
- Modify: `products/cycling-agent/backend/tests/test_ride_record_repository.py`

- [ ] **Step 1: Write the failing repository tests for month range queries**

```python
def test_list_ride_records_by_date_range_returns_only_records_inside_month(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)
    repository = _load_repository_module()

    repository.save_ride_record(
        database_url,
        {
            "ride_record_no": "RR-202606-001",
            "entry_mode": "manual",
            "ride_date": "2026-06-03",
            "completion_status": "completed",
            "effort_feeling": "steady",
            "mood_after": "refreshed",
            "tags": [],
        },
    )
    repository.save_ride_record(
        database_url,
        {
            "ride_record_no": "RR-202605-001",
            "entry_mode": "manual",
            "ride_date": "2026-05-28",
            "completion_status": "completed",
            "effort_feeling": "steady",
            "mood_after": "refreshed",
            "tags": [],
        },
    )

    records = repository.list_ride_records_by_date_range(database_url, "2026-06-01", "2026-06-30")

    assert [record["ride_record_no"] for record in records] == ["RR-202606-001"]


def test_list_recent_non_cancelled_ride_records_skips_cancelled_records(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)
    repository = _load_repository_module()

    repository.save_ride_record(
        database_url,
        {
            "ride_record_no": "RR-CANCELLED",
            "entry_mode": "manual",
            "ride_date": "2026-06-10",
            "completion_status": "cancelled",
            "effort_feeling": "easy",
            "mood_after": "normal",
            "tags": [],
        },
    )
    repository.save_ride_record(
        database_url,
        {
            "ride_record_no": "RR-DONE",
            "entry_mode": "manual",
            "ride_date": "2026-06-08",
            "completion_status": "completed",
            "effort_feeling": "steady",
            "mood_after": "refreshed",
            "tags": [],
        },
    )

    records = repository.list_recent_non_cancelled_ride_records(
        database_url,
        before_date="2026-06-15",
        lookback_days=30,
        limit=5,
    )

    assert [record["ride_record_no"] for record in records] == ["RR-DONE"]
```

- [ ] **Step 2: Run the repository test to verify it fails**

Run:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
. products/cycling-agent/backend/.venv/bin/activate
pytest products/cycling-agent/backend/tests/test_ride_record_repository.py -v
```

Expected: FAIL with missing `list_ride_records_by_date_range` and `list_recent_non_cancelled_ride_records`.

- [ ] **Step 3: Add the monthly-summary schemas in `ride_plan.py`**

```python
class RideMonthlySummaryActionSchema(BaseModel):
    action_key: str = Field(
        pattern="^(schedule_easy_city_ride|resume_with_short_ride|maintain_weekly_rhythm|take_recovery_window)$"
    )
    title: str
    body: str
    suggested_scene: str = Field(pattern="^(city_ride|weekend_trip)$")
    suggested_entry: str | None = None


class RideMonthlySummaryPayloadSchema(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    period_start: date
    period_end: date
    ride_count: int = Field(ge=0)
    ride_day_count: int = Field(ge=0)
    completed_count: int = Field(ge=0)
    shortened_count: int = Field(ge=0)
    cancelled_count: int = Field(ge=0)
    total_distance_km: float = Field(ge=0)
    total_duration_hours: float = Field(ge=0)
    planned_count: int = Field(ge=0)
    manual_count: int = Field(ge=0)
    last_ride_date: date | None = None
    days_since_last_ride: int | None = Field(default=None, ge=0)
    weekly_streak: int = Field(ge=0)
    habit_status: str = Field(pattern="^(starting|rebuilding|steady|overreaching)$")
    next_action: RideMonthlySummaryActionSchema
    summary_headline: str
    summary_body: str
    top_start_region: str | None = None
    top_tag: str | None = None
    hard_effort_count: int = Field(default=0, ge=0)
    tired_mood_count: int = Field(default=0, ge=0)
    matched_plan_count: int = Field(default=0, ge=0)
    month_to_date: bool = False
    recent_30d_ride_count: int = Field(default=0, ge=0)


class RideMonthlySummaryResponseSchema(BaseModel):
    ride_monthly_summary: RideMonthlySummaryPayloadSchema
```

- [ ] **Step 4: Add repository range helpers in `ride_record_repository.py`**

```python
def list_ride_records_by_date_range(database_url: str, start_date: str, end_date: str) -> list[dict[str, Any]]:
    with connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT ride_record_no, entry_mode, source_request_no, ride_date, intent, plan_kind, route_code, route_title,
                   destination_name, start_point, origin_region, completion_status, actual_duration_hours,
                   actual_distance_km, effort_feeling, mood_after, notes, tags_json, payload_json, created_at
            FROM ride_records
            WHERE ride_date >= ? AND ride_date <= ?
            ORDER BY ride_date DESC, ride_record_no DESC
            """,
            (start_date, end_date),
        ).fetchall()
    return [_hydrate_ride_record(row) for row in rows]


def list_recent_non_cancelled_ride_records(
    database_url: str,
    *,
    before_date: str,
    lookback_days: int,
    limit: int,
) -> list[dict[str, Any]]:
    window_start = (date.fromisoformat(before_date) - timedelta(days=lookback_days)).isoformat()
    with connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT ride_record_no, entry_mode, source_request_no, ride_date, intent, plan_kind, route_code, route_title,
                   destination_name, start_point, origin_region, completion_status, actual_duration_hours,
                   actual_distance_km, effort_feeling, mood_after, notes, tags_json, payload_json, created_at
            FROM ride_records
            WHERE ride_date < ?
              AND ride_date >= ?
              AND completion_status != 'cancelled'
            ORDER BY ride_date DESC, ride_record_no DESC
            LIMIT ?
            """,
            (before_date, window_start, limit),
        ).fetchall()
    return [_hydrate_ride_record(row) for row in rows]
```

- [ ] **Step 5: Run repository tests to verify they pass**

Run:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
. products/cycling-agent/backend/.venv/bin/activate
pytest products/cycling-agent/backend/tests/test_ride_record_repository.py -v
```

Expected: PASS, including the two new range-query tests.

- [ ] **Step 6: Commit**

```bash
git add \
  products/cycling-agent/backend/app/schemas/ride_plan.py \
  products/cycling-agent/backend/app/repositories/ride_record_repository.py \
  products/cycling-agent/backend/tests/test_ride_record_repository.py
git commit -m "feat: add monthly ride record query helpers"
```

---

## Task 2: Add Rule-First Monthly Summary Service And API

**Files:**
- Create: `products/cycling-agent/backend/app/services/ride_monthly_summary_service.py`
- Modify: `products/cycling-agent/backend/app/api/routes/ride_record.py`
- Create: `products/cycling-agent/backend/tests/test_ride_monthly_summary_service.py`
- Create: `products/cycling-agent/backend/tests/test_ride_monthly_summary_api.py`

- [ ] **Step 1: Write the failing service test for a steady month**

```python
def test_build_ride_monthly_summary_marks_active_month_as_steady() -> None:
    summary = build_ride_monthly_summary(
        month="2026-06",
        monthly_records=[
            {
                "ride_record_no": "RR-1",
                "entry_mode": "planned",
                "ride_date": "2026-06-03",
                "completion_status": "completed",
                "actual_duration_hours": 2.0,
                "actual_distance_km": 35.0,
                "effort_feeling": "steady",
                "mood_after": "refreshed",
                "origin_region": "滨江",
                "tags": ["晚骑"],
                "source_request_no": "RQ-1",
            },
            {
                "ride_record_no": "RR-2",
                "entry_mode": "manual",
                "ride_date": "2026-06-10",
                "completion_status": "shortened",
                "actual_duration_hours": 1.5,
                "actual_distance_km": 22.0,
                "effort_feeling": "steady",
                "mood_after": "normal",
                "origin_region": "滨江",
                "tags": ["晚骑"],
                "source_request_no": None,
            },
            {
                "ride_record_no": "RR-3",
                "entry_mode": "planned",
                "ride_date": "2026-06-14",
                "completion_status": "completed",
                "actual_duration_hours": 2.2,
                "actual_distance_km": 40.4,
                "effort_feeling": "steady",
                "mood_after": "refreshed",
                "origin_region": "西湖",
                "tags": ["周末"],
                "source_request_no": "RQ-3",
            },
        ],
        recent_non_cancelled_records=[
            {"ride_record_no": "RR-3", "ride_date": "2026-06-14", "completion_status": "completed", "effort_feeling": "steady", "mood_after": "refreshed"},
            {"ride_record_no": "RR-2", "ride_date": "2026-06-10", "completion_status": "shortened", "effort_feeling": "steady", "mood_after": "normal"},
        ],
        source_plans_by_request_no={
            "RQ-1": {"recommended_plan": {"estimated_duration_hours": 2.0}},
            "RQ-3": {"recommended_plan": {"estimated_duration_hours": 2.0}},
        },
        today="2026-06-15",
    )

    validated = RideMonthlySummaryPayloadSchema.model_validate(summary)
    assert validated.ride_count == 3
    assert validated.ride_day_count == 3
    assert validated.total_distance_km == 97.4
    assert validated.habit_status == "steady"
    assert validated.planned_count == 2
    assert validated.manual_count == 1
    assert validated.top_start_region == "滨江"
    assert validated.next_action.action_key == "maintain_weekly_rhythm"
```

- [ ] **Step 2: Write the failing API tests**

```python
def test_get_monthly_summary_returns_aggregate_payload(tmp_path, client) -> None:
    _seed_ride_record(client, ride_record_no="RR-1", ride_date="2026-06-03", completion_status="completed")
    _seed_ride_record(client, ride_record_no="RR-2", ride_date="2026-06-14", completion_status="shortened")

    response = client.get("/api/v1/rides/monthly-summary?month=2026-06")

    assert response.status_code == 200
    body = response.json()["ride_monthly_summary"]
    assert body["month"] == "2026-06"
    assert body["ride_count"] == 2
    assert body["next_action"]["action_key"]


def test_get_monthly_summary_rejects_invalid_month(client) -> None:
    response = client.get("/api/v1/rides/monthly-summary?month=2026-6")

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid-month-format"


def _seed_ride_record(client, *, ride_record_no: str, ride_date: str, completion_status: str) -> None:
    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": ride_date,
            "route_title": ride_record_no,
            "completion_status": completion_status,
            "actual_duration_hours": 1.5 if completion_status != "cancelled" else None,
            "actual_distance_km": 24 if completion_status != "cancelled" else None,
            "effort_feeling": "steady",
            "mood_after": "refreshed",
            "tags": [],
        },
    )
    assert response.status_code == 200
```

- [ ] **Step 3: Run service and API tests to verify they fail**

Run:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
. products/cycling-agent/backend/.venv/bin/activate
pytest \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_service.py \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_api.py -v
```

Expected: FAIL with missing service module and missing route behavior.

- [ ] **Step 4: Implement the rule-first monthly summary service**

```python
# products/cycling-agent/backend/app/services/ride_monthly_summary_service.py
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from app.services.ride_summary_service import build_ride_summary

STARTING_GAP_DAYS = 14
REBUILDING_RIDE_DAY_THRESHOLD = 3


def build_ride_monthly_summary(
    *,
    month: str,
    monthly_records: list[dict[str, Any]],
    recent_non_cancelled_records: list[dict[str, Any]],
    source_plans_by_request_no: dict[str, dict[str, Any]],
    today: str | None = None,
) -> dict[str, Any]:
    current_day = _parse_date(today) if today else date.today()
    period_start = date.fromisoformat(f"{month}-01")
    period_end = _month_end(period_start)
    non_cancelled = [record for record in monthly_records if record.get("completion_status") != "cancelled"]
    completed = [record for record in monthly_records if record.get("completion_status") == "completed"]
    shortened = [record for record in monthly_records if record.get("completion_status") == "shortened"]
    cancelled = [record for record in monthly_records if record.get("completion_status") == "cancelled"]
    last_ride_date = _latest_ride_date(non_cancelled)
    days_since_last_ride = None if last_ride_date is None else (current_day - last_ride_date).days
    hard_effort_count = sum(1 for record in non_cancelled if record.get("effort_feeling") == "hard")
    tired_mood_count = sum(1 for record in non_cancelled if record.get("mood_after") == "tired")
    matched_plan_count = _matched_plan_count(non_cancelled, source_plans_by_request_no)
    habit_status = _habit_status(
        ride_day_count=len({record["ride_date"] for record in non_cancelled}),
        days_since_last_ride=days_since_last_ride,
        recent_non_cancelled_records=recent_non_cancelled_records,
    )
    next_action = _next_action(habit_status)
    return {
        "month": month,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "ride_count": len(monthly_records),
        "ride_day_count": len({record["ride_date"] for record in non_cancelled}),
        "completed_count": len(completed),
        "shortened_count": len(shortened),
        "cancelled_count": len(cancelled),
        "total_distance_km": round(sum(float(record.get("actual_distance_km") or 0) for record in non_cancelled), 1),
        "total_duration_hours": round(sum(float(record.get("actual_duration_hours") or 0) for record in non_cancelled), 1),
        "planned_count": sum(1 for record in monthly_records if record.get("entry_mode") == "planned"),
        "manual_count": sum(1 for record in monthly_records if record.get("entry_mode") == "manual"),
        "last_ride_date": None if last_ride_date is None else last_ride_date.isoformat(),
        "days_since_last_ride": days_since_last_ride,
        "weekly_streak": _weekly_streak(non_cancelled, current_day),
        "habit_status": habit_status,
        "next_action": next_action,
        "summary_headline": _summary_headline(habit_status, len(non_cancelled)),
        "summary_body": _summary_body(len(monthly_records), days_since_last_ride, habit_status),
        "top_start_region": _counter_winner(record.get("origin_region") for record in non_cancelled),
        "top_tag": _counter_winner(tag for record in non_cancelled for tag in record.get("tags", [])),
        "hard_effort_count": hard_effort_count,
        "tired_mood_count": tired_mood_count,
        "matched_plan_count": matched_plan_count,
        "month_to_date": current_day >= period_start and current_day <= period_end,
        "recent_30d_ride_count": len(recent_non_cancelled_records),
    }


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _month_end(period_start: date) -> date:
    next_month = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def _latest_ride_date(records: list[dict[str, Any]]) -> date | None:
    if not records:
        return None
    return max(_parse_date(str(record["ride_date"])) for record in records)


def _matched_plan_count(
    records: list[dict[str, Any]],
    source_plans_by_request_no: dict[str, dict[str, Any]],
) -> int:
    matched = 0
    for record in records:
        request_no = record.get("source_request_no")
        if not request_no:
            continue
        source_plan = source_plans_by_request_no.get(str(request_no))
        if not source_plan:
            continue
        summary = build_ride_summary(record, source_plan=source_plan)
        if summary.get("plan_alignment") == "matched-core-plan":
            matched += 1
    return matched


def _habit_status(
    *,
    ride_day_count: int,
    days_since_last_ride: int | None,
    recent_non_cancelled_records: list[dict[str, Any]],
) -> str:
    if days_since_last_ride is None or days_since_last_ride >= STARTING_GAP_DAYS:
        return "starting"
    last_two = recent_non_cancelled_records[:2]
    if len(last_two) == 2 and all(
        record.get("effort_feeling") == "hard" or record.get("mood_after") == "tired"
        for record in last_two
    ):
        return "overreaching"
    if ride_day_count < REBUILDING_RIDE_DAY_THRESHOLD:
        return "rebuilding"
    return "steady"


def _next_action(habit_status: str) -> dict[str, Any]:
    mapping = {
        "starting": {
            "action_key": "resume_with_short_ride",
            "title": "先把下一次出门门槛降下来。",
            "body": "先安排一次短而轻松的城市骑，把节奏重新接上。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。",
        },
        "rebuilding": {
            "action_key": "schedule_easy_city_ride",
            "title": "这周再补一趟轻松骑会更稳。",
            "body": "你已经在恢复节奏了，再补一次低压力短骑最合适。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周再安排一次 2 小时内、不追强度的轻松骑。",
        },
        "steady": {
            "action_key": "maintain_weekly_rhythm",
            "title": "这周再补一趟轻松骑就能把节奏续上。",
            "body": "你最近的骑行频率比较稳，下一次继续安排一趟不追强度的城市骑就够了。",
            "suggested_scene": "city_ride",
            "suggested_entry": "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。",
        },
        "overreaching": {
            "action_key": "take_recovery_window",
            "title": "先把恢复放在前面。",
            "body": "最近两次骑行的体感偏顶，下一次更适合恢复骑或直接休息。",
            "suggested_scene": "city_ride",
            "suggested_entry": "明天不追强度，只安排一次轻松恢复骑，或者直接休息。",
        },
    }
    return mapping[habit_status]


def _summary_headline(habit_status: str, non_cancelled_count: int) -> str:
    if non_cancelled_count == 0:
        return "这个月还没把骑行重新接起来。"
    return {
        "starting": "现在最重要的是把下一次轻松出门接上。",
        "rebuilding": "你已经在把骑行节奏慢慢找回来了。",
        "steady": "这个月你已经把骑行节奏续起来了。",
        "overreaching": "这个月有输出，但恢复要跟上。",
    }[habit_status]


def _summary_body(ride_count: int, days_since_last_ride: int | None, habit_status: str) -> str:
    if ride_count == 0:
        return "这个月还没有实际骑行记录，下一次先安排一趟容易出门的短骑就够了。"
    recency = "暂无最近骑行日期" if days_since_last_ride is None else f"最近一次距离现在 {days_since_last_ride} 天"
    return {
        "starting": f"本月已有 {ride_count} 条记录，但当前节奏还不稳定，{recency}。",
        "rebuilding": f"本月已有 {ride_count} 条记录，说明你已经在恢复骑行习惯，{recency}。",
        "steady": f"本月已有 {ride_count} 条记录，整体节奏比较稳定，{recency}。",
        "overreaching": f"本月已有 {ride_count} 条记录，不过最近输出偏顶，{recency}。",
    }[habit_status]


def _counter_winner(values: Any) -> str | None:
    counter = Counter(str(value) for value in values if value)
    return counter.most_common(1)[0][0] if counter else None


def _weekly_streak(records: list[dict[str, Any]], current_day: date) -> int:
    weeks = {(_parse_date(str(record["ride_date"]))).isocalendar()[:2] for record in records}
    streak = 0
    cursor = current_day
    while True:
        year_week = cursor.isocalendar()[:2]
        if year_week not in weeks:
            return streak
        streak += 1
        cursor -= timedelta(days=7)
```

- [ ] **Step 5: Add the API route to `ride_record.py`**

```python
@router.get("/monthly-summary", response_model=RideMonthlySummaryResponseSchema)
async def get_ride_monthly_summary(month: str, request: Request) -> RideMonthlySummaryResponseSchema:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise HTTPException(status_code=422, detail="invalid-month-format")

    database_url = _require_database_url(request)
    period_start, period_end = _month_bounds(month)
    monthly_records = list_ride_records_by_date_range(database_url, period_start.isoformat(), period_end.isoformat())
    recent_non_cancelled_records = list_recent_non_cancelled_ride_records(
        database_url,
        before_date=min(date.today(), period_end + timedelta(days=1)).isoformat(),
        lookback_days=30,
        limit=30,
    )
    source_plans = get_ride_plans(
        database_url,
        [record["source_request_no"] for record in monthly_records if record.get("source_request_no")],
    )
    summary = build_ride_monthly_summary(
        month=month,
        monthly_records=monthly_records,
        recent_non_cancelled_records=recent_non_cancelled_records,
        source_plans_by_request_no=source_plans,
    )
    return RideMonthlySummaryResponseSchema(ride_monthly_summary=summary)
```

- [ ] **Step 6: Run the targeted backend tests to verify they pass**

Run:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
. products/cycling-agent/backend/.venv/bin/activate
pytest \
  products/cycling-agent/backend/tests/test_ride_record_repository.py \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_service.py \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_api.py -v
```

Expected: PASS for repository, service, and API coverage.

- [ ] **Step 7: Commit**

```bash
git add \
  products/cycling-agent/backend/app/services/ride_monthly_summary_service.py \
  products/cycling-agent/backend/app/api/routes/ride_record.py \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_service.py \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_api.py
git commit -m "feat: add monthly ride summary api"
```

---

## Task 3: Add `/rides` Summary Band And Planner Re-Entry

**Files:**
- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
- Modify: `products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx`
- Modify: `products/cycling-agent/frontend/src/pages/HomePage.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/ride-record-list-page.test.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/home-page.test.tsx`

- [ ] **Step 1: Write the failing `/rides` page test for summary band and list independence**

```tsx
test("renders monthly summary band above recent rides and keeps list visible", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/v1/rides/monthly-summary?month=2026-06") {
        return {
          ok: true,
          json: async () => ({
            ride_monthly_summary: {
              month: "2026-06",
              period_start: "2026-06-01",
              period_end: "2026-06-30",
              ride_count: 4,
              ride_day_count: 4,
              completed_count: 3,
              shortened_count: 1,
              cancelled_count: 0,
              total_distance_km: 112.4,
              total_duration_hours: 7.1,
              planned_count: 3,
              manual_count: 1,
              last_ride_date: "2026-06-14",
              days_since_last_ride: 1,
              weekly_streak: 3,
              habit_status: "steady",
              next_action: {
                action_key: "maintain_weekly_rhythm",
                title: "这周再补一趟轻松骑就能把节奏续上。",
                body: "你最近的骑行频率比较稳。",
                suggested_scene: "city_ride",
                suggested_entry: "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。"
              },
              summary_headline: "这个月你已经把骑行节奏续起来了。",
              summary_body: "本月累计 4 次骑行。",
              top_start_region: "滨江",
              top_tag: "晚骑",
              hard_effort_count: 1,
              tired_mood_count: 1,
              matched_plan_count: 2,
              month_to_date: true,
              recent_30d_ride_count: 5
            }
          }),
        };
      }
      if (url === "/api/v1/rides/records?limit=12") {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                ride_record_no: "RR-TEST0001",
                ride_date: "2026-06-15",
                route_title: "滨江-钱塘江休闲往返线",
                destination_name: "钱塘江南岸",
                completion_status: "completed",
                summary_headline: "滨江-钱塘江休闲往返线这次完成得很稳。"
              }
            ]
          })
        };
      }
      throw new Error(`unexpected fetch ${url}`);
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides?month=2026-06"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("这个月你已经把骑行节奏续起来了。")).toBeInTheDocument();
  expect(screen.getByText("112.4 km")).toBeInTheDocument();
  expect(screen.getByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "按这个建议去规划" })).toHaveAttribute(
    "href",
    "/?intent=ride_plan&planning_scene=city_ride&query=%E8%BF%99%E5%91%A8%E6%89%BE%E4%B8%AA%E5%82%8D%E6%99%9A%EF%BC%8C%E5%AE%89%E6%8E%92%E4%B8%80%E6%AC%A1%201.5%20%E5%88%B0%202%20%E5%B0%8F%E6%97%B6%E7%9A%84%E8%BD%BB%E6%9D%BE%E9%AA%91%E3%80%82",
  );
});


test("shows summary error without blocking recent ride list", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/v1/rides/monthly-summary?month=2026-06") {
        return { ok: false, status: 503 };
      }
      if (url === "/api/v1/rides/records?limit=12") {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                ride_record_no: "RR-TEST0001",
                ride_date: "2026-06-15",
                route_title: "滨江-钱塘江休闲往返线",
                destination_name: "钱塘江南岸",
                completion_status: "completed",
                summary_headline: "滨江-钱塘江休闲往返线这次完成得很稳。"
              }
            ]
          }),
        };
      }
      throw new Error(`unexpected fetch ${url}`);
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides?month=2026-06"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole("alert")).toHaveTextContent("本月摘要暂时不可用，请稍后再试。");
  expect(screen.getByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
});
```

- [ ] **Step 2: Write the failing HomePage handoff test**

```tsx
test("prefills planner query from next-action handoff url", async () => {
  render(
    <MemoryRouter initialEntries={["/?intent=ride_plan&planning_scene=city_ride&query=%E8%BF%99%E5%91%A8%E6%89%BE%E4%B8%AA%E5%82%8D%E6%99%9A"]}>
      <Routes>
        <Route path="/" element={<HomePage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(screen.getByRole("button", { name: "帮我安排一次骑行" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByLabelText("骑行需求")).toHaveValue("这周找个傍晚");
});
```

- [ ] **Step 3: Run the frontend tests to verify they fail**

Run:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend
npm test -- src/tests/ride-record-list-page.test.tsx src/tests/home-page.test.tsx
```

Expected: FAIL because monthly summary fetch/types/UI and planner handoff do not exist yet.

- [ ] **Step 4: Add monthly summary types and fetch helper to `api.ts`**

```ts
export type RideMonthlySummaryAction = {
  action_key:
    | "schedule_easy_city_ride"
    | "resume_with_short_ride"
    | "maintain_weekly_rhythm"
    | "take_recovery_window";
  title: string;
  body: string;
  suggested_scene: PlanningScene;
  suggested_entry?: string | null;
};

export type RideMonthlySummary = {
  month: string;
  period_start: string;
  period_end: string;
  ride_count: number;
  ride_day_count: number;
  completed_count: number;
  shortened_count: number;
  cancelled_count: number;
  total_distance_km: number;
  total_duration_hours: number;
  planned_count: number;
  manual_count: number;
  last_ride_date?: string | null;
  days_since_last_ride?: number | null;
  weekly_streak: number;
  habit_status: "starting" | "rebuilding" | "steady" | "overreaching";
  next_action: RideMonthlySummaryAction;
  summary_headline: string;
  summary_body: string;
  top_start_region?: string | null;
  top_tag?: string | null;
  hard_effort_count: number;
  tired_mood_count: number;
  matched_plan_count: number;
  month_to_date: boolean;
  recent_30d_ride_count: number;
};

export type RideMonthlySummaryResponse = {
  ride_monthly_summary: RideMonthlySummary;
};

export async function getRideMonthlySummary(month: string): Promise<RideMonthlySummaryResponse> {
  const searchParams = new URLSearchParams({ month });
  const response = await fetch(`/api/v1/rides/monthly-summary?${searchParams.toString()}`);
  if (!response.ok) {
    throw new Error(`ride-monthly-summary-request-failed:${response.status}`);
  }
  return response.json() as Promise<RideMonthlySummaryResponse>;
}
```

- [ ] **Step 5: Extend `RideRecordsPage.tsx` with summary-band state and month controls**

```tsx
const [searchParams, setSearchParams] = useSearchParams();
const selectedMonth = searchParams.get("month")?.trim() || currentMonth();
const [monthlySummary, setMonthlySummary] = useState<RideMonthlySummary | null>(null);
const [summaryLoading, setSummaryLoading] = useState(true);
const [summaryError, setSummaryError] = useState<string | null>(null);

useEffect(() => {
  let active = true;
  setSummaryLoading(true);
  setSummaryError(null);

  void getRideMonthlySummary(selectedMonth)
    .then((payload) => {
      if (!active) return;
      setMonthlySummary(payload.ride_monthly_summary);
      setSummaryLoading(false);
    })
    .catch(() => {
      if (!active) return;
      setSummaryError("本月摘要暂时不可用，请稍后再试。");
      setSummaryLoading(false);
    });

  return () => {
    active = false;
  };
}, [selectedMonth]);

function shiftMonth(offset: number) {
  const nextMonth = addMonth(selectedMonth, offset);
  setSearchParams({ month: nextMonth });
}

function currentMonth(): string {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
}

function addMonth(month: string, offset: number): string {
  const [year, monthValue] = month.split("-").map(Number);
  const cursor = new Date(year, monthValue - 1 + offset, 1);
  return `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}`;
}

function formatHabitStatus(status: RideMonthlySummary["habit_status"]): string {
  return {
    starting: "重新起步",
    rebuilding: "恢复节奏中",
    steady: "节奏稳定",
    overreaching: "恢复优先",
  }[status];
}

function buildPlannerHandoffLink(action: RideMonthlySummaryAction): string {
  const searchParams = new URLSearchParams({
    intent: "ride_plan",
    planning_scene: action.suggested_scene,
  });
  if (action.suggested_entry) {
    searchParams.set("query", action.suggested_entry);
  }
  return `/?${searchParams.toString()}`;
}
```

```tsx
<section className="detail-panel detail-panel-primary">
  <div className="section-heading">
    <p className="section-kicker">Monthly Habit</p>
    <h2>{monthlySummary?.summary_headline ?? `${selectedMonth} 骑行摘要`}</h2>
  </div>
  <div className="planner-actions">
    <button type="button" onClick={() => shiftMonth(-1)}>上个月</button>
    <span>{selectedMonth}</span>
    <button type="button" onClick={() => shiftMonth(1)}>下个月</button>
  </div>
  {summaryLoading ? <p>正在读取本月骑行摘要...</p> : null}
  {summaryError ? <p role="alert">{summaryError}</p> : null}
  {!summaryLoading && !summaryError && monthlySummary ? (
    <>
      <p className="summary-copy">{monthlySummary.summary_body}</p>
      <div className="metric-row">
        <span>{monthlySummary.ride_count} 次骑行</span>
        <span>{monthlySummary.total_distance_km} km</span>
        <span>{monthlySummary.total_duration_hours} h</span>
        <span>状态：{formatHabitStatus(monthlySummary.habit_status)}</span>
      </div>
      <article className="state-panel">
        <h3>{monthlySummary.next_action.title}</h3>
        <p>{monthlySummary.next_action.body}</p>
        <p className="hero-link-row">
          <Link to={buildPlannerHandoffLink(monthlySummary.next_action)}>按这个建议去规划</Link>
        </p>
      </article>
    </>
  ) : null}
</section>
```

- [ ] **Step 6: Support planner handoff in `HomePage.tsx`**

```tsx
const [searchParams] = useSearchParams();
const seededIntent = searchParams.get("intent");
const seededPlanningScene = searchParams.get("planning_scene");
const seededQuery = searchParams.get("query");

useEffect(() => {
  if (seededPlanningScene === "weekend_trip") {
    setIntent("weekend_recommendation");
  } else if (seededIntent === "ride_plan" || seededIntent === "ride_today" || seededIntent === "weekend_recommendation") {
    setIntent(seededIntent);
  }
  if (seededQuery) {
    setQuery(seededQuery);
  }
}, [seededIntent, seededPlanningScene, seededQuery, setIntent, setQuery]);
```

- [ ] **Step 7: Run the targeted frontend tests to verify they pass**

Run:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend
npm test -- src/tests/ride-record-list-page.test.tsx src/tests/home-page.test.tsx
```

Expected: PASS for the summary-band and planner-handoff tests.

- [ ] **Step 8: Run broader frontend regression for impacted pages**

Run:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend
npm test -- src/tests/plan-result-page.test.tsx src/tests/ride-record-page.test.tsx src/tests/ride-record-list-page.test.tsx src/tests/home-page.test.tsx
npm run build
```

Expected: PASS for all targeted tests and a successful production build.

- [ ] **Step 9: Commit**

```bash
git add \
  products/cycling-agent/frontend/src/features/planner/api.ts \
  products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx \
  products/cycling-agent/frontend/src/pages/HomePage.tsx \
  products/cycling-agent/frontend/src/tests/ride-record-list-page.test.tsx \
  products/cycling-agent/frontend/src/tests/home-page.test.tsx
git commit -m "feat: add rides monthly summary ui"
```

---

## Task 4: Update Docs And Run End-To-End Verification

**Files:**
- Modify: `products/cycling-agent/docs/current-implementation-overview.md`
- Modify: `products/cycling-agent/docs/manual-test-script.md`

- [ ] **Step 1: Update implementation overview**

Add these bullets to `products/cycling-agent/docs/current-implementation-overview.md`:

```md
- `/api/v1/rides/monthly-summary`: 返回基于 `ride_records` 的月度骑行摘要和一致性反馈。
- `/rides`: 在最近骑行记录上方新增本月习惯摘要带，支持月份切换和回到规划入口。
- `ride_monthly_summary_service.py`: 规则优先的跨骑行聚合服务，用于月度骑行统计、状态判断和下一步建议。
```

- [ ] **Step 2: Add a manual verification scenario**

Append this scenario to `products/cycling-agent/docs/manual-test-script.md`:

```md
## Scenario 16: 月度骑行摘要与回到规划闭环

1. 先保存至少 2 条本月骑行记录，其中 1 条 planned、1 条 manual。
2. 打开 `/rides?month=2026-06`。
3. 确认页面顶部显示：
   - 本月骑行次数
   - 总距离或总时长
   - consistency 状态
   - 下一步建议
4. 确认下面的最近骑行记录列表仍然正常渲染。
5. 点击“按这个建议去规划”。
6. 确认跳回首页后，规划输入框被建议文案预填。
7. 切换到上个月，确认摘要会刷新。
8. 模拟月度摘要接口失败，确认顶部显示失败态，但最近骑行记录列表仍可显示。
```

- [ ] **Step 3: Run the full verification commands**

Run:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
. products/cycling-agent/backend/.venv/bin/activate
pytest products/cycling-agent/backend/tests -q
```

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend
npm test
npm run build
```

Expected: backend full suite green, frontend full suite green, build green.

- [ ] **Step 4: Commit**

```bash
git add \
  products/cycling-agent/docs/current-implementation-overview.md \
  products/cycling-agent/docs/manual-test-script.md
git commit -m "docs: document package 2b monthly summary"
```

---

## Final Review Gate

- [ ] Dispatch a fresh final reviewer over the full package 2b commit range.
- [ ] Resolve any Critical or Important review findings.
- [ ] Re-run the full verification commands after the last fix.
- [ ] Keep the branch clean before handing back.
