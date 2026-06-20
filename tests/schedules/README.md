# Test Schedules

Generated `test-schedule` artifacts live here.

Schedules split one active spec change into isolated work tracks:

- `execution`: implementation work plus implementation-coupled unit tests.
- `testing`: spec-and-contract-only API, E2E, UI, and business scenario verification.

This repository does not yet treat a generated schedule runner as accepted live
infrastructure. Until such a runner is accepted, schedules should be stored as
repository-owned routing artifacts when needed, and the independent test
console should continue to consume normalized files from `tests/results/`.
