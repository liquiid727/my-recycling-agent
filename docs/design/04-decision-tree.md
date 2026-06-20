# Decision Tree

注意：这里不要写 Prompt，全部写规则。

## Decision 01: 今天骑不骑

IF:
```yaml
weather == rain
```

THEN:
```yaml
rest_today
```

## Decision 02: 最近太久没骑

IF:
```yaml
last_ride_days > 14
```

THEN:
```yaml
recovery_ride
```

## Decision 03: 今天时间不多

IF:
```yaml
available_time < 60
```

THEN:
```yaml
short_ride
```

## Decision 04: 用户情绪低落

IF:
```yaml
mood == stressed
```

THEN:
```yaml
scenic_route
```

## Decision 05: 连续加班

IF:
```yaml
overtime_days > 3
```

THEN:
```yaml
easy_ride
```
