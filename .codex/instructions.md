# Codex Instructions For SpecOS

## Default Behavior

- Respond in Chinese unless the user asks otherwise.
- Treat SpecOS as a spec-driven orchestration project, not only a frontend app.
- Read root `AGENTS.md` before making repository changes.
- Use `.agents/manifest.yaml` to choose role context for multi-step work.
- When a role is selected, only load that role's `role_prompt`, `canonical`, declared `skills`, and `context_includes`.
- Do not expand repository-local or external skills unless they are bound to the selected role or explicitly requested by the user.
- Use `.rules/project.md` as the compact rule entrypoint.

## Planning

- For non-trivial work, identify the source spec, impacted artifacts, validation command, and reviewer role.
- If there is no accepted spec, keep changes draft-scoped or ask whether to promote the draft.
- Prefer narrow changes that preserve traceability.
- Prefer switching roles or splitting work over adding more skills to a single role context.

## Requirement Intake

- For any new requirement, feature request, behavior change, UI flow, API change, test asset, workflow, or agent/rule change, use `spec-draft/requirement-intake-flow.md` as the default intake process.
- Classify the request before editing as one of: raw requirement, draft-only, active change, implementation, test, review, acceptance, or tooling/configuration.
- If the request is raw or draft-only, first preserve it under `spec-draft/` or explicitly state why the current work is only exploratory.
- Do not implement against a raw requirement when a normalized change package is needed; first create or identify `specs/changes/<change-id>/` and use `specs/current/` as the accepted baseline.
- For implementation and testing, work from `specs/current/` plus the active `specs/changes/<change-id>/` package, then keep generated artifacts traceable to that change.
- Do not promote content into `specs/current/` until implementation, tests, review, and acceptance evidence exist.
- In final summaries for requirement work, name the draft or change id, impacted artifacts, validation evidence, assumptions, and any skipped link in the chain.

## Validation Hints

- Frontend package path: `spec-web-ui/`.
- Frontend tests: `npm run test`.
- Frontend build: `npm run build`.
- Spec and rule changes require manual consistency checks across names, links, and scope.

## Safety

- Do not modify `.codex/config.toml` provider settings unless explicitly asked.
- Do not commit, push, or create branches unless explicitly asked.
- Do not add generated caches, secrets, or machine-local artifacts.
