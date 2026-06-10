# 城市 AI 骑行计划 Agent 详细技术规格

版本：v0.1  
更新时间：2026-05-31  
状态：草稿

## 1. 目标

本文档补充详细技术设计，覆盖：

- 数据模型设计
- 接口文档设计
- Agent 角色设计
- Agent 协作设计
- MCP 等工具集成
- 前端开发设计
- 后端开发设计
- 具体功能实现

## 2. 数据模型设计

当前工程按 `planning_mode` 隔离两类规划结果：

- `route`：mvp1 路线规划，沿用 `RideRequest`、`RouteTemplate`、`RiskAssessment`、`DecisionResult`。
- `nearby_trip`：mvp2 周边游规划，新增 `NearbyDestination` 与 `TripTemplate`，并在同一个审计链路中保存请求、天气、候选风险和最终决策。

### 2.1 主键与业务编号规范

统一约定如下：

- `id`：数据库主键，统一使用 `uuidv7`
- `xxid` / `xxno`：业务主键，采用 `业务前缀 + uuidv7短串`
- `uid`：用户对外编号，使用 8 位字符串，从 `00000001` 开始顺序递增
- `uuidv7` 短串：从完整 `uuidv7` 派生约 10 位可读短串，供 `xxno` / `xxid` 使用

建议格式示例：

- `request_no`: `RQ-01J8X4K7PM`
- `route_no`: `RT-01J8X4K7PM`
- `decision_no`: `DC-01J8X4K7PM`
- `risk_no`: `RS-01J8X4K7PM`

说明：

- `id` 只用于数据库关联和内部引用
- `xxid` / `xxno` 用于日志、接口返回、人工排查和外部引用
- `uid` 作为稳定的人类可读用户编号，不直接暴露数据库主键
- `uuidv7` 短串建议控制在约 10 位长度，保持可识别且便于排查

### 2.2 核心实体

#### UserProfile

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUIDv7 | 用户数据库主键 |
| uid | string | 用户业务编号，8 位字符串，如 `00000001` |
| nickname | string | 可选昵称 |
| home_region | string | 常用出发区域 |
| fitness_level | string | 体力等级：low / medium / high |
| ride_style_preferences | jsonb | 风格偏好 |
| slope_tolerance | string | 爬坡接受度 |
| created_at | datetime | 创建时间 |

#### RideRequest

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUIDv7 | 请求数据库主键 |
| request_no | string | 请求业务编号，如 `RQ-01J...` |
| user_id | UUIDv7 nullable | 用户主键 |
| raw_query | text | 用户原始输入 |
| city_code | string | 城市编码，MVP 默认 `hangzhou` |
| origin_region | string | 出发区域 |
| origin_place_name | string nullable | 具体出发点或常用出发地名称 |
| origin_lng | numeric nullable | 出发点经度 |
| origin_lat | numeric nullable | 出发点纬度 |
| available_hours | numeric nullable | 可骑时长 |
| target_distance_km | numeric nullable | 目标距离 |
| fitness_level | string | 体力等级 |
| ride_style | string | 休闲 / 刷圈 / 爬坡 / 风景 |
| weather_date | date | 目标日期 |
| parsed_constraints | jsonb | 解析后的结构化约束 |
| created_at | datetime | 创建时间 |

#### RouteTemplate

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUIDv7 | 路线模板数据库主键 |
| route_no | string | 路线业务编号，如 `RT-01J...` |
| city_code | string | 城市编码 |
| name | string | 路线名称 |
| region_tags | jsonb | 所属区域标签 |
| ride_style_tags | jsonb | 风格标签 |
| distance_km | numeric | 距离 |
| elevation_gain_m | numeric | 爬升 |
| estimated_duration_hours | numeric | 预计时长 |
| difficulty_level | string | easy / medium / hard |
| supply_score | integer | 补给便利度 |
| return_difficulty_score | integer | 返程难度 |
| route_source | string | 模板来源 |
| status | string | active / inactive |

#### WeatherSnapshot

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUIDv7 | 快照数据库主键 |
| weather_no | string | 快照业务编号，如 `WS-01J...` |
| city_code | string | 城市编码 |
| region_code | string | 区域编码 |
| forecast_date | date | 日期 |
| temperature_min | numeric | 最低温 |
| temperature_max | numeric | 最高温 |
| precipitation_probability | numeric | 降雨概率 |
| wind_speed | numeric | 风速 |
| wind_direction | string | 风向 |
| weather_summary | string | 天气概述 |
| raw_payload | jsonb | 原始天气返回 |
| fetched_at | datetime | 拉取时间 |

#### RiskAssessment

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUIDv7 | 风险评估数据库主键 |
| risk_no | string | 风险评估业务编号，如 `RS-01J...` |
| request_id | UUIDv7 | 请求主键 |
| route_template_id | UUIDv7 | 路线主键 |
| overall_risk_score | numeric | 总风险分 |
| risk_level | string | low / medium / high |
| weather_risk_score | numeric | 天气风险 |
| climb_risk_score | numeric | 爬升风险 |
| traffic_risk_score | numeric | 道路风险 |
| supply_risk_score | numeric | 补给风险 |
| return_risk_score | numeric | 返程风险 |
| reasons | jsonb | 风险原因列表 |
| mitigation_advice | jsonb | 规避建议 |
| created_at | datetime | 创建时间 |

#### DecisionResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUIDv7 | 决策结果数据库主键 |
| decision_no | string | 决策业务编号，如 `DC-01J...` |
| request_id | UUIDv7 | 请求主键 |
| recommended_route_id | UUIDv7 | 推荐路线主键 |
| backup_route_ids | jsonb | 备选路线 ID 列表 |
| go_decision | string | go / caution / no_go |
| explanation | text | 推荐理由 |
| roadbook | jsonb | 解释型路书 |
| created_at | datetime | 创建时间 |

### 2.3 城市策略配置模型

#### CityStrategyConfig

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUIDv7 | 配置数据库主键 |
| config_no | string | 配置业务编号，如 `CF-01J...` |
| city_code | string | 城市编码 |
| config_type | string | route_rule / seasonal_rule / district_rule / risk_bias |
| config_key | string | 配置键 |
| config_value | jsonb | 配置值 |
| status | string | active / inactive |

### 2.4 样板城市路线库字段设计

MVP 阶段建议优先建设“路线模板库”，而不是完全依赖开放式地图即席生成。这样更容易保证结果质量、本地感和风险可控性。

杭州是第一套样板路线库，其他城市后续复用相同结构扩展自己的路线模板、片区标签和风险规则。

### 2.4.1 RouteTemplate 扩展字段

在基础 `RouteTemplate` 之外，杭州样板路线建议补充以下字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| route_code | string | 人类可读路线编码，如 `HZ-RIVER-001` |
| start_point_name | string | 推荐出发点名称 |
| start_point_lng | numeric | 出发点经度 |
| start_point_lat | numeric | 出发点纬度 |
| end_point_name | string | 终点名称 |
| loop_type | string | loop / out_and_back / one_way |
| district_tags | jsonb | 片区标签，如滨江、西湖、余杭 |
| season_tags | jsonb | 适骑季节标签 |
| best_time_slots | jsonb | 推荐出发时间段 |
| avoid_time_slots | jsonb | 不建议出发时间段 |
| surface_type | string | asphalt / mixed / greenway |
| traffic_level | string | low / medium / high |
| scenic_score | integer | 风景分，1-10 |
| training_score | integer | 训练感分，1-10 |
| beginner_friendly | boolean | 是否适合新手 |
| climb_segments | jsonb | 关键爬坡段信息 |
| supply_points | jsonb | 关键补给点列表 |
| bailout_options | jsonb | 可中止或缩短方案 |
| holiday_penalty_level | string | 节假日拥挤惩罚等级 |
| weather_sensitivity | jsonb | 天气敏感特征 |
| route_notes | text | 本地经验说明 |
| gpx_ref | string nullable | GPX 文件引用 |

### 2.4.2 杭州样板路线样例

#### 样例 1：钱塘江休闲往返线

```json
{
  "route_code": "HZ-RIVER-001",
  "name": "滨江-钱塘江休闲往返线",
  "city_code": "hangzhou",
  "district_tags": ["滨江", "钱塘江"],
  "ride_style_tags": ["relaxed", "scenic", "weekend"],
  "start_point_name": "闻涛路滨江段",
  "loop_type": "out_and_back",
  "distance_km": 42,
  "elevation_gain_m": 180,
  "estimated_duration_hours": 2.8,
  "difficulty_level": "easy",
  "traffic_level": "low",
  "scenic_score": 8,
  "training_score": 4,
  "beginner_friendly": true,
  "best_time_slots": ["06:30-09:30", "16:30-18:30"],
  "avoid_time_slots": ["11:00-15:00"],
  "supply_score": 8,
  "return_difficulty_score": 3,
  "holiday_penalty_level": "medium",
  "weather_sensitivity": {
    "heat": "medium",
    "rain": "medium",
    "crosswind": "medium"
  },
  "route_notes": "适合周末晨骑，风景稳定，整体节奏轻松。"
}
```

#### 样例 2：西湖-龙井轻爬坡线

```json
{
  "route_code": "HZ-HILL-002",
  "name": "西湖-龙井轻爬坡体验线",
  "city_code": "hangzhou",
  "district_tags": ["西湖", "龙井"],
  "ride_style_tags": ["climb", "scenic", "half_day"],
  "start_point_name": "杨公堤南口",
  "loop_type": "loop",
  "distance_km": 36,
  "elevation_gain_m": 520,
  "estimated_duration_hours": 3.2,
  "difficulty_level": "medium",
  "traffic_level": "medium",
  "scenic_score": 9,
  "training_score": 7,
  "beginner_friendly": false,
  "best_time_slots": ["06:00-08:30"],
  "avoid_time_slots": ["09:30-17:00", "节假日全天"],
  "supply_score": 6,
  "return_difficulty_score": 5,
  "holiday_penalty_level": "high",
  "weather_sensitivity": {
    "heat": "high",
    "rain": "high",
    "crosswind": "low"
  },
  "route_notes": "景观好，但游客与机动车干扰更明显，更适合早骑。"
}
```

#### 样例 3：湘湖半日轻度郊游线

```json
{
  "route_code": "HZ-LEISURE-003",
  "name": "湘湖半日郊游线",
  "city_code": "hangzhou",
  "district_tags": ["湘湖", "萧山"],
  "ride_style_tags": ["relaxed", "half_day", "leisure"],
  "start_point_name": "湘湖游客中心",
  "loop_type": "loop",
  "distance_km": 30,
  "elevation_gain_m": 210,
  "estimated_duration_hours": 2.4,
  "difficulty_level": "easy",
  "traffic_level": "low",
  "scenic_score": 8,
  "training_score": 3,
  "beginner_friendly": true,
  "best_time_slots": ["07:00-10:00", "15:30-18:00"],
  "avoid_time_slots": ["12:00-15:00"],
  "supply_score": 7,
  "return_difficulty_score": 2,
  "holiday_penalty_level": "medium",
  "weather_sensitivity": {
    "heat": "medium",
    "rain": "medium",
    "crosswind": "low"
  },
  "route_notes": "适合新手和情侣向休闲骑，骑后可衔接吃饭休息。"
}
```

### 2.5 Phase 2 周边游增量模型

Phase 2 不改变 MVP 的编排主干，而是在路线模板之外增加目的地和周边游方案模板。这样可以把“骑一条路线”扩展为“执行一次半日 / 一日周边骑行计划”，同时继续保持结构化、可审计和可降级。

#### NearbyDestination

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | UUIDv7 | 目的地数据库主键 |
| destination_no | string | 目的地业务编号，如 `DST-HZ-RIVER-CAFE` |
| city_code | string | 城市编码 |
| name | string | 目的地名称 |
| destination_type | string | 公园 / 古镇 / 江边 / 湖区 / 咖啡 / 观景点 |
| region_tags | jsonb | 区域与偏好标签 |
| suitable_duration | jsonb | half_day / one_day |
| stay_duration_minutes | integer | 建议停留时长 |
| crowd_level | jsonb | 平日、周末、节假日拥挤规则 |
| supply_summary | text | 补给和餐饮摘要 |
| public_transport_options | jsonb | 公共交通返程选项 |
| stay_suggestion | text | 到达后的停留建议 |
| status | string | active / inactive |

#### TripTemplate

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| trip_no | string | 周边游方案编号，如 `TRIP-HZ-RIVER-CAFE` |
| city_code | string | 城市编码 |
| route_template_id | string | 关联 mvp1 路线模板 `route_code` |
| destination_no | string | 关联目的地业务编号 |
| name | string | 周边游方案名称 |
| origin_region_tags | jsonb | 适配出发区域 |
| total_duration_hours | numeric | 总出行时长 |
| ride_duration_hours | numeric | 骑行时长 |
| trip_style_tags | jsonb | 周边游标签 |
| return_mode_options | jsonb | 骑回 / 公共交通 / 缩短路线 |
| fallback_plan | text | 降级或撤退方案 |
| status | string | active / inactive |

#### TripDecisionResult

Phase 2 可以复用 `DecisionResult`，并在 `roadbook` 中增加 `trip_plan` 结构；如果后续查询量和分析需求增大，再独立拆表。

建议 `trip_plan` 最小结构：

```json
{
  "trip_name": "湘湖半日休闲骑",
  "destination_name": "湘湖",
  "total_duration_hours": 4.5,
  "ride_duration_hours": 2.4,
  "recommended_departure_time": "08:00",
  "schedule_blocks": [
    {"title": "去程骑行", "duration_minutes": 80},
    {"title": "湖边停留和补给", "duration_minutes": 90},
    {"title": "返程", "duration_minutes": 70}
  ],
  "return_options": ["ride_back", "public_transport"],
  "fallback_plan": "如午后升温明显，缩短湖区绕行并从湘湖站公共交通返程"
}
```

## 3. 接口文档设计

### 3.1 `POST /api/v1/ride/plan`

用途：创建一次骑行决策请求。

请求示例：

```json
{
  "query": "周六早上从滨江出发骑3小时，不想太累，最好风景好一点",
  "target_date": "2026-05-30",
  "city_code": "hangzhou",
  "origin_place": {
    "name": "滨江",
    "region": "滨江"
  },
  "user_profile": {
    "fitness_level": "medium",
    "ride_style_preferences": ["scenic", "relaxed"]
  }
}
```

响应示例：

```json
{
  "request_no": "RQ-01J8X4K7PM",
  "parsed_constraints": {
    "city_code": "hangzhou",
    "origin_region": "滨江",
    "origin_place_name": "滨江",
    "available_hours": 3,
    "ride_style": "scenic_relaxed",
    "fitness_level": "medium"
  },
  "recommended_plan": {
    "go_decision": "go",
    "route_name": "滨江-钱塘江休闲往返线",
    "distance_km": 42,
    "elevation_gain_m": 180,
    "estimated_duration_hours": 2.8,
    "risk_level": "low",
    "summary_reason": "时长匹配，风景好，风险较低"
  },
  "alternatives": []
}
```

### 3.2 `GET /api/v1/ride/plan/{request_no}`

用途：查看完整决策结果和路书详情。

### 3.3 `GET /api/v1/routes/recommended`

用途：获取热门路线模板或首页推荐路线。

支持参数：

- `city_code`
- `origin_region`
- `ride_style`

### 3.4 `POST /api/v1/admin/routes`

用途：录入或更新路线模板。

### 3.5 `POST /api/v1/admin/city-strategy`

用途：维护城市策略配置。MVP 默认维护杭州策略，但接口应保留 `city_code`，避免把城市逻辑写死在实现中。

### 3.6 接口 Schema 草案

#### RidePlanRequest

```json
{
  "type": "object",
  "required": ["query", "target_date"],
  "properties": {
    "query": { "type": "string", "minLength": 3 },
    "target_date": { "type": "string", "format": "date" },
    "city_code": { "type": "string", "default": "hangzhou" },
    "user_profile": {
      "type": "object",
      "properties": {
        "home_region": { "type": "string" },
        "fitness_level": {
          "type": "string",
          "enum": ["low", "medium", "high"]
        },
        "ride_style_preferences": {
          "type": "array",
          "items": { "type": "string" }
        },
        "slope_tolerance": {
          "type": "string",
          "enum": ["avoid", "neutral", "prefer"]
        }
      }
    }
  }
}
```

#### RidePlanResponse

```json
{
  "type": "object",
  "required": ["request_no", "recommended_plan", "alternatives"],
  "properties": {
    "request_no": { "type": "string" },
    "parsed_constraints": { "type": "object" },
    "recommended_plan": {
      "type": "object",
      "required": [
        "go_decision",
        "route_name",
        "distance_km",
        "elevation_gain_m",
        "estimated_duration_hours",
        "risk_level"
      ],
      "properties": {
        "go_decision": {
          "type": "string",
          "enum": ["go", "caution", "no_go"]
        },
        "route_name": { "type": "string" },
        "distance_km": { "type": "number" },
        "elevation_gain_m": { "type": "number" },
        "estimated_duration_hours": { "type": "number" },
        "risk_level": {
          "type": "string",
          "enum": ["low", "medium", "high"]
        },
        "summary_reason": { "type": "string" },
        "risk_reasons": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "alternatives": {
      "type": "array",
      "items": { "type": "object" }
    },
    "roadbook": {
      "type": "object",
      "properties": {
        "departure_window": { "type": "string" },
        "segments": {
          "type": "array",
          "items": { "type": "object" }
        },
        "supply_advice": {
          "type": "array",
          "items": { "type": "string" }
        },
        "mitigation_advice": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

## 4. Agent 角色设计

MVP 推荐采用“一个主编排器 + 两个 LLM Agent + 三个确定性服务模块”的受控协作方式，而不是完全自治多 Agent。

### 4.1 MVP 编排总原则

- 只有 `RidePlanningOrchestrator` 能推进阶段
- 只有 `QueryParserAgent` 和 `RoadbookGeneratorAgent` 允许调用 LLM
- `RoutePlanner`、`RiskEvaluator`、`DecisionEngine` 在 MVP 中保持 deterministic
- 任一阶段只能消费上游的结构化输出，不能绕过中间层直接修改最终结论
- 所有阶段都必须输出 `stage_result` 和 `trace`

### 4.2 RidePlanningOrchestrator

定位：

- 唯一编排入口
- 不直接给用户产出推荐结论
- 只负责阶段调度、上下文装配、失败降级、审计记录

职责：

- 创建一次请求级执行上下文
- 顺序调用 Query Parser、Route Planner、Risk Evaluator、Decision Engine、Roadbook Generator
- 在工具失败、字段缺失、模型异常时执行降级
- 汇总 `request_no`、中间阶段产物、工具调用轨迹、最终响应

输入：

- `query`
- `target_date`
- `city_code`
- `user_profile`

输出：

- `RidePlanResponse`
- `execution_trace`
- `fallback_reason[]`

建议内部接口：

```python
class RidePlanningOrchestrator:
    async def execute(self, payload: RidePlanRequestSchema) -> RidePlanResponseSchema:
        ...
```

### 4.3 QueryParserAgent

定位：

- LLM Agent
- 负责把自然语言转成结构化骑行约束

职责：

- 理解原始 query
- 提取出发区域、时长、目标距离、风格偏好、体力约束、日期偏好
- 判断哪些关键字段缺失
- 输出严格结构化 JSON，不产出路线推荐

允许能力：

- `LLM API`
- 不直接调用地图、POI、天气 MCP

输入：

- 原始 `query`
- `target_date`
- `city_code`
- `user_profile`

输出：

- `ParsedConstraints`
- `missing_fields[]`
- `confidence`

建议输出 Schema：

```json
{
  "origin_region": "滨江",
  "available_hours": 3,
  "target_distance_km": null,
  "ride_style": "scenic_relaxed",
  "fitness_level": "medium",
  "slope_tolerance": "avoid",
  "missing_fields": [],
  "confidence": 0.91
}
```

System Prompt 骨架：

```text
你是骑行查询解析器。你的任务不是推荐路线，而是把用户输入解析为结构化约束。
你必须：
1. 只输出 JSON
2. 不得虚构天气、路线、POI、距离事实
3. 信息不足时保留 null，并写入 missing_fields
4. 优先复用用户画像补全 fitness_level、ride_style_preferences、slope_tolerance
5. ride_style 只允许输出预定义枚举或组合枚举
```

停止条件：

- 输出满足 JSON Schema
- 未满足 Schema 时允许最多 1 次模型重试
- 仍失败则降级到规则解析器

### 4.4 RoutePlanner

定位：

- 确定性服务模块，不是自由 Agent

职责：

- 根据结构化约束从本地路线模板库筛选候选路线
- 必要时调用地图 / POI 服务补充路线上下文
- 生成候选路线及匹配分，不输出最终推荐

允许能力：

- 本地 `RouteTemplateRepository`
- `高德 Web 服务`
- 可选天气 / POI MCP

输入：

- `ParsedConstraints`
- `CityStrategyConfig`
- 路线模板库

输出：

- `route_candidates[]`
- `tool_trace[]`

建议输出字段：

- `route_id`
- `route_no`
- `route_name`
- `match_score`
- `match_reasons[]`
- `distance_km`
- `estimated_duration_hours`
- `poi_summary`

实现原则：

- 先模板库过滤，再做地图增强
- 高德只补事实，不直接决定匹配分
- 候选数量建议限制在 `3 ~ 5`

### 4.5 RiskEvaluator

定位：

- 确定性服务模块，不是自由 Agent

职责：

- 读取天气、路线特征、城市补丁规则
- 为每条路线计算风险分和风险等级
- 输出可解释的结构化风险依据

允许能力：

- `WeatherProvider`
- `RouteProvider`
- `PoiProvider`
- 天气 / 节假日 / 外部知识 MCP

输入：

- `route_candidates[]`
- `weather_snapshot`
- `city_strategy_rules`

输出：

- `risk_assessments[]`

建议输出字段：

- `route_id`
- `risk_no`
- `overall_risk_score`
- `risk_level`
- `dimension_scores`
- `reasons[]`
- `mitigation_advice[]`

实现原则：

- 风险分必须可回放
- 不允许 LLM 直接生成风险分
- 天气缺失时必须标记 `fallback_reason`

### 4.6 DecisionEngine

定位：

- 确定性服务模块，不是自由 Agent

职责：

- 综合匹配度、风险分、城市策略偏置
- 输出主推荐、备选、`go_decision`

输入：

- `route_candidates[]`
- `risk_assessments[]`

输出：

- `recommended_route`
- `alternatives[]`
- `go_decision`
- `decision_reason_codes[]`

建议排序公式：

```text
recommendation_score = match_score - risk_penalty + city_bonus
```

实现原则：

- 排序依据必须结构化可解释
- 不允许下游文案模块覆盖排序结果

### 4.7 RoadbookGeneratorAgent

定位：

- LLM Agent
- 只负责把结构化结论组织成用户可读结果

职责：

- 生成推荐说明
- 生成出发窗口、补给建议、风险规避建议
- 生成解释型 roadbook

允许能力：

- `LLM API`
- 默认不直接调用高德、天气、POI MCP

输入：

- `ParsedConstraints`
- `recommended_route`
- `alternatives[]`
- `risk_assessments[]`

输出：

- `summary_reason`
- `roadbook`
- `user_facing_explanation`

建议 Prompt 骨架：

```text
你是骑行建议解释器。你的任务是把结构化决策结果组织成自然、简洁、可信的中文输出。
你必须：
1. 只使用输入中已提供的事实
2. 不得新增不存在的天气、路线细节、POI、时间结论
3. 不得修改 go_decision、risk_level、distance_km 等结构化结果
4. 优先解释“为什么推荐”和“要注意什么”
5. 文风自然，不要出现 AI 套话
```

停止条件：

- 输出满足 response schema
- 文案失败时使用模板化兜底说明

### 4.8 为什么 MVP 不把五个角色都做成自由 Agent

- `RoutePlanner`、`RiskEvaluator`、`DecisionEngine` 的输出都直接影响推荐正确性
- 这些环节更适合规则、权重和数据库查询，而不是开放式推理
- 这样能显著降低模型幻觉、结果漂移和排障复杂度
- 后续若要升级为更多 Agent，自由度也应建立在当前结构化接口之上

## 5. Agent 协作设计

### 5.1 推荐协作顺序

```text
User Query
  -> RidePlanningOrchestrator
    -> QueryParserAgent
    -> RoutePlanner
    -> RiskEvaluator
    -> DecisionEngine
    -> RoadbookGeneratorAgent
  -> API Response
```

### 5.2 阶段间交接协议

每个阶段都必须输出统一的 `StageResult`：

```json
{
  "stage_name": "query_parser",
  "status": "success",
  "data": {},
  "tool_trace": [],
  "fallback_reason": null,
  "started_at": "2026-05-27T10:00:00Z",
  "finished_at": "2026-05-27T10:00:01Z"
}
```

字段约定：

- `stage_name`：阶段标识
- `status`：`success` / `fallback` / `failed`
- `data`：该阶段结构化输出
- `tool_trace`：本阶段所有工具调用摘要
- `fallback_reason`：降级原因

### 5.3 推荐阶段契约

1. `QueryParserAgent`
输入：原始 query + user_profile  
输出：`ParsedConstraints`

2. `RoutePlanner`
输入：`ParsedConstraints` + 城市策略 + 路线库  
输出：`route_candidates[]`

3. `RiskEvaluator`
输入：`route_candidates[]` + 天气 / 地图上下文 + 风险规则  
输出：`risk_assessments[]`

4. `DecisionEngine`
输入：`route_candidates[]` + `risk_assessments[]`  
输出：`recommended_route` + `alternatives[]` + `go_decision`

5. `RoadbookGeneratorAgent`
输入：结构化推荐结果  
输出：用户可读 explanation + roadbook

### 5.4 协作原则

- 每个 Agent 只负责单一职责
- 决策结果必须保留中间结构化证据
- 生成文案不能反向篡改结构化结论
- 下游阶段不得直接回写上游结构化字段
- 每个阶段必须可单独回放与测试

### 5.5 编排器执行逻辑

```text
if query_parser fails:
  use fallback parser

if route_candidates is empty:
  return no_match response

if weather tool fails:
  mark weather fallback and continue

if roadbook generation fails:
  return templated explanation
```

### 5.6 为什么这样设计

- 容易调试
- 易于替换单模块实现
- 能控制模型幻觉风险
- 后续可平滑升级为更复杂编排

## 6. MCP 与工具集成设计

### 6.1 可集成的工具类型

- 天气工具：获取目标日期天气
- 地图工具：获取路线距离、路径、爬升
- POI 工具：补给点、休息点、咖啡店等

### 6.2 工具接入原则

- 所有外部结果先做归一化
- 工具结果要记录来源和时间
- 关键字段缺失时必须降级

### 6.3 建议的内部工具适配层

定义统一的 provider interface：

- `WeatherProvider`
- `RouteProvider`
- `PoiProvider`

上层 Agent 只依赖接口，不依赖具体服务商。

### 6.3.1 本项目建议接入的外部 API

MVP 阶段建议明确使用以下三类外部能力：

- `LLM API`：负责自然语言解析、推荐理由生成、roadbook 文案润色、缺失参数补问
- `高德地图 Web 服务`：负责地理编码、路径规划、距离计算、POI 搜索、骑行上下文补充
- `Unsplash Access Key`：负责结果页和路线详情页的城市骑行氛围图、封面图、背景图

原则上，这三类能力都通过后端统一代理，不直接由前端暴露密钥。

### 6.3.2 各 API 的职责边界

#### LLM API

适合交给模型的任务：

- 将用户输入解析为结构化约束
- 对多个候选路线生成人类可读解释
- 在字段缺失时生成澄清问题
- 把规则引擎结果组织成自然语言 roadbook

不适合直接交给模型的任务：

- 直接虚构路线距离、海拔、天气、POI 数量
- 直接决定最终风险分
- 绕过规则引擎输出推荐结论

建议接口定义：

- `POST /v1/chat/completions` 或兼容 OpenAI 风格接口
- 模型输出必须限制为 JSON Schema 或结构化对象
- 温度建议 `0.1 ~ 0.3`，优先稳定性而不是发散创意

建议环境变量：

```bash
LLM_API_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=20
```

#### 高德地图 Web 服务

建议使用高德开放平台 Web Service API 承担以下能力：

- 地理编码 / 逆地理编码：识别“滨江”“龙井”“湘湖”等输入
- 路径规划：补充距离、时长、路线概览
- POI 搜索：补给点、咖啡店、便利店、地铁站、医院、卫生间
- 行政区和道路上下文：辅助 route template 匹配与风险补丁

建议优先接入的接口：

- `地理编码 API`
- `逆地理编码 API`
- `路径规划 API`
- `周边搜索 / 关键字搜索 API`
- `输入提示 API`

建议环境变量：

```bash
AMAP_WEB_API_KEY=
AMAP_BASE_URL=https://restapi.amap.com
AMAP_TIMEOUT_SECONDS=10
```

说明：

- 前端如需展示地图，可额外接 JS SDK，但决策核心依然使用后端 Web Service 查询
- 高德返回结果需要统一转换成内部 `RouteProvider` / `PoiProvider` 结构

#### Unsplash Access Key

Unsplash 不参与核心决策，只承担视觉素材补充：

- 首页 Hero 图
- 推荐路线卡片封面
- 路线详情页氛围图

使用原则：

- 仅在前端展示层使用，不进入风险评分和路线决策链路
- 优先缓存已选图片元数据，避免每次请求都重新搜索
- 保留图片作者与来源信息，满足 Unsplash 使用要求

建议环境变量：

```bash
UNSPLASH_ACCESS_KEY=
UNSPLASH_BASE_URL=https://api.unsplash.com
UNSPLASH_TIMEOUT_SECONDS=8
```

推荐搜索词示例：

- `hangzhou cycling`
- `west lake bike`
- `qiantang river trail`
- `tea hill road cycling`

### 6.3.3 API 与 MCP 的组合方式

这里建议把“API 调用”和“MCP 工具调用”视为同一层能力接入，只是协议不同：

- 直连 API：适合稳定、固定、强结构化的数据服务，例如 LLM、高德、Unsplash
- MCP 工具：适合未来可替换、可扩展的外部能力，例如天气、知识检索、额外 POI 数据源

推荐后端统一抽象为：

- `ToolClient`：屏蔽 API / MCP 差异
- `ProviderAdapter`：把原始响应映射到内部 Schema
- `ToolCallLog`：记录请求参数、来源、耗时、失败原因

建议调用顺序：

1. 先用 LLM API 做意图解析，抽取时间、距离、强度、风景偏好、出发区域
2. 再用高德 Web 服务补足地理位置、候选路径距离、POI 和返程信息
3. 如有天气或外部知识 MCP，再补充天气、节假日、拥挤度等上下文
4. 进入规则引擎做风险评分与排序
5. 最后再调用 LLM API 生成推荐说明和 roadbook

这样可以保证：

- 地图、POI、距离等事实来自工具
- 风险判断来自规则
- 可读性解释来自 LLM

### 6.3.4 Agent 到工具的映射

| 模块 | LLM API | 高德 Web 服务 | 天气 / 知识 MCP | Unsplash |
| --- | --- | --- | --- | --- |
| RidePlanningOrchestrator | 否 | 否 | 否 | 否 |
| QueryParserAgent | 是 | 否 | 否 | 否 |
| RoutePlanner | 否 | 是 | 可选 | 否 |
| RiskEvaluator | 否 | 可选 | 是 | 否 |
| DecisionEngine | 否 | 否 | 否 | 否 |
| RoadbookGeneratorAgent | 是 | 否 | 否 | 否 |
| Frontend Presentation Layer | 否 | 可选展示 SDK | 否 | 是 |

MVP 白名单原则：

- `QueryParserAgent` 不得直接访问地图和天气工具
- `RoadbookGeneratorAgent` 不得二次查询外部事实
- `DecisionEngine` 不得依赖 LLM
- 只有 `RoutePlanner` 和 `RiskEvaluator` 可以消费地图 / 天气 / POI 工具数据

### 6.3.5 后端配置与安全要求

- 所有密钥仅存放在后端环境变量或密钥管理系统
- 前端绝不直接持有 `LLM_API_KEY`、`AMAP_WEB_API_KEY`、`UNSPLASH_ACCESS_KEY`
- 外部调用必须配置超时、重试、熔断和日志追踪
- 对 LLM 输出做 JSON 校验，对高德输出做字段完整性校验
- 对 Unsplash 图片结果做缓存，避免触发频控

建议配置对象：

```json
{
  "llm": {
    "base_url": "https://example-llm-provider.com/v1",
    "model": "gpt-4.1-mini",
    "timeout_seconds": 20
  },
  "amap": {
    "base_url": "https://restapi.amap.com",
    "timeout_seconds": 10
  },
  "unsplash": {
    "base_url": "https://api.unsplash.com",
    "timeout_seconds": 8
  }
}
```

### 6.3.6 失败降级策略

- `LLM API` 不可用：返回结构化兜底模板，仅基于规则引擎输出基础推荐文本
- `高德 Web 服务` 不可用：退回本地 route template 数据，不做实时距离与 POI 增强
- `Unsplash` 不可用：使用本地图集、默认封面或纯色占位图
- `MCP` 工具不可用：跳过对应外部上下文，不阻断主推荐链路

## 6.4 Provider 响应归一化 Schema 草案

### NormalizedWeather

```json
{
  "region_code": "binjiang",
  "forecast_date": "2026-05-30",
  "temperature_min": 22,
  "temperature_max": 31,
  "precipitation_probability": 0.15,
  "wind_speed": 4.8,
  "wind_direction": "SE",
  "weather_summary": "cloudy"
}
```

### NormalizedRouteCandidate

```json
{
  "route_template_id": "uuid",
  "route_name": "滨江-钱塘江休闲往返线",
  "distance_km": 42,
  "elevation_gain_m": 180,
  "estimated_duration_hours": 2.8,
  "difficulty_level": "easy",
  "match_score": 0.84,
  "match_reasons": ["时长接近", "新手友好", "风景偏好匹配"]
}
```

### NormalizedPoi

```json
{
  "name": "闻涛路便利店",
  "category": "supply",
  "lng": 120.201,
  "lat": 30.208,
  "open_hours": "06:00-22:00",
  "reliability_score": 0.78
}
```

## 6.5 风险评分规则表和权重

MVP 建议采用可解释的规则评分，而不是直接把风险判断完全交给大模型。

### 6.5.1 总体评分公式

```text
overall_risk_score =
  weather_risk_score * 0.35 +
  climb_risk_score * 0.20 +
  traffic_risk_score * 0.20 +
  supply_risk_score * 0.10 +
  return_risk_score * 0.10 +
  crowd_risk_score * 0.05
```

风险等级建议映射：

- `0.00 - 0.29` -> `low`
- `0.30 - 0.59` -> `medium`
- `0.60 - 1.00` -> `high`

### 6.5.2 规则表

| 维度 | 权重 | 触发规则 | 分值建议 |
| --- | --- | --- | --- |
| 天气 | 0.35 | 降雨概率 >= 0.5 | +0.35 |
| 天气 | 0.35 | 最高温 >= 33C 且路线无遮阴 | +0.25 |
| 天气 | 0.35 | 风速 >= 8m/s 且江边/开阔路线 | +0.25 |
| 爬升 | 0.20 | 爬升 > 500m 且用户体力 low | +0.35 |
| 爬升 | 0.20 | 爬升密度高于城市样板阈值 | +0.20 |
| 道路 | 0.20 | 路线 traffic_level = high | +0.30 |
| 道路 | 0.20 | 节假日热门景区路段 | +0.20 |
| 补给 | 0.10 | 30km 内补给点过少 | +0.25 |
| 补给 | 0.10 | 高温天且补水点稀疏 | +0.30 |
| 返程 | 0.10 | 单向返程困难且 bailout 少 | +0.25 |
| 返程 | 0.10 | 末段逆风明显 | +0.20 |
| 人流 | 0.05 | 西湖 / 龙井假日高峰 | +0.20 |

### 6.5.3 用户画像修正系数

在规则分之外，再加入用户画像修正：

| 条件 | 修正 |
| --- | --- |
| fitness_level = low 且 difficulty = hard | +0.15 |
| slope_tolerance = avoid 且路线含连续爬坡 | +0.10 |
| 用户偏好 scenic 且路线 scenic_score >= 8 | -0.05 |
| 用户偏好 relaxed 且 traffic_level = low | -0.05 |

### 6.5.4 杭州特定规则补丁

- 西湖核心景区在节假日白天默认增加 `crowd_risk_score`
- 龙井及周边爬坡线在夏季午间默认增加 `weather_risk_score`
- 钱塘江沿线在大风天提高横风风险
- 湘湖等休闲线在高温天风险提升较缓，可作为保守备选

## 7. 前端开发设计

### 7.1 页面结构

- 首页
- 结果页
- 路线详情页
- 偏好设置页

### 7.2 组件设计

建议组件：

- `QueryInputPanel`
- `ParsedConstraintChips`
- `RecommendationCard`
- `AlternativeRouteList`
- `RiskBreakdownCard`
- `RoadbookSection`

### 7.3 前端状态设计

核心状态：

- 当前 query
- 解析参数
- 加载态
- 推荐结果
- 风险详情

### 7.4 体验重点

- 首屏输入简单
- 结果结构清楚
- 风险卡片醒目
- 解释文本不要像 AI 套话

### 7.5 前端目录结构草案

```text
products/cycling-agent/frontend/
  src/
    app/
      router.tsx
      providers.tsx
    pages/
      HomePage.tsx
      ResultPage.tsx
      RouteDetailPage.tsx
      SettingsPage.tsx
    components/
      QueryInputPanel.tsx
      ParsedConstraintChips.tsx
      RecommendationCard.tsx
      AlternativeRouteList.tsx
      RiskBreakdownCard.tsx
      RoadbookSection.tsx
    features/
      planner/
        api.ts
        hooks.ts
        schemas.ts
        mappers.ts
      settings/
        store.ts
    lib/
      http.ts
      zod.ts
      constants.ts
    styles/
      tokens.css
      base.css
    tests/
      planner.test.tsx
```

### 7.6 前端 TypeScript Schema 草案

```ts
export type GoDecision = "go" | "caution" | "no_go";
export type RiskLevel = "low" | "medium" | "high";

export interface ParsedConstraints {
  originRegion?: string;
  availableHours?: number;
  targetDistanceKm?: number;
  fitnessLevel?: "low" | "medium" | "high";
  rideStyle?: string;
}

export interface RoutePlanCard {
  routeName: string;
  distanceKm: number;
  elevationGainM: number;
  estimatedDurationHours: number;
  riskLevel: RiskLevel;
  summaryReason: string;
}

export interface RidePlanResponse {
  requestNo: string;
  parsedConstraints: ParsedConstraints;
  recommendedPlan: RoutePlanCard & { goDecision: GoDecision };
  alternatives: RoutePlanCard[];
  roadbook?: {
    departureWindow?: string;
    supplyAdvice?: string[];
    mitigationAdvice?: string[];
  };
}
```

## 8. 后端开发设计

### 8.1 模块划分

建议目录：

```text
backend/
  app/
    api/
    schemas/
    services/
    agents/
    providers/
    repositories/
    models/
    core/
```

### 8.2 服务模块

- `query_service.py`
- `route_service.py`
- `risk_service.py`
- `decision_service.py`
- `roadbook_service.py`

### 8.3 技术要点

- 使用 Pydantic 做请求响应建模
- 使用 SQLAlchemy 或 SQLModel 管理数据模型
- 使用异步 HTTP client 调外部服务
- 使用统一日志字段串联请求链路

### 8.4 后端目录结构草案

```text
products/cycling-agent/backend/
  app/
    main.py
    api/
      routes/
        ride_plan.py
        routes_admin.py
        city_strategy_admin.py
    schemas/
      ride_plan.py
      route_template.py
      risk_assessment.py
    models/
      user_profile.py
      ride_request.py
      route_template.py
      weather_snapshot.py
      risk_assessment.py
      decision_result.py
      city_strategy_config.py
    services/
      ride_planning_service.py
      route_match_service.py
      risk_scoring_service.py
      decision_service.py
      roadbook_service.py
    agents/
      query_parser_agent.py
      route_planner_agent.py
      risk_evaluator_agent.py
      decision_agent.py
      roadbook_generator_agent.py
    providers/
      weather_provider.py
      route_provider.py
      poi_provider.py
    repositories/
      route_template_repository.py
      ride_request_repository.py
      city_strategy_repository.py
    core/
      config.py
      logging.py
      database.py
      cache.py
    tests/
      test_ride_plan_api.py
      test_risk_scoring_service.py
      test_query_parser_agent.py
```

### 8.5 Pydantic Schema 草案

```python
from datetime import date
from pydantic import BaseModel, Field


class UserProfilePayload(BaseModel):
    home_region: str | None = None
    fitness_level: str | None = Field(default=None, pattern="^(low|medium|high)$")
    ride_style_preferences: list[str] = []
    slope_tolerance: str | None = Field(default=None, pattern="^(avoid|neutral|prefer)$")


class RidePlanRequestSchema(BaseModel):
    query: str = Field(min_length=3)
    target_date: date
    city_code: str = "hangzhou"
    user_profile: UserProfilePayload | None = None


class RoutePlanCardSchema(BaseModel):
    route_name: str
    distance_km: float
    elevation_gain_m: float
    estimated_duration_hours: float
    risk_level: str
    summary_reason: str


class RidePlanResponseSchema(BaseModel):
    request_no: str
    parsed_constraints: dict
    recommended_plan: dict
    alternatives: list[dict]
    roadbook: dict | None = None
```

## 9. 具体功能实现说明

### 9.1 自然语言解析

实现方式建议：

- 先规则提取基础实体
- 再用 LLM 补足意图与缺失参数
- 输出严格 JSON Schema

### 9.2 候选路线生成

MVP 建议优先采用：

- 杭州本地人工整理路线模板库
- 按约束做向量或标签过滤
- 必要时补充地图 provider 的基础路线计算

这样比完全让模型自由生成更稳。

### 9.3 风险评分

MVP 建议采用规则评分模型：

- 天气维度权重
- 路线难度维度权重
- 补给与返程维度权重

总分再映射为：

- `low`
- `medium`
- `high`

### 9.4 决策排序

推荐综合分：

`recommendation_score = route_match_score - risk_penalty + city_bonus`

其中：

- `route_match_score`：匹配用户需求程度
- `risk_penalty`：风险惩罚
- `city_bonus`：杭州本地经验偏置

### 9.5 路书生成

路书分段建议输出：

- 为什么推荐这条
- 什么时候出发更合适
- 哪一段是关键路段
- 哪些点适合补给
- 哪些情况应中止或缩短

## 10. 安全与边界

### 10.1 产品边界提示

系统必须明确声明：

- 本建议不替代实时导航
- 极端天气下应以人工判断为准
- 路况变化存在延迟

### 10.2 工程边界

- 外部服务失败要有降级
- 任何模型输出都不能直接跳过结构化校验

## 11. 测试建议

### 11.1 后端测试

- Query 解析单测
- 风险评分规则单测
- 决策排序单测
- API 集成测试

### 11.2 前端测试

- 输入提交流程测试
- 结果页渲染测试
- 风险展示测试

### 11.3 验收测试

准备杭州典型 query 集合，覆盖：

- 休闲骑
- 刷圈
- 轻爬坡
- 高温天
- 大风天
- 降雨天
