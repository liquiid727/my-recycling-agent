# Package 2C Growth Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a rule-first growth-review and milestone layer on top of package 2b so `/rides` can show recent growth, not just this-month rhythm.

**Architecture:** Keep package 2c additive and read-only. Extend the current `rides` router with one growth-review endpoint, add one dedicated rolling-window aggregation service, and render a growth panel below the monthly summary band on `/rides`. Reuse the planner handoff pattern from package 2b for the “next focus” CTA.

**Tech Stack:** FastAPI, Pydantic, SQLite/PostgreSQL compatibility layer, React, React Router, TypeScript, Vitest, Testing Library, pytest.

---

## File Structure

### Backend

- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`
  - add growth-review response models and stable enums
- Modify: `products/cycling-agent/backend/app/repositories/ride_record_repository.py`
  - add rolling-window read helpers if existing helpers are not enough
- Modify: `products/cycling-agent/backend/app/api/routes/ride_record.py`
  - add `GET /api/v1/rides/growth-review`
- Create: `products/cycling-agent/backend/app/services/ride_growth_review_service.py`
  - compute deterministic rolling-window aggregates, milestones, and next focus

### Frontend

- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
  - add growth-review types and fetch helper
- Modify: `products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx`
  - add growth-review state, window controls, and next-focus CTA
- Modify: `products/cycling-agent/frontend/src/tests/ride-record-list-page.test.tsx`
  - add growth-panel and failure-independence coverage

### Docs

- Modify: `products/cycling-agent/docs/current-implementation-overview.md`
- Modify: `products/cycling-agent/docs/manual-test-script.md`

---

## Task 1: Define the Growth Review Contract

**Files:**
- Modify: `products/cycling-agent/backend/app/schemas/ride_plan.py`

- [ ] Add `RideGrowthStatus`, `RideGrowthMilestone`, `RideGrowthNextFocus`, `RideGrowthReviewPayload`, and `RideGrowthReviewResponse` schemas.
- [ ] Keep the enum set stable and small.
- [ ] Add validation for `window_days` at the API boundary with a tiny supported range such as `30 | 90 | 180`.

Verification:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
. products/cycling-agent/backend/.venv/bin/activate
pytest products/cycling-agent/backend/tests/test_ride_record_repository.py -v
```

---

## Task 2: Build the Rolling-Window Aggregation Service and API

**Files:**
- Modify: `products/cycling-agent/backend/app/repositories/ride_record_repository.py`
- Modify: `products/cycling-agent/backend/app/api/routes/ride_record.py`
- Create: `products/cycling-agent/backend/app/services/ride_growth_review_service.py`
- Create: `products/cycling-agent/backend/tests/test_ride_growth_review_service.py`
- Create: `products/cycling-agent/backend/tests/test_ride_growth_review_api.py`

- [ ] Write failing tests for:
  - zeroed review
  - invalid `window_days`
  - stable growth review
  - expanding review after a clear recent increase
  - resetting review after a long gap
  - milestone extraction such as longest distance / best streak
- [ ] Implement the smallest repository helper set needed for rolling windows.
- [ ] Implement `build_ride_growth_review(...)` as a deterministic service.
- [ ] Add `GET /api/v1/rides/growth-review`.
- [ ] Reuse the current planner-compatible CTA contract style.

Verification:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment
. products/cycling-agent/backend/.venv/bin/activate
pytest \
  products/cycling-agent/backend/tests/test_ride_growth_review_service.py \
  products/cycling-agent/backend/tests/test_ride_growth_review_api.py -v
```

---

## Task 3: Extend `/rides` With the Growth Panel

**Files:**
- Modify: `products/cycling-agent/frontend/src/features/planner/api.ts`
- Modify: `products/cycling-agent/frontend/src/pages/RideRecordsPage.tsx`
- Modify: `products/cycling-agent/frontend/src/tests/ride-record-list-page.test.tsx`
- Modify: `products/cycling-agent/frontend/src/styles.css`

- [ ] Write failing UI tests for:
  - growth panel renders under the monthly summary band
  - growth fetch failure does not block the monthly summary band or recent list
  - switching the window re-fetches only the growth review
  - next-focus CTA points back to planner handoff
- [ ] Add growth-review types and fetch helper.
- [ ] Add a compact window switcher such as `30 / 90 / 180 天`.
- [ ] Render:
  - growth headline/body
  - key milestones
  - next-focus CTA
- [ ] Keep the existing `/rides` list contract intact.

Verification:

```bash
cd /Users/liquiid/code/cycling-agent-docs/.worktrees/feature-package1-planning-alignment/products/cycling-agent/frontend
npx vitest run src/tests/ride-record-list-page.test.tsx
npm run build
```

---

## Task 4: Update Docs and Manual Verification

**Files:**
- Modify: `products/cycling-agent/docs/current-implementation-overview.md`
- Modify: `products/cycling-agent/docs/manual-test-script.md`

- [ ] Document the new growth-review API and `/rides` growth panel.
- [ ] Add one manual scenario that covers:
  - growth panel load
  - window switch
  - CTA handoff
  - admin/event verification if tracked

---

## Final Review Gate

- [ ] Dispatch a fresh final reviewer over the full package 2c change range.
- [ ] Resolve any Critical or Important findings.
- [ ] Re-run backend targeted pytest, frontend targeted vitest, and frontend build after the last fix.
- [ ] Keep the branch clean before handing back.
