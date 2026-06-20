# Cycling-Agent Project Rules

## Core Principle

Every meaningful change should preserve the chain:

`draft -> change spec -> generated artifact -> test -> review/report -> promote to current -> archive`

If a task skips any link in the chain, call that out explicitly.

The product truth for this repository is the runnable cycling-agent MVP in
`products/cycling-agent/`, not a generic SpecOS example.

## Work Intake

- Identify whether the request is draft, spec, implementation, test, CI, or review work.
- Locate the closest source of truth before editing.
- For active development, read `specs/current/` as the accepted baseline and `specs/changes/<change-id>/` as the proposed delta. Do not treat a new requirement as accepted current state until the change has passed implementation, tests, review, and acceptance.
- Use `spec-draft/` and `draft/` as intake material only; normalize them into `specs/changes/<change-id>/` before implementation work whenever possible.
- Record assumptions when the source of truth is incomplete.
- Treat `docs/design/` as exploratory or historical unless an accepted change
  explicitly promotes part of it into `specs/current/`.

## Artifact Rules

- Specs must include goals, non-goals, flows, rules, exceptions, tests, observability, and open questions when applicable.
- API artifacts must include request/response examples and stable error semantics.
- Test artifacts must map to business scenarios and cover happy path, limit cases, and error cases.
- UI artifacts must cover empty, loading, success, and failure states.
- Workflow artifacts must document inputs, outputs, gates, and human approval points.
- Promotion into `specs/current/` is a finalization step. It should happen only after the related change package has evidence from implementation, test results, review/report, and human or release approval.
- Golden datasets and test plans must describe real cycling-agent flows and API
  surfaces, not placeholder business domains from unrelated examples.

## Engineering Rules

- Keep changes minimal and aligned with existing directory boundaries.
- Prefer documented templates over ad-hoc formats.
- Do not duplicate canonical rules; link to `rules/` instead.
- Keep generated outputs deterministic and reviewable.
- Protect human-authored drafts, review notes, reports, and task files from accidental overwrite.
- Do not leave fake execution paths or stale product names in workflow docs,
  manifests, or test assets once the real repository structure is known.

## Validation Rules

- Run the most specific available validation for changed code.
- For `products/cycling-agent/frontend`, validate with `npm test` and
  `npm run build` when frontend behavior changes.
- For `products/cycling-agent/backend`, validate with targeted `pytest`
  commands or `pytest tests -v` when backend behavior changes.
- For documentation and rules, validate by checking links, names, and consistency with the affected workflow.
- If validation is not run, state the reason and the exact command that should be run next.
