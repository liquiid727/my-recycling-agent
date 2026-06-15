# Changelog

## Proposed

- add a rolling-window `ride_growth_review`
- add deterministic growth status and milestone extraction
- add a `/rides` growth panel with planner-compatible next-focus CTA

## Implemented In Worktree

- backend now exposes `GET /api/v1/rides/growth-review?window_days=30|90|180`
- frontend now renders a growth-review panel under the monthly summary band on `/rides`
- growth-review observability now reuses `ride_monthly_summary_events` for request, invalid-window, zeroed-review, and CTA-click tracking
- targeted backend and frontend verification has been recorded for package 2c

## Not Yet Finalized

- this package is still waiting for git-stage / commit evidence in the current environment
