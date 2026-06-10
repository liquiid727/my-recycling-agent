# Requirement Intake Flow / 需求进入 SpecOS 的流程草稿

> Status: draft-only
> Source: README.md, todo/specos-current-implemented-flow.md, spec-draft/README.md, spec-web-ui/README.md
> Scope: describe how a new requirement should move through SpecOS today, and what the target closed-loop flow should become.

## 1. 背景

SpecOS 的核心不是让 AI 直接从一句需求生成代码，而是把需求、spec、规则、开发、测试、报告和验收串成一条可追溯的交付链。

因此，“拿到一个需求以后怎么走”需要分成两层：

1. **MVP 可实现流程**：基于当前仓库已经具备的能力，定义今天可以人工配合跑通的流程。
2. **目标闭环流程**：定义 SpecOS 未来应该自动化打通的完整链路。

这两层不能混在一起。MVP 流程解决“现在怎么用”，目标闭环流程解决“产品应该长成什么样”。

## 2. 流程 A：MVP 可实现流程

### 2.1 适用场景

MVP 流程适用于一个项目仓库内的新需求整理、规格化准备、测试计划生成和测试结果展示。

它承认一个现实：当前系统还没有完整实现 `raw requirement -> normalized change package` 的自动化链路，所以需求进入正式 change package 前，需要人工或 agent 参与整理。

`spec-web-ui` 不属于单个项目的需求交付主流程。它是一个工具站点和资产工作台，用来维护平时积累的 rules、skills、spec templates、agent templates、workflow templates 和 test patterns。项目可以从这类资产库选择或导入配置，但一个具体需求的 draft、change、test-plan、result 和 acceptance 仍然应该落在目标项目自己的仓库边界内。

### 2.2 主流程

```text
原始需求
-> 记录到目标项目的 spec-draft/
-> 人工或 spec-editor agent 整理为 normalized spec/change 草稿
-> 放入 specs/changes/<change-id>/
-> 用 CLI 从 normalized spec 生成 test-plan / test-schedule
-> 用 test-runner 读取 test-plan 并生成 normalized result
-> 用 test-console 查看结果
-> 人工评审、修正、验收
-> 验收通过后再更新 specs/current/
```

### 2.3 角色分工

| 角色 | 职责 |
| --- | --- |
| Product / requester | 提供原始需求、业务目标、边界、验收口径 |
| Engineer | 将需求整理成可执行草稿，补充技术约束和影响范围 |
| Asset/tooling maintainer | 维护可复用 rules、skills、spec templates、agent templates；不直接承载具体项目需求状态 |
| Spec editor agent | 将 draft 整理成规范化 change package |
| Test editor agent | 基于 normalized spec 生成 test-plan / test-schedule |
| Execution / implementation agent | 基于 `specs/current + specs/changes/<change-id>` 实现 |
| Reviewer | 检查 spec、实现、测试和结果是否一致 |

### 2.4 关键产物

| 阶段 | 产物 | 当前状态 |
| --- | --- | --- |
| 需求进入 | `spec-draft/*.md` | 可人工维护 |
| 规格化变更 | `specs/changes/<change-id>/spec.json` | 需要人工或 agent 准备 |
| 测试计划 | `tests/plans/*.test-plan.json` | CLI 已支持从 normalized spec 生成 |
| 测试调度 | `tests/schedules/*.test-schedule.json` | CLI 已支持生成 |
| 测试结果 | `tests/results/*.json` | runner 已支持生成 normalized result |
| 展示 | test-console 页面 | 可消费现有 plans/results |

### 2.5 MVP 流程的通过标准

一个需求在 MVP 流程里可以被认为“走完”，需要满足：

- 原始需求已经有 draft 记录。
- draft 已经被整理为一个明确的 change id。
- change package 能说明它基于哪个 current baseline。
- 已生成对应 test-plan 和 test-schedule。
- 已产出 normalized test result。
- 人工评审明确记录通过、失败或阻塞原因。
- 只有通过验收的内容才允许更新 `specs/current/`。

### 2.6 MVP 流程的明确限制

- draft 到 normalized change package 仍然不是全自动。
- test-runner 当前偏向模拟和规范化结果生成，不代表所有真实 Bruno / Playwright / 单元测试都已经接入。
- 可复用资产库可以辅助项目初始化和规范选择，但不应该成为单个项目需求状态的唯一存放位置。
- bundle workflow 当前更像安装与运行链路 smoke test，不是完整交付编排引擎。

## 3. 流程 B：目标闭环流程

### 3.1 目标

目标闭环流程描述 SpecOS 作为 Spec-Driven AI IDE 应该支持的完整产品能力。

它的核心原则是：

```text
任何开发、测试、文档和验收动作，都必须能追溯到 spec、draft 或 rule。
```

### 3.2 主流程

```text
原始需求输入
-> 需求澄清与结构化
-> 生成 spec-draft
-> draft review
-> 生成 specs/changes/<change-id>/ change package
-> 基于 specs/current + active change 做影响分析
-> 生成开发任务、Agent 分工、测试计划、接口/场景资产
-> 执行实现与测试
-> 汇总 normalized result、review notes、acceptance report
-> 验收门禁
-> promote accepted content into specs/current
-> archive completed change
```

### 3.3 产品分层

目标闭环可以拆成五个产品层：

| 层 | 目标 | 主要产物 |
| --- | --- | --- |
| Intake | 把自然语言需求变成可审查草稿 | draft、澄清问题、假设 |
| Normalize | 把 draft 变成正式 change package | spec.json、change metadata、trace map |
| Plan | 基于 current + change 生成执行计划 | impact analysis、tasks、test-plan、schedule |
| Execute | 执行开发、测试和审查 | code changes、test results、review notes |
| Accept | 验收并更新系统事实 | current update、archive、release notes |

### 3.4 每一层的输入输出

#### Intake

输入：

- 原始需求文本、会议记录、截图、Issue 或 PRD。
- 业务目标、用户角色、成功标准。
- 项目已选用的 rules、skills、spec templates 和 agent templates。

输出：

- `spec-draft/<topic>.md`
- 未决问题列表。
- 明确假设。
- 初步影响范围。

#### Normalize

输入：

- `spec-draft/<topic>.md`
- `rules/` 和 `.rules/`
- `specs/current/`

输出：

- `specs/changes/<change-id>/spec.json`
- change metadata。
- requirement-to-spec trace map。
- 与 current baseline 的关系说明。

#### Plan

输入：

- `specs/current/`
- `specs/changes/<change-id>/`
- `ai/agents/` 和 `.agents/`
- `tests/` templates。

输出：

- impact analysis。
- Agent task breakdown。
- `tests/plans/*.test-plan.json`
- `tests/schedules/*.test-schedule.json`
- API / UI / scenario test assets。

#### Execute

输入：

- Active change package。
- Agent task breakdown。
- Test schedule。

输出：

- 实现变更。
- API / UI / migration / documentation updates。
- `tests/results/*.json`
- review notes。

#### Accept

输入：

- 实现结果。
- 测试结果。
- review notes。
- 验收结论。

输出：

- 更新后的 `specs/current/`。
- `specs/archive/<change-id>/`。
- release / delivery report。
- CI gate result。

## 4. MVP 到目标闭环的演进路径

### 4.1 第一阶段：把人工流程固定下来

目标：

- 明确 draft 模板。
- 明确 change package 最小结构。
- 明确从 draft 到 change package 的人工 checklist。
- 让每个需求至少能追踪到 draft、change id、test-plan 和 result。
- 明确可复用资产库只提供模板和规则来源，需求状态留在项目仓库内。

判断标准：

- 新需求不会直接改 `specs/current/`。
- 每个需求都有独立 change id。
- 每次测试结果都能反查到 spec 或 change。
- 单个需求流程不依赖 `spec-web-ui` 的 workspace 状态。

### 4.2 第二阶段：自动生成 change package

目标：

- 由 spec-editor agent 根据 draft 生成 normalized spec。
- 自动标记影响的 domains、flows、rules、APIs、UI states、tests。
- 生成 trace map。
- 允许从项目已安装或已选择的资产模板中读取规范，但输出仍写入目标项目的 `specs/changes/<change-id>/`。

判断标准：

- draft 到 `specs/changes/<change-id>/` 不再完全依赖人工手写。
- change package 可被 CLI 和 test tooling 消费。

### 4.3 第三阶段：自动生成计划与测试资产

目标：

- 基于 current + change 自动生成 impact analysis。
- 自动生成 test-plan、test-schedule、Bruno / Playwright / scenario assets。
- 明确 execution agent 与 test agent 的输入输出边界。

判断标准：

- 测试计划不是事后补写，而是由 spec 派生。
- 测试失败能追溯到具体 requirement、flow、rule 或 acceptance criterion。

### 4.4 第四阶段：验收门禁和 promote

目标：

- 只有实现、测试、review、验收全部通过的 change 才能 promote 到 current。
- archive 保留 change 的完整上下文。
- CI gate 能阻止未验收或未对齐的变更进入主线。

判断标准：

- `specs/current/` 始终代表已验收事实。
- `specs/changes/` 始终代表进行中的变更。
- `specs/archive/` 始终保留历史交付依据。

## 5. 后续可转成 spec 的需求草稿

### 5.1 Feature: Requirement Intake Workflow

SpecOS should provide a requirement intake workflow that guides a new requirement from raw input to draft, normalized change package, generated test assets, execution result, and accepted current spec update.

### 5.2 Goals

- Prevent raw requirements from directly mutating `specs/current/`.
- Make every requirement traceable through draft, change, plan, result, and acceptance.
- Separate current accepted facts from active proposed changes.
- Support a practical MVP path before the full closed-loop workflow is automated.

### 5.3 Non-goals

- This draft does not require full automatic implementation generation.
- This draft does not require all real test runners to be integrated immediately.
- This draft does not define the standalone asset workbench product.
- This draft does not make `spec-web-ui` a required runtime dependency for requirement intake.

### 5.4 MVP Requirements

- The system must allow a raw requirement to be recorded as a draft.
- The process must assign or derive a stable `change-id` before formal planning begins.
- The process must produce or reference a normalized spec under `specs/changes/<change-id>/`.
- The process must generate or reference a test-plan under `tests/plans/`.
- The process must generate or reference normalized test results under `tests/results/`.
- The process must require explicit acceptance before updating `specs/current/`.

### 5.5 Target Requirements

- The system should guide requirement clarification before draft finalization.
- The system should generate a normalized change package from an approved draft.
- The system should compare `specs/current/` and `specs/changes/<change-id>/` to produce impact analysis.
- The system should derive test-plan and test-schedule from the active change package.
- The system should route execution tasks to appropriate agents.
- The system should collect implementation evidence, test evidence, review notes, and acceptance status.
- The system should promote accepted content into `specs/current/` only after gates pass.
- The system should archive completed changes with enough context to reconstruct the delivery.

### 5.6 Open Questions

- What is the minimum normalized spec schema required for a change package in the next MVP?
- What is the minimal contract for importing reusable assets from an external tool site into a project?
- What evidence is required before a change can be promoted into `specs/current/`?
- Which real runners should be integrated first: Bruno, Playwright, unit tests, or scenario-level checks?

## 6. Relationship to spec-web-ui

`spec-web-ui` should be treated as a separate product surface from the requirement intake workflow.

Its role:

- Maintain reusable rules, skills, spec templates, agent templates, workflow templates, and test patterns.
- Help users browse, preview, combine, and export project configuration assets.
- Eventually become an independently maintained and deployed tool site.

Its non-role:

- It should not be the source of truth for a concrete project requirement.
- It should not hold the canonical state of `draft -> change -> test-plan -> result -> acceptance`.
- It should not be required for every requirement intake run.

The project requirement flow may use assets exported from `spec-web-ui`, but after assets are installed or copied into a target project, the requirement lifecycle belongs to the target project repository.

## 7. Naming and Traceability Rules

- A requirement should receive a stable `change-id` before implementation work begins.
- Generated files should include or reference the `change-id`.
- Test plans should reference spec ids, versions, flows, rules, or acceptance criteria.
- Test results should reference the originating test-plan and change context.
- Review notes should name the affected spec, rule, or draft.
- `specs/current/` should only be updated after explicit acceptance.
