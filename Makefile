DC := docker compose -f docker-compose.yaml -f docker-compose.dev.yaml
RUN := $(DC) run --rm -e DJANGO_RUN_MIGRATIONS=0 web
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)
TEST_ARGS ?= tests

.PHONY: help
help:
	@echo "Task Manager Makefile"
	@echo ""
	@echo "  make dev             - Start development containers"
	@echo "  make dev-build       - Build development containers"
	@echo "  make dev-stop        - Stop development containers"
	@echo "  make dev-clear       - Stop containers and remove database volume"
	@echo "  make lock            - Regenerate poetry.lock in Docker"
	@echo "  make migrate         - Apply database migrations"
	@echo "  make migration name=... - Create migrations"
	@echo "  make createsuperuser - Create an administrator"
	@echo "  make shell           - Open Django shell"
	@echo "  make test            - Run tests (override TEST_ARGS for a subset)"
	@echo "  make test-cov        - Run tests with coverage"
	@echo "  make lint            - Check Ruff rules and formatting"
	@echo "  make format          - Apply Ruff fixes and formatting"
	@echo "  make typecheck       - Run mypy"
	@echo "  make check-django    - Run Django and migration checks"
	@echo "  make check           - Run all automated checks"
	@echo "  make clean           - Remove local caches and coverage files"

.PHONY: dev dev-build dev-stop dev-clear
dev:
	$(DC) up -d --build

dev-build:
	$(DC) build

dev-stop:
	$(DC) down

dev-clear:
	$(DC) down -v

.PHONY: lock
lock:
	docker run --rm -v "$(CURDIR):/app" -w /app python:3.12-slim sh -c 'pip install --no-cache-dir "poetry==2.1.3" && poetry lock && chown $(HOST_UID):$(HOST_GID) /app/poetry.lock'

.PHONY: migrate migration createsuperuser shell
migrate:
	$(RUN) poetry run python manage.py migrate

migration:
	@test -n "$(name)" || (echo "Error: specify name=\"description\"" && exit 1)
	$(RUN) poetry run python manage.py makemigrations --name "$(name)"
	docker run --rm -v "$(CURDIR):/app" python:3.12-slim chown -R "$(HOST_UID):$(HOST_GID)" /app/apps

createsuperuser:
	$(RUN) poetry run python manage.py createsuperuser

shell:
	$(RUN) poetry run python manage.py shell

.PHONY: test test-cov
test:
	$(RUN) poetry run pytest $(TEST_ARGS)

test-cov:
	$(RUN) poetry run pytest tests --cov=apps --cov-report=term-missing --cov-fail-under=85

.PHONY: lint format typecheck check-django check
lint:
	$(RUN) poetry run ruff check config apps tests manage.py
	$(RUN) poetry run ruff format --check config apps tests manage.py

format:
	$(RUN) poetry run ruff check --fix config apps tests manage.py
	$(RUN) poetry run ruff format config apps tests manage.py

typecheck:
	$(RUN) poetry run mypy config apps manage.py

check-django:
	$(RUN) poetry run python manage.py check
	$(RUN) poetry run python manage.py makemigrations --check --dry-run

check: lint typecheck check-django test-cov

.PHONY: clean
clean:
	docker run --rm -v "$(CURDIR):/app" -w /app python:3.12-slim sh -c 'find . -type f -name "*.py[co]" -delete && find . -type d -name "__pycache__" -delete && rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov coverage.xml .coverage && chown -R $(HOST_UID):$(HOST_GID) .'
