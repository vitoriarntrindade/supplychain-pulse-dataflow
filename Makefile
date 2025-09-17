.PHONY: setup lint format test shell

setup:
	poetry install

lint:
	poetry run task lint

format:
	poetry run task format

test:
	poetry run pytest

shell:
	poetry shell

run-api:
	poetry run uvicorn src.scpulse.main:app --reload

# Docker
docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-clean:
	docker system prune -af --volumes