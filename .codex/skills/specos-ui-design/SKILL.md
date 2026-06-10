---
name: specos-ui-design
description: Use when designing or changing SpecOS spec-web-ui screens, layouts, components, visual hierarchy, interaction states, copy hierarchy, responsive behavior, or UI handoff notes. Applies to frontend UI work that must stay traceable to specs, drafts, React delivery rules, or Pencil prototype rules.
---

# SpecOS UI Design

Use this skill for UI-facing work under `spec-web-ui/`.

## Source Order

1. Root `README.md` for SpecOS product intent.
2. `.rules/project.md` for traceability and artifact rules.
3. `rules/frontend/react-workbench-delivery.md` for React workbench delivery.
4. `rules/ui/pencil-prototype-ui.md` when prototype or handoff material is involved.
5. Relevant `spec/` bundle; if absent, use `spec-draft/` and mark the work draft-only.
6. Existing `spec-web-ui/app/`, `spec-web-ui/tests/`, and catalog assets.
7. `.skills/tool-config-ui/SKILL.md` for tool-style configuration pages.

## UI Workflow

1. Identify the source spec, draft, rule, or prototype frame.
2. Name the affected route, screen, user flow, and scenario terms.
3. Define empty, loading, success, and failure states before implementation.
4. Prefer reusable sections/components and stable copy hierarchy.
5. Note responsive behavior for key workspace panels.
6. Keep validation explicit: `npm run test` and, when routes/layouts change, `npm run build`.

## Output Contract

When handing off or summarizing UI work, include:

- Source: spec, draft, rule, or prototype reference.
- Changed screens/components.
- State coverage: empty/loading/success/failure.
- Assumptions and open questions.
- Validation performed or skipped with exact command.

## Guardrails

- Do not introduce new dependencies for visual polish unless the need is explicit.
- For configuration pages, prefer the patterns and visual tokens in `.skills/tool-config-ui/`.
- Do not duplicate canonical rules; link to `rules/` instead.
- Do not overwrite human-authored drafts, specs, reports, or review notes.
- If the request is only exploratory, keep outputs as draft-only notes.
