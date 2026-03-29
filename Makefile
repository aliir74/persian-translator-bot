.PHONY: install dev test lint format typecheck check run deploy clean

install:
	uv sync

dev:
	uv sync --all-extras

test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run ty check src/

check: lint typecheck test

run:
	uv run python -m persian_translator_bot

deploy:
	./deploy.sh

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
