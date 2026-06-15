# Architecture Review

## Summary

Package 2c should remain a pure read-model addition:

- no new user-history write path
- no mutation to package 2a facts
- no dependency on external fitness data

## Domain Boundaries

- `ride_records` remain the only user-history fact source.
- `ride_growth_review` is a derived rolling-window read model.
- Any observability events remain separate from user-history facts.

## Storage Impact

- likely no new table required for the first slice
- existing `ride_records` queries may need one rolling-window helper

## Runtime Impact

- one new read endpoint
- one extra frontend fetch on `/rides`

## Risk Notes

- window semantics must stay explicit
- growth rules must avoid accidental training-product language
- `/rides` now becomes a three-surface page:
  - recent list
  - monthly summary
  - growth panel

## Recommendation

Package 2c is architecturally sound only if it reuses the existing ride-review loop and does not introduce a second history model.
