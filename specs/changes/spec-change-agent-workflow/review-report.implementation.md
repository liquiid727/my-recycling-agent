# Implementation Review Gate

## Status

Proposed. This file models the output contract for the first reviewer gate after execution tracks report.

## Gate Checklist

- Each selected execution route produced its route-specific implementation report.
- Implementation changes remain traceable to the active change package.
- Execution tracks stayed inside implementation-owned assets and did not create independent verification outputs.
- Architecture and design constraints are reflected in implementation notes.

## Failure Routing

- Frontend-only issues return to `frontend-execution-agent`.
- Backend-only issues return to `backend-execution-agent`.
- Migration-only issues return to `migration-execution-agent`.
- Spec-clarity issues return to `spec-agent` only when the reviewer identifies a real spec gap.
