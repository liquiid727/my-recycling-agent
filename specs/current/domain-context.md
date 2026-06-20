# Domain Context

## Status

This file records accepted domain language and bounded-context guidance for the
cycling-agent product. Feature-specific domain analysis should live under
`specs/changes/<change-id>/` until accepted.

## Core Product Language

- Rider request: a natural-language planning request plus optional structured
  constraints and profile hints
- Planning scene: the user-facing intent class of a request; current accepted
  values are `city_ride` and `weekend_trip`
- Planning mode: the implementation path used by the backend; current accepted
  values are `route` and `nearby_trip`
- Clarification: a follow-up prompt emitted when key planning constraints are
  missing
- Route template: a reusable route candidate with distance, elevation, time,
  risk-relevant attributes, supply facts, and local notes
- Nearby destination: a destination-oriented fact record used by weekend-trip
  planning
- Trip template: a reusable multi-hour or multi-day trip pattern that connects
  route and destination facts
- Weather snapshot: normalized weather facts for a planning date and region
- Risk assessment: structured weather, climb, traffic, supply, return, and
  crowd risk evidence
- Decision summary: the user-facing recommendation outcome such as `go`,
  `caution`, or `no_go`, with reasons and advice
- Roadbook: explanatory guidance derived from accepted structured facts
- Tool trace: a normalized summary of stage execution and fallback behavior
- Planning audit: persisted request, weather, risk, and decision records used
  for debugging and review

## Accepted Planning Scenes

### `city_ride`

This scene covers same-day or same-evening city riding where the main questions
are:

- should I go today
- from where should I start
- how long or how far should I ride
- which route best matches current time, effort, and conditions

### `weekend_trip`

This scene covers nearby leisure or holiday riding plans where the main
questions are:

- whether the trip is worth arranging
- which direction or destination is most suitable
- whether one day, two days, or three days fit best
- whether overnight planning, return options, and equipment are acceptable

## Core Entities

The current accepted entity set includes:

- `UserProfile`
- `RideRequest`
- `RouteTemplate`
- `NearbyDestination`
- `TripTemplate`
- `WeatherSnapshot`
- `RiskAssessment`
- `DecisionResult`
- `CityStrategyConfig`
- `RiskRule`
- persisted plan result and planning audit records

The exact storage shape can evolve, but accepted terminology should stay aligned
with the current backend schemas and repositories.

## Bounded Contexts

- Request understanding: parsing natural-language requests, merging structured
  constraints, and deciding whether clarification is required
- Planning orchestration: stage sequencing, fallback handling, provider trace,
  and final response assembly
- Route knowledge: route templates, route facts, POI facts, and dynamic route
  enhancement
- Trip knowledge: nearby destinations, trip templates, return options, lodging,
  and multi-day rhythm generation
- Risk and strategy: weather facts, route risk scoring, city bias, and
  operator-maintained risk rules
- User experience delivery: frontend request entry, result rendering, route
  details, settings, and admin surfaces
- Verification and audit: tests, provider traces, query logs, and normalized
  audit records

## Accepted Input Semantics

The current baseline accepts:

- natural-language-first input
- optional structured constraints
- optional stored or submitted rider profile data
- optional concrete start-point or origin-location information

The current product is allowed to ask for clarification when core fields are
missing. It is not required to overfit vague input into a false-precision plan.

## Accepted Output Semantics

The current baseline response model is decision-first:

- result status
- parsed constraints
- clarification prompt when needed
- weather snapshot
- fallback reasons and tool trace
- recommended city route or weekend trip
- alternatives
- decision summary
- roadbook or trip rhythm / trip risks when applicable

For this product, a recommendation without explicit risk and fallback semantics
is incomplete.

## Domain Guardrails

- Do not treat optional LLM output as authoritative route, weather, or risk
  facts.
- Do not collapse `planning_scene` and `planning_mode` into one term unless the
  accepted API and implementation both change.
- Do not introduce city-agnostic wording that hides the current Hangzhou-first
  seed-data dependency.
- Do not promote early CIM, prompt-spec, or eval ideas from `docs/design/`
  directly into accepted truth unless they are backed by current implementation
  or accepted change evidence.
- Keep rider-facing product terms separate from repository workflow terms such
  as role routing, manifest loading, or spec orchestration.

## Current Accepted Limitations

- The current knowledge base is primarily a Hangzhou MVP seed set rather than a
  generalized multi-city catalog.
- Weekend-trip planning is accepted as part of the product surface, but its
  quality is still bounded by template coverage and fallback behavior.
- Risk scoring is rule-based in the accepted baseline; it is not a learned
  model.
- The repository contains historical CIM and eval material, but those assets are
  not yet the accepted golden regression system for current product behavior.
