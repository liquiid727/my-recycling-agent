# Cycling Agent Docs

这是城市 AI 骑行计划 Agent 的集中设计文档目录。

产品面向周末和节假日休闲骑行用户，帮助用户从一句简单询问出发，快速得到可执行的骑行计划。杭州是当前 MVP 的默认城市和首个样板城市，但产品长期不限定在杭州。

## 目录结构

```text
cycling-agent-docs/
  README.md
  docs/
    product/
    technical/
    plans/
    archive/
```

## 说明

### `docs/product/`

产品层文档，回答“为什么做、做什么、MVP 到哪里”：

- `00-overview.md`
- `01-prd-overall.md`
- `02-prd-mvp.md`
- `03-prd-phase2-nearby-trips.md`

### `docs/technical/`

技术层文档，回答“系统怎么设计、字段怎么定、规则怎么落”：

- `03-technical-architecture.md`
- `04-technical-spec.md`
- `07-hangzhou-route-seed-table.md`

### `docs/plans/`

路线与执行层文档，回答“分阶段怎么推进、怎么开始做”：

- `05-roadmap.md`
- `06-implementation-plan.md`
- `07-phase2-nearby-trips-implementation.md`

### `docs/archive/`

归档草稿和原始需求记录：

- `recycle-agent.md`

## 推荐阅读顺序

1. `docs/product/00-overview.md`
2. `docs/product/01-prd-overall.md`
3. `docs/product/02-prd-mvp.md`
4. `docs/product/03-prd-phase2-nearby-trips.md`
5. `docs/technical/03-technical-architecture.md`
6. `docs/technical/04-technical-spec.md`
7. `docs/plans/06-implementation-plan.md`
