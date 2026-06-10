# Project Context

## Status

This file records accepted project-level facts for SpecOS. Agents may use it as baseline context together with active change packages under `specs/changes/`.

## Product Intent

SpecOS is a spec-driven AI IDE for engineering and business-system delivery. Its core asset is a structured, reusable Spec that keeps requirements, implementation, tests, documentation, review, and delivery evidence aligned.

The system should help teams move work through this chain:

```text
raw requirement
-> spec-draft/
-> specs/changes/<change-id>/
-> development, tests, review, and reports
-> specs/current/
-> specs/archive/<change-id>/
```

## Core Principles

- Specs are the coordination protocol across agents, code, tests, and delivery artifacts.
- `specs/current/` is the accepted system baseline, not the first write target for new requirements.
- `specs/changes/<change-id>/` is the working area for proposed or in-progress changes.
- Human-authored drafts, review notes, reports, and task files must not be overwritten without explicit approval.
- Every meaningful output should cite the spec, draft, rule, or workflow it uses.

## Current Product Surfaces

- CLI: initializes and checks SpecOS project skeletons, validates and installs bundles, and lists or runs workflows.
- `spec-web-ui`: catalogs rules, templates, agent roles, workflows, and test patterns; creates project workspaces; edits drafts; exports bundle snapshots.
- `test-console`: reads prepared test plans, triggers runners, and visualizes normalized test results.
- Agent assets: define scoped roles, prompts, routing metadata, rules, and workflow contracts.

## Source Of Truth Order

Agents should load context in this order unless a role-specific manifest narrows the scope:

1. Repository README.
2. `.rules/` and `rules/`.
3. `spec-draft/`.
4. `specs/current/`.
5. `specs/changes/`.
6. `tests/`.
7. `ai/agents/` and `.agents/`.

## Open Questions

- Which business-domain sample should become the first complete end-to-end reference bundle?
- Which workflow runner responsibilities belong in the CLI versus host agent runtime?
