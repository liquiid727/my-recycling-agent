# Cycling-Agent Asset Map

## Purpose

This file is the human-readable master index for the four core cycling-agent
asset layers:

- Domain Map
- Rule Library
- Knowledge Base
- Golden Dataset

Use this file to answer two questions quickly:

1. Which repository assets are currently accepted truth?
2. Which assets are only supporting reference or exploratory material?

## Layer Status

| Layer | Status | Primary accepted assets | Main gap |
| --- | --- | --- | --- |
| Domain Map | partial | `specs/current/domain-context.md`, `specs/current/architecture-context.md`, `docs/technical/04-technical-spec.md` | no single normalized domain package for CIM + rules + entities |
| Rule Library | partial | `.rules/project.md`, `.rules/rule-map.yaml`, `.agents/manifest.yaml`, `rules/` | business ride rules still split across docs and code |
| Knowledge Base | partial | `products/cycling-agent/data/*.json`, backend repositories and services | missing versioning, provenance, and city-expansion contract |
| Golden Dataset | baseline added | `tests/plans/cycling-agent-mvp.test-plan.json`, `tests/scenarios/cycling-agent-golden-dataset.yaml`, `tests/results/cycling-agent-mvp.scenario-result.example.json` | not yet wired to one accepted automated runner |

## Accepted Assets

### 1. Domain Map

Accepted baseline:

- `specs/current/project-context.md`
- `specs/current/architecture-context.md`
- `specs/current/domain-context.md`

Accepted supporting design references:

- `docs/technical/03-technical-architecture.md`
- `docs/technical/04-technical-spec.md`
- `products/cycling-agent/docs/current-implementation-overview.md`

Exploratory or historical inputs:

- `docs/design/03-domain-model.md`
- `docs/design/04-decision-tree.md`
- duplicated early design files under `docs/design/`

### 2. Rule Library

Accepted governance and routing:

- `.rules/project.md`
- `.rules/rule-map.yaml`
- `.agents/manifest.yaml`
- `.agents/roles/`
- `ai/agents/`
- `rules/backend/`
- `rules/frontend/`
- `rules/shared/`
- `rules/ci/`

Accepted business-rule execution surfaces:

- `products/cycling-agent/backend/app/agents/query_parser_agent.py`
- `products/cycling-agent/backend/app/services/risk_scoring_service.py`
- `products/cycling-agent/backend/app/services/city_strategy_service.py`
- `products/cycling-agent/backend/app/services/ride_planning_orchestrator.py`

### 3. Knowledge Base

Accepted seed knowledge:

- `products/cycling-agent/data/hangzhou_routes.json`
- `products/cycling-agent/data/hangzhou_nearby_destinations.json`
- `products/cycling-agent/data/hangzhou_trip_templates.json`

Accepted consumption surfaces:

- `products/cycling-agent/backend/app/repositories/route_template_repository.py`
- `products/cycling-agent/backend/app/repositories/nearby_trip_repository.py`
- `products/cycling-agent/backend/app/services/ride_planning_orchestrator.py`

Accepted operator-facing references:

- `docs/technical/07-hangzhou-route-seed-table.md`
- `products/cycling-agent/docs/current-implementation-overview.md`

### 4. Golden Dataset

Accepted baseline assets:

- `tests/plans/cycling-agent-mvp.test-plan.json`
- `tests/scenarios/cycling-agent-golden-dataset.yaml`
- `tests/results/cycling-agent-mvp.scenario-result.example.json`

Accepted concrete validation sources that the golden layer points to:

- `products/cycling-agent/backend/tests/test_query_parser_agent.py`
- `products/cycling-agent/backend/tests/test_ride_plan_api.py`
- `products/cycling-agent/backend/tests/test_chat_turn_api.py`
- `products/cycling-agent/backend/tests/test_nearby_trip_api.py`
- `products/cycling-agent/backend/tests/test_provider_fallback_api.py`
- `products/cycling-agent/docs/manual-test-script.md`

## Directory Policy

- `specs/current/`: accepted baseline facts and accepted asset index
- `.rules/`, `rules/`, `.agents/`, `ai/agents/`: accepted governance and role routing
- `products/cycling-agent/data/`: accepted seed knowledge used by the live product
- `tests/`: accepted golden/test-plan/result assets
- `docs/product/`, `docs/technical/`, `docs/plans/`: supporting references
- `docs/design/`: exploratory and historical, not current source of truth

## Update Rules

- Add or move accepted assets here only after they are supported by runnable
  code, repository-owned tests, or explicit operator evidence.
- When a supporting or exploratory asset becomes accepted truth, update both
  this file and `agent-asset-index.json`.
- Do not add placeholder domains or fake runners to any of the four layers.
