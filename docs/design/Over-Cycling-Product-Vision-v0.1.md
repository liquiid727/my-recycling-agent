# Over Cycling（偶尔骑行）
## Product Vision & Domain Model v0.1

Author: Asa
Date: 2026-06-15

---

# 1. 产品定位

## 产品名称

**Over Cycling（偶尔骑行）**

Slogan:

> 为那些喜欢骑车，但没打算成为骑行大神的人设计。

---

## 核心理念

Over Cycling 不是专业训练平台。

不是 Garmin。

不是 Strava。

不是 TrainerRoad。

而是一个帮助普通人真正骑出去的骑行陪伴 Agent。

解决的问题：

```text
想骑车
↓
不知道什么时候骑
↓
不知道去哪骑
↓
不知道骑多少
↓
懒得规划
↓
最后没骑
```

Over Cycling 的使命：

```text
从想骑
↓
到真的骑出去
```

---

# 2. 目标用户

## 核心用户

程序员、产品经理、设计师、自由职业者等脑力工作者。

特点：

- 长期久坐
- 工作繁忙
- 喜欢户外
- 有自行车
- 骑行频率不高
- 希望保持运动习惯

---

## 用户画像

```yaml
Age:
  25-40

Occupation:
  Programmer
  Product Manager
  Designer

Ride Frequency:
  1-8 rides/month

Bike:
  Road Bike
  Folding Bike
  City Bike

Motivation:
  Relax
  Exercise
  Explore
  Build Habit
```

---

# 3. 用户目标模型

传统骑行产品关注：

- FTP
- 功率
- VO2Max
- 比赛成绩

Over Cycling 关注：

```yaml
Goals:

  Relax
  放松

  Exercise
  活动身体

  Explore
  看看城市和风景

  Social
  和朋友骑车

  Recover
  缓解工作压力

  BuildHabit
  建立骑行习惯
```

---

# 4. 核心产品价值

## Value 01

今天适合骑吗？

---

## Value 02

帮我安排一次轻松的骑行。

---

## Value 03

我已经很久没骑了。

---

## Value 04

周末去哪骑比较舒服？

---

## Value 05

记录我的骑行成长。

---

# 5. 核心领域模型

## User Model

```yaml
User:

  Basic:
    age:
    gender:

  Cycling:
    bike_type:
    experience:
    ride_frequency:

  Habit:
    monthly_rides:
    monthly_distance:

  Preference:
    favorite_routes:
    favorite_distance:

  Status:
    fatigue:
    mood:
    available_time:
```

---

## Ride Readiness Model

用于判断今天是否适合骑车。

```yaml
RideReadiness:

  weather:

  temperature:

  wind_speed:

  available_time:

  fatigue:

  last_ride_days:

  mood:
```

输出：

```yaml
Result:

  Ride Today

  Ride Lightly

  Rest Today
```

---

## Ride Planning Model

输入：

```yaml
Today:

  available_time: 2h

  weather: sunny

  mood: relax
```

输出：

```yaml
Plan:

  distance: 35km

  duration: 2h

  route_type: riverside

  intensity: easy
```

---

## Habit Model

```yaml
Habit:

  ride_count_30d:

  ride_count_90d:

  streak_days:

  average_distance:

  favorite_route:
```

输出：

```text
已经连续 12 天没有骑车

建议本周安排一次恢复骑
```

---

# 6. 用户生命周期

## 骑前

用户问题：

```text
今天适合骑吗？
周末去哪骑？
帮我安排一下。
```

Agent职责：

- 天气分析
- 时间评估
- 骑行建议
- 路线推荐

---

## 骑中

用户问题：

```text
前面有暴雨怎么办？

我有点累了。
```

Agent职责：

- 实时建议
- 补给提醒
- 安全提醒

---

## 骑后

用户问题：

```text
今天骑得怎么样？
```

Agent职责：

- 骑行总结
- 成就反馈
- 习惯记录

---

## 恢复阶段

用户问题：

```text
明天还要骑吗？
```

Agent职责：

- 恢复建议
- 下次骑行规划

---

# 7. V1 Agent 能力

## Today Ride

```text
今天适合骑吗？
```

---

## Ride Planner

```text
帮我安排一次骑行
```

---

## Ride Summary

```text
总结今天的骑行
```

---

## Habit Coach

```text
最近有没有偷懒
```

---

## Weekend Ride

```text
周末推荐路线
```

---

# 8. 不做什么

V1 不做：

- FTP分析
- 功率训练
- 比赛备赛
- 专业教练系统
- 骑行社交社区
- 骑行商城

保持简单。

聚焦：

```text
帮助用户骑出去
```

---

# 9. 产品哲学

很多骑行软件都在帮助用户骑得更快。

Over Cycling 希望帮助用户骑得更久。

不是成为职业骑手。

而是在工作和生活之间，保留一份属于自己的骑行时间。

---

# 10. North Star

```text
每周至少骑一次
``

如果用户持续一年做到这一点。

Over Cycling 就成功了。
