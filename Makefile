amend:
	git commit --amend --no-edit -a

install:
	python -m pip install --upgrade pip
	python -m pip install --upgrade poetry
	poetry install

lock:
	poetry lock

update:
	poetry update

format:
	poetry run ruff format apexdevkit tests
	poetry run ruff check  apexdevkit tests --fix

format-unsafe:
	poetry run ruff check  apexdevkit tests --fix --unsafe-fixes

lint:
	poetry check --strict
	poetry run ruff format apexdevkit tests --check
	poetry run ruff check apexdevkit tests
	poetry run mypy apexdevkit tests

test:
	poetry run pytest tests \
		--cov \
		--last-failed \
		--record-mode once \
		--approvaltests-use-reporter='PythonNative'

approve:
	find tests -type f -name '*_actual.*' -exec sh -c \
	'mv "$$0" "$${0%_actual.*}.$${0##*.}"' {} \;

test-ci:
	poetry run pytest tests
