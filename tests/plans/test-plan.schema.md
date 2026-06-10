# Test Plan Schema

Normalized `test-plan` artifacts should be generated from accepted specs before selecting execution tools.

Required fields:

- `specId`
- `specVersion`
- `featureName`
- `source`
- `flows[]`
- `endpoints[]`
- `scenarios[]`

Flow entries should define:

- flow name
- ordered `stages[]`

Each stage should define:

- stage name
- `scenarioNames[]`
- `stepNames[]`

Endpoint entries should define:

- interface name
- method and path
- priority
- branch list
- preconditions
- expected results
- related rule

Scenario entries should define:

- scenario name
- priority
- branch list
- preconditions
- expected results
- ordered steps
