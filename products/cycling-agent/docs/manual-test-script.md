# Manual Test Script

## Goal

验证杭州骑行 Agent MVP01 是否完成“自然语言输入 -> 关键追问 -> 决策结论 -> 路线 / 周末出行计划”的基础闭环。

## Preconditions

1. 启动后端：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/backend
uvicorn app.main:app --reload
```

2. 启动前端：

```bash
cd /Users/liquiid/code/cycling-agent-docs/products/cycling-agent/frontend
npm run dev
```

3. 打开 `http://127.0.0.1:5173`

## Scenario 1: 市区即时骑行模糊输入澄清

1. 在输入框中填入 `我今天晚上想出去骑行一下`
2. 点击 `开始规划`
3. 验证系统先提示补充准确出发地点和可骑时长或目标距离
4. 验证页面切换到补齐信息表单，而不是直接生成弱推荐

## Scenario 2: 市区即时骑行成功规划

1. 在输入框中填入 `今晚从闻涛路滨江段出发骑2小时，不要爬坡`
2. 点击 `开始规划`
3. 验证页面先显示 `正在生成今晚骑行建议`
4. 验证首页加载态里会逐步出现阶段反馈，例如 `query_parser`、`weather_provider`、`decision_engine`
5. 验证页面跳转到 `/plans/:requestNo`
6. 验证结果页展示：
   - 决策结论卡片，包含建议去 / 谨慎 / 不建议
   - 1 条主推荐路线
   - 至少 1 条备选路线
   - 风险拆解卡片
   - 天气状态卡片
   - 装备建议
   - 解释型路书
   - 路书中的补给建议和缩短建议
   - 外部增强轨迹区块
   - POI 增强摘要

## Scenario 3: 周末 2 到 3 天游模糊输入澄清

1. 切换到 `周末骑行出行`
2. 输入 `周末想出去骑车，附近有什么推荐线路么`
3. 点击 `开始规划`
4. 验证系统提示补充准确出发点、出行时长和是否接受过夜

## Scenario 4: 周末 2 到 3 天游成功规划

1. 切换到 `周末骑行出行`
2. 输入或表单填写 `这周末想去千岛湖骑两天`
3. 设置出发点为 `闻涛路滨江段`，出行时长为 `两天`，过夜偏好为 `接受过夜`
4. 点击 `开始规划`
5. 验证结果页展示：
   - 决策结论卡片
   - 千岛湖方向主方案
   - 每日节奏
   - 住宿建议
   - 装备建议
   - 天气窗口
   - 返程和撤退方案

## Scenario 5: 空输入校验

1. 清空输入框
2. 点击 `开始规划`
3. 验证页面提示 `请输入你的骑行需求`

## Scenario 6: 无匹配结果

1. 输入 `周六从滨江出发骑12小时，不想太累，最好风景好一点`
2. 点击 `开始规划`
3. 验证页面跳转到 `/plans/:requestNo`
4. 验证结果页出现 `当前没有合适路线`
5. 验证页面没有强推主推荐路线卡片

## Scenario 7: 后端失败态

1. 停止后端服务
2. 重复 Scenario 1
3. 验证页面提示 `规划服务暂时不可用，请稍后再试。`

## Scenario 8: 天气降级提示

1. 将后端的天气 provider 配置为不可访问地址，或断开外网后重新请求
2. 重复 Scenario 1
3. 验证结果页仍有推荐结果
4. 验证天气状态卡片显示 `天气数据已降级`

## Scenario 9: Route/POI provider 降级

1. 启动后端前设置：

```bash
CYCLING_AGENT_ROUTE_PROVIDER_MODE=amap \
CYCLING_AGENT_POI_PROVIDER_MODE=amap \
CYCLING_AGENT_AMAP_WEB_API_KEY=你的高德key \
uvicorn app.main:app --reload
```

2. 如不配置可用 key，直接重复 Scenario 1
3. 验证结果页仍然有推荐结果
4. 验证结果页能看到 provider trace
5. 验证响应对应的 UI 出现 route/poi provider fallback 轨迹，而不是白屏或空结果
6. 如配置了真实 key，再重复 Scenario 1
7. 验证 provider trace 里的 `route_provider` 和 `poi_provider` 显示 `success`
8. 可选：在 backend 目录执行 `pytest tests/test_amap_live_integration.py -v` 或 `python scripts/verify_amap_live.py`，确认输出 JSON 中 `roadbook.route_context.provider_name` 为 `amap-route`

## Scenario 10: LLM live 验证

1. 启动后端前设置：

```bash
CYCLING_AGENT_LLM_API_BASE_URL=你的兼容接口 \
CYCLING_AGENT_LLM_API_KEY=你的key \
CYCLING_AGENT_LLM_MODEL=你的model \
uvicorn app.main:app --reload
```

2. 重复 Scenario 1
3. 验证结果里的 `tool_trace` 中 `query_parser` 和 `roadbook_generator` 显示 `success`
4. 可选：在 backend 目录执行 `pytest tests/test_llm_live_integration.py -v` 或 `python scripts/verify_llm_live.py`

## Scenario 11: 路线详情页

1. 在首页成功生成结果后，点击主推荐卡片
2. 验证进入 `/routes/:routeCode`
3. 验证页面能看到：
   - 起点、终点、路线形态
   - 推荐时间窗和规避时段
   - 补给点列表
   - 缩短或撤退方案
   - 关键路段或爬坡段

## Scenario 12: 后台维护面

1. 打开 `http://127.0.0.1:5173/admin`
2. 验证页面能看到：
   - 路线模板列表
   - 城市策略列表
   - 风险规则列表
   - 查询日志列表
3. 在城市策略表单里填入策略键和配置 JSON，点击 `保存策略`
4. 验证新策略出现在策略列表中
5. 在风险规则表单里填入规则键和规则 JSON，点击 `保存风险规则`
6. 验证新规则出现在风险规则列表中
7. 从任意一次成功规划里记下 `requestNo`
8. 打开 `GET /api/v1/admin/planning-audit/{requestNo}`
9. 验证返回里同时包含 `ride_request`、`weather_snapshot`、`risk_assessments`、`decision_result`

## Scenario 13: 用户偏好远端同步

1. 打开 `http://127.0.0.1:5173/settings`
2. 验证页面会先尝试同步已保存偏好
3. 修改 `体力等级`、`爬坡接受度` 和 `风格偏好`
4. 点击 `保存偏好`
5. 验证页面提示 `偏好已保存，下次规划会自动带入。`
6. 打开 `GET /api/v1/profile/default`
7. 验证返回里包含默认用户偏好，且 `uid = 00000001`
8. 返回首页重新发起规划
9. 验证请求会自动带上刚保存的 `user_profile`

## Scenario 14: PostgreSQL + Redis live 验证

1. 在 `products/cycling-agent/` 目录执行：

```bash
docker compose -f docker-compose.dev.yml up -d
```

2. 启动后端前设置：

```bash
export CYCLING_AGENT_DATABASE_URL=postgresql://cycling:cycling@127.0.0.1:54329/cycling_agent
export CYCLING_AGENT_REDIS_URL=redis://127.0.0.1:63799/0
```

3. 在 backend 目录执行 `pytest tests/test_storage_live_integration.py -v` 或 `python scripts/verify_storage_live.py`
4. 验证第二次相同请求命中 `plan_cache`
5. 验证写入城市策略或风险规则后，后续相同请求不再继续命中旧 cache
6. 验证 `GET /api/v1/admin/planning-audit/{requestNo}` 仍然能返回结构化审计记录
