# Architecture Context

## Status

This file records accepted architecture facts and placement rules for the
cycling-agent product. Proposed architecture changes should begin under
`specs/changes/<change-id>/` and be promoted here only after acceptance.

## Runtime Architecture

The accepted runtime is a web application with:

- a FastAPI backend in `products/cycling-agent/backend/`
- a React + Vite frontend in `products/cycling-agent/frontend/`
- Hangzhou-first JSON seed data in `products/cycling-agent/data/`
- optional external providers for weather, route, POI, and LLM integration

The backend remains the orchestration center. The frontend gathers user input,
shows clarification and planning progress, and renders result or admin views.

## Canonical Planning Model

The accepted planning model is still a single orchestrator with deterministic
decision logic:

- one orchestrator: `RidePlanningOrchestrator`
- one parsing stage that can use deterministic fallback or optional LLM parsing
- deterministic route or trip candidate discovery
- deterministic risk scoring
- deterministic decision ranking
- explanatory roadbook generation from structured facts

The current baseline must not be described as a free-form multi-agent runtime.

## Supported Planning Paths

The current product exposes two user-facing scenes and two implementation paths:

- `planning_scene=city_ride` usually maps to `planning_mode=route`
- `planning_scene=weekend_trip` usually maps to `planning_mode=nearby_trip`

These are compatibility and product-boundary facts. New accepted behavior should
preserve the distinction unless an explicit accepted change removes it.

## Backend Boundaries

Accepted backend module boundaries:

- `agents/`: query parsing and chat-turn logic
- `api/routes/`: HTTP and SSE endpoints
- `core/`: config, ids, storage, cache
- `providers/`: weather, route, POI, and LLM adapters
- `repositories/`: persistence and seed-backed data access
- `schemas/`: request, response, admin, and audit payload shapes
- `services/`: orchestration, route matching, nearby-trip planning, roadbook,
  city strategy, and risk scoring

Business ranking, risk, and final recommendation selection remain backend-owned.

## Data And Infrastructure Boundaries

- Default local baseline: SQLite plus in-memory cache
- Optional live infrastructure: PostgreSQL plus Redis
- Default weather: Open-Meteo with fallback snapshot behavior
- Default route and POI enrichment: local or template-backed behavior, with
  optional AMap-backed enhancement
- Optional LLM integration: OpenAI-compatible API shape, with deterministic
  fallback when configuration is absent or timing out

Seed data is part of the accepted runtime boundary. Route, destination, and trip
templates are not incidental fixtures; they are core planning inputs.

## Frontend Boundaries

The frontend owns:

- request entry and clarification UX
- planning progress and fallback display
- plan result pages and route detail views
- profile editing
- admin maintenance surfaces for route, destination, trip, strategy, and risk
  rule data

The frontend must not silently replace backend decision semantics with client
side ranking logic.

## Repository Placement Rules

- Accepted product code lives under `products/cycling-agent/`.
- Accepted product baseline facts live under `specs/current/`.
- New requirements start in `spec-draft/` and active accepted change work lives
  in `specs/changes/`.
- `tests/` holds spec-driven verification assets and schemas.
- `.agents/manifest.yaml` defines workflow routing and role context, but it does
  not replace accepted product architecture facts.

## Verification And Promotion Rule

Architecture facts may be promoted into `specs/current/` only after there is
evidence from at least one of:

- runnable code under `products/cycling-agent/`
- automated backend or frontend tests
- accepted operator-facing documentation that matches the real implementation
- explicit manual verification scripts where automation is not yet available

## Current Accepted Limitations

- Dynamic route discovery exists, but Hangzhou template and seed data still
  anchor the product's quality floor.
- Optional provider integrations do not change the accepted fallback boundary:
  the system must continue to degrade honestly when live dependencies are
  missing or fail.
- The spec workflow assets in `.agents/`, `.specos/`, and `ai/workflows/` remain
  governance tools around the product, not the product runtime itself.
