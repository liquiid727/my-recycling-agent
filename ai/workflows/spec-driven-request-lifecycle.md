# Spec-Driven Request Lifecycle

## Goal

Make every request enter the same lifecycle boundary before code, tests, review, promotion, or archive work begins.

## Flow

`request intake -> spec-draft -> architecture/design -> spec-change -> execution routing -> implementation review -> independent tests -> final review -> acceptance -> current promote + archive`

## Stage Contract

1. `request-intake`
   - Owner: `spec-draft-agent`
   - Output: request class, draft note, change-id suggestion
2. `draft-normalize`
   - Owner: `spec-draft-agent`
   - Output: structured draft, assumptions, open questions
3. `architecture-review`
   - Owner: `architecture-agent`
   - Output: `architecture-review.md`, route recommendations
4. `ui-design-review`
   - Owner: `ui-design-agent`
   - Conditional: only for frontend, interaction, or user-flow changes
5. `spec-change-create`
   - Owner: `spec-agent`
   - Output: active change package under `specs/changes/<change-id>/`
6. `execution-routing`
   - Owner: `architecture-agent`
   - Output: `routing-summary.json`
7. `implementation-execution`
   - Owners: `frontend-execution-agent`, `backend-execution-agent`, `migration-execution-agent`
8. `implementation-review-gate`
   - Owner: `reviewer`
   - Mode: `implementation_gate`
9. `independent-test-planning`
   - Owner: `test-editor`
10. `independent-test-execution`
   - Owners: `bruno-test-agent`, `e2e-test-agent`, `playwright-test-agent`, `specialized-check-agent`
11. `final-review-gate`
   - Owner: `reviewer`
   - Mode: `final_gate`
12. `acceptance-promote-archive`
   - Owner: `spec-agent`

## Artifact Boundary

Each active request lives under one change directory:

```text
specs/changes/<change-id>/
  spec.md
  architecture-review.md
  design-review.md
  execution-plan.md
  routing-summary.json
  implementation-report.frontend.md
  implementation-report.backend.md
  implementation-report.migration.md
  review-report.implementation.md
  review-report.final.md
  test-result-summary.md
  changelog.md
```

`design-review.md` may be marked `not-applicable` when the request is backend-only or tooling-only.

## Gate Rules

- Architecture blocked: route back to `spec-draft-agent`
- Implementation review blocked: route only the failed execution tracks back to execution
- Independent tests blocked: preserve normalized result evidence and carry blockers into final review
- Final review blocked or rejected: do not update `specs/current/`
- Acceptance requires implementation review pass, final review pass, test pass or explicit waiver, and complete traceability
