# Execution Plan

## Scope

Implement and verify package 2a + 2b as one ride-review-loop change package.

## Routes

- backend
- frontend
- docs

## Backend Tasks

1. Persist and read `ride_records`
2. Generate deterministic `ride_summary`
3. Add month/date-range repository helpers
4. Add deterministic `ride_monthly_summary`
5. Add lightweight summary observability events

## Frontend Tasks

1. Add `/rides/new` and `/rides/:rideRecordNo` review flow
2. Render recent rides list
3. Render monthly summary band
4. Route summary CTA back to `/`
5. Track CTA clicks

## Validation Tasks

1. backend targeted pytest
2. frontend targeted vitest
3. frontend build
4. runtime readback for monthly summary and event endpoints

## Current Blocker

The implementation is functionally ready, but branch hygiene cannot be completed because this worktree cannot write:

`/Users/liquiid/code/cycling-agent-docs/.git/worktrees/feature-package1-planning-alignment/index.lock`
