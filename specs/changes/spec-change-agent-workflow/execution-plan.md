# Execution Plan

## Scope

Implement the first slice of the spec-change request lifecycle workflow:

- Lifecycle role boundaries in `.agents/manifest.yaml`.
- Lifecycle stage metadata in `.specos/workflows/spec-driven-default.yaml`.
- Documented request lifecycle and dual review gates.
- Example active change package showing the route summary and report outputs.
- Local validation command that checks the workflow assets stay aligned.

## Commands

Validate the lifecycle assets:

```bash
node scripts/checks/validate-spec-driven-lifecycle.mjs
```

Run the contract test suite:

```bash
node --test scripts/checks/spec-driven-request-lifecycle.test.mjs
```

## Expected Outputs

- Updated `.agents/manifest.yaml` with lifecycle roles, request classes, route definitions, and reviewer gate modes.
- Updated `.specos/workflows/spec-driven-default.yaml` with lifecycle stages, gates, route combinations, and validation steps.
- `ai/workflows/spec-driven-request-lifecycle.md`
- `specs/changes/spec-change-agent-workflow/routing-summary.json`
- `implementation-report.frontend.md`
- `implementation-report.backend.md`
- `implementation-report.migration.md`
- `review-report.implementation.md`
- `review-report.final.md`
- `test-result-summary.md`

Execution tracks can write implementation-coupled unit tests such as `tests/unit/<spec-id>/`. Execution tracks cannot write independent verification directories such as `tests/bruno/`, `tests/scenarios/`, `tests/e2e/`, `tests/playwright/`, or `tests/results/`. Testing tracks cannot write implementation source or unit-test paths.
