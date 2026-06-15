# Design Review

## User-Facing Shape

Package 2c should feel like an extension of `/rides`, not a dashboard fork.

The right hierarchy is:

1. this month
2. recent growth
3. recent ride list

## UX Notes

- Milestones should be short, factual, and low-drama.
- Growth status must stay low-pressure and readable.
- The next-focus CTA should feel like a continuation of the current planner, not a new coaching mode.

## State Coverage

The growth panel must explicitly cover:

- loading
- failure
- zeroed review
- success

with failure isolation from the already-existing monthly-summary and recent-list surfaces.

## Recommendation

This direction is aligned if the panel answers “what changed recently” without asking the user to think like a training athlete.
