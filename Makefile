.PHONY: install-dev lint format run help

help:
	@echo "Available commands:"
	@echo "  make install-dev - Install development dependencies"
	@echo "  make lint        - Run Ruff and Ty"
	@echo "  make format      - Format code with Ruff"
	@echo "  make run         - Run the application"

install-dev:
	uv sync --group dev

lint:
	uv run ruff check .
	uv run ty check

format:
	uv run ruff format .

run:
	uv run user-management-service
