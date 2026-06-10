# Specs

SpecOS keeps formal spec work under `specs/`.

The structure follows an OpenSpec-inspired current/change/archive model, but it remains SpecOS-owned:

- `current/`: accepted and active system facts. Agents should treat this as the baseline source of truth, not as the first write target for new requirements.
- `changes/`: proposed or in-progress business changes. Each change should live in its own folder until accepted, and active development should use it together with `current/`.
- `archive/`: completed changes after their accepted content has been merged into `current/`.
- `_rules/`: spec governance and normalization rules.
- `_template/`: reusable spec bundle templates.

Recommended lifecycle:

```text
spec-draft/
  -> specs/changes/<change-id>/
  -> develop / test / review against specs/current/ + specs/changes/<change-id>/
  -> promote accepted content into specs/current/
  -> archive completed change in specs/archive/<change-id>/
```

Spec bundles should keep both human-readable Markdown and machine-readable YAML when applicable. Agents working on active changes must read YAML and Markdown from both `specs/current/` and the relevant `specs/changes/<change-id>/`. Agents should write to `specs/current/` only as a final promotion step after the change has implementation, test, review, and acceptance evidence.
