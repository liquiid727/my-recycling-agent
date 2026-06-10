# SpecOS Agent Instructions

## Project Intent

SpecOS is a Spec-Driven AI IDE. Agents must treat specs, rules, tests, and generated artifacts as one traceable delivery chain instead of isolated files.

## Source Of Truth

Read context in this order before changing behavior:

1. `README.md` or `readme.md` for product intent.
2. `rules/` and `.rules/` for engineering governance.
3. `spec-draft/` for human-authored draft intent.
4. `specs/current/` for accepted, normalized spec bundles.
5. `tests/` for scenario, API, and UI verification assets.
6. `ai/agents/` and `.agents/` for role-specific responsibilities.

## Required Workflow

- Start from an accepted spec or clearly state that the work is draft-only.
- Keep every generated artifact traceable to a spec, draft, or rule.
- Prefer small, reviewable changes over broad rewrites.
- Do not overwrite human-authored drafts, specs, reports, or review notes unless explicitly asked.
- If a requirement is ambiguous, record the assumption or ask before implementation.
- For user-facing flows, cover empty, loading, success, and failure states.
- For backend/API changes, include error semantics, migration impact, and test coverage notes.

## Repository Boundaries

- `rules/`: canonical reusable rule documents.
- `.rules/`: agent-facing rule index and execution policy.
- `ai/`: prompt, workflow, agent, and reviewer assets for SpecOS orchestration.
- `.agents/`: local agent manifests and role routing for coding assistants.
- `.codex/`: Codex-specific local configuration and operating notes.
- `spec-draft/`: draft inputs that may still be incomplete or exploratory.
- `specs/`: normalized spec workspace with `current/`, `changes/`, and `archive/`.
- `tests/`: spec-driven verification assets and scenario test templates.
- `spec-web-ui/`: Next.js UI for SpecOS.

## Coding Standards

- Keep changes aligned with existing style and file organization.
- Do not add new dependencies without a clear reason and lockfile update.
- Do not commit secrets, provider keys, tokens, generated caches, or local machine paths.
- Use stable names for flows, scenarios, error codes, and generated artifacts.
- Prefer explicit schemas and examples over implicit conventions.

## Validation

- For `spec-web-ui/`, use `npm run test` and `npm run build` from `spec-web-ui/` when relevant.
- For spec/rule changes, verify cross-links and naming consistency manually.
- For generated tests or contracts, keep the command or workflow that produced them documented.

## Communication

- Summaries should name changed files and the spec/rule they support.
- Call out unresolved questions, assumptions, and skipped validation.
- Do not claim completion without evidence from file inspection, tests, or explicit manual verification.
