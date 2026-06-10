# Tool Config UI Patterns

## Form Page

Use for one object with grouped settings.

- Structure: summary header, grouped cards, inline help, validation panel, sticky action bar.
- Field labels: noun-first and stable, for example `Timeout`, `Retry policy`, `Provider`.
- Help text: explain impact, accepted values, and default behavior.
- Validation: inline for field errors; panel for cross-field or runtime errors.
- Save model: prefer draft save before apply when changes affect runtime behavior.

## Strategy Configuration

Use for policies, routing rules, priority order, fallback behavior, or scoring weights.

- Show the active strategy and pending draft separately.
- Use ordered cards or table rows for precedence-sensitive rules.
- Provide move up/down controls instead of drag-only interactions.
- Preview selected examples against the strategy before apply.
- Warn when a new rule shadows or disables an existing rule.

## Switchboard

Use for feature flags, provider toggles, role permissions, or agent capabilities.

- Group toggles by user goal, not implementation package.
- Show current value, default value, source, and last changed metadata.
- Require confirmation for toggles that affect production, billing, security, or data loss.
- Avoid hiding dependent fields; disable with explanation when possible.

## Table Manager

Use for lists of rules, keys, mappings, endpoints, agents, templates, or presets.

- Columns: name, type/status, source, last updated, validation, actions.
- Provide empty state, search/filter, row-level errors, and bulk action limits.
- Keep destructive row actions behind a menu or confirmation.
- Let users inspect details before editing large structured records.

## Empty State

Use empty states to teach the next safe action.

- Include title, one-sentence explanation, primary action, and optional import/sample action.
- Mention the missing source when traceability is required.
- Avoid celebratory illustration when the state blocks configuration.

## Dangerous Operation

Use for delete, reset, rollback, force apply, key rotation, provider disable, or policy bypass.

- Separate from normal save/apply controls.
- Explain impact, affected scope, reversibility, and audit trail.
- Require explicit confirmation text for irreversible actions.
- Provide rollback or export backup when possible.
- Show success and failure outcomes with next steps.

## Loading And Failure

- Initial loading: skeletons that preserve layout, not spinners replacing the page.
- Saving/applying: disable conflicting controls and show operation-specific progress text.
- Validation failure: list actionable fixes; distinguish blocking errors from warnings.
- Network failure: preserve unsaved edits and offer retry.
- Conflict: show local draft vs remote version and require a deliberate choice.
