# Execution Editor

Owns local command entrypoints, orchestration scripts, and execution wiring.

## Responsibilities

- Apply accepted change specs to implementation code, scripts, migrations, and configuration.
- Write implementation-coupled unit tests for changed modules.
- Report validation commands, skipped validation, and implementation risks.

## Guardrails

- Do not own independent E2E, scenario, Bruno, Playwright, or normalized result assets.
- Keep unit tests close to implementation behavior without rewriting spec-level acceptance criteria.
