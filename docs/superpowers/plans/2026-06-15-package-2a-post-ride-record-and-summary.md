# Package 2A Post-Ride Record And Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add post-ride record creation, post-ride summary generation, and recent-ride retrieval on top of the existing ride-planning product.

**Architecture:** Keep package 2a additive. Persist one new `ride_records` fact layer, generate `ride_summary` from the saved record plus optional source `ride_plan`, and expose dedicated `/api/v1/rides/records` endpoints. On the frontend, bridge from `PlanResultPage` with a post-ride CTA, support manual backfill, and add a minimal recent-rides surface.

**Tech Stack:** FastAPI, Pydantic, SQLite/PostgreSQL compatibility layer, React, React Router, TypeScript, Vitest, Testing Library, pytest.

---

## File Structure

### Backend

- Modify: `products/cycling-agent/backend/app/core/storage.py`
  - add `ride_records` table in both SQLite/Postgres schema blocks
  - add compatible migration columns for new table
- Modify: `products/cycling-agent/backend/app/main.py`
  - register the new ride-record router
- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
  - add request/response models for ride records and ride summaries to stay consistent with the current single-schema-file pattern
- Create: `products/cycling-agent/backend/app/repositories/ride_record_repository.py`
  - save/list/get ride records
- Create: `products/cycling-agent/backend/app/services/ride_summary_service.py`
  - derive structured summaries from one saved ride record and an optional source plan
- Create: `products/cycling-agent/backend/app/api/routes/ride_record.py`
  - create/list/get ride-record endpoints

### Frontend

- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
  - add ride-record request/response/list types and fetch helpers
- Modify: `products/cycling-agent/frontend/src/app/router.tsx`
  - add ride-record editor/detail/list routes
- Modify: `products/cycling-agent/frontend/src/components/PlanResultView.tsx`
  - add the “记录这次骑行” entry action
- Create: `products/cycling-agent/frontend/src/pages/RideRecordPage.tsx`
  - create form for planned/manual ride record entry
- Create: `products/cycling-agent/frontend/src/pages/RideRecordDetailPage.tsx`
  - render saved record and generated summary
- Create: `products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx`
  - minimal recent-rides list

### Tests

- Create: `products/cycling-agent/backend/tests/test_ride_record_repository.py`
- Create: `products/cycling-agent/backend/tests/test_ride_summary_service.py`
- Create: `products/cycling-agent/backend/tests/test_ride_record_api.py`
- Create: `products/cycling-agent/frontend/src/tests/ride-record-page.test.tsx`
- Create: `products/cycling-agent/frontend/src/tests/ride-record-list-page.test.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/plan-result-page.test.tsx`
- Modify: `products/cycling-agent/docs/current-implementation-overview.md`

## Task 1: Add Ride-Record Persistence And Schemas

**Files:**
- Modify: `products/cycling-agent/backend/app/core/storage.py`
- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
- Create: `products/cycling-agent/backend/app/repositories/ride_record_repository.py`
- Test: `products/cycling-agent/backend/tests/test_ride_record_repository.py`

- [ ] **Step 1: Write the failing repository test**

```python
from app.core.storage import init_storage
from app.repositories.ride_record_repository import get_ride_record, list_ride_records, save_ride_record


def test_ride_record_can_be_saved_listed_and_loaded(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'cycling-agent.db'}"
    init_storage(database_url)

    payload = {
        "ride_record_no": "RR-TEST0001",
        "entry_mode": "planned",
        "source_request_no": "RQ-TEST0001",
        "ride_date": "2026-06-15",
        "intent": "ride_plan",
        "plan_kind": "route",
        "route_code": "HZ-RIVER-001",
        "route_title": "滨江晚风稳妥线",
        "origin_region": "滨江",
        "completion_status": "completed",
        "actual_duration_hours": 2.1,
        "actual_distance_km": 38.5,
        "effort_feeling": "steady",
        "mood_after": "refreshed",
        "notes": "后半段逆风，比预期累一点。",
        "tags": ["windy"],
    }

    save_ride_record(database_url, payload)

    loaded = get_ride_record(database_url, "RR-TEST0001")
    recent = list_ride_records(database_url, limit=5)

    assert loaded is not None
    assert loaded["route_title"] == "滨江晚风稳妥线"
    assert loaded["tags"] == ["windy"]
    assert recent[0]["ride_record_no"] == "RR-TEST0001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment && . products/cycling-agent/backend/.venv/bin/activate && pytest products/cycling-agent/backend/tests/test_ride_record_repository.py -v`

Expected: FAIL with `ModuleNotFoundError` or missing `ride_record_repository`.

- [ ] **Step 3: Write the minimal persistence and schema implementation**

```python
# products/cycling-agent/backend/app/repositories/ride_record_repository.py
from __future__ import annotations

import json
from typing import Any

from app.core.storage import connect


def save_ride_record(database_url: str, payload: dict[str, Any]) -> None:
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO ride_records (
                ride_record_no,
                entry_mode,
                source_request_no,
                ride_date,
                intent,
                plan_kind,
                route_code,
                route_title,
                destination_name,
                start_point,
                origin_region,
                completion_status,
                actual_duration_hours,
                actual_distance_km,
                effort_feeling,
                mood_after,
                notes,
                tags_json,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ride_record_no) DO UPDATE SET
                completion_status = excluded.completion_status,
                actual_duration_hours = excluded.actual_duration_hours,
                actual_distance_km = excluded.actual_distance_km,
                effort_feeling = excluded.effort_feeling,
                mood_after = excluded.mood_after,
                notes = excluded.notes,
                tags_json = excluded.tags_json,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                payload["ride_record_no"],
                payload["entry_mode"],
                payload.get("source_request_no"),
                payload["ride_date"],
                payload.get("intent"),
                payload.get("plan_kind"),
                payload.get("route_code"),
                payload.get("route_title"),
                payload.get("destination_name"),
                payload.get("start_point"),
                payload.get("origin_region"),
                payload["completion_status"],
                payload.get("actual_duration_hours"),
                payload.get("actual_distance_km"),
                payload["effort_feeling"],
                payload["mood_after"],
                payload.get("notes"),
                json.dumps(payload.get("tags", []), ensure_ascii=False),
                json.dumps(payload, ensure_ascii=False),
            ),
        )


def get_ride_record(database_url: str, ride_record_no: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            "SELECT payload_json FROM ride_records WHERE ride_record_no = ?",
            (ride_record_no,),
        ).fetchone()
    return None if row is None else json.loads(row["payload_json"])


def list_ride_records(database_url: str, *, limit: int = 20) -> list[dict[str, Any]]:
    with connect(database_url) as connection:
        rows = connection.execute(
            "SELECT payload_json FROM ride_records ORDER BY ride_date DESC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]
```

```python
# products/cycling-agent/backend/app/schemas/ride_plan.py
class CreateRideRecordRequestSchema(BaseModel):
    entry_mode: str = Field(pattern="^(planned|manual)$")
    source_request_no: str | None = None
    ride_date: date
    route_code: str | None = None
    route_title: str | None = None
    destination_name: str | None = None
    start_point: str | None = None
    origin_region: str | None = None
    completion_status: str = Field(pattern="^(completed|shortened|cancelled)$")
    actual_duration_hours: float | None = None
    actual_distance_km: float | None = None
    effort_feeling: str = Field(pattern="^(easy|steady|hard)$")
    mood_after: str = Field(pattern="^(refreshed|normal|tired)$")
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)


class RideRecordPayload(BaseModel):
    ride_record_no: str
    entry_mode: str = Field(pattern="^(planned|manual)$")
    source_request_no: str | None = None
    ride_date: date
    intent: str | None = Field(default=None, pattern=INTENT_PATTERN)
    plan_kind: str | None = Field(default=None, pattern="^(route|weekend_recommendation)$")
    route_code: str | None = None
    route_title: str | None = None
    destination_name: str | None = None
    start_point: str | None = None
    origin_region: str | None = None
    completion_status: str = Field(pattern="^(completed|shortened|cancelled)$")
    actual_duration_hours: float | None = None
    actual_distance_km: float | None = None
    effort_feeling: str = Field(pattern="^(easy|steady|hard)$")
    mood_after: str = Field(pattern="^(refreshed|normal|tired)$")
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)


class RideSummarySchema(BaseModel):
    headline: str
    summary: str
    completion_assessment: str
    effort_assessment: str
    recovery_advice: str
    next_ride_prompt: str
    plan_alignment: str | None = None
    confidence_notes: list[str] = Field(default_factory=list)


class RideRecordListItemSchema(BaseModel):
    ride_record_no: str
    ride_date: date
    route_title: str | None = None
    destination_name: str | None = None
    completion_status: str
    summary_headline: str | None = None


class RideRecordListResponseSchema(BaseModel):
    items: list[RideRecordListItemSchema] = Field(default_factory=list)


class RideRecordDetailResponseSchema(BaseModel):
    ride_record: RideRecordPayload
    ride_summary: RideSummarySchema
```

```python
# products/cycling-agent/backend/app/core/storage.py
"""
CREATE TABLE IF NOT EXISTS ride_records (
    ride_record_no TEXT PRIMARY KEY,
    entry_mode TEXT NOT NULL,
    source_request_no TEXT,
    ride_date TEXT NOT NULL,
    intent TEXT,
    plan_kind TEXT,
    route_code TEXT,
    route_title TEXT,
    destination_name TEXT,
    start_point TEXT,
    origin_region TEXT,
    completion_status TEXT NOT NULL,
    actual_duration_hours REAL,
    actual_distance_km REAL,
    effort_feeling TEXT NOT NULL,
    mood_after TEXT NOT NULL,
    notes TEXT,
    tags_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""
```

- [ ] **Step 4: Run repository test to verify it passes**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment && . products/cycling-agent/backend/.venv/bin/activate && pytest products/cycling-agent/backend/tests/test_ride_record_repository.py -v`

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the persistence layer**

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
git add products/cycling-agent/backend/app/core/storage.py \
  products/cycling-agent/backend/app/schemas/ride_plan.py \
  products/cycling-agent/backend/app/repositories/ride_record_repository.py \
  products/cycling-agent/backend/tests/test_ride_record_repository.py
git commit -m "feat: add ride record persistence"
```

## Task 2: Add Rule-First Ride Summary Generation

**Files:**
- Create: `products/cycling-agent/backend/app/services/ride_summary_service.py`
- Test: `products/cycling-agent/backend/tests/test_ride_summary_service.py`

- [ ] **Step 1: Write the failing summary-service tests**

```python
from app.services.ride_summary_service import build_ride_summary


def test_build_ride_summary_marks_completed_steady_ride_as_stable() -> None:
    summary = build_ride_summary(
        {
            "entry_mode": "planned",
            "completion_status": "completed",
            "effort_feeling": "steady",
            "mood_after": "refreshed",
            "actual_duration_hours": 2.1,
            "actual_distance_km": 38.5,
        },
        source_plan={"recommended_plan": {"estimated_duration_hours": 2.0, "distance_km": 36}},
    )

    assert summary["completion_assessment"] == "completed-as-planned"
    assert summary["effort_assessment"] == "matched-expected-effort"
    assert "很稳" in summary["headline"]


def test_build_ride_summary_treats_cancelled_ride_as_low_friction_restart() -> None:
    summary = build_ride_summary(
        {
            "entry_mode": "manual",
            "completion_status": "cancelled",
            "effort_feeling": "easy",
            "mood_after": "normal",
        },
        source_plan=None,
    )

    assert summary["completion_assessment"] == "cancelled"
    assert "不要有负担" in summary["summary"]
    assert "轻松" in summary["next_ride_prompt"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment && . products/cycling-agent/backend/.venv/bin/activate && pytest products/cycling-agent/backend/tests/test_ride_summary_service.py -v`

Expected: FAIL because `ride_summary_service` does not exist.

- [ ] **Step 3: Write the minimal summary builder**

```python
# products/cycling-agent/backend/app/services/ride_summary_service.py
from __future__ import annotations

from typing import Any


def build_ride_summary(record: dict[str, Any], *, source_plan: dict[str, Any] | None) -> dict[str, Any]:
    completion_status = record["completion_status"]
    effort_feeling = record["effort_feeling"]
    mood_after = record["mood_after"]

    if completion_status == "cancelled":
        return {
            "headline": "这次没骑成也没关系。",
            "summary": "这次先放下不代表掉队，重点是把下一次重新出门的门槛降下来，不要有负担。",
            "completion_assessment": "cancelled",
            "effort_assessment": "not-started",
            "plan_alignment": "not-ridden",
            "recovery_advice": "今天以休息和补水为主。",
            "next_ride_prompt": "下次先安排一次更轻松、更容易出门的短骑就够了。",
            "confidence_notes": [],
        }

    duration_gap = _duration_gap(record, source_plan)
    effort_assessment = "matched-expected-effort"
    if effort_feeling == "hard" or duration_gap > 0.4:
        effort_assessment = "slightly-harder-than-expected"

    completion_assessment = "completed-as-planned" if completion_status == "completed" else "partially-completed"

    return {
        "headline": "这次骑行完成得很稳。",
        "summary": "你完成了这次骑行，整体节奏可控，恢复反馈也是正向的。",
        "completion_assessment": completion_assessment,
        "effort_assessment": effort_assessment,
        "plan_alignment": "matched-core-plan" if source_plan else None,
        "recovery_advice": "明天优先轻松骑或休息，补水和拉伸要跟上。",
        "next_ride_prompt": "下次可以继续安排相近时长，或者略微增加一点探索感。",
        "confidence_notes": [],
    }


def _duration_gap(record: dict[str, Any], source_plan: dict[str, Any] | None) -> float:
    if not source_plan:
        return 0.0
    planned = float(source_plan.get("recommended_plan", {}).get("estimated_duration_hours") or 0)
    actual = float(record.get("actual_duration_hours") or 0)
    return abs(actual - planned)
```

- [ ] **Step 4: Run summary-service tests to verify they pass**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment && . products/cycling-agent/backend/.venv/bin/activate && pytest products/cycling-agent/backend/tests/test_ride_summary_service.py -v`

Expected: PASS with `2 passed`.

- [ ] **Step 5: Commit the summary service**

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
git add products/cycling-agent/backend/app/services/ride_summary_service.py \
  products/cycling-agent/backend/tests/test_ride_summary_service.py
git commit -m "feat: add ride summary service"
```

## Task 3: Add Ride-Record API And App Wiring

**Files:**
- Create: `products/cycling-agent/backend/app/api/routes/ride_record.py`
- Modify: `products/cycling-agent/backend/app/main.py`
- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
- Test: `products/cycling-agent/backend/tests/test_ride_record_api.py`

- [ ] **Step 1: Write the failing API tests**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_create_ride_record_from_saved_plan_returns_summary(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    plan_response = client.post(
        "/api/v1/ride/plan",
        json={"query": "今晚从滨江骑两小时", "target_date": "2026-06-15"},
    )
    request_no = plan_response.json()["request_no"]

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "planned",
            "source_request_no": request_no,
            "ride_date": "2026-06-15",
            "completion_status": "completed",
            "actual_duration_hours": 2.0,
            "actual_distance_km": 35,
            "effort_feeling": "steady",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ride_record"]["ride_record_no"].startswith("RR-")
    assert body["ride_summary"]["completion_assessment"] == "completed-as-planned"


def test_create_manual_ride_record_requires_title_or_destination(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": "2026-06-15",
            "completion_status": "completed",
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "ride-record-manual-title-missing"


def test_list_and_get_ride_records_return_saved_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CYCLING_AGENT_DATABASE_URL", f"sqlite:///{tmp_path / 'cycling-agent.db'}")
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/rides/records",
        json={
            "entry_mode": "manual",
            "ride_date": "2026-06-15",
            "route_title": "湘湖绕湖骑",
            "completion_status": "completed",
            "actual_duration_hours": 1.5,
            "actual_distance_km": 24,
            "effort_feeling": "easy",
            "mood_after": "refreshed",
        },
    ).json()

    ride_record_no = created["ride_record"]["ride_record_no"]
    listed = client.get("/api/v1/rides/records?limit=5")
    loaded = client.get(f"/api/v1/rides/records/{ride_record_no}")

    assert listed.status_code == 200
    assert listed.json()["items"][0]["ride_record_no"] == ride_record_no
    assert loaded.status_code == 200
    assert loaded.json()["ride_summary"]["headline"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment && . products/cycling-agent/backend/.venv/bin/activate && pytest products/cycling-agent/backend/tests/test_ride_record_api.py -v`

Expected: FAIL with missing route or 404.

- [ ] **Step 3: Implement the API router and validations**

```python
# products/cycling-agent/backend/app/api/routes/ride_record.py
from fastapi import APIRouter, HTTPException, Query, Request

from app.core.ids import generate_business_no
from app.repositories.plan_result_repository import get_ride_plan
from app.repositories.ride_record_repository import get_ride_record, list_ride_records, save_ride_record
from app.schemas.ride_plan import (
    CreateRideRecordRequestSchema,
    RideRecordDetailResponseSchema,
    RideRecordListItemSchema,
    RideRecordListResponseSchema,
)
from app.services.ride_summary_service import build_ride_summary

router = APIRouter(prefix="/api/v1/rides", tags=["rides"])


@router.post("/records", response_model=RideRecordDetailResponseSchema)
async def create_ride_record(payload: CreateRideRecordRequestSchema, request: Request) -> RideRecordDetailResponseSchema:
    source_plan = None
    if payload.entry_mode == "planned":
        if not payload.source_request_no:
            raise HTTPException(status_code=422, detail="ride-record-source-request-missing")
        source_plan = get_ride_plan(request.app.state.database_url, payload.source_request_no)
        if source_plan is None:
            raise HTTPException(status_code=404, detail="ride-record-source-plan-not-found")
    if payload.entry_mode == "manual" and not (payload.route_title or payload.destination_name):
        raise HTTPException(status_code=422, detail="ride-record-manual-title-missing")
    if payload.completion_status == "completed" and payload.actual_duration_hours is None and payload.actual_distance_km is None:
        raise HTTPException(status_code=422, detail="ride-record-completed-metrics-missing")

    record = _normalize_record(payload, source_plan)
    save_ride_record(request.app.state.database_url, record)
    return RideRecordDetailResponseSchema(
        ride_record=record,
        ride_summary=build_ride_summary(record, source_plan=source_plan),
    )


@router.get("/records", response_model=RideRecordListResponseSchema)
async def get_ride_records(request: Request, limit: int = Query(default=20, ge=1, le=100)) -> RideRecordListResponseSchema:
    items = list_ride_records(request.app.state.database_url, limit=limit)
    return RideRecordListResponseSchema(items=[RideRecordListItemSchema.model_validate(item) for item in items])


@router.get("/records/{ride_record_no}", response_model=RideRecordDetailResponseSchema)
async def get_one_ride_record(ride_record_no: str, request: Request) -> RideRecordDetailResponseSchema:
    record = get_ride_record(request.app.state.database_url, ride_record_no)
    if record is None:
        raise HTTPException(status_code=404, detail="ride-record-not-found")
    source_plan = get_ride_plan(request.app.state.database_url, record["source_request_no"]) if record.get("source_request_no") else None
    return RideRecordDetailResponseSchema(
        ride_record=record,
        ride_summary=build_ride_summary(record, source_plan=source_plan),
    )


def _normalize_record(payload: CreateRideRecordRequestSchema, source_plan: dict | None) -> dict:
    base = payload.model_dump(mode="json")
    recommendation = (source_plan or {}).get("recommended_plan", {})
    trip = (source_plan or {}).get("recommended_trip", {})
    return {
        "ride_record_no": generate_business_no("RR"),
        "entry_mode": payload.entry_mode,
        "source_request_no": payload.source_request_no,
        "ride_date": base["ride_date"],
        "intent": (source_plan or {}).get("intent"),
        "plan_kind": (source_plan or {}).get("plan", {}).get("kind"),
        "route_code": payload.route_code or recommendation.get("route_code"),
        "route_title": payload.route_title or recommendation.get("route_name") or trip.get("trip_name"),
        "destination_name": payload.destination_name or trip.get("destination_name"),
        "start_point": payload.start_point,
        "origin_region": payload.origin_region,
        "completion_status": payload.completion_status,
        "actual_duration_hours": payload.actual_duration_hours,
        "actual_distance_km": payload.actual_distance_km,
        "effort_feeling": payload.effort_feeling,
        "mood_after": payload.mood_after,
        "notes": payload.notes,
        "tags": payload.tags,
    }
```

```python
# products/cycling-agent/backend/app/main.py
from app.api.routes.ride_record import router as ride_record_router

app.include_router(ride_record_router)
```

- [ ] **Step 4: Run backend API tests**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment && . products/cycling-agent/backend/.venv/bin/activate && pytest products/cycling-agent/backend/tests/test_ride_record_api.py -v`

Expected: PASS with create/list/get coverage green.

- [ ] **Step 5: Commit the API layer**

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
git add products/cycling-agent/backend/app/api/routes/ride_record.py \
  products/cycling-agent/backend/app/main.py \
  products/cycling-agent/backend/app/schemas/ride_plan.py \
  products/cycling-agent/backend/tests/test_ride_record_api.py
git commit -m "feat: add ride record api"
```

## Task 4: Add Frontend Ride-Record Flows

**Files:**
- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
- Modify: `products/cycling-agent/frontend/src/app/router.tsx`
- Modify: `products/cycling-agent/frontend/src/components/PlanResultView.tsx`
- Create: `products/cycling-agent/frontend/src/pages/RideRecordPage.tsx`
- Create: `products/cycling-agent/frontend/src/pages/RideRecordDetailPage.tsx`
- Create: `products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/plan-result-page.test.tsx`
- Create: `products/cycling-agent/frontend/src/tests/ride-record-page.test.tsx`
- Create: `products/cycling-agent/frontend/src/tests/ride-record-list-page.test.tsx`

- [ ] **Step 1: Write the failing frontend tests**

```tsx
test("plan result page links to post-ride record entry", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    json: async () => ({
      request_no: "RQ-TEST0001",
      intent: "ride_plan",
      parsed_constraints: {},
      recommended_plan: {
        go_decision: "go",
        route_name: "滨江-钱塘江休闲往返线",
        route_code: "HZ-RIVER-001",
        distance_km: 42,
        elevation_gain_m: 180,
        estimated_duration_hours: 2.8,
        risk_level: "low",
        summary_reason: "时长匹配，轻松稳定。"
      },
      alternatives: [],
      weather_snapshot: {
        region_code: "binjiang",
        forecast_date: "2026-05-30",
        temperature_min: 22,
        temperature_max: 31,
        precipitation_probability: 0.15,
        wind_speed: 4.8,
        wind_direction: "SE",
        weather_summary: "cloudy",
        provider_name: "stub",
        raw_payload: {}
      },
      fallback_reason: [],
      tool_trace: [],
      roadbook: null
    })
  })));

  render(
    <MemoryRouter initialEntries={["/plans/RQ-TEST0001"]}>
      <Routes>
        <Route path="/plans/:requestNo" element={<PlanResultPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole("link", { name: "记录这次骑行" })).toHaveAttribute(
    "href",
    "/rides/new?sourceRequestNo=RQ-TEST0001",
  );
});


test("ride record page submits planned ride payload and renders summary", async () => {
  const fetchMock = vi.fn(async (url, init?: RequestInit) => {
    if (String(url).startsWith("/api/v1/ride/plan/")) {
      return {
        ok: true,
        json: async () => ({
          request_no: "RQ-TEST0001",
          recommended_plan: {
            route_name: "滨江晚风稳妥线",
            route_code: "HZ-RIVER-001",
            distance_km: 42,
            elevation_gain_m: 180,
            estimated_duration_hours: 2.8,
            risk_level: "low",
            summary_reason: "时长匹配，轻松稳定。"
          },
          alternatives: [],
          weather_snapshot: null,
          fallback_reason: [],
          tool_trace: [],
          roadbook: null,
          parsed_constraints: {}
        })
      };
    }

    return {
      ok: true,
      json: async () => ({
        ride_record: {
          ride_record_no: "RR-TEST0001",
          entry_mode: "planned",
          source_request_no: "RQ-TEST0001",
          ride_date: "2026-06-15",
          route_title: "滨江晚风稳妥线",
          completion_status: "completed",
          effort_feeling: "steady",
          mood_after: "refreshed",
          actual_duration_hours: 2.0,
          actual_distance_km: 35
        },
        ride_summary: {
          headline: "这次骑行完成得很稳。",
          summary: "你完成了这次骑行，整体节奏可控，恢复反馈也是正向的。",
          completion_assessment: "completed-as-planned",
          effort_assessment: "matched-expected-effort",
          recovery_advice: "明天优先轻松骑或休息，补水和拉伸要跟上。",
          next_ride_prompt: "下次可以继续安排相近时长。"
        }
      })
    };
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter initialEntries={["/rides/new?sourceRequestNo=RQ-TEST0001"]}>
      <Routes>
        <Route path="/rides/new" element={<RideRecordPage />} />
      </Routes>
    </MemoryRouter>,
  );

  fireEvent.change(await screen.findByLabelText("骑行日期"), { target: { value: "2026-06-15" } });
  fireEvent.change(screen.getByLabelText("实际时长"), { target: { value: "2.0" } });
  fireEvent.change(screen.getByLabelText("实际距离"), { target: { value: "35" } });
  fireEvent.click(screen.getByRole("button", { name: "保存骑行记录" }));

  expect(await screen.findByText("这次骑行完成得很稳。")).toBeInTheDocument();
  expect(fetchMock.mock.calls.some(([url]) => String(url) === "/api/v1/rides/records")).toBe(true);
});


test("recent ride records page renders saved items", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    json: async () => ({
      items: [
        {
          ride_record_no: "RR-TEST0001",
          ride_date: "2026-06-15",
          route_title: "湘湖绕湖骑",
          completion_status: "completed",
          summary_headline: "这次骑行完成得很稳。"
        }
      ]
    })
  })));

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("湘湖绕湖骑")).toBeInTheDocument();
  expect(screen.getByText("这次骑行完成得很稳。")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend tests to verify they fail**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend && npx vitest run src/tests/plan-result-page.test.tsx src/tests/ride-record-page.test.tsx src/tests/ride-record-list-page.test.tsx`

Expected: FAIL because new routes/components/helpers do not exist yet.

- [ ] **Step 3: Implement the frontend API and pages**

```ts
// products/cycling-agent/frontend/src/features/planner/api.ts
export type RideRecordRequest = {
  entry_mode: "planned" | "manual";
  source_request_no?: string;
  ride_date: string;
  route_title?: string;
  destination_name?: string;
  origin_region?: string;
  completion_status: "completed" | "shortened" | "cancelled";
  actual_duration_hours?: number;
  actual_distance_km?: number;
  effort_feeling: "easy" | "steady" | "hard";
  mood_after: "refreshed" | "normal" | "tired";
  notes?: string;
};

export type RideSummary = {
  headline: string;
  summary: string;
  completion_assessment: string;
  effort_assessment: string;
  recovery_advice: string;
  next_ride_prompt: string;
  plan_alignment?: string | null;
};

export type RideRecord = {
  ride_record_no: string;
  entry_mode: "planned" | "manual";
  source_request_no?: string;
  ride_date: string;
  route_title?: string;
  destination_name?: string;
  completion_status: "completed" | "shortened" | "cancelled";
  actual_duration_hours?: number;
  actual_distance_km?: number;
  effort_feeling: "easy" | "steady" | "hard";
  mood_after: "refreshed" | "normal" | "tired";
  notes?: string;
};

export type RideRecordDetailResponse = {
  ride_record: RideRecord;
  ride_summary: RideSummary;
};

export type RideRecordListResponse = {
  items: Array<RideRecord & { summary_headline?: string }>;
};

export async function createRideRecord(payload: RideRecordRequest): Promise<RideRecordDetailResponse> {
  const response = await fetch("/api/v1/rides/records", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("ride-record-save-failed");
  }
  return response.json() as Promise<RideRecordDetailResponse>;
}

export async function getRideRecord(rideRecordNo: string): Promise<RideRecordDetailResponse> {
  const response = await fetch(`/api/v1/rides/records/${rideRecordNo}`);
  if (!response.ok) {
    throw new Error("ride-record-load-failed");
  }
  return response.json() as Promise<RideRecordDetailResponse>;
}

export async function listRideRecords(limit = 20): Promise<RideRecordListResponse> {
  const response = await fetch(`/api/v1/rides/records?limit=${limit}`);
  if (!response.ok) {
    throw new Error("ride-record-list-failed");
  }
  return response.json() as Promise<RideRecordListResponse>;
}
```

```tsx
// products/cycling-agent/frontend/src/components/PlanResultView.tsx
<p className="hero-link-row">
  <Link to={`/rides/new?sourceRequestNo=${result.request_no}`}>记录这次骑行</Link>
</p>
```

```tsx
// products/cycling-agent/frontend/src/pages/RideRecordPage.tsx
const location = useLocation();
const params = new URLSearchParams(location.search);
const sourceRequestNo = params.get("sourceRequestNo");
const isPlanned = Boolean(sourceRequestNo);

async function handleSubmit(event: FormEvent<HTMLFormElement>) {
  event.preventDefault();
  setSaving(true);
  const saved = await createRideRecord({
    entry_mode: isPlanned ? "planned" : "manual",
    source_request_no: sourceRequestNo ?? undefined,
    ride_date,
    route_title,
    completion_status,
    actual_duration_hours: duration ? Number(duration) : undefined,
    actual_distance_km: distance ? Number(distance) : undefined,
    effort_feeling,
    mood_after,
    notes,
  });
  navigate(`/rides/${saved.ride_record.ride_record_no}`);
}
```

```tsx
// products/cycling-agent/frontend/src/pages/RideRecordDetailPage.tsx
const { rideRecordNo = "" } = useParams();
const [detail, setDetail] = useState<RideRecordDetailResponse | null>(null);

useEffect(() => {
  void getRideRecord(rideRecordNo).then(setDetail).catch(() => setError("骑行记录暂时不可用"));
}, [rideRecordNo]);
```

```tsx
// products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx
const [records, setRecords] = useState<RideRecordListResponse["items"]>([]);

useEffect(() => {
  void listRideRecords(20)
    .then((payload) => setRecords(payload.items))
    .catch(() => setError("最近骑行暂时不可用"));
}, []);
```

```tsx
// products/cycling-agent/frontend/src/app/router.tsx
{ path: "/rides", element: <RideRecordsPage /> },
{ path: "/rides/new", element: <RideRecordPage /> },
{ path: "/rides/:rideRecordNo", element: <RideRecordDetailPage /> },
```

- [ ] **Step 4: Run frontend tests and build**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend && npm test`

Expected: PASS with the new ride-record page tests and existing planner/result tests still green.

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend && npm run build`

Expected: PASS build output.

- [ ] **Step 5: Commit the frontend flow**

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
git add products/cycling-agent/frontend/src/features/planner/api.ts \
  products/cycling-agent/frontend/src/app/router.tsx \
  products/cycling-agent/frontend/src/components/PlanResultView.tsx \
  products/cycling-agent/frontend/src/pages/RideRecordPage.tsx \
  products/cycling-agent/frontend/src/pages/RideRecordDetailPage.tsx \
  products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx \
  products/cycling-agent/frontend/src/tests/plan-result-page.test.tsx \
  products/cycling-agent/frontend/src/tests/ride-record-page.test.tsx \
  products/cycling-agent/frontend/src/tests/ride-record-list-page.test.tsx
git commit -m "feat: add ride record frontend flows"
```

## Task 5: Align Docs And Run End-To-End Verification

**Files:**
- Modify: `products/cycling-agent/docs/current-implementation-overview.md`
- Modify if needed: `products/cycling-agent/docs/manual-test-script.md`

- [ ] **Step 1: Add the implementation doc coverage**

```md
## Package 2A: Post-Ride Record And Summary

- Save a ride record from an existing `ride_plan` result via `/api/v1/rides/records`
- Manually backfill one ride without a source plan
- Generate a structured `ride_summary` from the saved record plus optional source plan
- Review recent ride records in the frontend at `/rides`
```

- [ ] **Step 2: Run the focused backend verification**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment && . products/cycling-agent/backend/.venv/bin/activate && pytest products/cycling-agent/backend/tests/test_ride_record_repository.py products/cycling-agent/backend/tests/test_ride_summary_service.py products/cycling-agent/backend/tests/test_ride_record_api.py -v`

Expected: PASS for all new backend tests.

- [ ] **Step 3: Run the full regression gates that cover touched surfaces**

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment && . products/cycling-agent/backend/.venv/bin/activate && pytest products/cycling-agent/backend/tests`

Expected: PASS with no regressions beyond existing skips.

Run: `cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend && npm test && npm run build`

Expected: PASS for frontend tests and build.

- [ ] **Step 4: Final commit**

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
git add products/cycling-agent/docs/current-implementation-overview.md \
  products/cycling-agent/docs/manual-test-script.md
git commit -m "docs: document post-ride record flows"
```

- [ ] **Step 5: Final evidence capture before review**

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
git status --short --branch
git log --oneline -5
```

Expected:

- branch stays `feature/package1-planning-alignment` or a package-2 branch if split later
- worktree is clean before asking for final review
- the latest commits cover persistence, summary service, frontend, and docs

## Self-Review

- Spec coverage check:
  - `ride_record` fact layer: Task 1
  - `ride_summary` rule-first generation: Task 2
  - create/list/get APIs with stable errors: Task 3
  - result-page bridge, manual backfill, recent-rides UI, loading/error/success states: Task 4
  - docs and observability-adjacent verification evidence: Task 5
- Placeholder scan:
  - no `TODO`, `TBD`, or “implement later” markers remain
- Type consistency:
  - `entry_mode`, `completion_status`, `effort_feeling`, and `mood_after` use one enum family across backend and frontend
