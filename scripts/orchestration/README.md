# Orchestration Scripts

Pipeline scripts that connect spec generation, review, test generation, and validation belong here.

## Test Runner

Use `test-runner.mjs` to simulate or normalize a spec-driven test execution into a `tests/results/` artifact.

Example:

```bash
node scripts/orchestration/test-runner.mjs reward-order 1.2.0 all
```

Inputs:

- `specId`
- optional `specVersion`
- optional `runScope` of `api`, `scenario`, or `all`

Output:

- one normalized result file under `tests/results/`
