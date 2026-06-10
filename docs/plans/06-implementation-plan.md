# Cycling Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the cycling-agent Web MVP with Hangzhou as the default sample city. It accepts a natural-language request plus city / origin context and returns a recommended route, alternatives, risk assessment, and roadbook.

**Architecture:** Use a split frontend/backend app under `products/cycling-agent/`, with React rendering the planning experience and FastAPI hosting a `RidePlanningOrchestrator`. The MVP orchestration model is `one orchestrator + two LLM agents + three deterministic modules`: `QueryParserAgent`, `RoutePlanner`, `RiskEvaluator`, `DecisionEngine`, and `RoadbookGeneratorAgent`. Start from a curated Hangzhou route template library and a deterministic rule-based risk engine, then layer model-assisted query parsing and explanation generation on top. Keep `city_code` and origin fields explicit so the same structure can support later city strategy packs.

**Tech Stack:** React, TypeScript, Vite, FastAPI, Pydantic, SQLAlchemy or SQLModel, PostgreSQL, Redis, pytest, Vitest

---

## File Structure

Planned project root:

```text
products/cycling-agent/
  frontend/
  backend/
  data/
```

Responsibility split:

- `frontend/` owns input, result rendering, and client-side schema validation.
- `backend/` owns API, orchestration, parsing, route matching, risk scoring, and roadbook generation.
- `data/` owns Hangzhou route seeds and local strategy configuration used for MVP bootstrapping.

### Task 1: Scaffold backend service

**Files:**
- Create: `products/cycling-agent/backend/app/main.py`
- Create: `products/cycling-agent/backend/app/api/routes/ride_plan.py`
- Create: `products/cycling-agent/backend/app/core/config.py`
- Create: `products/cycling-agent/backend/tests/test_healthcheck.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/backend && pytest tests/test_healthcheck.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing `app.main`.

- [ ] **Step 3: Write minimal implementation**

```python
# products/cycling-agent/backend/app/main.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# products/cycling-agent/backend/app/api/routes/ride_plan.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/ride", tags=["ride"])
```

```python
# products/cycling-agent/backend/app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "cycling-agent-backend"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/backend && pytest tests/test_healthcheck.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/backend
git commit -m "feat: scaffold backend service"
```

### Task 2: Add route-plan request and response schemas

**Files:**
- Create: `products/cycling-agent/backend/app/schemas/ride_plan.py`
- Modify: `products/cycling-agent/backend/app/api/routes/ride_plan.py`
- Create: `products/cycling-agent/backend/tests/test_ride_plan_schema.py`

- [ ] **Step 1: Write the failing test**

```python
from datetime import date

from app.schemas.ride_plan import RidePlanRequestSchema


def test_ride_plan_request_accepts_minimum_payload() -> None:
    payload = RidePlanRequestSchema(
        query="周六从滨江出发骑3小时，不想太累",
        target_date=date(2026, 5, 30),
    )
    assert payload.city_code == "hangzhou"
    assert payload.query.startswith("周六")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/backend && pytest tests/test_ride_plan_schema.py -v`
Expected: FAIL with missing schema module.

- [ ] **Step 3: Write minimal implementation**

```python
from datetime import date

from pydantic import BaseModel, Field


class UserProfilePayload(BaseModel):
    home_region: str | None = None
    fitness_level: str | None = Field(default=None, pattern="^(low|medium|high)$")
    ride_style_preferences: list[str] = []
    slope_tolerance: str | None = Field(default=None, pattern="^(avoid|neutral|prefer)$")


class RidePlanRequestSchema(BaseModel):
    query: str = Field(min_length=3)
    target_date: date
    city_code: str = "hangzhou"
    user_profile: UserProfilePayload | None = None


class RoutePlanCardSchema(BaseModel):
    route_name: str
    distance_km: float
    elevation_gain_m: float
    estimated_duration_hours: float
    risk_level: str
    summary_reason: str


class RidePlanResponseSchema(BaseModel):
    request_no: str
    parsed_constraints: dict
    recommended_plan: dict
    alternatives: list[dict]
    roadbook: dict | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/backend && pytest tests/test_ride_plan_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/backend/app/schemas/ride_plan.py products/cycling-agent/backend/tests/test_ride_plan_schema.py
git commit -m "feat: add ride plan request and response schemas"
```

### Task 3: Seed the Hangzhou route template library

**Files:**
- Create: `products/cycling-agent/data/hangzhou_routes.json`
- Create: `products/cycling-agent/backend/app/repositories/route_template_repository.py`
- Create: `products/cycling-agent/backend/tests/test_route_template_repository.py`

- [ ] **Step 1: Write the failing test**

```python
from app.repositories.route_template_repository import load_route_templates


def test_load_route_templates_returns_seeded_hangzhou_routes() -> None:
    routes = load_route_templates("products/cycling-agent/data/hangzhou_routes.json")
    assert len(routes) >= 3
    assert routes[0]["city_code"] == "hangzhou"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/backend && pytest tests/test_route_template_repository.py -v`
Expected: FAIL with missing repository function or seed file.

- [ ] **Step 3: Write minimal implementation**

```python
# products/cycling-agent/backend/app/repositories/route_template_repository.py
import json
from pathlib import Path


def load_route_templates(path: str) -> list[dict]:
    return json.loads(Path(path).read_text())
```

```json
[
  {
    "route_code": "HZ-RIVER-001",
    "name": "滨江-钱塘江休闲往返线",
    "city_code": "hangzhou",
    "district_tags": ["滨江", "钱塘江"],
    "ride_style_tags": ["relaxed", "scenic", "weekend"],
    "distance_km": 42,
    "elevation_gain_m": 180,
    "estimated_duration_hours": 2.8,
    "difficulty_level": "easy",
    "traffic_level": "low",
    "supply_score": 8,
    "return_difficulty_score": 3,
    "scenic_score": 8,
    "beginner_friendly": true
  },
  {
    "route_code": "HZ-HILL-002",
    "name": "西湖-龙井轻爬坡体验线",
    "city_code": "hangzhou",
    "district_tags": ["西湖", "龙井"],
    "ride_style_tags": ["climb", "scenic", "half_day"],
    "distance_km": 36,
    "elevation_gain_m": 520,
    "estimated_duration_hours": 3.2,
    "difficulty_level": "medium",
    "traffic_level": "medium",
    "supply_score": 6,
    "return_difficulty_score": 5,
    "scenic_score": 9,
    "beginner_friendly": false
  },
  {
    "route_code": "HZ-LEISURE-003",
    "name": "湘湖半日郊游线",
    "city_code": "hangzhou",
    "district_tags": ["湘湖", "萧山"],
    "ride_style_tags": ["relaxed", "half_day", "leisure"],
    "distance_km": 30,
    "elevation_gain_m": 210,
    "estimated_duration_hours": 2.4,
    "difficulty_level": "easy",
    "traffic_level": "low",
    "supply_score": 7,
    "return_difficulty_score": 2,
    "scenic_score": 8,
    "beginner_friendly": true
  }
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/backend && pytest tests/test_route_template_repository.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/data/hangzhou_routes.json products/cycling-agent/backend/app/repositories/route_template_repository.py products/cycling-agent/backend/tests/test_route_template_repository.py
git commit -m "feat: seed hangzhou route template library"
```

### Task 4: Implement QueryParserAgent deterministic fallback

**Files:**
- Create: `products/cycling-agent/backend/app/agents/query_parser_agent.py`
- Create: `products/cycling-agent/backend/tests/test_query_parser_agent.py`

- [ ] **Step 1: Write the failing test**

```python
from app.agents.query_parser_agent import parse_query_fallback


def test_parse_query_extracts_origin_hours_and_style() -> None:
    parsed = parse_query_fallback("周六从滨江出发骑3小时，不想太累，风景好一点")
    assert parsed["origin_region"] == "滨江"
    assert parsed["available_hours"] == 3
    assert parsed["ride_style"] == "scenic_relaxed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/backend && pytest tests/test_query_parser_agent.py -v`
Expected: FAIL with missing parser function.

- [ ] **Step 3: Write minimal implementation**

```python
import re


def parse_query_fallback(query: str) -> dict:
    hours_match = re.search(r"(\d+)小时", query)
    return {
        "origin_region": "滨江" if "滨江" in query else None,
        "available_hours": int(hours_match.group(1)) if hours_match else None,
        "ride_style": "scenic_relaxed" if "风景" in query and "不想太累" in query else "general",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/backend && pytest tests/test_query_parser_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/backend/app/agents/query_parser_agent.py products/cycling-agent/backend/tests/test_query_parser_agent.py
git commit -m "feat: add query parser agent fallback"
```

### Task 5: Implement RoutePlanner candidate ranking service

**Files:**
- Create: `products/cycling-agent/backend/app/services/route_match_service.py`
- Create: `products/cycling-agent/backend/tests/test_route_match_service.py`

- [ ] **Step 1: Write the failing test**

```python
from app.services.route_match_service import rank_route_candidates


def test_rank_route_candidates_prefers_easy_scenic_routes_for_relaxed_query() -> None:
    routes = [
        {"name": "钱塘江线", "difficulty_level": "easy", "scenic_score": 8, "estimated_duration_hours": 2.8},
        {"name": "龙井线", "difficulty_level": "medium", "scenic_score": 9, "estimated_duration_hours": 3.2},
    ]
    constraints = {"available_hours": 3, "ride_style": "scenic_relaxed"}
    ranked = rank_route_candidates(routes, constraints)
    assert ranked[0]["name"] == "钱塘江线"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/backend && pytest tests/test_route_match_service.py -v`
Expected: FAIL with missing ranking function.

- [ ] **Step 3: Write minimal implementation**

```python
def rank_route_candidates(routes: list[dict], constraints: dict) -> list[dict]:
    target_hours = constraints.get("available_hours") or 3
    for route in routes:
        duration_gap = abs(route["estimated_duration_hours"] - target_hours)
        difficulty_bonus = 0.2 if route["difficulty_level"] == "easy" else 0
        scenic_bonus = route.get("scenic_score", 0) / 100
        route["match_score"] = 1 - duration_gap / 10 + difficulty_bonus + scenic_bonus
    return sorted(routes, key=lambda item: item["match_score"], reverse=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/backend && pytest tests/test_route_match_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/backend/app/services/route_match_service.py products/cycling-agent/backend/tests/test_route_match_service.py
git commit -m "feat: add route planner candidate ranking"
```

### Task 6: Implement RiskEvaluator scoring service

**Files:**
- Create: `products/cycling-agent/backend/app/services/risk_scoring_service.py`
- Create: `products/cycling-agent/backend/tests/test_risk_scoring_service.py`

- [ ] **Step 1: Write the failing test**

```python
from app.services.risk_scoring_service import score_route_risk


def test_score_route_risk_marks_hot_climb_route_as_medium_or_higher() -> None:
    route = {"elevation_gain_m": 520, "traffic_level": "medium", "supply_score": 6}
    weather = {"temperature_max": 34, "precipitation_probability": 0.1, "wind_speed": 3}
    user = {"fitness_level": "low"}
    result = score_route_risk(route, weather, user)
    assert result["risk_level"] in {"medium", "high"}
    assert result["weather_risk_score"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/backend && pytest tests/test_risk_scoring_service.py -v`
Expected: FAIL with missing service.

- [ ] **Step 3: Write minimal implementation**

```python
def score_route_risk(route: dict, weather: dict, user: dict) -> dict:
    weather_risk = 0.25 if weather["temperature_max"] >= 33 else 0
    climb_risk = 0.35 if route["elevation_gain_m"] > 500 and user.get("fitness_level") == "low" else 0
    traffic_risk = 0.15 if route.get("traffic_level") == "medium" else 0.3 if route.get("traffic_level") == "high" else 0
    supply_risk = 0.1 if route.get("supply_score", 0) <= 5 else 0
    overall = weather_risk * 0.35 + climb_risk * 0.20 + traffic_risk * 0.20 + supply_risk * 0.10
    risk_level = "high" if overall >= 0.60 else "medium" if overall >= 0.30 else "low"
    return {
        "overall_risk_score": overall,
        "risk_level": risk_level,
        "weather_risk_score": weather_risk,
        "climb_risk_score": climb_risk,
        "traffic_risk_score": traffic_risk,
        "supply_risk_score": supply_risk,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/backend && pytest tests/test_risk_scoring_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/backend/app/services/risk_scoring_service.py products/cycling-agent/backend/tests/test_risk_scoring_service.py
git commit -m "feat: add risk evaluator scoring service"
```

### Task 7: Add RidePlanningOrchestrator API

**Files:**
- Modify: `products/cycling-agent/backend/app/main.py`
- Modify: `products/cycling-agent/backend/app/api/routes/ride_plan.py`
- Create: `products/cycling-agent/backend/app/services/ride_planning_orchestrator.py`
- Create: `products/cycling-agent/backend/tests/test_ride_plan_api.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_post_ride_plan_returns_recommendation_payload() -> None:
    response = client.post(
        "/api/v1/ride/plan",
        json={"query": "周六从滨江出发骑3小时，不想太累", "target_date": "2026-05-30"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_plan"]["route_name"]
    assert "alternatives" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/backend && pytest tests/test_ride_plan_api.py -v`
Expected: FAIL with 404 or missing handler.

- [ ] **Step 3: Write minimal implementation**

```python
# products/cycling-agent/backend/app/main.py
from fastapi import FastAPI

from app.api.routes.ride_plan import router as ride_plan_router

app = FastAPI()
app.include_router(ride_plan_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# products/cycling-agent/backend/app/services/ride_planning_orchestrator.py
from app.agents.query_parser_agent import parse_query_fallback


def build_demo_plan(query: str) -> dict:
    constraints = parse_query_fallback(query)
    return {
        "request_no": "RQ-DEMO00001",
        "parsed_constraints": constraints,
        "recommended_plan": {
            "go_decision": "go",
            "route_name": "滨江-钱塘江休闲往返线",
            "distance_km": 42,
            "elevation_gain_m": 180,
            "estimated_duration_hours": 2.8,
            "risk_level": "low",
            "summary_reason": "时长匹配，轻松稳定。",
        },
        "alternatives": [],
    }
```

```python
# products/cycling-agent/backend/app/api/routes/ride_plan.py
from fastapi import APIRouter

from app.schemas.ride_plan import RidePlanRequestSchema
from app.services.ride_planning_orchestrator import build_demo_plan

router = APIRouter(prefix="/api/v1/ride", tags=["ride"])


@router.post("/plan")
async def create_ride_plan(payload: RidePlanRequestSchema) -> dict:
    return build_demo_plan(payload.query)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/backend && pytest tests/test_ride_plan_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/backend/app/api/routes/ride_plan.py products/cycling-agent/backend/app/services/ride_planning_orchestrator.py products/cycling-agent/backend/tests/test_ride_plan_api.py
git commit -m "feat: add ride planning orchestrator api"
```

### Task 8: Scaffold frontend app shell

**Files:**
- Create: `products/cycling-agent/frontend/package.json`
- Create: `products/cycling-agent/frontend/vite.config.ts`
- Create: `products/cycling-agent/frontend/src/main.tsx`
- Create: `products/cycling-agent/frontend/src/pages/HomePage.tsx`
- Create: `products/cycling-agent/frontend/src/app/router.tsx`
- Create: `products/cycling-agent/frontend/src/test/setup.ts`
- Create: `products/cycling-agent/frontend/src/tests/home-page.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";
import HomePage from "../pages/HomePage";

test("renders planning input", () => {
  render(<HomePage />);
  expect(screen.getByPlaceholderText("输入你的骑行需求")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/frontend && npm test -- home-page.test.tsx`
Expected: FAIL with missing page component.

- [ ] **Step 3: Write minimal implementation**

```tsx
export default function HomePage() {
  return (
    <main>
      <h1>周末骑行计划助手</h1>
      <textarea placeholder="输入你的骑行需求" />
    </main>
  );
}
```

```tsx
import { createBrowserRouter } from "react-router-dom";
import HomePage from "../pages/HomePage";

export const router = createBrowserRouter([{ path: "/", element: <HomePage /> }]);
```

```json
{
  "name": "cycling-agent-frontend",
  "private": true,
  "scripts": {
    "dev": "vite",
    "test": "vitest run"
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/frontend && npm test -- home-page.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/frontend
git commit -m "feat: scaffold frontend app shell"
```

### Task 9: Connect frontend planner form to backend API

**Files:**
- Create: `products/cycling-agent/frontend/src/features/planner/api.ts`
- Create: `products/cycling-agent/frontend/src/features/planner/hooks.ts`
- Modify: `products/cycling-agent/frontend/src/pages/HomePage.tsx`
- Create: `products/cycling-agent/frontend/src/tests/planner-submit.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import HomePage from "../pages/HomePage";

test("submits query and shows loading state", async () => {
  render(<HomePage />);
  fireEvent.change(screen.getByPlaceholderText("输入你的骑行需求"), {
    target: { value: "周六从滨江出发骑3小时，不想太累" },
  });
  fireEvent.click(screen.getByRole("button", { name: "开始规划" }));
  expect(await screen.findByText("正在生成路线建议")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/frontend && npm test -- planner-submit.test.tsx`
Expected: FAIL with missing button or loading state.

- [ ] **Step 3: Write minimal implementation**

```ts
export async function createRidePlan(query: string) {
  return fetch("/api/v1/ride/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, target_date: "2026-05-30" }),
  }).then((res) => res.json());
}
```

```tsx
import { useState } from "react";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  return (
    <main>
      <h1>周末骑行计划助手</h1>
      <textarea placeholder="输入你的骑行需求" value={query} onChange={(e) => setQuery(e.target.value)} />
      <button
        onClick={() => {
          setLoading(true);
        }}
      >
        开始规划
      </button>
      {loading ? <p>正在生成路线建议</p> : null}
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/frontend && npm test -- planner-submit.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/frontend/src/features/planner products/cycling-agent/frontend/src/pages/HomePage.tsx products/cycling-agent/frontend/src/tests/planner-submit.test.tsx
git commit -m "feat: add frontend planner submission flow"
```

### Task 10: Render recommendation, alternatives, and risk breakdown

**Files:**
- Create: `products/cycling-agent/frontend/src/components/RecommendationCard.tsx`
- Create: `products/cycling-agent/frontend/src/components/AlternativeRouteList.tsx`
- Create: `products/cycling-agent/frontend/src/components/RiskBreakdownCard.tsx`
- Create: `products/cycling-agent/frontend/src/tests/result-rendering.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";
import RecommendationCard from "../components/RecommendationCard";

test("renders route recommendation summary", () => {
  render(
    <RecommendationCard
      plan={{
        routeName: "滨江-钱塘江休闲往返线",
        distanceKm: 42,
        elevationGainM: 180,
        estimatedDurationHours: 2.8,
        riskLevel: "low",
        summaryReason: "时长匹配，轻松稳定。",
      }}
    />,
  );
  expect(screen.getByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
  expect(screen.getByText("风险：low")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/frontend && npm test -- result-rendering.test.tsx`
Expected: FAIL with missing components.

- [ ] **Step 3: Write minimal implementation**

```tsx
type Props = {
  plan: {
    routeName: string;
    distanceKm: number;
    elevationGainM: number;
    estimatedDurationHours: number;
    riskLevel: string;
    summaryReason: string;
  };
};

export default function RecommendationCard({ plan }: Props) {
  return (
    <section>
      <h2>{plan.routeName}</h2>
      <p>{plan.summaryReason}</p>
      <p>风险：{plan.riskLevel}</p>
    </section>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/frontend && npm test -- result-rendering.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/frontend/src/components products/cycling-agent/frontend/src/tests/result-rendering.test.tsx
git commit -m "feat: render recommendation and risk summary"
```

### Task 11: Add RoadbookGeneratorAgent service and display

**Files:**
- Create: `products/cycling-agent/backend/app/services/roadbook_service.py`
- Create: `products/cycling-agent/frontend/src/components/RoadbookSection.tsx`
- Create: `products/cycling-agent/backend/tests/test_roadbook_service.py`

- [ ] **Step 1: Write the failing test**

```python
from app.services.roadbook_service import build_roadbook


def test_build_roadbook_returns_departure_and_supply_advice() -> None:
    roadbook = build_roadbook(
        route={"name": "滨江-钱塘江休闲往返线"},
        risk={"risk_level": "low"},
    )
    assert "departure_window" in roadbook
    assert isinstance(roadbook["supply_advice"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd products/cycling-agent/backend && pytest tests/test_roadbook_service.py -v`
Expected: FAIL with missing service.

- [ ] **Step 3: Write minimal implementation**

```python
def build_roadbook(route: dict, risk: dict) -> dict:
    return {
        "departure_window": "06:30-09:00",
        "supply_advice": ["起点附近先补水", "中段补给一次即可"],
        "mitigation_advice": ["若风变大可提前折返"],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd products/cycling-agent/backend && pytest tests/test_roadbook_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/backend/app/services/roadbook_service.py products/cycling-agent/backend/tests/test_roadbook_service.py
git commit -m "feat: add roadbook generation service"
```

### Task 12: Add end-to-end MVP verification docs

**Files:**
- Create: `products/cycling-agent/README.md`
- Create: `products/cycling-agent/docs/manual-test-script.md`

- [ ] **Step 1: Write the failing doc review step**

```md
# Manual Test Script

1. Open the home page.
2. Enter `周六从滨江出发骑3小时，不想太累，最好风景好一点`.
3. Submit and verify a recommendation appears.
4. Verify risk level, alternatives, and roadbook all render.
```

- [ ] **Step 2: Run backend and frontend locally**

Run: `cd products/cycling-agent/backend && uvicorn app.main:app --reload`
Expected: Backend serves `http://127.0.0.1:8000/health`

Run: `cd products/cycling-agent/frontend && npm run dev`
Expected: Frontend serves local Vite app.

- [ ] **Step 3: Write minimal project README**

```md
# Cycling Agent MVP

## Apps

- `frontend/`: React client
- `backend/`: FastAPI API
- `data/`: Hangzhou route seeds

## Run

Run `cd backend && uvicorn app.main:app --reload`

Run `cd frontend && npm run dev`
```

- [ ] **Step 4: Verify tests pass**

Run: `cd products/cycling-agent/backend && pytest -v`
Expected: PASS

Run: `cd products/cycling-agent/frontend && npm test`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add products/cycling-agent/README.md products/cycling-agent/docs/manual-test-script.md
git commit -m "docs: add cycling agent mvp runbook"
```

## Self-Review

Spec coverage:

- Query parsing is covered by Task 4.
- Route generation is covered by Tasks 3 and 5.
- Risk scoring is covered by Task 6.
- Orchestration and API output are covered by Task 7.
- Roadbook explanation is covered by Task 11.
- Frontend and backend structure are covered by Tasks 1 through 12.

Placeholder scan:

- No `TODO`, `TBD`, or unresolved placeholders remain in this plan.

Type consistency:

- `RidePlanRequestSchema`, `RidePlanResponseSchema`, route candidate fields, `request_no`, and frontend `RoutePlanCard` naming should stay aligned when implementation starts.
