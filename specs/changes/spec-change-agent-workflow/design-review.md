# Design Review

## User Behavior Impact

The workflow keeps user-facing scenario language stable from draft to test report. Scenario names, flow stages, expected results, and endpoint targets are generated from the spec and reused by test scheduling.

## Required States

- Draft refined: requirement has structured intent and open questions.
- Change created: active change package exists and references current baseline.
- Architecture/design reviewed: implementation and test tracks can start.
- Execution ready: execution agent has implementation context only.
- Test ready: test agent has spec, API contract, and scenario context only.
- Tests passed or gaps recorded: normalized result evidence exists.
- Reviewed: reviewers decide whether release is blocked.
- Promoted and archived: spec agent updates current and archives the change.

## UI Test Position

UI behavior remains important, but this slice records UI test gaps rather than pretending Playwright execution exists. Each UI gap task links back to the same scenario vocabulary used by the spec and API tests.

design-review.md can be marked `not-applicable` when a change is backend-only or tooling-only and the workflow intentionally skips `ui-design-agent`.
