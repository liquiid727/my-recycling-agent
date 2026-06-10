# Domain Context

## Status

This file records accepted domain language and bounded-context guidance for SpecOS itself. Feature-specific domain analysis should live under `specs/changes/<change-id>/` until accepted.

## Core Domain Language

- Spec: the shared engineering contract for product intent, flows, rules, exceptions, APIs, data, UI, tests, observability, and acceptance.
- Draft: an engineer- or product-authored input that captures intent before formal spec normalization.
- Change: a bounded proposed update that is developed and reviewed against `specs/current/`.
- Bundle: a portable set of rules, templates, agent roles, workflows, tests, or generated assets.
- Agent role: a scoped responsibility definition used to produce or review one category of artifact.
- Workflow: an orchestration contract that connects inputs, agent roles, outputs, validation gates, and human approval points.
- Test plan: a normalized verification plan mapped to spec scenarios and acceptance criteria.
- Result: normalized evidence from API, scenario, UI, or specialized checks.

## Bounded Contexts

- Spec Workspace: owns draft, current, change, archive, spec rules, and spec templates.
- Agent Orchestration: owns role manifests, canonical agent descriptions, prompt assembly, scoped skills, and routing rules.
- Rule Catalog: owns reusable governance documents and compact rule indexes.
- Bundle Catalog: owns selectable assets and exportable project bundles.
- Test Verification: owns test plans, scenarios, runners, results, and report surfaces.
- UI Workbench: owns `spec-web-ui` project workspace, draft editing, discovery, and export flows.
- CLI Runtime: owns project initialization, skeleton checks, bundle validation, bundle installation, and workflow command entrypoints.

## Domain Guardrails

- Do not introduce new domain terms without mapping them to existing user-facing language.
- Keep agent orchestration concepts separate from accepted spec facts.
- Keep generated artifacts traceable to a draft, spec, change, rule, workflow, or explicit user request.
- Surface unclear ownership as an open question instead of hiding it behind generic services.

## Open Questions

- Should bundle selection and project workspace management remain a UI Workbench concern, or become a first-class CLI workflow concern?
- Which SpecOS domain should own long-lived memory and context snapshots?
