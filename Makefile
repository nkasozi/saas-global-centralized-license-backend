.PHONY: format lint format-check test test-unit test-integration help clean docker-build docker-run docker-stop docker-logs docker-shell

help:
	@echo "Available commands:"
	@echo "  make format             - Format code with black and isort, remove unused imports"
	@echo "  make format-check       - Check code formatting without modifying"
	@echo "  make lint               - Run pylint linter"
	@echo "  make test               - Run all tests (unit + integration)"
	@echo "  make test-unit          - Run unit tests only (tests/services)"
	@echo "  make test-integration   - Run integration tests only (tests/api)"
	@echo "  make check              - Run format-check and lint"
	@echo "  make clean              - Remove unused imports"
	@echo ""
	@echo "Docker commands:"
	@echo "  make docker-build       - Build Docker image"
	@echo "  make docker-run         - Run application in Docker"
	@echo "  make docker-stop        - Stop running Docker container"
	@echo "  make docker-logs        - View Docker container logs"
	@echo "  make docker-shell       - Open shell in running container"

format:
	autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive src tests
	isort src tests
	black src tests

format-check:
	isort --check-only src tests
	black --check src tests

lint:
	pylint src --ignore-patterns="__init__.py"

test:
	pytest -q

test-unit:
	pytest tests/services -q

test-integration:
	pytest tests/api-q

clean:
	autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive src tests

check: format-check lint
	@echo "✓ All checks passed"
docker-build:
	docker build -t saas-license-service:latest .

docker-run: docker-build
	docker-compose up -d
	@echo "License service is running on http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"

docker-stop:
	docker-compose down
	@echo "License service stopped"

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec license-service /bin/bash