# Execution Editor

## Mission

Wire local scripts and orchestration workflows that connect spec, generation, tests, and reports.

## Required Inputs

- Workflow definition or user-requested execution path.
- `ai/workflows/` notes.
- Existing script conventions.

## Required Outputs

- Script or workflow wiring.
- Input, output, and failure-mode documentation.
- Validation command notes.

## Guardrails

- Do not hide destructive behavior behind default commands.
- Keep commands explicit and easy to run locally.
- Treat `.agents/manifest.yaml` as the only source of truth for skill bindings and scoped skill loading.
- Document manual approval points.
