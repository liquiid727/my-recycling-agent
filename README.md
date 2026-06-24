# Over Cycling

[中文](./README.md) | [English](./README.en.md)

Over Cycling 是一个面向城市轻骑行用户的开源 AI 骑行规划系统。

它把一句自然语言请求转换成一份可执行的骑行决策: 去哪骑、骑多远、预留多久、需要注意什么风险，以及为什么今天更适合这样安排。

它服务的是“想更常骑出去的人”，而不是“正在为比赛做训练的人”。

## 功能特性

Over Cycling 当前聚焦两类骑行规划场景：

### 支持场景

- `city_ride`：当天 / 当晚的城市短时骑行
- `weekend_trip`：周末或节假日的周边骑行出游

### 核心能力

- **自然语言规划**  
  从一句话开始，而不是从一大堆表单开始。

- **决策优先输出**  
  返回的不只是路线列表，而是“今天更适合怎么骑”的建议。

- **可解释的结果**  
  输出包含原因、取舍和风险背景，而不是只有黑箱分数。

- **结合天气与路线上下文的规划**  
  系统会组合请求解析、天气信息、候选路线和 POI 增强结果。

- **确定性核心 + 可选 AI 增强**  
  即使 LLM 不可用，主规划链路仍能依赖结构化逻辑和本地数据正常工作。

- **结果持久化与后台维护能力**  
  规划结果可以回看，内容和规则也有对应的后台维护入口。

## 如何运作

运行时，Over Cycling 的主规划链路大致如下：

```text
Web 请求
-> Query 解析
-> 约束不完整时发起澄清
-> 天气查询
-> 路线或行程候选发现
-> 路线 / POI 增强
-> 确定性风险评分
-> 推荐排序
-> 解释与路书生成
-> 结果持久化
-> 前端结果展示
```

### 运行角色

- **Frontend**  
  负责收集用户输入、展示规划进度、呈现已保存结果和后台页面。

- **Backend**  
  负责解析请求、查询天气、发现候选、评分、排序和持久化。

- **Providers**  
  提供可选的天气、地图、POI 和 LLM 外部能力接入。

- **Repositories 与种子数据**  
  提供路线模板、周边目的地、周边行程模板和规划结果存储。

### 示例请求

```text
今晚我有两个小时，想骑一条轻松一点的江边路线，附近最好能喝咖啡。
```

典型输出会包含：

- 一条主推荐路线或周边出游方案
- 预估骑行距离和时长
- 天气和骑行风险背景
- 一段自然语言解释
- 可回看的持久化结果

## 架构

当前运行时是一个 Web 应用，由以下部分组成：

- **Backend:** FastAPI
- **Frontend:** React + Vite
- **Storage:** PostgreSQL
- **Cache:** 默认内存缓存，可切 Redis
- **Weather:** 默认 Open-Meteo
- **Map / POI:** 默认本地 provider，可切 AMap
- **LLM:** 可选 OpenAI-compatible 接入，默认保留确定性 fallback

后端是整个系统的编排中心。前端负责用户输入、过程反馈、结果展示和后台工作流。

## 快速开始

### 运行要求

- Python 3.12+
- Node.js + npm

### 本地运行

在仓库根目录执行：

```bash
make install
make infra-up
make dev
```

启动后访问：

- 前端：`http://127.0.0.1:5173`
- 后端健康检查：`http://127.0.0.1:8000/health`

默认情况下需要本地 PostgreSQL：

- 数据库：PostgreSQL
- 缓存：内存实现（Redis 可选）
- 路线 / POI：本地 provider
- LLM：可选，不配置也能运行

### 常用命令

```bash
make install
make infra-up
make dev
make test
make build
make backend-test
make frontend-test
make frontend-build
```

高级本地验证：

```bash
make infra-up
make infra-down
make storage-test
make amap-test
make llm-test
make spec-check
make asset-check
```

### 配置

根目录 `.env` 会被 `Makefile` 自动加载。

常见配置分组如下：

#### 基础设施

- `CYCLING_AGENT_DATABASE_URL`
- `CYCLING_AGENT_REDIS_URL`

#### 地图 / POI

- `CYCLING_AGENT_ROUTE_PROVIDER_MODE`
- `CYCLING_AGENT_POI_PROVIDER_MODE`
- `CYCLING_AGENT_AMAP_WEB_API_KEY`

#### LLM

- `CYCLING_AGENT_LLM_API_BASE_URL`
- `CYCLING_AGENT_LLM_API_KEY`
- `CYCLING_AGENT_LLM_MODEL`
- `CYCLING_AGENT_LLM_THINKING`

#### 前端

- `VITE_API_PROXY_TARGET`
- `VITE_AMAP_JS_API_KEY`

更细的运行说明见 [products/cycling-agent/README.md](./products/cycling-agent/README.md)。

## 仓库结构

```text
.
├── Makefile
├── products/
│   └── cycling-agent/
│       ├── backend/
│       ├── frontend/
│       ├── data/
│       └── docs/
├── specs/
├── spec-draft/
├── rules/
└── tests/
```

常用入口：

- [products/cycling-agent/](./products/cycling-agent/)：可运行的产品代码
- [products/cycling-agent/backend/](./products/cycling-agent/backend/)：FastAPI 后端
- [products/cycling-agent/frontend/](./products/cycling-agent/frontend/)：React 前端
- [products/cycling-agent/docs/current-implementation-overview.md](./products/cycling-agent/docs/current-implementation-overview.md)：当前实现结构和请求链路说明
- [Makefile](./Makefile)：安装、运行、测试、构建入口

## 仓库是如何组织的

这个仓库不只有应用代码，也包含支撑产品演进的规格、规则和验证资产。

- `products/cycling-agent/`：可运行产品
- `specs/current/`：当前 accepted baseline
- `specs/changes/`：活跃 change package
- `spec-draft/`：需求草稿和早期方案
- `rules/` 与 `.rules/`：工程与工作流规则
- `tests/`：spec-driven 验证资产

## 范围与非目标

当前仓库提供的是一个 Hangzhou-first MVP，这意味着：

- 杭州是当前唯一完整种子城市
- 核心产品是一个包含前后端和本地种子数据的 Web 应用
- 这个系统服务于规划与决策支持，而不是竞赛训练

当前非目标包括：

- FTP 分析
- 功率训练工作流
- 比赛备赛
- 骑行社交网络能力

## 贡献说明

Over Cycling 目前仍是一个持续演进中的 MVP，而不是最终完成品。

这个仓库把应用代码和最小必要的 spec / rule / test 资产放在一起，是为了让改动更容易被提出、实现、审查和验证。

如果你要参与贡献，建议阅读顺序如下：

1. [README.md](./README.md)
2. [specs/current/](./specs/current/)
3. [products/cycling-agent/docs/current-implementation-overview.md](./products/cycling-agent/docs/current-implementation-overview.md)
4. [products/cycling-agent/](./products/cycling-agent/)
5. [tests/](./tests/)

## License

如果仓库准备正式公开发布，建议在根目录补充 `LICENSE` 文件；当前 README 本身不构成许可证声明。
