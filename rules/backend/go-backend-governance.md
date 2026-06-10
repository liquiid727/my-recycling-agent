# Go Backend Governance

## Purpose

Standardize backend feature delivery for Go services that will be driven by accepted specs.

## Required Practices

- API changes must map back to an accepted spec bundle.
- Error responses should use domain-specific prefixes and machine-readable codes.
- Database changes should ship with forward and rollback migration guidance.
- Redis keys must use domain-scoped prefixes and lifecycle notes.
- CI checks should verify spec alignment, tests, and generated artifacts.

## Draft Injection Hints

- Clarify idempotency requirements for write APIs.
- Describe audit and traceability requirements for sensitive operations.
- List rollback expectations for migrations and side effects.
