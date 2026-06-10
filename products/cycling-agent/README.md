# Cycling Agent MVP

杭州 AI 骑行决策 Agent 的 MVP 工程，覆盖路线推荐、风险评估和解释型路书的最小 Web 闭环。

当前工程按规划模式隔离两类内容：

- `planning_mode=route`：mvp1 路线规划，来源于 `docs/product/02-prd-mvp.md`。
- `planning_mode=nearby_trip`：mvp2 周边游增强，来源于 `docs/product/03-prd-phase2-nearby-trips.md`。

## 目录

- `backend/`: FastAPI API、规则式解析、候选路线排序、风险评分、路书生成
- `frontend/`: React + Vite Web 客户端，负责输入、加载态、结果展示和失败态
- `data/`: 杭州首批样板路线、周边目的地和周边游方案种子
- `docs/current-implementation-overview.md`: 当前实现现状、内部结构和请求链路速览
- `docs/backend-to-ai-agent-tutorial.md`: 面向后端转 AI 应用和 Agent 开发新手的图文教程

## 本地运行

### Backend

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/backend
python3 -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

健康检查：`http://127.0.0.1:8000/health`

默认使用本地 SQLite 文件 `backend/cycling-agent.db`。
如需切换数据库文件位置：

```bash
CYCLING_AGENT_DATABASE_URL=sqlite:///./tmp/cycling-agent.db uvicorn app.main:app --reload
```

当前存储层已经支持两类 `database_url`：

- `sqlite:///...`
- `postgresql://...` / `postgres://...`

当前环境默认仍跑 SQLite，但 `connect()/init_storage()` 已经具备 PostgreSQL 兼容适配层，repository 继续复用统一接口。

当前也已经按技术规格拆出第一版规范化审计实体：

- `ride_requests`
- `weather_snapshots`
- `risk_assessments`
- `decision_results`
- 以及现有的 `ride_plans`、`query_logs`、路线模板与策略表

这样一次规划请求除了完整 payload，还会同步写入请求、天气、逐路线风险和最终决策四类记录，便于后续迁移到 PostgreSQL 时保持实体边界。

当前用户偏好也已经支持后端持久化：

- `GET /api/v1/profile/default`
- `PUT /api/v1/profile/default`

前端 `/settings` 会优先同步远端偏好，再保留本地 `localStorage` fallback，避免同一浏览器里的偏好丢失。

如需本地起真实 `PostgreSQL + Redis`：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent
docker compose -f docker-compose.dev.yml up -d
```

对应环境变量示例：

```bash
export CYCLING_AGENT_DATABASE_URL=postgresql://cycling:cycling@127.0.0.1:54329/cycling_agent
export CYCLING_AGENT_REDIS_URL=redis://127.0.0.1:63799/0
```

默认天气 provider 使用 [Open-Meteo Forecast API](https://open-meteo.com/en/docs)。
当外部天气请求超时或失败时，后端会返回 fallback weather snapshot，并在响应里的 `fallback_reason` 标记降级原因。

LLM 相关能力当前采用“可接入、默认降级”的模式：

- `CYCLING_AGENT_LLM_API_BASE_URL`
- `CYCLING_AGENT_LLM_API_KEY`
- `CYCLING_AGENT_LLM_MODEL`
- `CYCLING_AGENT_LLM_TIMEOUT_SECONDS`

如未配置这些变量，`QueryParserAgent` 和 `RoadbookGeneratorAgent` 会继续使用当前 deterministic fallback，并在 `tool_trace` 中体现。

缓存层当前采用“默认内存缓存、可切 Redis”的方式：

- `CYCLING_AGENT_REDIS_URL`
- `CYCLING_AGENT_WEATHER_CACHE_TTL_SECONDS`
- `CYCLING_AGENT_RIDE_PLAN_CACHE_TTL_SECONDS`

未配置 `CYCLING_AGENT_REDIS_URL` 时，后端会退回进程内内存缓存；配置后会优先使用 Redis。当前缓存覆盖：

- 天气快照短缓存
- 相同输入请求的热查询缓存

地图 / POI provider 当前采用“抽象已接通，默认本地 stub”的模式：

- `CYCLING_AGENT_ROUTE_PROVIDER_MODE=local|amap`
- `CYCLING_AGENT_POI_PROVIDER_MODE=local|amap`
- `CYCLING_AGENT_AMAP_BASE_URL`
- `CYCLING_AGENT_AMAP_WEB_API_KEY`
- `CYCLING_AGENT_AMAP_TIMEOUT_SECONDS`

默认 `local` 会使用本地 route template 和 POI 事实增强，并返回 provider trace。
如果切到 `amap` 但未完成真实接入，系统会自动降级回 template-only 结果，并在 `fallback_reason` 与 `tool_trace` 中体现。
当前 `amap` 已经实现的适配范围：

- `RouteProvider`: 地理编码、逆地理编码、骑行路径规划字段归一化
- `PoiProvider`: 周边 POI 搜索字段归一化

当前仍然保留的限制：

- 没有 live key 时，本地无法证明真实高德端到端调用成功
- 回环路线仍优先复用模板距离与时长，高德更偏向补充起点道路上下文和单向/往返事实

### Frontend

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/frontend
npm install
npm run dev
```

默认地址：`http://127.0.0.1:5173`

前端开发服务器已配置 `/api` 代理到 `http://127.0.0.1:8000`。
如果本机 `8000` 端口被占用，可在启动前端时覆盖代理目标：

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:18000 npm run dev
```

结果页路线图优先加载高德 JS SDK。配置前端 key 后会展示真实地图；未配置或加载失败时，页面会降级展示起终点、补给点和撤退点：

```bash
VITE_AMAP_JS_API_KEY=你的高德JSKey npm run dev
```

## 验证

### Backend tests

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/backend
pytest tests -v
```

如果已经配置可用高德 key，可额外跑 live 集成验证：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/backend
CYCLING_AGENT_AMAP_WEB_API_KEY=你的高德key pytest tests/test_amap_live_integration.py -v
python scripts/verify_amap_live.py
```

如果已经配置可用 LLM 参数，也可额外跑 live 集成验证：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/backend
CYCLING_AGENT_LLM_API_BASE_URL=... \
CYCLING_AGENT_LLM_API_KEY=... \
CYCLING_AGENT_LLM_MODEL=... \
pytest tests/test_llm_live_integration.py -v
python scripts/verify_llm_live.py
```

如果已经起了本地 `PostgreSQL + Redis`，也可额外跑基础设施 live 验证：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/backend
CYCLING_AGENT_DATABASE_URL=postgresql://cycling:cycling@127.0.0.1:54329/cycling_agent \
CYCLING_AGENT_REDIS_URL=redis://127.0.0.1:63799/0 \
pytest tests/test_storage_live_integration.py -v
python scripts/verify_storage_live.py
```

### Frontend tests

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/frontend
npm test
```

### Frontend build

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/frontend
npm run build
```

## 当前接口

- `POST /api/v1/ride/plan`: 创建一次骑行规划并持久化结果
- `POST /api/v1/ride/plan/stream`: 以 `text/event-stream` 返回阶段性规划反馈，并在结束时返回最终结果
- `GET /api/v1/ride/plan/{request_no}`: 读取已保存的规划结果
- `GET /api/v1/routes/recommended`: 按城市、区域、骑行风格读取推荐路线模板
- `GET /api/v1/routes/{route_code}`: 读取单条路线的完整详情，包括时间窗、补给点、撤退方案和关键爬坡段
- `GET /api/v1/profile/default`: 读取默认用户偏好
- `PUT /api/v1/profile/default`: 保存默认用户偏好
- `POST /api/v1/admin/routes`: 录入或更新路线模板
- `GET /api/v1/admin/routes`: 读取后台路线模板列表
- `POST /api/v1/admin/city-strategy`: 录入或更新城市策略配置
- `GET /api/v1/admin/city-strategy`: 读取城市策略配置列表
- `POST /api/v1/admin/risk-rules`: 录入或更新风险规则
- `GET /api/v1/admin/risk-rules`: 读取风险规则列表
- `POST /api/v1/admin/nearby-destinations`: 录入或更新周边目的地模板
- `GET /api/v1/admin/nearby-destinations`: 读取周边目的地模板列表
- `POST /api/v1/admin/trip-templates`: 录入或更新周边游方案模板
- `GET /api/v1/admin/trip-templates`: 读取周边游方案模板列表
- `GET /api/v1/admin/query-logs`: 读取最近的查询日志摘要
- `GET /api/v1/admin/planning-audit/{request_no}`: 读取一次规划的规范化审计记录，请求 / 天气 / 风险 / 决策分开返回

`POST /api/v1/ride/plan` 的响应目前额外包含：

- `weather_snapshot`: 归一化后的天气快照
- `fallback_reason[]`: 外部 provider 降级原因
- `tool_trace[]`: weather / route / poi provider 的调用摘要与降级轨迹

`POST /api/v1/ride/plan/stream` 会先推送 `planning_started`，随后逐步推送 `stage_update`，当前覆盖：

- `query_parser`
- `weather_provider`
- `route_planner`
- `route_provider`
- `poi_provider`
- `risk_evaluator`
- `decision_engine`
- `roadbook_generator`

最后会发送 `plan_ready`，载荷与普通 `POST /api/v1/ride/plan` 一致。

当热查询缓存命中时，`tool_trace` 第一项会出现 `plan_cache`，并为当前请求重新分配新的 `request_no`，随后照常写入持久化与审计表。

当前 `risk_bias` 类型的城市策略配置已经进入推荐链路：

- 可通过 `district_tags` 或 `route_code` 匹配路线
- 可增加 `crowd_risk_delta`、`heat_weather_risk_delta`、`crosswind_weather_risk_delta`
- 可通过 `city_bonus` 直接影响最终推荐排序

当前风险规则维护也已经进入风险评分链路：

- 使用独立的 `/api/v1/admin/risk-rules` 接口维护
- 支持按 `route_code`、`district_tags_any`、天气阈值、路线天气敏感度、补给/返程阈值等条件命中
- 可把增量风险加到 `weather`、`climb`、`traffic`、`supply`、`return`、`crowd` 等维度

当前路线模板库也补齐了第一版详情字段：

- 起终点、路线形态、适骑季节、推荐/规避时段
- 关键补给点、缩短/撤退方案、关键爬坡段
- 路书会直接复用这些事实，而不是只返回通用模板句子

当前 RoutePlanner provider 层也已经落地第一版：

- `RouteProvider` 默认返回结构化路线增强上下文，如平均速度、路线形态、surface type
- `PoiProvider` 默认返回补给点/撤退点摘要
- 首页结果页会展示 provider trace，路书会展示 POI 增强摘要
- `amap` 模式下会尝试调用 geocode / regeo / bicycling / place around，并统一映射到内部字段

当前 QueryParser fallback 也会显式标记信息不足：

- `parsed_constraints` 里包含 `origin_region`、`available_hours`、`target_distance_km`、`ride_style`
- 如存在用户画像，还会补入 `fitness_level`、`slope_tolerance`
- 同时包含 `missing_fields` 和 `confidence`
- 当缺少出发区域或可骑时长等关键字段时，结果页会前置显示澄清提示，而不是假装理解完整

当前后台也支持按 `request_no` 读取结构化审计：

- `ride_request`: 原始输入与解析后的约束
- `weather_snapshot`: 归一化天气事实
- `risk_assessments`: 各候选路线的风险评分明细
- `decision_result`: 最终主推荐、备选和路书

当前业务编号也已经统一到时间有序短号：

- `request_no`: `RQ-<12位时间有序后缀>`
- `decision_no`: `DC-<沿 request_no 派生的后缀>`
- `risk_no`: `RS-<沿 request_no 派生的后缀>`
- `weather_no`: `WS-<沿 request_no 派生的后缀>`

当前也已经预留了 LLM 驱动的两处增强：

- `QueryParserAgent` 可走 OpenAI-compatible `/chat/completions`
- `RoadbookGeneratorAgent` 可走同一 LLM provider 生成更自然的结构化 roadbook

当前结果页也支持 `no_match` 分支：

- 当时长等约束明显超出当前 MVP 模板库支持范围时，会返回 `status=no_match`
- 前端会显示“当前没有合适路线”，而不是硬推默认路线

## 当前前端页面

- `/`: 规划输入、流式阶段反馈、天气状态、主推荐、备选路线、风险拆解、路书
- `/plans/:requestNo`: 已保存的推荐结果页，提交后会跳转到这里并复用后端持久化结果
- `/routes/:routeCode`: 路线详情页，会拉取后端详情接口并展示时间窗、补给点、撤退方案、关键路段
- `/settings`: 偏好设置页，支持远端同步保存，并把 `user_profile` 自动带入规划请求
- `/admin`: 后台维护面，支持路线模板录入、城市策略维护、风险规则维护、查询日志查看

当前 `/admin` 的路线模板维护已经覆盖第一版关键详情字段：

- 起终点、时间窗、季节标签、surface type
- 补给点、撤退方案、关键爬坡段、天气敏感度
- 这些字段会直接影响路线详情页、路书和 provider 增强展示
