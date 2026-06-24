# Execution Plan

## Scope

Implement a PostgreSQL-only backend baseline and add the first backend slice of post-ride share generation.

## Steps

1. Update backend storage/config/docs/tests from dual SQLite/PostgreSQL language to PostgreSQL-only accepted behavior.
2. Add PostgreSQL DDL and repository support for `completed_rides`, `media_assets`, and `post_ride_shares`.
3. Add a media-storage abstraction and a local filesystem implementation for uploaded and generated images.
4. Extend the OpenAI-compatible provider with image-edit and share-copy generation methods.
5. Add new experience-layer schemas and routes for completed rides, photo assets, and post-ride shares.
6. Add targeted backend tests for PostgreSQL-only config, completed-ride flows, upload validation, share generation success/failure, and idempotency.
7. Run focused backend validation and record residual gaps.

## Commands

Backend tests:

```bash
cd /Users/mac_liquiid/Desktop/my-recycling-agent/products/cycling-agent/backend
pytest tests/test_storage_adapter.py tests/test_experience_share_api.py -v
```

Optional broader regression:

```bash
cd /Users/mac_liquiid/Desktop/my-recycling-agent/products/cycling-agent/backend
pytest tests -v
```

## Expected Outputs

- updated backend storage/config/runtime docs
- PostgreSQL-backed repositories and tests
- new experience-share routes, schemas, and service helpers
- new change-package evidence files under `specs/changes/cycling-agent-postgres-post-ride-share/`
