# Tests

Spec-driven verification assets for the cycling-agent repository live here.

## Expected Layers

- `tests/plans/`: normalized `test-plan` artifacts that define business flows,
  endpoints, scenarios, branches, and preconditions for the cycling-agent
  product.
- `tests/schedules/`: generated agent routing schedules that split execution work, implementation-coupled unit tests, and independent testing work.
- `tests/results/`: normalized `scenario-result` artifacts that the independent test console consumes.
- `tests/bruno/`: API request collections and HTTP assertions derived from accepted specs.
- `tests/scenarios/`: business-flow, golden-dataset, and E2E scenario assets.

## Current Repository Baseline

The current real baseline should center on:

- city-ride clarification and successful plan generation
- weekend-trip clarification and successful nearby-trip plan generation
- no-match and provider fallback behavior
- normalized result examples that reflect actual cycling-agent endpoints and
  flow names

Do not keep unrelated example business domains here once repository-owned
cycling-agent assets exist.

## Result Model

The report UI must consume normalized results instead of framework-specific output. Every test run should be traceable to:

- `spec_id`
- `spec_version`
- `run_id`
- `test_type`
- `status`
- `summary`
- `evidence`

## V1 Scope

The first release focuses on API and Scenario/E2E verification. Unit and specialized checks are reserved in the model so the report UI can expand without changing the core schema.

## Agent Isolation

For active changes, derive or update `test-plan` and `test-schedule` artifacts
from the normalized spec before assigning implementation and testing tasks.

The generated schedule records two separate tracks:

- `execution`: implementation-only work, owned by the execution agent.
- `testing`: spec-and-contract-only work, owned by test agents.

Execution tasks may write implementation-coupled unit tests under `tests/unit/` or existing module-local test paths. Execution tasks must not write independent verification assets under `tests/bruno/`, `tests/scenarios/`, `tests/e2e/`, `tests/playwright/`, or `tests/results/`. Test tasks must not write implementation source paths or unit-test assets.

## Execution Boundary

This repository does not currently treat `packages/cli/dist/main.js` as a live
accepted execution path. Until a real generator or runner is accepted here,
test-plan and golden-dataset assets should be maintained as repository-owned
artifacts and mapped to concrete commands manually.

Current concrete validation surfaces include:

- backend API and service tests under `products/cycling-agent/backend/tests/`
- frontend tests under `products/cycling-agent/frontend/src/tests/`
- manual scripts in `products/cycling-agent/docs/manual-test-script.md`

Normalized result examples under `tests/results/` should describe how these
concrete validations map back to flows and scenarios.
