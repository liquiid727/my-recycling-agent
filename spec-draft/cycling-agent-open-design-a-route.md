# Cycling Agent Open Design A Route Draft

## 背景

当前 `products/cycling-agent/frontend` 是以规划工具为主的 React + Vite 工作台，首页由聊天、结构化表单、阶段状态和结果区复合组成。新的 Open Design 原型把产品表达改成 `Lifestyle 骑行伙伴`，首页以品牌叙事、今日建议、精选路线、AI 伙伴、周末计划和骑行日记为主，不再以传统规划表单为信息架构中心。

## 目标

把用户侧前端整体替换成新的生活方式产品表达，并补齐内容编排后台与新的体验型 API，使首页、结果页、路线详情、偏好页和后台都以同一套内容模型和视觉语言工作。

## 非目标

- 不在本次工作里保留旧首页的主题切换和双模式入口壳子。
- 不要求保留旧的页面构成和组件层级。
- 不把 Open Design HTML 直接作为代码源或事实源。

## 用户角色

- 终端用户：浏览首页、询问 AI 伙伴、查看骑行建议、管理生活方式偏好。
- 内容运营：维护首页文案、今日建议、精选路线、AI 伙伴语气、周末计划模板和日记卡片。
- 路线运营：通过保留的路线/周边游资产能力支持前台内容编排。

## User Flow

1. 用户进入首页，看见品牌化叙事和今日建议，而不是旧的规划控制台。
2. 用户通过 AI 伙伴输入一句生活方式语气的需求，例如想去树多、咖啡或日落附近骑一小圈。
3. 系统返回澄清或直接生成编辑化的结果摘要，并持久化为结果页。
4. 用户进入结果页查看推荐路线、原因、风险提示、停靠建议和轻量日记式文案。
5. 运营在后台维护首页和结果页所依赖的内容块，不直接操作旧的技术后台信息架构。

## System Flow

1. 前端调用体验型首页接口读取首页编排内容和精选资产。
2. 前端调用体验型 companion 接口完成单轮澄清或生成建议。
3. 后端在需要时复用现有规划、路线、天气、风险能力，生成新的体验响应。
4. 结果页和详情页通过新的体验接口读取编辑化结果载荷。
5. 后台通过新的内容编排接口读取和保存内容配置。

## API 草案

- `GET /api/v1/experience/home`
- `POST /api/v1/experience/companion/plan`
- `GET /api/v1/experience/results/{request_no}`
- `GET /api/v1/experience/routes/{route_code}`
- `GET /api/v1/profile/lifestyle`
- `PUT /api/v1/profile/lifestyle`
- `GET /api/v1/admin/experience-content`
- `PUT /api/v1/admin/experience-content`

## 状态机

- 首页：`loading -> ready | error`
- AI 伙伴：`idle -> submitting -> clarification | planned | error`
- 结果页：`loading -> ready | empty | error`
- 路线详情：`loading -> ready | not_found | error`
- 偏好页：`loading -> editing -> saving -> saved | error`
- 内容后台：`loading -> ready -> saving -> saved | error`

## 数据模型

- `hero`
- `today_nudges`
- `curated_routes`
- `companion_persona`
- `weekend_plan_templates`
- `journal_cards`
- `cta_footer`
- `lifestyle_profile`
- `experience_result`

## 业务规则

- 所有用户侧页面必须覆盖 empty / loading / success / failure。
- 前端使用 Tailwind CSS 作为主要样式系统，组件在本仓库本地维护。
- 保留旧 URL，不保留旧页面构成。
- 旧规划和路线能力作为内部能力层复用，不再直接决定首页 IA。

## 异常场景

- 首页内容读取失败
- AI 伙伴输入不足，需要澄清
- AI 伙伴生成失败，规划能力不可用
- 结果页 request_no 不存在
- 路线详情 route_code 不存在
- 内容后台保存失败

## 测试场景

- 首页成功渲染全部主要区块
- 首页内容加载失败
- AI 伙伴返回澄清
- AI 伙伴直接返回推荐结果
- 结果页成功/空态/失败
- 路线详情成功/404
- 偏好页读取与保存
- 内容后台读取与保存

## 运营/后台配置

- 首页品牌文案
- 今日建议条目
- 精选路线分组
- AI 伙伴 persona 和快捷提示
- 周末计划模板
- 骑行日记卡片
- CTA/footer

## 指标与日志

- 首页内容读取成功率
- companion 请求成功率、澄清率、失败率
- 结果页读取成功率
- 内容后台保存成功率

## 待确认问题

- 结果页里保留多少旧规划字段给运营和用户可见。
- 旧 admin 里的路线/风险规则入口在新后台中是直接暴露还是下沉为高级区域。
