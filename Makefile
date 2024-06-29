install:
	python -m pip install --upgrade pip
	python -m pip install --upgrade poetry
	poetry install

lock:
	poetry lock --no-update

amend:
	git commit --amend --no-edit -a

update:
	poetry update

format:
	poetry run ruff format apexdevkit tests
	poetry run ruff check  apexdevkit tests --fix

lint:
	poetry run ruff format apexdevkit tests --check
	poetry run ruff check apexdevkit tests
	poetry run mypy apexdevkit tests

test:
	poetry run pytest \
		--cov \
		--last-failed \
		--record-mode once

test-ci:
	poetry run pytest

run:
	uvicorn tests.resource.setup:app --factory
