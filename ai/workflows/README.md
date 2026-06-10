# Workflows

Use this directory for documented orchestration flows that connect prompts, agent roles, review stages, and execution gates.

## Spec-Driven Request Lifecycle

The `spec-driven-request-lifecycle.md` workflow documents the mixed orchestration loop:

`request intake -> spec-draft -> architecture/design -> spec-change -> execution routing -> implementation review -> independent tests -> final review -> acceptance -> current promote + archive`

This repository stores the contract, role boundaries, gates, and artifact shape. The first implementation slice validates that the workflow assets remain aligned even though the host runtime still performs the actual agent dispatch.

## Test Console Workflow

The `test-console-v1.yaml` workflow documents the minimal independent verification loop:

`accepted spec -> test-plan -> API/Scenario execution -> normalized result -> report UI`
