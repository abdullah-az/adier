.PHONY: help install dev lint fmt format test clean worker

help:
    @echo "Available commands:"
    @echo "  make install  - Install dependencies using Poetry"
    @echo "  make dev      - Run the development server"
    @echo "  make worker   - Run the standalone worker process"
    @echo "  make lint     - Run linting checks"
    @echo "  make fmt      - Format code"
    @echo "  make test     - Run tests"
    @echo "  make clean    - Clean up generated files"

install:
    poetry install

dev:
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
    poetry run ruff check app/

fmt:
    poetry run ruff format app/

format: fmt

test:
    poetry run pytest tests/ -v

worker:
    poetry run python -m app.workers.runner

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name "*.egg-info" -exec rm -rf {} +
