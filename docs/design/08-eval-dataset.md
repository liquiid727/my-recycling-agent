# Over Cycling Eval Dataset

Version: 0.1

## Case001

User:
```yaml
age: 30
ride_frequency: 1/month
goal: relax
available_time: 2h
weather: sunny
```

Expected:
```yaml
ride_today
distance: 20-40km
intensity: easy
```

## Case002

User:
```yaml
ride_frequency: 0
goal: build_habit
available_time: 1h
weather: cloudy
```

Expected:
```yaml
ride_today
distance: 10-20km
```

## Case003

User:
```yaml
ride_frequency: weekly
goal: exercise
fatigue: high
available_time: 3h
```

Expected:
```yaml
ride_lightly
distance: <30km
```

## Case004

User:
```yaml
goal: relax
weather: rain
```

Expected:
```yaml
rest_today
```

## Evaluation Metrics

- Ride Decision Accuracy
- Habit Suggestion Accuracy
- Route Recommendation Accuracy
- User Satisfaction
- Weekly Retention
- Monthly Ride Growth

## Target

```yaml
decision_accuracy > 85%
user_satisfaction > 90%
```
