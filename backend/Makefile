.PHONY: help install dev lint format test clean

POETRY_BIN := $(shell command -v poetry 2>/dev/null)

ifdef POETRY_BIN
RUNNER := poetry run
else
RUNNER :=
endif

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies (Poetry or pip)"
	@echo "  make dev      - Run the development server"
	@echo "  make lint     - Run linting checks (ruff, black, isort)"
	@echo "  make format   - Format code (ruff, black, isort)"
	@echo "  make test     - Run the pytest suite"
	@echo "  make clean    - Clean up generated files"

install:
ifdef POETRY_BIN
	poetry install
else
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt
endif

dev:
ifdef POETRY_BIN
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
else
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
endif

lint:
	$(RUNNER) ruff check app/ tests/
	$(RUNNER) black --check app tests
	$(RUNNER) isort --check-only app tests

format:
	$(RUNNER) ruff format app tests
	$(RUNNER) black app tests
	$(RUNNER) isort app tests

test:
	$(RUNNER) pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
