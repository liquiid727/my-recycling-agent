# Draft Template / 草稿模板

This directory contains reusable templates for engineering teams to draft feature requirements before they are converted into formal specs.  
该目录包含可复用的模板，供研发团队在需求正式进入 spec 前编写功能草稿。

## Purpose / 目的

`spec-draft` is a transition stage between incoming product requirements and finalized spec documents. It helps teams organize intent, dependencies, and implementation boundaries before formalization.  
`spec-draft` 是产品需求与正式 spec 之间的过渡阶段，用于在正式化之前梳理目标、依赖关系和实现边界。

## Why This Matters / 为什么需要这个阶段

For a brand-new system, one draft may map directly to one standalone spec.  
对于全新系统，一个 draft 往往可以直接对应一个独立 spec。

For an in-progress system, a new requirement often affects multiple existing domains.  
对于开发中的系统，新需求通常会影响多个既有领域。

For example, adding a single API may also require:  
例如，新增一个接口时，可能同时需要：

- New error codes that may already be referenced by other modules.
- Updates to shared business flows and cross-module handling.
- Alignment with existing context boundaries instead of creating an isolated spec.
- 新增错误码（而这些错误码可能已被其他模块引用）。
- 更新共享业务链路及跨模块处理逻辑。
- 与既有上下文边界对齐，而不是强行拆分为完全独立的 spec。

In these cases, creating a fully independent spec is usually not the best choice. A draft-first process helps determine whether the requirement should be merged into existing specs or introduced as a new one.  
在这类场景下，完全独立新开 spec 往往并不合适。先经过 draft 阶段，可以判断需求应并入现有 spec 还是新建 spec。

## Workflow / 工作流程

1. Engineers convert product requirements into a structured `spec-draft`.
2. The `spec-draft` agent formats and normalizes the draft using project rules.
3. Spec and architecture agents collaborate to turn the draft into a formal change package under `specs/changes/<change-id>/`.
4. Implementation and tests run against `specs/current/` plus the active change package.
5. After implementation, tests, review, and acceptance are complete, the accepted change content is promoted into `specs/current/` and the completed change is archived.
1. 研发将产品需求整理为结构化 `spec-draft`。
2. `spec-draft` agent 基于项目规则完成格式化与规范化。
3. spec 与架构相关 agent 协同，将 draft 转化为 `specs/changes/<change-id>/` 下可落地的正式变更包。
4. 开发与测试基于 `specs/current/` 和当前 change package 一起执行。
5. 实现、测试、评审和验收完成后，再把已接受内容更新到 `specs/current/`，并归档完成的 change。

## Responsibilities / 职责分工

- Engineers: capture requirement intent, business context, and technical constraints in the draft.
- `spec-draft` agent: enforce format consistency and apply rules for IDs, error codes, response conventions, and related standards.
- `spec-draft`: provide a clear, engineer-oriented intermediate document that improves the accuracy and efficiency of formal spec generation.
- 研发：在 draft 中明确需求意图、业务上下文与技术约束。
- `spec-draft` agent：统一格式与排版，并应用规则生成符合项目规范的 ID、错误码、响应处理等内容。
- `spec-draft`：作为面向研发的中间文档，提升后续正式 spec 产出的准确度与效率。
