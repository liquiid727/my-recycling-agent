# Architecture Review

## Summary

Package 2 remains additive and respects the existing repo boundaries:

- backend API routes stay under `products/cycling-agent/backend/app/api/routes/`
- data access stays in repositories
- deterministic aggregation stays in services
- frontend changes stay inside the existing `/rides` surface

## Domain Boundaries

- `ride_records` are the only history fact source.
- `ride_summary` and `ride_monthly_summary` are derived read models.
- `ride_monthly_summary_events` are observability-only and must not feed product logic.

## Data / Migration Impact

- no destructive migration
- additive storage change: `ride_monthly_summary_events`
- existing `ride_records` schema remains the same user-history source

## Runtime Impact

- adds one month summary endpoint
- adds one CTA event write endpoint
- adds one admin read endpoint for events

## Risk Notes

- month parsing and date normalization are high-value contract edges
- streak semantics can drift if route and service disagree on time windows
- `/rides` now has multiple independent read states and must preserve failure isolation

## Recommendation

Promote this package only after:

1. targeted backend and frontend validation are recorded
2. final review is documented
3. git-blocked commit state is resolved so the branch can be handed off cleanly
