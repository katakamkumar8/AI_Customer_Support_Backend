# ── AI Customer Support Agent – Developer Makefile ────────────────────────────

.PHONY: help install install-dev run dev migrate migrate-auto \
        test test-cov lint format clean

VENV      := .venv
PYTHON    := $(VENV)/bin/python
PIP       := $(VENV)/bin/pip
UVICORN   := $(VENV)/bin/uvicorn
PYTEST    := $(VENV)/bin/pytest
ALEMBIC   := $(VENV)/bin/alembic

help:                           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | \
		awk 'BEGIN{FS=":.*##"}{printf "  \033[36m%-18s\033[0m %s\n",$$1,$$2}'

# ── Setup ──────────────────────────────────────────────────────────────────────

install:                        ## Create venv and install production deps
	python3.12 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install-dev: install            ## Install dev + test dependencies on top
	$(PIP) install -r requirements-dev.txt

# ── Run ────────────────────────────────────────────────────────────────────────

run:                            ## Run production server
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8000

dev:                            ## Run dev server with hot-reload
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# ── Database ───────────────────────────────────────────────────────────────────

migrate:                        ## Apply all Alembic migrations
	$(ALEMBIC) upgrade head

migrate-auto:                   ## Auto-generate a new migration (MSG=description)
	$(ALEMBIC) revision --autogenerate -m "$(MSG)"

migrate-down:                   ## Rollback last migration
	$(ALEMBIC) downgrade -1

# ── Testing ────────────────────────────────────────────────────────────────────

test:                           ## Run test suite
	$(PYTEST) tests/ -v

test-cov:                       ## Run tests with coverage report
	$(PYTEST) tests/ --cov=app --cov-report=term-missing --cov-report=html

test-watch:                     ## Run tests on file change (requires pytest-watch)
	$(VENV)/bin/ptw tests/ app/ --runner "$(PYTEST) tests/"

# ── Code quality ──────────────────────────────────────────────────────────────

lint:                           ## Lint with ruff
	$(VENV)/bin/ruff check app/ tests/

format:                         ## Format with ruff + black
	$(VENV)/bin/ruff check --fix app/ tests/
	$(VENV)/bin/black app/ tests/

# ── Misc ───────────────────────────────────────────────────────────────────────

clean:                          ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	rm -f .coverage
