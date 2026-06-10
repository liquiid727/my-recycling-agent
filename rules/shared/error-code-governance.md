# Error Code Governance

## Purpose

Keep backend and frontend aligned on machine-readable failures, copy, and remediation actions.

## Required Practices

- Errors should have stable prefixes per domain or subsystem.
- User-facing messages and machine-readable codes must both be documented.
- Recoverable and non-recoverable failures should be distinguishable.
- Spec and tests should reference the same error semantics.

## Draft Injection Hints

- 为主要异常场景补充错误码和处理动作。
- 区分用户可重试与人工介入场景。
- 记录前端提示文案是否需要本地化。
