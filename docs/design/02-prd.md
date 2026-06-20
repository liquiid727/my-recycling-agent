# Over Cycling PRD

Version: 0.1

## 产品定位

帮助用户真正骑出去。

不是训练平台。

不是比赛平台。

而是骑行陪伴 Agent。

## 核心功能

### 01. 今日适合骑吗

Agent 分析：
- 天气
- 时间
- 状态

输出：
```text
今天适合骑

推荐 25km

预计 90 分钟
```

### 02. 帮我安排骑行

输入：
```text
今天有2小时
```

输出：
```text
推荐35km

河边路线

轻松骑
```

### 03. 骑后总结

输入：
- 骑行记录

输出：
```text
骑行总结

消耗

亮点

建议
```

### 04. 习惯追踪

统计：
```yaml
month_distance
month_rides
streak
```

输出：
```text
本月骑行4次

累计112km
```

### 05. 周末推荐

输入：
```yaml
location
weather
available_time
```

输出：
```yaml
recommended_routes
```

## V1 技术栈

### Frontend
- Next.js
- Shadcn
- Tailwind

### Backend
- NestJS

### Agent
- OpenAI
- Claude

### Storage
- PostgreSQL

### Map
- 高德地图
- Google Maps
