# Test Result Summary

## Recorded Commands

Backend:

```bash
. products/cycling-agent/backend/.venv/bin/activate
pytest \
  products/cycling-agent/backend/tests/test_ride_plan_api.py \
  products/cycling-agent/backend/tests/test_ride_record_api.py \
  products/cycling-agent/backend/tests/test_ride_record_repository.py \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_service.py \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_api.py \
  products/cycling-agent/backend/tests/test_ride_growth_review_service.py \
  products/cycling-agent/backend/tests/test_ride_growth_review_api.py -q
```

Observed result:

- `59 passed`

Frontend:

```bash
cd products/cycling-agent/frontend
npx vitest run src/tests/ride-record-list-page.test.tsx src/tests/home-page.test.tsx
npm run build
```

Observed result:

- `12 passed`
- build passed

Live runtime readback:

```bash
curl -s http://127.0.0.1:8003/health
curl -s 'http://127.0.0.1:8003/api/v1/rides/records?limit=5'
curl -s 'http://127.0.0.1:8003/api/v1/rides/monthly-summary?month=2026-06'
curl -s 'http://127.0.0.1:8003/api/v1/rides/growth-review?window_days=90'
curl -s http://127.0.0.1:8004/health
curl -s 'http://127.0.0.1:8004/api/v1/rides/growth-review?window_days=90'
curl -s -X POST 'http://127.0.0.1:8004/api/v1/rides/growth-review-events' \
  -H 'Content-Type: application/json' \
  -d '{"window_days":90,"action_key":"resume_with_short_ride","suggested_scene":"city_ride","growth_status":"building"}'
curl -s 'http://127.0.0.1:8004/api/v1/rides/growth-review?window_days=45'
curl -s 'http://127.0.0.1:8004/api/v1/admin/ride-monthly-summary-events'
```

Observed result:

- backend health returned `{"status":"ok"}`
- recent rides returned a real saved record `RR-06FCPB8FFW00`
- monthly summary returned a real June summary with `ride_count=1`
- growth review returned a real rolling-window review with `growth_status=building`
- fresh backend on `127.0.0.1:8004` returned a zeroed growth review on an empty database
- `POST /api/v1/rides/growth-review-events` returned `growth_review_cta_click`
- admin event readback on `127.0.0.1:8004` showed:
  - `growth_review_request` with `requested_window_days=90`, `growth_status=building`, `is_zero_growth_review=true`
  - `growth_review_cta_click`
  - `growth_review_invalid_window` with `requested_window_days=45`

Structured handoff regression:

- `test_preflight_accepts_handoff_context_and_uses_it_to_fill_missing_duration`
- homepage test verifies seeded banner plus structured planner prefill from query params
- rides-page CTA test verifies monthly-summary and growth-review links both carry structured handoff context

Growth-review observability regression:

- API tests verify request, invalid-window, zeroed-review, and CTA-click event persistence
- rides-page test verifies growth CTA sends `keepalive` tracking to `/api/v1/rides/growth-review-events`

## Remaining Gap

Commit and branch-clean evidence is still missing because `.git/worktrees/.../index.lock` is not writable in the current environment.

Browser readback on `http://127.0.0.1:5177` is also blocked by the local in-app browser security policy, so UI runtime evidence is limited to automated frontend tests plus backend live readback.
