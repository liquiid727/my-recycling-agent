# Spec Release Gates

## Purpose

Define release checks that ensure generated artifacts still match accepted spec decisions.

## Required Practices

- CI should verify spec, generated contract, tests, and bundle outputs stay aligned.
- Failing scenario tests must block release for affected flows.
- Reviewers should see which spec bundle version a release references.
- Human approval is required before irreversible workflow steps in V1.
- Repository-owned gates should verify the cycling-agent asset baseline before a
  release candidate is treated as aligned. At minimum this includes:
  `specs/current/`, `.rules/`, `.agents/manifest.yaml`, `tests/plans/`,
  `tests/scenarios/`, and `tests/results/`.

## Draft Injection Hints

- 说明哪些测试是发布阻断项。
- 标记需要人工确认的 workflow step。
- 记录本次功能对应的 spec version 或 bundle id。
