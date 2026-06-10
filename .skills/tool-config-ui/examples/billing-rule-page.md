# Example: Billing Rule Page

## Scenario

Finance or product operators configure pricing rules, discounts, limits, and effective dates.

## Layout

- Header: `Billing Rule Editor`, market/plan scope, effective status.
- Status strip: draft saved, validation passed, scheduled apply time.
- Main editor:
  - rule metadata
  - conditions builder
  - pricing formula
  - caps and exceptions
  - customer preview cases
- Right rail:
  - revenue impact warnings
  - rule precedence
  - approval requirements

## States

- Empty: no billing rules; offer `Create rule` or `Import template`.
- Loading: skeleton condition builder and preview panel.
- Success: preview cases pass and rule scheduled.
- Failure: invalid date range, conflicting rule, negative price, approval missing.

## Safety

- Require preview against representative customer cases.
- Separate `Schedule` from `Force apply now`.
- Keep destructive `Archive rule` behind confirmation and audit note.
