# Scenario Result Schema

Normalized result records for the independent test console should include:

- `runId`
- `specId`
- `specVersion`
- `featureName`
- `status`
- `releaseDecision`
- `startedAt`
- `endedAt`
- `summary`
- `flowResults[]`
- `items[]`

Each `flowResults[]` entry should include:

- `name`
- `status`
- `stages[]`

Each stage should include:

- `name`
- `status`
- `scenarios[]`
- `endpoints[]`

Each scenario should include:

- `name`
- `status`
- `relatedEndpointTargets[]`
- `steps[]`

Each endpoint should include:

- `target`
- `name`
- `method`
- `path`
- `status`
- timing and rule fields when available

Each `items[]` entry should include:

- `testType`
- `target`
- `flowName` when applicable
- `stageName` when applicable
- `scenarioName` when applicable
- `branchType` when applicable
- `stepName` when applicable
- `relatedEndpointTargets` when applicable
- `status`
- `durationMs`
- `summary`
- `evidence`

API entries may also include endpoint timing and rule linkage. Scenario entries may also include screenshots, videos, logs, and trace identifiers.
