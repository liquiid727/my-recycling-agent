# Spec Change Agent Workflow

## Meta

- Domain: `specos`
- Feature: `spec-change-agent-workflow`
- Source Draft: direct user clarification in current Codex thread
- Status: proposed

## Goal

Make every new requirement move through a traceable lifecycle from request intake to accepted current state, with explicit spec-draft, architecture/design, spec-change, execution routing, implementation review, independent testing, final review, promotion, and archive stages.

## Non-Goals

- This change does not implement a generic hosted agent runtime.
- This change does not make UI/Playwright execution mandatory in the first API-focused runner phase.
- This change does not allow new requirements to update `specs/current/` before review, test, and acceptance evidence exists.

## Lifecycle

1. A request enters `spec-draft-agent`, which classifies it and records or updates `spec-draft/`.
2. `spec-draft-agent` normalizes the draft into structured intent, assumptions, open questions, stable vocabulary, and a `change-id` suggestion.
3. `architecture-agent` reviews system impact, dependencies, migration implications, and execution routes.
4. `ui-design-agent` runs only when the request affects frontend, interaction, or user-facing states; otherwise `design-review.md` is marked `not-applicable`.
5. `spec-agent` reads `specs/current/` and creates `specs/changes/<change-id>/` for the proposed delta.
6. `execution-routing` selects one or more isolated tracks:
   - `frontend-execution-agent`
   - `backend-execution-agent`
   - `migration-execution-agent`
7. `reviewer` performs an `implementation_gate` before independent test planning starts.
8. `test-editor` generates independent verification plans and routes framework-specific test agents without reading execution-private notes.
9. `reviewer` performs a `final_gate` after independent testing.
10. After implementation and tests pass, `spec-agent` records the changelog, promotes accepted facts into `specs/current/`, and archives the change.

## Change Package Shape

Each active change should keep its lifecycle evidence in one directory:

```text
specs/changes/<change-id>/
  spec.md
  architecture-review.md
  design-review.md
  execution-plan.md
  routing-summary.json
  implementation-report.frontend.md
  implementation-report.backend.md
  implementation-report.migration.md
  review-report.implementation.md
  review-report.final.md
  test-result-summary.md
  changelog.md
```

`spec.md` is the coordination contract. Other files record the agent outputs and gate evidence derived from that contract.

## Agent Boundaries

### Spec Draft Agent

- Owns request classification, draft normalization, stable terminology, and `change-id` suggestion.
- Must not treat raw requests as accepted spec language or bypass draft creation for new requirements.

### Architecture Agent

- Reviews domain boundaries, system impact, migration impact, contracts, risk, and execution routes before implementation and testing split.
- Produces `architecture-review.md`.

### Design Agent

- Reviews user behavior, UI states, scenario vocabulary, and user-facing acceptance language when the change touches frontend or interaction behavior.
- Produces `design-review.md`, or `not-applicable` when skipped by workflow condition.

### Spec Agent

- Owns change package creation, changelog maintenance, promotion into `specs/current/`, and archive handoff.
- Must not replace implementation, test, architecture, or design review outputs with unstated assumptions.

### Frontend / Backend / Migration Execution Agents

- Own implementation artifacts and implementation-coupled unit tests per selected route.
- Allowed inputs: current specs, active change spec, architecture review, design review, explicit implementation plan.
- Forbidden inputs: independent E2E/scenario/API/UI test implementation details, generated independent test assertions, raw independent test result explanations.
- Produce route-specific implementation reports.
- May produce unit-test files under `tests/unit/` or existing module-local test paths.

### Test Agent

- `test-editor` owns independent test-plan, test-schedule, API/UI/scenario test assets, real execution routing, and normalized result mapping.
- Allowed inputs: current specs, active change spec, OpenAPI/API contract, user flows, acceptance conditions, rules.
- Forbidden inputs: implementation explanations, source-code strategy notes, execution-agent private assumptions.
- Produces test plan artifacts, test assets, and `test-result-summary.md`.
- Does not own implementation-coupled unit tests.

### Review Agents

- Evaluate evidence after implementation and test outputs exist.
- `implementation_gate` produces `review-report.implementation.md`.
- `final_gate` produces `review-report.final.md`.
- Must report blockers in business-flow language and link them to spec scenarios, rules, or acceptance criteria.

## Routing Contract

`routing-summary.json` records the split between execution and testing:

- `selectedRoutes[]`: any combination of `frontend`, `backend`, `migration`.
- `executionMode`: `parallel` or `test-after-execution`.
- `reasoning[]`: why each route was selected.
- `handoffArtifacts[]`: files required by execution and test stages.
- `gates[]`: required states before promotion and archive.

The execution track may write implementation-coupled unit tests under `tests/unit/` or module-local test paths. It must not write independent verification assets under `tests/bruno/`, `tests/scenarios/`, `tests/e2e/`, `tests/playwright/`, or `tests/results/`. The testing track must not write implementation source paths or unit tests.

## First Implementation Slice

The first implementation slice provides:

- Lifecycle metadata in `.specos/workflows/spec-driven-default.yaml`
- Role boundaries in `.agents/manifest.yaml`
- A human-readable workflow contract in `ai/workflows/spec-driven-request-lifecycle.md`
- Example change-package shape with route summaries and dual review gates
- Validation that the workflow assets stay aligned

Real API runner integration can consume this schedule in the next slice without changing the lifecycle contract.
