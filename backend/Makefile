.PHONY: help install dev lint format test clean

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies using Poetry"
	@echo "  make dev      - Run the development server"
	@echo "  make lint     - Run linting checks"
	@echo "  make format   - Format code"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up generated files"

install:
	poetry install

dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	poetry run ruff check app/

format:
	poetry run ruff format app/

test:
	poetry run pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
