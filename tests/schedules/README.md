# Test Schedules

Generated `test-schedule` artifacts live here.

Schedules split one active spec change into isolated work tracks:

- `execution`: implementation work plus implementation-coupled unit tests.
- `testing`: spec-and-contract-only API, E2E, UI, and business scenario verification.

The schedule is generated from a normalized spec through:

```bash
node packages/cli/dist/main.js generate-test-plan specs/changes/<change-id>/spec.json --change <change-id>
```

The independent test console still consumes normalized files from `tests/results/`; schedules describe agent routing and execution boundaries before those results exist.
