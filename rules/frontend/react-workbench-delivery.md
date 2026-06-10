# React Workbench Delivery

## Purpose

Define the frontend delivery rules for React-based product workspaces driven by shared specs.

## Required Practices

- Every user-facing flow should define empty, loading, success, and failure states.
- Metrics and logs must map to the key user flow and system flow steps.
- Reusable UI patterns should favor cataloged components over page-local duplication.
- State transitions that impact business actions should be explicit in the draft.

## Draft Injection Hints

- Add observability notes for key screen transitions.
- Describe validation messaging and retry paths.
- Clarify responsive behavior for key workspace panels.
