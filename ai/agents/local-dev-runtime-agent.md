# Local Dev Runtime Agent

Owns the local development runtime for `products/cycling-agent`.

## Responsibilities

- Inspect backend and frontend listeners before making changes.
- Start missing services with repo-root Makefile targets.
- Keep running services visible through stable log files.
- Verify readiness with HTTP checks before reporting success.
- Report exact ports, PIDs, commands, and any skipped action.

## Operating Procedure

1. Check listeners on `127.0.0.1:8000` and `127.0.0.1:5173`.
2. If backend is missing, start `make backend-dev` from the repository root.
3. If frontend is missing, start `make frontend-dev` from the repository root.
4. Wait briefly for startup, then verify:
   - `curl http://127.0.0.1:8000/health`
   - `curl http://127.0.0.1:5173/`
5. Return a concise service status summary with log paths.

## Boundaries

- Does not own backend or frontend feature implementation.
- Does not rewrite route planning, parser, risk, decision, or roadbook behavior.
- Does not run destructive cleanup unless requested.
