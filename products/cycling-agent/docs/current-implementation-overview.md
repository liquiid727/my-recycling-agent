# Cycling Agent MVP Current Implementation Overview

本文档记录当前 MVP 的工程现状，方便快速理解代码如何组织、一次规划请求如何流转，以及哪些能力已经落地。

Traceability:

- Product source: `docs/product/04-prd-mvp01-redefined.md` for the current MVP01 product definition; `docs/product/02-prd-mvp.md` and `docs/product/03-prd-phase2-nearby-trips.md` remain legacy / engineering-mode references
- Technical source: `docs/technical/03-technical-architecture.md`, `docs/technical/04-technical-spec.md`
- Implementation plan source: `docs/plans/08-mvp01-redefined-implementation-plan.md`
- Code root: `products/cycling-agent/`

## 1. 当前定位

当前项目已经从设计文档推进到可运行的 MVP 工程。产品口径按 `planning_scene` 识别真实场景，工程仍保留 `planning_mode` 兼容路径：

- `planning_scene=city_ride`：今晚 / 下午市区即时骑行，工程路径仍使用 `planning_mode=route`。
- `planning_scene=weekend_trip`：周末 / 节假日 2 到 3 天附近骑行出行，工程路径仍使用扩展后的 `planning_mode=nearby_trip`。

- 后端：FastAPI，提供骑行规划、路线目录、用户偏好、后台维护和规划审计 API。
- 前端：React + Vite，提供首页规划、结果页、路线详情、设置页和后台页。
- 数据：`data/hangzhou_routes.json`、`data/hangzhou_nearby_destinations.json`、`data/hangzhou_trip_templates.json` 作为杭州 mvp1 / mvp2 模板种子。
- 基础设施：默认 SQLite + 内存缓存，可切 PostgreSQL + Redis。
- 外部能力：天气默认 Open-Meteo；路线/POI 可切高德；LLM 可接 OpenAI-compatible API，未配置时走 deterministic fallback。

## 2. 目录结构

```text
products/cycling-agent/
  README.md
  docker-compose.dev.yml
  data/
    hangzhou_routes.json
    hangzhou_nearby_destinations.json
    hangzhou_trip_templates.json
  backend/
    app/
      agents/
      api/routes/
      core/
      providers/
      repositories/
      schemas/
      services/
    scripts/
    tests/
    pyproject.toml
  frontend/
    src/
      app/
      components/
      features/
      pages/
      tests/
      styles.css
    package.json
    vite.config.ts
  docs/
    current-implementation-overview.md
    manual-test-script.md
```

不纳入人工理解主线的内容：

- `frontend/node_modules/`: 前端依赖。
- `frontend/dist/`: 构建产物。
- `backend/.deps/`, `__pycache__/`, `.pytest_cache/`: 本地依赖或缓存。
- `*.json`, lockfile, 数据库文件：JSON/lockfile/SQLite 不能安全加入代码注释，需通过文档说明。

## 3. 后端结构

后端入口是 `backend/app/main.py`。`create_app()` 会读取配置、初始化存储、构建 provider、种子化路线模板、挂载 API 路由。

主要模块：

- `agents/query_parser_agent.py`: QueryParserAgent 的 deterministic fallback，负责把自然语言需求解析成结构化约束，并生成澄清提示。
- `api/routes/ride_plan.py`: 规划入口，包含普通 `POST /api/v1/ride/plan` 和 SSE `POST /api/v1/ride/plan/stream`。
- `api/routes/route_catalog.py`: 推荐路线列表和路线详情。
- `api/routes/profile.py`: 默认用户偏好读取与保存。
- `api/routes/admin.py`: 路线模板、周边目的地、周边游模板、城市策略、风险规则、查询日志、审计记录后台接口。
- `core/config.py`: 环境变量配置。
- `core/storage.py`: SQLite/PostgreSQL 兼容存储初始化与轻量迁移。
- `core/cache.py`: 内存缓存和 Redis 缓存统一接口。
- `providers/`: 天气、路线、POI、LLM provider。
- `repositories/`: 数据访问层，保持 API/服务不直接写 SQL。
- `schemas/ride_plan.py`: Pydantic API schema 和审计 schema。
- `services/`: 路线匹配、周边游匹配、风险评分、城市策略、路书、主编排器。

## 4. 一次规划请求如何流转

当前主链路集中在 `services/ride_planning_orchestrator.py`。`planning_scene=city_ride` 的 `planning_mode=route` 链路为：

```text
用户输入
-> ride_plan API
-> RidePlanningOrchestrator / build_demo_plan()
-> QueryParserAgent fallback 或 LLM 解析
-> WeatherProvider 获取或兜底天气
-> Route template library + RouteProvider 增强
-> PoiProvider 增强补给/撤退点
-> RiskScoringService 计算确定性风险
-> CityStrategyService 套用杭州本地策略
-> DecisionEngine 选择主推荐和备选
-> RoadbookService 或 LLM 生成路书和装备建议
-> DecisionSummary 生成建议去 / 谨慎 / 不建议的结论
-> 持久化完整结果、查询日志、结构化审计
-> 返回普通 JSON 或 SSE plan_ready
```

`planning_scene=weekend_trip` 的 `planning_mode=nearby_trip` 在天气之后切到周边出行模板链路：

```text
用户输入
-> ride_plan API
-> RidePlanningOrchestrator / build_demo_plan()
-> QueryParserAgent fallback 或 LLM 解析
-> WeatherProvider 获取或兜底天气
-> Trip template library + NearbyDestination library + Route template library
-> RiskScoringService 计算路线基础风险
-> TripPlanner 计算目的地、时长、偏好、过夜、住宿、返程匹配分
-> DecisionEngine 选择主周边游和备选
-> TripRoadbookGenerator 生成多天节奏、住宿、装备、天气窗口、返程和撤退方案
-> DecisionSummary 生成周末出行结论
-> 持久化完整结果、查询日志、结构化审计
-> 返回普通 JSON 或 SSE plan_ready
```

当前阶段事件会进入 `tool_trace`，SSE 模式会逐步推送：

- `query_parser`
- `weather_provider`
- `route_planner`
- `route_provider`
- `poi_provider`
- `risk_evaluator`
- `decision_engine`
- `roadbook_generator`

mvp2 额外包含：

- `trip_planner`
- `trip_roadbook_generator`

## 5. 当前核心业务能力

已经落地：

- 自然语言需求解析：出发点、可骑时长、目标距离、骑行风格、体能、坡度容忍、`planning_scene`、周末天数、过夜偏好。
- 澄清提示：当缺少准确出发点、时间预算、周末天数或过夜偏好时，先提示补充信息。
- 决策优先输出：响应新增 `decision_summary`，先给建议去 / 谨慎 / 不建议、原因、可信依据和装备建议。
- 模板路线推荐：基于杭州路线库做匹配和排序。
- 天气事实：Open-Meteo 正常返回时使用真实快照，失败时返回 fallback snapshot。
- 路线/POI provider trace：默认本地增强，可切高德模式。
- 风险评分：天气、爬升、交通、补给、返程、人流等维度。
- 城市策略：`risk_bias` 可影响风险和推荐分。
- 风险规则后台维护：支持可配置风险增量规则。
- 路书：基于结构化事实生成分段建议、补给、撤退和风险提示。
- no_match 分支：模板库无法匹配时不强推默认路线。
- 热查询缓存：相同输入可命中缓存，但会重新分配 request_no 并继续持久化。
- 结构化审计：请求、天气、候选风险、最终决策分表保存。
- 周边出行模式：支持主周边出行方案、1 到 2 个备选方案、目的地停留、多天节奏、住宿、装备、天气窗口、天气 / 拥挤 / 体力 / 返程风险和 fallback plan。
- 周边后台维护：支持 `NearbyDestination` 和 `TripTemplate` 维护，TripTemplate 显式关联 mvp1 路线模板与周边目的地模板。

## 6. 前端结构

前端入口是 `frontend/src/main.tsx`，路由定义在 `frontend/src/app/router.tsx`。

页面：

- `/`: `HomePage.tsx`，输入需求、切换“今晚 / 下午骑一下”和“周末骑行出行”场景、展示阶段反馈、澄清提示和即时规划结果。
- `/plans/:requestNo`: `PlanResultPage.tsx`，读取后端保存的规划结果。
- `/routes/:routeCode`: `RouteDetailPage.tsx`，查看路线模板详情。
- `/settings`: `SettingsPage.tsx`，编辑体能、坡度容忍、骑行风格，并同步到后端。
- `/admin`: `AdminPage.tsx`，维护路线模板、周边目的地、周边游方案模板、城市策略、风险规则，查看查询日志。

主要前端模块：

- `features/planner/api.ts`: 封装规划请求、SSE 解析、路线详情和历史结果读取。
- `features/planner/hooks.ts`: 管理首页规划流程状态，SSE 失败时回退普通请求。
- `features/settings/store.ts`: 用户偏好远端同步与 localStorage fallback。
- `components/*`: 结果展示组件，包括推荐卡片、天气、风险拆解、路书、备选路线。

## 7. 存储与外部依赖

默认本地运行：

- Database: `sqlite:///./cycling-agent.db`
- Cache: in-memory
- Weather: Open-Meteo + fallback
- Route/POI: local provider
- LLM: 未配置时关闭，走 deterministic fallback

可选 live 运行：

- PostgreSQL: `docker-compose.dev.yml` 暴露 `54329`
- Redis: `docker-compose.dev.yml` 暴露 `63799`
- AMap: 配置 `CYCLING_AGENT_AMAP_WEB_API_KEY`
- LLM: 配置 `CYCLING_AGENT_LLM_API_BASE_URL`, `CYCLING_AGENT_LLM_API_KEY`, `CYCLING_AGENT_LLM_MODEL`

## 8. 测试与验证资产

后端测试覆盖：

- API：规划、路线、用户偏好、后台、审计。
- 服务：路线匹配、风险评分、城市策略、路书。
- provider：天气、路线、POI、LLM fallback/live 边界。
- 存储：SQLite/PostgreSQL 兼容层、缓存层、业务编号。

前端测试覆盖：

- 首页提交和状态展示。
- no_match 与澄清提示。
- 结果页、路线详情页、设置页、后台页。
- 天气卡片和结果渲染组件。

常用验证命令：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/backend
pytest tests -v

cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/frontend
npm test
npm run build
```

## 9. 当前限制

- 路线推荐仍以杭州模板库为核心，高德更多用于补充上下文，不是完整动态路径规划。
- 没有 live key 时，无法证明高德和 LLM 的真实端到端调用质量。
- 风险评分是 MVP 规则引擎，不是模型学习结果。
- 前端仍是 MVP 工作台形态，但用户可见主入口已经改为真实使用场景；后台维护表单仍偏工程化。
- JSON 数据、lockfile、SQLite 数据库和构建产物不能加代码注释，后续理解以本文档和 schema 为主。

## 10. 快速阅读顺序

1. `products/cycling-agent/README.md`
2. `products/cycling-agent/docs/current-implementation-overview.md`
3. `products/cycling-agent/backend/app/services/ride_planning_orchestrator.py`
4. `products/cycling-agent/backend/app/schemas/ride_plan.py`
5. `products/cycling-agent/frontend/src/features/planner/api.ts`
6. `products/cycling-agent/frontend/src/pages/HomePage.tsx`
7. `products/cycling-agent/frontend/src/pages/AdminPage.tsx`
