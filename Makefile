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
