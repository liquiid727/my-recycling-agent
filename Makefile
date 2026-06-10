PRODUCT_DIR := products/cycling-agent
BACKEND_DIR := $(PRODUCT_DIR)/backend
FRONTEND_DIR := $(PRODUCT_DIR)/frontend
ENV_FILE := .env
LOAD_ENV := set -a; [ ! -f $(ENV_FILE) ] || . ./$(ENV_FILE); set +a;

RUNTIME_PYTHON := /Users/liquiid/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
PYTHON ?= $(shell if [ -x "$(RUNTIME_PYTHON)" ]; then printf "%s" "$(RUNTIME_PYTHON)"; else command -v python3; fi)

BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000
BACKEND_URL := http://$(BACKEND_HOST):$(BACKEND_PORT)
FRONTEND_PORT ?= 5173
VITE_API_PROXY_TARGET ?= $(BACKEND_URL)

POSTGRES_URL ?= postgresql://cycling:cycling@127.0.0.1:54329/cycling_agent
REDIS_URL ?= redis://127.0.0.1:63799/0

.PHONY: help all install backend-install frontend-install dev backend-dev frontend-dev \
	backend-test frontend-test frontend-build test build infra-up infra-down \
	storage-test amap-test llm-test clean

help:
	@printf "Cycling Agent local commands\n\n"
	@printf "  make install         Install backend and frontend dependencies\n"
	@printf "  make dev             Run backend and frontend dev servers together\n"
	@printf "  make backend-dev     Run FastAPI backend at %s\n" "$(BACKEND_URL)"
	@printf "  make frontend-dev    Run Vite frontend at http://127.0.0.1:%s\n" "$(FRONTEND_PORT)"
	@printf "  make all             Install dependencies, run tests, and build frontend\n"
	@printf "  make test            Run backend and frontend tests\n"
	@printf "  make build           Build frontend\n"
	@printf "  make infra-up        Start local PostgreSQL and Redis\n"
	@printf "  make infra-down      Stop local PostgreSQL and Redis\n"
	@printf "  make storage-test    Run PostgreSQL/Redis live storage test\n"
	@printf "  make amap-test       Run AMap live integration test, requires CYCLING_AGENT_AMAP_WEB_API_KEY\n"
	@printf "  make llm-test        Run LLM live integration test, requires LLM env vars\n"

all: install test build

install: backend-install frontend-install

backend-install:
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install -e ".[dev]"

frontend-install:
	cd $(FRONTEND_DIR) && npm ci

dev:
	trap 'kill 0' INT TERM EXIT; \
	$(LOAD_ENV) \
	(cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload) & \
	(cd $(FRONTEND_DIR) && VITE_API_PROXY_TARGET=$(VITE_API_PROXY_TARGET) npm run dev -- --host 127.0.0.1 --port $(FRONTEND_PORT)) & \
	wait

backend-dev:
	$(LOAD_ENV) cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload

frontend-dev:
	cd $(FRONTEND_DIR) && VITE_API_PROXY_TARGET=$(VITE_API_PROXY_TARGET) npm run dev -- --host 127.0.0.1 --port $(FRONTEND_PORT)

test: backend-test frontend-test

backend-test:
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests -v

frontend-test:
	cd $(FRONTEND_DIR) && npm test

build: frontend-build

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

infra-up:
	cd $(PRODUCT_DIR) && docker compose -f docker-compose.dev.yml up -d

infra-down:
	cd $(PRODUCT_DIR) && docker compose -f docker-compose.dev.yml down

storage-test:
	cd $(BACKEND_DIR) && \
	CYCLING_AGENT_DATABASE_URL=$(POSTGRES_URL) \
	CYCLING_AGENT_REDIS_URL=$(REDIS_URL) \
	$(PYTHON) -m pytest tests/test_storage_live_integration.py -v

amap-test:
	$(LOAD_ENV) cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/test_amap_live_integration.py -v

llm-test:
	$(LOAD_ENV) cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/test_llm_live_integration.py -v

clean:
	rm -rf $(FRONTEND_DIR)/dist
	rm -rf $(BACKEND_DIR)/.pytest_cache $(FRONTEND_DIR)/node_modules/.vite
