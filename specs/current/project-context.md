# Project Context

## Status

This file records accepted project-level facts for the cycling-agent repository
as it exists today. Use it as the baseline together with any active change
package under `specs/changes/`.

## Product Intent

This repository's primary runnable product is the Hangzhou-first cycling-agent
MVP in `products/cycling-agent/`.

The product helps a rider start from a short natural-language request and
receive a decision-first cycling plan with route or trip recommendations, risk
assessment, and explanatory guidance.

The current accepted product supports two user-facing planning scenes:

- `city_ride`: same-day or same-evening city riding from a concrete start point
  with a limited time budget
- `weekend_trip`: nearby weekend or holiday riding plans that may span one to
  three days and may require overnight planning

## Accepted Product Surfaces

- Backend API: FastAPI planning, route catalog, profile, admin, chat-turn, and
  audit endpoints under `products/cycling-agent/backend/app/`
- Frontend web app: React + Vite user and admin surfaces under
  `products/cycling-agent/frontend/`
- Seed data: Hangzhou route, nearby destination, and trip-template JSON assets
  under `products/cycling-agent/data/`
- Operator docs: runnable implementation and manual verification notes under
  `products/cycling-agent/docs/`

## Current Delivery Chain

New work in this repository should follow:

```text
raw requirement
-> spec-draft/
-> specs/changes/<change-id>/
-> implementation in products/cycling-agent/ and related tests
-> review and validation evidence
-> specs/current/
-> specs/archive/<change-id>/
```

`specs/current/` is the accepted baseline, not the first write target.

## Source Of Truth Order

Unless a role-specific manifest narrows the scope, load context in this order:

1. `README.md`
2. `.rules/` and `rules/`
3. `specs/current/`
4. active `specs/changes/<change-id>/`
5. `products/cycling-agent/docs/current-implementation-overview.md`
6. `products/cycling-agent/` code and tests
7. `tests/` for spec-driven verification assets
8. `spec-draft/` for new intake and unaccepted work
9. `ai/agents/` and `.agents/` for workflow and role routing

## Supporting Versus Accepted Docs

- `docs/product/`, `docs/technical/`, and `docs/plans/` are supporting
  references for intent, design, and rollout history.
- `docs/design/` is historical and exploratory material. It may contain useful
  early domain ideas, but it is not the accepted baseline for current product
  behavior.
- `products/cycling-agent/docs/current-implementation-overview.md` is the
  accepted operator-facing implementation map until a newer accepted change
  explicitly replaces it.

## Promotion Evidence Rule

Content should be promoted into `specs/current/` only when all of the following
are true:

- the behavior exists in runnable backend or frontend code, or in accepted
  operator-facing repository assets
- the affected tests or manual verification steps are recorded and reproducible
- terminology matches the current API schemas, route data, and UI copy closely
  enough to avoid dual meanings
- any remaining limitations are stated explicitly instead of hidden behind draft
  language

## Current Known Baseline Constraints

- Hangzhou is the only fully seeded city in the current baseline.
- The system is a planning and decision product, not a professional training
  platform.
- Route and trip recommendations remain deterministic at their core even when
  optional LLM providers are configured.
- The spec workflow skeleton exists in this repository, but accepted truth must
  always resolve back to the real cycling-agent product rather than to a generic
  SpecOS meta-example.
