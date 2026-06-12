# Makefile for FastAPI Large Application Template
# Standard conventions: uppercase targets are user-facing, lowercase are helpers

# =============================================================================
# Configuration & Variables
# =============================================================================
# Allow overriding commands via environment variables
UV ?= uv
PYTHON ?= python3

# Common command templates
UV_RUN = $(UV) run
PYTEST = $(UV) run pytest
RUFF = $(UV) run ruff
RUFF_CHECK = $(UV) run ruff check
RUFF_FORMAT = $(UV) run ruff format --check
MYPY = $(UV) run mypy
ALEMBIC = $(UV) run alembic -c app/alembic.ini

# Shell configuration - use absolute path and enable strict mode
SHELL := bash
.ONESHELL:
.SHELLFLAGS = -euo pipefail -c

# =============================================================================
# PHONY Targets
# =============================================================================
.PHONY: help install dev prod test test-unit test-integration test-e2e lint format typecheck migrate migrate-create migrate-check clean check-env ci up down logs up-observability down-observability

# docker compose wrappers
COMPOSE ?= docker compose
COMPOSE_OBS = $(COMPOSE) -f docker/observability/docker-compose.yml

# =============================================================================
# Default target
# =============================================================================
help:
	@echo "FastAPI Large Application Template - Available Commands"
	@echo ""
	@echo "Usage: make <target> [UV=<command>] [PYTHON=<command>]"
	@echo ""
	@echo "Development:"
	@echo "  install         Install dependencies and setup git hooks"
	@echo "  dev             Run development server"
	@echo "  prod            Run production server"
	@echo ""
	@echo "Testing:"
	@echo "  test            Run all tests"
	@echo "  test-unit       Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-e2e        Run e2e tests only"
	@echo ""
	@echo "Database:"
	@echo "  migrate         Apply database migrations"
	@echo "  migrate-create  Create new migration (use MSG='your message')"
	@echo ""
	@echo "Code Quality:"
	@echo "  check-env       Verify environment and dependencies"
	@echo "  lint            Check for linting issues"
	@echo "  format          Check code formatting"
	@echo "  typecheck       Run type checking"
	@echo "  ci              Run full CI pipeline (lint, format, typecheck, test)"
	@echo ""
	@echo "Local Docker stack:"
	@echo "  up              Build and start app + postgres + redis (detached)"
	@echo "  down            Stop and remove the local stack"
	@echo "  logs            Follow the app container logs"
	@echo "  up-observability   Start the Grafana/Tempo/Prometheus/OTel stack"
	@echo "  down-observability Stop the observability stack"
	@echo ""
	@echo "Utilities:"
	@echo "  clean           Remove generated files and caches"

# =============================================================================
# Prerequisites Check
# =============================================================================
check-env:
	@echo "Checking environment..."
	@$(PYTHON) --version || { echo "Error: Python not found"; exit 1; }
	@$(UV) --version > /dev/null 2>&1 || { echo "Error: uv not found"; exit 1; }
	@$(UV) run alembic --version > /dev/null 2>&1 || { echo "Error: alembic not installed"; exit 1; }
	@$(UV) run ruff --version > /dev/null 2>&1 || { echo "Error: ruff not installed"; exit 1; }
	@$(UV) run mypy --version > /dev/null 2>&1 || { echo "Error: mypy not installed"; exit 1; }
	@$(UV) run pytest --version > /dev/null 2>&1 || { echo "Error: pytest not installed"; exit 1; }
	@echo "Environment check passed"

# =============================================================================
# Installation & Setup
# =============================================================================
install: check-env
	@echo "Installing dependencies..."
	$(UV) sync --all-extras
	@echo "Installing Git hooks..."
	$(UV) run pre-commit install

# =============================================================================
# Development & Production
# =============================================================================
dev: check-env
	@echo "Starting development server..."
	$(UV_RUN) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

prod:
	@echo "Starting production server..."
	@test -f ./run.sh && chmod +x ./run.sh || { echo "Error: run.sh not found"; exit 1; }
	bash ./run.sh

# =============================================================================
# Testing
# =============================================================================
test: check-env
	@echo "Running all tests..."
	$(PYTEST) tests/ --cov=app --cov-report=term-missing

test-unit: check-env
	@echo "Running unit tests..."
	$(PYTEST) -m unit tests/

test-integration: check-env
	@echo "Running integration tests..."
	$(PYTEST) -m integration tests/

test-e2e: check-env
	@echo "Running e2e tests..."
	$(PYTEST) -m e2e tests/

# =============================================================================
# Database Migrations
# =============================================================================
migrate: check-env
	@echo "Running database migrations..."
	@test -n "${DATABASE_URL:-}" -o -f .env || { echo "Error: DATABASE_URL not set and .env not found"; exit 1; }
	$(ALEMBIC) upgrade head

migrate-create: check-env
ifndef MSG
	$(error MSG is undefined. Usage: make migrate-create MSG="your message")
endif
	@echo "Creating new migration: $(MSG)"
	$(ALEMBIC) revision --autogenerate -m "$(MSG)"

migrate-check: check-env
	@echo "Checking for pending model changes..."
	$(ALEMBIC) check

# =============================================================================
# Code Quality
# =============================================================================
lint: check-env
	@echo "Checking for linting issues..."
	$(RUFF_CHECK) .

format: check-env
	@echo "Checking code formatting..."
	$(RUFF_FORMAT) .

typecheck: check-env
	@echo "Running type checking..."
	$(MYPY) .

# Full CI pipeline
ci: check-env lint format typecheck migrate-check test
	@echo "CI pipeline completed successfully"

# =============================================================================
# Local Docker stack
# =============================================================================
up:
	@echo "Building and starting app + postgres + redis..."
	$(COMPOSE) up --build -d
	@echo "App available at http://localhost:8000/docs"

down:
	@echo "Stopping local stack..."
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f app

up-observability:
	@echo "Starting observability stack (Grafana/Tempo/Prometheus/OTel)..."
	$(COMPOSE_OBS) up -d

down-observability:
	@echo "Stopping observability stack..."
	$(COMPOSE_OBS) down

# =============================================================================
# Cleanup
# =============================================================================
clean:
	@echo "Cleaning generated files and caches..."
	@rm -rf .mypy_cache .ruff_cache .pytest_cache .hypothesis
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"
