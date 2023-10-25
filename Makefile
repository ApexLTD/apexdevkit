install:
	python -m pip install --upgrade pip
	python -m pip install --upgrade poetry
	poetry install

lock:
	poetry lock --no-update

update:
	poetry update

format:
	poetry run black pydevtools tests
	poetry run ruff --fix pydevtools tests

lint:
	poetry run black --check pydevtools tests
	poetry run ruff check pydevtools tests
	poetry run mypy pydevtools tests

test:
	poetry run pytest \
		--cov \
		--last-failed \
		--record-mode once

test-ci:
	poetry run pytest
