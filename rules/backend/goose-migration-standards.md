# Goose Migration Standards

## Purpose

Make schema changes explicit, reviewable, and reversible in spec-driven backend delivery.

## Required Practices

- Every schema change should define forward and rollback expectations.
- Migrations must state data backfill or dual-write requirements when relevant.
- Expensive migrations require rollout windows and operational safeguards.
- Contract and model updates must stay aligned with migration intent.

## Draft Injection Hints

- 标出是否需要历史数据回填。
- 说明上线顺序、回滚条件和兼容窗口。
- 如果涉及大表变更，补充分批策略。
