# Execution Plan

## Scope

Implement package 2c growth review as a read-only extension of the package 2 ride-review loop.

## Routes

- backend
- frontend
- docs

## Backend Tasks

1. add growth-review schemas
2. add rolling-window repository helper if needed
3. add deterministic growth-review service
4. add `GET /api/v1/rides/growth-review`

## Frontend Tasks

1. add growth-review fetch helper
2. render growth panel under the monthly summary band
3. add compact window switching
4. add planner-compatible next-focus CTA

## Validation Tasks

1. backend targeted pytest for growth-review service and API
2. frontend targeted vitest for `/rides`
3. frontend build
4. runtime readback for the new growth-review endpoint

## Current Status

This package is not yet implemented. The draft and plan exist, and the implementation should start from this change package rather than from the older superpowers drafts.
