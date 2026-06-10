# Architecture Review

## Decision

Use the active change package as the coordination boundary and add `routing-summary.json` as the machine-readable split between execution routing and independent testing.

## Rationale

- `specs/current/` remains the accepted baseline.
- `specs/changes/<change-id>/` holds proposed deltas and all lifecycle evidence.
- `routing-summary.json` records selected execution routes before implementation work starts.
- `tests/plans/` and `tests/schedules/` remain the semantic independent-test contracts after implementation review passes.

## Boundaries

- Core owns schema-level validation and deterministic artifact builders.
- CLI or local scripts may validate workflow assets and generated test artifacts.
- Agents remain documented role contracts until a future runtime can dispatch them directly.

## Risks

- Markdown specs are still descriptive inputs; a future runtime must translate them into executable dispatch payloads.
- UI design remains a conditional stage, so `design-review.md` can be marked `not-applicable`.
- Unit tests stay in execution tracks because they require implementation context.
- Parallel execution is represented in route metadata before the workflow runner supports native parallel steps.
