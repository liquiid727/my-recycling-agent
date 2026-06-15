Decision 01

今天骑不骑

IF:

  weather == rain

THEN:

  rest_today
Decision 02

最近太久没骑

IF:

  last_ride_days > 14

THEN:

  recovery_ride
Decision 03

今天时间不多

IF:

  available_time < 60

THEN:

  short_ride
Decision 04

用户情绪低落

IF:

  mood == stressed

THEN:

  scenic_route
Decision 05

连续加班

IF:

  overtime_days > 3

THEN:

  easy_ride

注意：

这里不要写 Prompt。

全部写规则。