# Current Specs

Accepted, active baseline facts for the cycling-agent product live here.

This directory is the current accepted source of truth for the real product in
`products/cycling-agent/`. It should describe behavior, boundaries, and
terminology that already exist in the repository and are supported by runnable
code, tests, or explicit operator documentation.

Do not update `specs/current/` at the start of a new requirement. New work
should start in `spec-draft/`, move into `specs/changes/<change-id>/`, and be
promoted here only after implementation, verification, and review evidence are
available.

## Baseline Context Files

- `project-context.md`: accepted product intent, active surfaces, source-of-truth order, and promotion evidence rules.
- `architecture-context.md`: accepted runtime architecture, module boundaries, delivery chain, and repository placement rules.
- `domain-context.md`: accepted cycling-agent domain language, planning scenes, core entities, response semantics, and guardrails.
- `agent-asset-map.md`: accepted index for Domain Map, Rule Library, Knowledge Base, and Golden Dataset.
- `agent-asset-index.json`: machine-readable index for the same four asset layers.

## Current Scope

The accepted baseline currently covers:

- the FastAPI + React/Vite cycling-agent MVP in `products/cycling-agent/`
- two supported planning scenes: `city_ride` and `weekend_trip`
- two implementation paths: `planning_mode=route` and `planning_mode=nearby_trip`
- Hangzhou-first route, destination, and trip-template seed data
- current backend, frontend, admin, audit, and verification surfaces

Supporting reference documents under `docs/product/`, `docs/technical/`, and
`docs/plans/` can explain intent and design history, but they do not outrank the
accepted facts recorded here.
