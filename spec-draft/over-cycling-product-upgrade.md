# `over-cycling-product-upgrade`

## 目标/Goal

把当前 `products/cycling-agent/` 的杭州优先骑行规划 MVP，逐步升级为符合 `Over Cycling（偶尔骑行）` 产品理念的完整产品。

当前 accepted baseline 仍然是一个“出发前决策”产品：

- `city_ride`
- `weekend_trip`
- 决策优先规划
- Hangzhou-first 路线和目的地模板

目标产品不再只是一次规划工具，而是一个服务“偶尔骑行的人”的骑行陪伴 App，覆盖：

- 骑前：今天适不适合骑、怎么骑
- 骑中：是否继续、是否缩短、补给与安全提醒
- 骑后：总结、反馈、恢复建议
- 长期：习惯养成、偏好记忆、轻量成长感

该升级不能直接把 `docs/design/` 的历史愿景文档当成 accepted truth 覆盖当前实现；需要先把其中可执行、可验证的部分拆成正式 change package。

## 流程

1. 以当前 accepted baseline 为起点，明确 MVP 已实现边界与限制。
2. 从 `docs/design/` 提炼可落地的产品理念、用户模型和领域模型。
3. 先升级“骑前”主链路，使其从单次规划器进化为更完整的个人骑行决策入口。
4. 再补齐“骑后”和“习惯”闭环，形成持续使用理由。
5. 最后视复杂度引入“骑中”能力，而不是一开始就做实时导航式系统。

## 接口

- 现有 `POST /api/v1/ride/plan`
- 现有 `POST /api/v1/ride/plan/stream`
- 现有 `/api/v1/profile/*`
- 后续需要新增或扩展：
  - rider state / readiness
  - ride history / habit summary
  - post-ride reflection
  - contextual recommendation surfaces

## 规则

- 以 `specs/current/` 为 accepted baseline；`docs/design/` 只作为历史产品方向输入。
- 不把产品升级理解成“继续给 planner 加字段”；这次升级本质上是产品边界升级。
- 第一阶段仍以“骑前”场景为核心，不先扩成泛社交、泛训练或重运动数据平台。
- 不引入专业训练导向能力，例如 FTP、功率训练、比赛备赛、排行榜。
- 先统一领域模型，再拆功能；避免继续把 `user_profile`、`lifestyle_profile`、`weather_snapshot`、`habit` 分散演进。
- 每个阶段都需要能落到明确的 API、前端页面、状态流和测试资产。

## 当前差距

- 当前 `UserProfile` 过薄，只能表达少量长期偏好，无法承载完整 rider model。
- 当前系统有天气上下文和风险判断，但没有正式的 `RideReadiness` 领域对象。
- 当前系统是“单次规划返回结果”，没有形成骑后反馈和长期习惯闭环。
- 当前 UI 更像规划工作台，还不是完整的“偶尔骑行”用户产品。
- 当前 accepted baseline 仍然是 Hangzhou-first seed product，不是通用城市级产品。

## 分阶段升级建议

### Phase 1: Planning Core Upgrade

先把 MVP 升级成更完整的“骑前决策产品”。

重点：

- 统一 rider domain model
- 引入 readiness / rider state
- 让首页从“提交请求”进化为“今天怎么骑”的决策入口
- 让结果页从“路线推荐页”进化为“行动建议页”

### Phase 2: Post-Ride And Habit Loop

在不引入复杂硬件依赖的前提下，补齐持续使用理由。

重点：

- ride journal / post-ride summary
- streak / habit score / last ride memory
- 下次建议与恢复建议
- 偏好学习与轻量画像修正

### Phase 3: In-Ride Assistance

只做轻量陪伴，不做重导航。

重点：

- 天气突变提醒
- 疲劳/缩短建议
- 补给和返程提醒
- 轻量安全兜底

## 可能需要新增的核心实体

- `RiderProfile`
- `RiderState`
- `RideReadiness`
- `RideHistory`
- `HabitSummary`
- `PostRideSummary`
- `PreferenceMemory`

## 备注

- 对应历史产品理念的主要参考文档：
  - `docs/design/Over-Cycling-Product-Vision-v0.1.md`
  - `docs/design/01-product-vision.md`
  - `docs/design/03-domain-model.md`
  - `docs/design/CIM.md`
- 对应当前 accepted baseline 的主要参考文档：
  - `specs/current/project-context.md`
  - `specs/current/domain-context.md`
  - `docs/product/04-prd-mvp01-redefined.md`
  - `products/cycling-agent/docs/current-implementation-overview.md`
- 下一步应把这份 draft 拆成一个正式 change package，至少包含：
  - product direction
  - domain model change
  - API and storage change
  - frontend surface change
  - validation and rollout plan
