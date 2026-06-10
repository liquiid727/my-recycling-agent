---
name: tool-config-ui
description: Use when designing or implementing robust tool-style configuration pages for SpecOS, including agent skill settings, policy forms, strategy editors, toggles, tables, empty states, validation, and dangerous operations in spec-web-ui.
---

# Tool Config UI

Use this skill when the UI is primarily a configuration surface: users inspect current state, edit structured settings, validate changes, and safely apply or rollback tool behavior.

## Source Order

1. Product intent: `readme.md`.
2. Project traceability: `.rules/project.md`.
3. Frontend delivery: `rules/frontend/react-workbench-delivery.md`.
4. UI/prototype handoff: `rules/ui/pencil-prototype-ui.md` when relevant.
5. Existing UI agent: `.agents/roles/ui-design-agent.md`.
6. Detailed references in this skill:
   - `.skills/tool-config-ui/patterns.md`
   - `.skills/tool-config-ui/visual-tokens.md`
   - `.skills/tool-config-ui/examples/`

## Design Principles

- Make configuration safe before making it clever.
- Separate read-only status, editable draft, validation result, and applied state.
- Prefer predictable forms, tables, and policy cards over decorative layouts.
- Explain consequences near the control that triggers them.
- Keep primary actions scarce: usually `Save draft`, `Validate`, `Apply`, or `Rollback`.
- Treat destructive actions as separate guarded flows, not adjacent secondary buttons.

## Required Page Anatomy

1. Header: title, short purpose, source spec/rule, current status.
2. Status strip: environment, last saved, last applied, validation state.
3. Main editor: grouped fields, strategy sections, toggles, or table rows.
4. Preview/diff: show what changes before apply when risk is non-trivial.
5. Validation panel: blocking errors, warnings, missing inputs, next action.
6. Footer/action bar: stable actions with disabled/loading/error states.

## State Coverage

Every config page must define:

- Empty: no config, no rules, no rows, or no connected source.
- Loading: initial load, validating, saving, applying, rolling back.
- Success: saved draft, validation passed, applied config, rollback complete.
- Failure: field error, schema error, conflict, permission denied, network failure.

## Output Contract

When using this skill, summarize:

- Source: spec, draft, rule, or prototype reference.
- Page type: form, policy editor, switchboard, table manager, dangerous operation.
- State coverage: empty/loading/success/failure.
- Safety model: validation, confirmation, diff, rollback, audit trail.
- Visual choices: tokens or patterns used.
- Validation command: usually `npm run test`; add `npm run build` for route/layout changes.

## References

- Patterns: `.skills/tool-config-ui/patterns.md`
- Visual tokens: `.skills/tool-config-ui/visual-tokens.md`
- Examples:
  - `.skills/tool-config-ui/examples/nginx-config-page.md`
  - `.skills/tool-config-ui/examples/redis-sentinel-page.md`
  - `.skills/tool-config-ui/examples/billing-rule-page.md`
  - `.skills/tool-config-ui/examples/agent-skill-config-page.md`
