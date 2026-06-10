# SpecOS Project Rules

## Core Principle

Every meaningful change should preserve the chain:

`draft -> change spec -> generated artifact -> test -> review/report -> promote to current -> archive`

If a task skips any link in the chain, call that out explicitly.

## Work Intake

- Identify whether the request is draft, spec, implementation, test, CI, or review work.
- Locate the closest source of truth before editing.
- For active development, read `specs/current/` as the accepted baseline and `specs/changes/<change-id>/` as the proposed delta. Do not treat a new requirement as accepted current state until the change has passed implementation, tests, review, and acceptance.
- Use `spec-draft/` and `draft/` as intake material only; normalize them into `specs/changes/<change-id>/` before implementation work whenever possible.
- Record assumptions when the source of truth is incomplete.

## Artifact Rules

- Specs must include goals, non-goals, flows, rules, exceptions, tests, observability, and open questions when applicable.
- API artifacts must include request/response examples and stable error semantics.
- Test artifacts must map to business scenarios and cover happy path, limit cases, and error cases.
- UI artifacts must cover empty, loading, success, and failure states.
- Workflow artifacts must document inputs, outputs, gates, and human approval points.
- Promotion into `specs/current/` is a finalization step. It should happen only after the related change package has evidence from implementation, test results, review/report, and human or release approval.

## Engineering Rules

- Keep changes minimal and aligned with existing directory boundaries.
- Prefer documented templates over ad-hoc formats.
- Do not duplicate canonical rules; link to `rules/` instead.
- Keep generated outputs deterministic and reviewable.
- Protect human-authored drafts, review notes, reports, and task files from accidental overwrite.

## Validation Rules

- Run the most specific available validation for changed code.
- For `spec-web-ui/`, validate with `npm run test` and `npm run build` when frontend behavior changes.
- For documentation and rules, validate by checking links, names, and consistency with the affected workflow.
- If validation is not run, state the reason and the exact command that should be run next.
