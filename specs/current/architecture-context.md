# Architecture Context

## Status

This file records accepted architecture facts and placement rules for SpecOS. Proposed architecture changes should start under `specs/changes/<change-id>/` and be promoted here only after acceptance.

## Architectural Model

SpecOS uses a current/change/archive model for formal system knowledge:

- `specs/current/`: accepted baseline facts.
- `specs/changes/<change-id>/`: proposed changes and active implementation context.
- `specs/archive/<change-id>/`: completed changes after accepted content has been merged into `current`.

Agent work is routed through `.agents/manifest.yaml`. The manifest defines role prompts, canonical agent descriptions, scoped skills, context includes, owned surfaces, and expected outputs.

## Agent Context Boundaries

- `.agents/roles/` contains local role execution contracts.
- `ai/agents/` contains canonical agent responsibilities.
- `.agents/manifest.yaml` is the routing and context assembly source of truth.
- Role prompts should describe how an agent works; they should not duplicate project background or accepted system facts.
- Stable project, architecture, and domain context belongs under `specs/current/`.

## Workflow Boundaries

- `spec-draft/` captures early human-authored intent and exploratory requirements.
- `specs/changes/<change-id>/` captures normalized active work, assumptions, design notes, generated artifacts, and review evidence for a bounded change.
- `tests/` captures scenario, API, UI, result, and test-plan assets tied to specs.
- `ai/workflows/` documents orchestration flows that connect prompts, agent roles, review stages, and gates.
- `rules/` and `.rules/` define reusable governance and compact agent-facing rule entrypoints.

## Promotion Rule

Agents should not write directly to `specs/current/` for new work. Promote content into `specs/current/` only after the related change has implementation, test, review, and acceptance evidence.

## Open Questions

- How much workflow execution should be encoded as YAML versus implemented by the host runtime?
- Which normalized artifact schemas should be required before a change can be promoted?
