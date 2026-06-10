# Current Specs

Accepted, active SpecOS spec bundles live here.

This directory is the accepted system baseline. It represents facts that have already passed implementation, tests, review, and acceptance.

Agents should not update `specs/current/` at the start of a new requirement. New work should first be captured under `spec-draft/`, then normalized into `specs/changes/<change-id>/`. During implementation and testing, agents should read `specs/current/` together with the active change package. Only after the change is accepted should its final content be promoted into `specs/current/`.

## Baseline Context Files

- `project-context.md`: accepted project intent, product surfaces, and source-of-truth order.
- `architecture-context.md`: accepted architecture placement rules and agent context boundaries.
- `domain-context.md`: accepted SpecOS domain language and bounded-context guidance.
