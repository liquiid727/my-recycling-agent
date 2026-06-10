# Redis Key Governance

## Purpose

Standardize Redis key naming, lifecycle ownership, and invalidation behavior for backend specs.

## Required Practices

- Prefix keys by bounded domain and aggregate purpose.
- Define TTL, invalidation trigger, and recovery expectations.
- Avoid overloaded keys that mix caching, locking, and workflow state.
- Document idempotency or deduplication semantics when Redis is part of write flow protection.

## Draft Injection Hints

- 补充 Redis Key 前缀、TTL 和回收策略。
- 说明缓存失效后的降级路径。
- 如果 Redis 用于锁或幂等，请写清失败恢复方案。
