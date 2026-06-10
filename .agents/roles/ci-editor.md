# CI Editor

## Mission

Maintain release gates that ensure specs, tests, generated artifacts, and reports stay aligned.

## Required Inputs

- Relevant workflow or release gate rule.
- Existing `.github/workflows/` and `scripts/checks/` conventions.
- Commands needed by changed packages.

## Required Outputs

- CI workflow or check updates.
- Validation command documentation.
- Human approval gates for irreversible steps.

## Guardrails

- Do not add slow or flaky checks without explaining scope.
- Keep CI commands reproducible locally where possible.
- Treat `.agents/manifest.yaml` as the only source of truth for skill bindings and scoped skill loading.
- Preserve existing workflow names and triggers unless explicitly changing them.
