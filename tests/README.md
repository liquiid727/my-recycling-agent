# Tests

Spec-driven verification assets live here.

## Expected Layers

- `tests/plans/`: spec-derived `test-plan` artifacts that define endpoints, scenarios, branches, and preconditions.
- `tests/plans/`: spec-derived `test-plan` artifacts that define business flows, stages, endpoints, scenarios, branches, and preconditions.
- `tests/schedules/`: generated agent routing schedules that split execution work, implementation-coupled unit tests, and independent testing work.
- `tests/results/`: normalized `scenario-result` artifacts that the independent test console consumes.
- `tests/bruno/`: API request collections and HTTP assertions derived from accepted specs.
- `tests/scenarios/`: business-flow and E2E scenario assets.

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

For active changes, generate `test-plan` and `test-schedule` artifacts from the normalized spec before assigning implementation and testing tasks.

```bash
node packages/cli/dist/main.js generate-test-plan specs/changes/<change-id>/spec.json --change <change-id>
```

The generated schedule records two separate tracks:

- `execution`: implementation-only work, owned by the execution agent.
- `testing`: spec-and-contract-only work, owned by test agents.

Execution tasks may write implementation-coupled unit tests under `tests/unit/` or existing module-local test paths. Execution tasks must not write independent verification assets under `tests/bruno/`, `tests/scenarios/`, `tests/e2e/`, `tests/playwright/`, or `tests/results/`. Test tasks must not write implementation source paths or unit-test assets.

## API Execution

API tests run through the CLI after a plan and schedule exist:

```bash
node packages/cli/dist/main.js generate-bruno-tests <specId>
node packages/cli/dist/main.js run-api-tests <specId>
```

`generate-bruno-tests` writes deterministic Bruno assets under `tests/bruno/<specId>/` from the test plan.

`run-api-tests` reads `tests/bruno/<specId>/` as the API execution asset location. If the Bruno collection or execution adapter is missing, it writes a blocked normalized result under `tests/results/` and exits non-zero so release gates can stop honestly.

Projects can bind a real adapter explicitly:

```bash
node packages/cli/dist/main.js run-api-tests <specId> --command "bru run tests/bruno/<specId>"
```

The adapter command is the boundary between generated test assets and concrete local execution. Its stdout, stderr, and exit code are captured into the normalized result.
