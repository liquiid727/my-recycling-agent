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

## Scenario 15: 骑后记录与骑后总结闭环

1. 先完成 Scenario 2，进入 `/plans/:requestNo`
2. 在结果页点击 `记录这次骑行`
3. 验证进入 `/rides/new?sourceRequestNo=...`
4. 验证页面展示关联规划摘要，且“预计骑行”只作为参考显示，不会自动填进“实际时长”
5. 只填写 `实际距离`、`备注`、`标签`，点击 `保存骑行记录`
6. 验证页面跳转到 `/rides/:rideRecordNo`
7. 验证详情页展示：
   - 骑行记录编号
   - 路线标题 / 目的地 / 起点 / 区域
   - 完成情况、体感、收尾感受
   - 骑后总结 headline / summary
   - 恢复建议、下次建议、计划对齐
8. 打开 `/rides`
9. 验证最近记录列表中出现刚保存的记录和 `summary_headline`
10. 打开 `/rides/new`
11. 不填写 `路线标题` 和 `目的地`，直接点击 `保存骑行记录`
12. 验证页面提示 `手动补录至少填写路线标题或目的地。`
13. 填写一条手动记录后再次保存
14. 验证手动记录也能进入详情页，且 `source_request_no` 不会被错误带入

## Scenario 16: 月度骑行总结与回流规划

1. 先完成至少 2 条本月骑行记录，其中至少 1 条为实际完成或缩短
2. 打开 `/rides`
3. 验证页面先显示“本月骑行总结”加载态，再展示 summary band
4. 验证 summary band 至少包含：
   - 当前查看月份
   - 本月记录数 / 骑行日数
   - 总距离 / 总时长
   - 连续周数
   - 当前 `habit_status`
   - 一条 `next_action`
5. 将月份切换到上个月
6. 验证页面只刷新 summary band，不影响最近记录列表的展示
7. 点击 `按这个建议去规划`
8. 验证跳回 `/`
9. 验证首页出现一条 planner handoff 提示，至少包含来源、状态或连续周数
10. 验证首页 intent 与输入框被新的建议文案 seed，且表单规划里能看到被带入的区域 / 时长
11. 在首页直接点击 `开始规划`
12. 验证新一轮规划仍走原有 planner 主链，没有进入空白页或错误态
13. 如可查看请求体或审计，验证 planner 请求里包含 handoff context
14. 打开 `GET /api/v1/admin/ride-monthly-summary-events`
15. 验证最近事件里至少包含：
   - 一条 `summary_request`
   - 点击 CTA 后的一条 `cta_click`
16. 请求非法月份，如 `GET /api/v1/rides/monthly-summary?month=2026-6`
17. 再次打开后台事件列表，验证出现 `invalid_month`

## Scenario 17: 增长回顾与窗口切换

1. 先保证近 90 天内至少有 3 条非 `cancelled` 骑行记录，且最好分布在最近 30 天和更早窗口里
2. 打开 `/rides`
3. 验证页面会独立显示“增长回顾”加载态
4. 验证增长面板成功后至少包含：
   - 当前滚动窗口
   - `growth_status`
   - `review_headline`
   - `review_body`
   - 最长距离 / 连续周数 / 活跃月份
   - 至少一条 milestone
   - 一条 `next_focus`
5. 点击 `近 180 天`
6. 验证只刷新增长面板，不影响月度总结或最近记录列表
7. 打开 `GET /api/v1/rides/growth-review?window_days=180`
8. 验证返回体包含：
   - `ride_growth_review`
   - `growth_status`
   - `milestones`
   - `recent_vs_previous_ride_delta`
9. 点击增长面板里的 `按这个方向继续安排` 或对应 CTA
10. 验证跳回 `/`
11. 验证首页出现一条 planner handoff 提示，至少包含来源、状态或连续周数
12. 验证首页 intent 与输入框被 growth review 的建议文案 seed，且表单规划里能看到被带入的区域 / 时长
13. 打开 `GET /api/v1/admin/ride-monthly-summary-events`
14. 验证最近事件里至少包含：
   - 一条 `growth_review_request`
   - 点击 CTA 后的一条 `growth_review_cta_click`
   - `requested_window_days`
   - `growth_status`
15. 请求非法窗口，如 `GET /api/v1/rides/growth-review?window_days=45`
16. 再次打开后台事件列表，验证出现 `growth_review_invalid_window`
17. 如当前窗口没有实际骑行，验证对应 `growth_review_request` 事件里 `is_zero_growth_review=true`
