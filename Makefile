.PHONY: help install sync format lint type-check test test-cov clean example all

help:
	@echo "Available commands:"
	@echo "  make install      - Install package in development mode"
	@echo "  make sync         - Sync all dependencies (including dev)"
	@echo "  make format       - Format code with ruff"
	@echo "  make lint         - Lint code with ruff"
	@echo "  make type-check   - Type check with pyright"
	@echo "  make test         - Run tests with pytest"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make example      - Run example generation"
	@echo "  make clean        - Clean build artifacts and cache"
	@echo "  make all          - Format, lint, type-check, and test"

install:
	uv pip install -e .

sync:
	uv sync --extra dev

format:
	ruff format src/ tests/ examples/
	ruff check --fix src/ tests/ examples/

lint:
	ruff check src/ tests/ examples/

type-check:
	pyright src/ tests/ examples/

test:
	pytest

test-cov:
	pytest --cov --cov-report=term-missing --cov-report=html

example:
	cd examples/simple-sensor-network && ./generate.sh

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: format lint type-check test
