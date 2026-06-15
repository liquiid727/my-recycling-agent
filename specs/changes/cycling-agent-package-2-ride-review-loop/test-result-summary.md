# Test Result Summary

## Recorded Commands

Backend:

```bash
. products/cycling-agent/backend/.venv/bin/activate
pytest \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_api.py \
  products/cycling-agent/backend/tests/test_ride_monthly_summary_service.py \
  products/cycling-agent/backend/tests/test_ride_record_api.py \
  products/cycling-agent/backend/tests/test_ride_record_repository.py -q
```

Observed result:

- `35 passed`

Frontend:

```bash
cd products/cycling-agent/frontend
npx vitest run src/tests/ride-record-list-page.test.tsx src/tests/home-page.test.tsx
npm run build
```

Observed result:

- `8 passed`
- build passed

## Runtime Readback

Verified against a fresh local backend on `127.0.0.1:8002` and frontend on `127.0.0.1:5176`:

- `GET /api/v1/rides/monthly-summary?month=2026-06`
- `GET /api/v1/admin/ride-monthly-summary-events`
- `POST /api/v1/rides/monthly-summary-events`
- `GET /rides`

## Remaining Gap

Commit and branch-clean evidence is still missing because `.git/worktrees/.../index.lock` is not writable in the current environment.
