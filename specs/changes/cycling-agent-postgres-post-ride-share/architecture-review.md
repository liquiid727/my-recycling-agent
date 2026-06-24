# Architecture Review

## Summary

This change selects `backend` and `migration` execution routes.

## Boundary Decisions

- New user-facing capability stays under the existing experience boundary rather than the planning orchestrator boundary.
- PostgreSQL becomes the single accepted runtime database target.
- Media bytes stay out of repository payload tables and are routed through a dedicated media-storage layer.

## Why This Placement

- Existing experience APIs already wrap planner results into editorialized payloads, so post-ride sharing belongs beside them rather than inside `RidePlanningOrchestrator`.
- Existing storage code centralizes runtime DDL and connection behavior, so the PostgreSQL-only pivot belongs in `app/core/storage.py` and `app/core/config.py`.
- Existing repositories already store large structured payloads as JSON plus indexed columns. The new share entities follow the same shape while keeping binary data external.

## Migration Implications

- Remove SQLite-specific connection and DDL paths.
- Add PostgreSQL DDL for `completed_rides`, `media_assets`, and `post_ride_shares`.
- Update test strategy away from per-test SQLite files toward PostgreSQL-backed fixtures.

## Risks

- Test harness churn is larger than the feature code because many backend tests currently assume SQLite urls.
- Inline image generation may create long request times until a later worker system exists.
- Media storage path design must avoid local absolute-path leakage into user-visible payloads.

## Recommended Execution Order

1. Land change-package contract.
2. Switch backend config and storage layer to PostgreSQL-only.
3. Replace backend test database setup with PostgreSQL fixtures.
4. Add completed-ride, photo-asset, and post-ride-share repositories/schemas/routes.
5. Add provider/media-storage integration and targeted tests.
