# Cycling Intelligence Model (CIM)

Version: 0.1

## Purpose

Over Cycling 的核心智能模型。

负责：

* 用户理解
* 骑行决策
* 骑行规划
* 习惯养成

不依赖具体模型。

可运行于：

* GPT
* Claude
* Gemini
* DeepSeek

---

# User Model

## Basic

```yaml
age:
gender:
height:
weight:
```

## Cycling

```yaml
bike_type:

experience:
  beginner
  casual
  regular

ride_frequency:

average_distance:
```

## Goal

```yaml
relax

exercise

explore

social

recover

build_habit
```

## Context

```yaml
available_time:

fatigue:

mood:

weather_preference:
```

---

# Ride Readiness Model

输入：

```yaml
weather
temperature
wind
available_time
fatigue
last_ride_days
mood
```

输出：

```yaml
ride_today
ride_lightly
rest_today
```

---

# Ride Planning Model

输入：

```yaml
goal
available_time
weather
mood
```

输出：

```yaml
distance

duration

route_type

intensity
```

---

# Habit Model

输入：

```yaml
ride_count_30d
ride_count_90d
last_ride_date
```

输出：

```yaml
habit_score
consistency_level
next_action
```

---

# Decision Priority

1 Weather

2 Available Time

3 User Mood

4 Last Ride

5 Habit Goal

6 Ride Plan
