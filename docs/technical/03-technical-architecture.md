# 城市 AI 骑行计划 Agent 技术架构总览

版本：v0.1  
更新时间：2026-05-31  
状态：草稿

## 1. 技术目标

技术方案需要同时满足三件事：

- 快速做出以杭州为默认城市的 Web MVP
- 支撑 A+B+C 的能力演进
- 支撑城市策略层复制到其他城市
- 保证后续可迁移到微信小程序

建议技术栈：

- 前端：React
- 后端：Python FastAPI
- Agent 编排：后端服务内实现，必要时接入外部模型与 MCP 工具
- 数据存储：PostgreSQL + Redis

## 2. 总体架构

```text
React Web
   |
   | HTTP / SSE
   v
FastAPI API Gateway
   |
   +-- RidePlanningOrchestrator
   |    +-- QueryParserAgent
   |    +-- RoutePlanner
   |    +-- RiskEvaluator
   |    +-- DecisionEngine
   |    +-- RoadbookGeneratorAgent
   |
   +-- City Strategy Layer (Hangzhou first)
   +-- Weather Provider
   +-- Map / Route Provider
   +-- POI / Supply Provider
   |
   +-- PostgreSQL
   +-- Redis
   +-- Observability / Logs
```

## 3. 分层设计

### 3.1 前端层

负责：

- 用户输入与参数补充
- 展示推荐结果
- 展示风险卡片与路书
- 支持流式返回和可解释反馈

### 3.2 API 层

FastAPI 作为统一入口，负责：

- 请求校验
- 会话管理
- 流式结果返回
- 聚合内部服务结果

### 3.3 决策服务层

MVP 阶段建议采用“一个编排器 + 两个 LLM Agent + 三个确定性模块”：

1. `RidePlanningOrchestrator`：唯一编排入口，负责阶段调度、上下文装配、降级和审计
2. `QueryParserAgent`：LLM Agent，负责把自然语言解析成结构化约束
3. `RoutePlanner`：确定性模块，负责候选路线筛选与地图增强
4. `RiskEvaluator`：确定性模块，负责天气 / 路线 / 规则风险评分
5. `DecisionEngine`：确定性模块，负责排序、主推荐与备选决策
6. `RoadbookGeneratorAgent`：LLM Agent，负责把结构化结论组织为自然语言说明和路书

### 3.4 城市策略层

通过配置和规则隔离城市差异：

- 城市片区划分
- 常用路线模板
- 风险规则偏置
- 热门时间段与区域经验

MVP 默认加载杭州策略，但请求模型仍应显式保留 `city_code` 和出发地点字段。缺少出发地点时不能直接生成路线，应返回澄清提示或参数缺失状态。

### 3.5 数据与工具层

外部能力包括：

- 天气数据
- 地图 / 路线规划
- POI / 补给点信息
- 可选 MCP 工具

## 4. 为什么选 FastAPI + React

### 4.1 FastAPI

适合本项目，因为：

- Python 生态适合 Agent、规则引擎和数据处理
- 易于接模型调用和外部工具
- 对异步 IO、SSE、API 聚合友好

### 4.2 React

适合本项目，因为：

- 结果页适合做组件化分块展示
- 后续迁移到小程序时，交互模型清晰
- 方便先快速验证输入和结果呈现

## 5. 核心请求链路

### 5.1 主请求流程

当前工程使用 `planning_mode` 隔离 mvp1 和 mvp2：

- `planning_mode=route`：Phase 1 / mvp1 路线规划。
- `planning_mode=nearby_trip`：Phase 2 / mvp2 周边半日游、一日游规划。

1. 前端提交自然语言请求
2. FastAPI 接收并创建请求上下文
3. `RidePlanningOrchestrator` 创建执行上下文
4. `QueryParserAgent` 提取结构化约束
5. `RoutePlanner` 生成候选路线并补充地图 / POI 事实
6. `RiskEvaluator` 对路线逐条评估
7. `DecisionEngine` 排序并给出结论
8. `RoadbookGeneratorAgent` 生成最终文案
9. 前端展示推荐、备选和路书

### 5.2 Phase 2 周边游流程

Phase 2 不新增自由 Agent，仍由 `RidePlanningOrchestrator` 调度。天气获取之后，`nearby_trip` 模式同时读取路线模板、周边目的地模板和周边游方案模板：

1. `QueryParserAgent` 解析城市、出发地点、半天 / 一天、目的地偏好、体力和返程偏好。
2. `TripPlanner` 用 `TripTemplate` 关联 `RouteTemplate` 与 `NearbyDestination`，按出发区域、时长、目的地偏好、返程偏好和风险排序。
3. `RiskEvaluator` 复用 mvp1 路线风险，并在 trip 结果中前置天气、拥挤、体力和返程风险。
4. `DecisionEngine` 输出 1 个主周边游方案和 1 到 2 个备选方案。
5. `TripRoadbookGenerator` 输出节奏安排、目的地停留、返程和撤退方案，不虚构目的地事实。

### 5.3 降级流程

当外部依赖不稳定时：

- 地图服务失败：降级到本地路线模板库
- 天气服务失败：降级到基础路线推荐并提示天气未更新
- POI 数据不足：隐藏补给精细建议，保留基础提醒

## 6. 数据存储设计

### 6.1 PostgreSQL

存储：

- 路线模板
- 城市策略配置
- 查询日志
- 风险规则
- 用户偏好

### 6.2 Redis

用途：

- 热门查询缓存
- 天气数据短缓存
- 会话态和中间结果缓存

## 7. Agent 架构策略

MVP 不建议做完全自由的多智能体自治系统，而建议做：

- 一个主编排器：`RidePlanningOrchestrator`
- 两个 LLM Agent：`QueryParserAgent`、`RoadbookGeneratorAgent`
- 三个确定性模块：`RoutePlanner`、`RiskEvaluator`、`DecisionEngine`
- 工具调用受控，能力白名单明确

这样可以降低不可控性，提高可解释性与调试效率。

关键边界：

- 只有编排器可以推进阶段
- 只有两个 LLM Agent 可以访问 `LLM API`
- 风险评分和最终排序不交给 LLM，而交给规则和权重模型
- 下游文案模块不得回写上游结构化结论

## 8. MCP / 工具集成策略

MCP / API 适合接入以下能力：

- 天气查询
- 地图搜索
- POI 获取
- 可选的外部知识查询
- 页面视觉素材获取

原则：

- 关键决策逻辑留在本系统
- 工具只提供数据，不直接决定结论
- 每次工具结果要进入统一归一化层
- 工具访问权限按模块白名单控制

MVP 工具分配：

- `QueryParserAgent`：只允许使用 `LLM API`
- `RoutePlanner`：允许使用高德地图 Web 服务，可选接 POI / 地图类 MCP
- `RiskEvaluator`：允许使用天气 / 节假日 / 外部知识 MCP，可选复用地图上下文
- `DecisionEngine`：不直接调用外部工具
- `RoadbookGeneratorAgent`：只允许使用 `LLM API`，不允许二次查询地图和天气事实
- `Frontend`：展示层可使用 `Unsplash`，但不进入决策链路

## 9. 可观测性

必须记录：

- 原始用户输入
- 解析后的约束
- 候选路线集合
- 每条路线的风险评分
- 最终推荐结果
- 失败原因和降级路径

这样后续才能优化规则、提示词和城市策略。

## 10. 部署建议

MVP 建议采用单仓前后端分离部署：

- 前端：Vercel 或静态站点托管
- 后端：云主机 / 容器部署 FastAPI
- 数据库：托管 PostgreSQL
- 缓存：托管 Redis

后续若进入小程序，再新增小程序 API 接入层即可。
