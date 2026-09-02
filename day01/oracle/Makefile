.PHONY: install run train test lint probe docker-build docker-run

install:
	uv sync

run:
	uv run uvicorn app.main:app --reload --port 8000

train:
	uv run python -m training.prepare_data
	uv run python -m training.train_income
	uv run python -m training.train_marriage

test:
	uv run pytest -q

lint:
	uv run ruff check . && uv run ruff format --check .

probe:
	uv run python -m scripts.probe_llm

docker-build:
	docker build -t oracle:day1 .

docker-run:
	docker run --rm -p 8000:8000 --env-file .env oracle:day1
