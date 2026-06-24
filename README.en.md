# Over Cycling

[中文](./README.md) | [English](./README.en.md)

Over Cycling is an open-source AI-assisted ride planning system for casual urban cyclists.

It turns a short natural-language request into a practical riding decision: where to go, how far to ride, how much time to budget, what risks to watch, and why that recommendation makes sense today.

It is designed for people who want to ride more often, not for riders training for races.

## Features

Over Cycling currently focuses on two ride-planning scenarios:

### Supported Scenarios

- `city_ride`: short same-day or same-evening city rides
- `weekend_trip`: nearby weekend or holiday ride planning

### Core Features

- **Natural-language planning**  
  Start from a sentence instead of a large form.

- **Decision-first output**  
  Get a recommendation, not just a list of routes.

- **Explainable results**  
  Output includes reasons, tradeoffs, and ride-risk context.

- **Weather- and route-aware planning**  
  The system combines request parsing, weather context, route candidates, and POI enrichment.

- **Deterministic core with optional AI enhancement**  
  The main planning path still works with structured logic and local data when LLM features are unavailable.

- **Persisted results and admin surfaces**  
  Plans can be reopened later, and content/rule management surfaces exist for operators.

## How It Works

At runtime, Over Cycling follows a planning pipeline like this:

```text
web request
-> query parsing
-> clarification when constraints are incomplete
-> weather lookup
-> route or trip candidate discovery
-> route / POI enrichment
-> deterministic risk scoring
-> recommendation ranking
-> explanation and roadbook generation
-> persisted result
-> frontend result view
```

### Runtime Roles

- **Frontend**  
  Collects user input, shows planning progress, renders saved results, and provides admin pages.

- **Backend**  
  Orchestrates parsing, weather lookup, candidate discovery, scoring, ranking, and persistence.

- **Providers**  
  Supply optional live weather, map, POI, and LLM integrations.

- **Repositories and seed data**  
  Provide route templates, trip templates, destinations, and stored planning results.

### Example Request

```text
I have two hours tonight and want an easy riverside ride with coffee nearby.
```

Typical output includes:

- a recommended route or nearby trip
- estimated ride distance and duration
- weather and ride-risk context
- a plain-language explanation
- saved result data for later viewing

## Architecture

The current runtime is a web application with:

- **Backend:** FastAPI
- **Frontend:** React + Vite
- **Storage:** PostgreSQL by default
- **Cache:** in-memory by default, Redis optional
- **Weather:** Open-Meteo by default
- **Map / POI:** local providers by default, AMap optional
- **LLM:** optional OpenAI-compatible integration with deterministic fallback

The backend is the orchestration center. The frontend handles user input, progress states, result rendering, and admin workflows.

## Quick Start

### Requirements

- Python 3.12+
- Node.js + npm

### Run Locally

From the repository root:

```bash
make install
make infra-up
make dev
```

Then open:

- Frontend: `http://127.0.0.1:5173`
- Backend health check: `http://127.0.0.1:8000/health`

By default, local PostgreSQL is required:

- database: PostgreSQL
- cache: in-memory (Redis optional)
- route / POI providers: local
- LLM: optional

### Common Commands

```bash
make install
make infra-up
make dev
make test
make build
make backend-test
make frontend-test
make frontend-build
```

Advanced local validation:

```bash
make infra-up
make infra-down
make storage-test
make amap-test
make llm-test
make spec-check
make asset-check
```

### Configuration

The root `.env` file is loaded automatically by the `Makefile`.

Common configuration groups:

#### Infrastructure

- `CYCLING_AGENT_DATABASE_URL`
- `CYCLING_AGENT_REDIS_URL`

#### Map / POI

- `CYCLING_AGENT_ROUTE_PROVIDER_MODE`
- `CYCLING_AGENT_POI_PROVIDER_MODE`
- `CYCLING_AGENT_AMAP_WEB_API_KEY`

#### LLM

- `CYCLING_AGENT_LLM_API_BASE_URL`
- `CYCLING_AGENT_LLM_API_KEY`
- `CYCLING_AGENT_LLM_MODEL`
- `CYCLING_AGENT_LLM_THINKING`

#### Frontend

- `VITE_API_PROXY_TARGET`
- `VITE_AMAP_JS_API_KEY`

More detailed runtime notes live in [products/cycling-agent/README.md](./products/cycling-agent/README.md).

## Repository Layout

```text
.
├── Makefile
├── products/
│   └── cycling-agent/
│       ├── backend/
│       ├── frontend/
│       ├── data/
│       └── docs/
├── specs/
├── spec-draft/
├── rules/
└── tests/
```

Useful entry points:

- [products/cycling-agent/](./products/cycling-agent/) - runnable product code
- [products/cycling-agent/backend/](./products/cycling-agent/backend/) - FastAPI backend
- [products/cycling-agent/frontend/](./products/cycling-agent/frontend/) - React frontend
- [products/cycling-agent/docs/current-implementation-overview.md](./products/cycling-agent/docs/current-implementation-overview.md) - current implementation map
- [Makefile](./Makefile) - install, run, test, and build entry points

## How The Repository Is Organized

This repository includes more than application code. It also contains the specification, rule, and verification assets used to evolve the product in a traceable way.

- `products/cycling-agent/`: runnable product
- `specs/current/`: accepted baseline
- `specs/changes/`: active change packages
- `spec-draft/`: draft requirements and early proposals
- `rules/` and `.rules/`: engineering and workflow rules
- `tests/`: spec-driven verification assets

## Scope And Non-Goals

This repository currently ships a Hangzhou-first MVP. That means:

- Hangzhou is the only fully seeded city in the current product
- the core product is a web app with backend, frontend, and local seed data
- the system is for planning and decision support, not for race training

Current non-goals:

- FTP analysis
- power-based training workflows
- race preparation
- cycling social network features

## Contributing Context

Over Cycling is an active MVP, not a finished product.

The repository keeps application code together with the minimum spec, rule, and test assets needed to make changes easier to propose, implement, review, and verify.

If you are contributing to the project, the most useful reading order is:

1. [README.en.md](./README.en.md)
2. [specs/current/](./specs/current/)
3. [products/cycling-agent/docs/current-implementation-overview.md](./products/cycling-agent/docs/current-implementation-overview.md)
4. [products/cycling-agent/](./products/cycling-agent/)
5. [tests/](./tests/)

## License

Add a root `LICENSE` file before publishing this repository publicly. This README does not define license terms by itself.
