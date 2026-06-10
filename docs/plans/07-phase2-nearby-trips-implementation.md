# Phase 2 Nearby Trips Implementation Notes

版本：v0.1  
更新时间：2026-05-31  
状态：mvp2 分支实现记录

## 1. 来源

- Product PRD: `docs/product/03-prd-phase2-nearby-trips.md`
- Technical architecture: `docs/technical/03-technical-architecture.md`
- Technical spec: `docs/technical/04-technical-spec.md`
- Code root: `products/cycling-agent/`

## 2. 隔离方式

Phase 1 已有能力保留为 `planning_mode=route`，在工程说明中称为 mvp1。

Phase 2 新增能力使用 `planning_mode=nearby_trip`，在工程说明中称为 mvp2。两者复用天气、风险、缓存、持久化和审计基础设施，但保持以下隔离：

- 输入：mvp2 增加 `duration_bucket`、`destination_preferences`、`return_preference`。
- 数据：mvp2 新增 `hangzhou_nearby_destinations.json` 与 `hangzhou_trip_templates.json`。
- 服务：mvp2 新增 `nearby_trip_planner.py`，不改写 mvp1 路线排序语义。
- UI：首页有“路线规划 / 周边游”模式入口；结果页对周边游优先展示 trip 方案、节奏、返程和风险。
- 后台：mvp2 新增周边目的地模板与周边游方案模板维护。

## 3. 已落地内容

用户端：

- 周边游模式入口
- 城市和出发地点输入沿用 mvp1 表单，出发地点仍为必填核心字段
- 半天 / 一天时间选择
- 目的地偏好选择
- 周边游结果页
- 节奏安排展示
- 返程和撤退方案展示

后台：

- 周边目的地模板维护
- 路线模板与目的地模板通过 `TripTemplate.route_template_id` 和 `destination_no` 关联
- 目的地停留建议维护
- 返程方式配置
- 节假日拥挤风险在 `NearbyDestination.crowd_level` 中维护
- 周边游查询日志复用 `query_logs`，推荐名称记录为主 trip 名称

数据模型：

- `NearbyDestination`
- `TripTemplate`
- `RidePlanRequestSchema.planning_mode`
- `RidePlanResponseSchema.recommended_trip`
- `RidePlanResponseSchema.trip_alternatives`
- `RidePlanResponseSchema.trip_rhythm`
- `RidePlanResponseSchema.trip_risks`

## 4. 验证命令

后端：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/backend
PYTHONPATH=.:.deps /Users/liquiid/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/test_nearby_trip_api.py tests/test_admin_catalog_api.py tests/test_query_log_api.py -q
```

前端：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/frontend
npm test -- src/tests/admin-page.test.tsx src/tests/home-page.test.tsx src/tests/nearby-trip-result.test.tsx
npm run build
```

