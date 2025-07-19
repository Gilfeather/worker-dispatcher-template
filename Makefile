# Worker Dispatcher Template Makefile

.PHONY: help install dev test lint format clean build run stop logs migrate

# Default target
help:
	@echo "Worker Dispatcher Template"
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Start development environment"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  clean      - Clean up temporary files"
	@echo "  build      - Build Docker images"
	@echo "  run        - Run the application"
	@echo "  stop       - Stop all services"
	@echo "  logs       - View logs"
	@echo "  migrate    - Run database migrations"

# Install dependencies
install:
	poetry install

# Install development dependencies
dev-install:
	poetry install --with dev
	poetry run pre-commit install

# Run tests
test:
	poetry run pytest

# Run tests with coverage
test-coverage:
	poetry run pytest --cov=app --cov-report=html --cov-report=term-missing

# Run linting
lint:
	poetry run black --check .
	poetry run isort --check-only .
	poetry run flake8 .
	poetry run mypy .

# Format code
format:
	poetry run black .
	poetry run isort .

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

# Build Docker images
build:
	docker-compose build

# Run the application
run:
	docker-compose up -d

# Run in development mode
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Stop all services
stop:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Run database migrations
migrate:
	poetry run alembic upgrade head

# Create new migration
migrate-create:
	poetry run alembic revision --autogenerate -m "$(message)"

# Reset database
migrate-reset:
	poetry run alembic downgrade base
	poetry run alembic upgrade head

# Start only database
db-start:
	docker-compose up -d db redis

# Stop only database
db-stop:
	docker-compose stop db redis

# Run application locally (without Docker)
run-local:
	poetry run uvicorn app.presentation.interface:app --reload --host 0.0.0.0 --port 8000

# Test dispatch/work workflow
test-workflow:
	poetry run python example_usage.py

# Run tests in watch mode
test-watch:
	poetry run pytest-watch

# Generate requirements.txt from poetry
requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

# Docker cleanup
docker-clean:
	docker system prune -f
	docker volume prune -f

# Full reset (careful!)
reset: stop clean docker-clean
	docker-compose down -v
	docker-compose build --no-cache

# Health check
health:
	curl -f http://localhost:8000/health || exit 1

# Load test data
load-test-data:
	poetry run python scripts/load_test_data.py

# Backup database
backup-db:
	docker-compose exec db pg_dump -U postgres worker_dispatcher > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore-db:
	docker-compose exec -T db psql -U postgres -d worker_dispatcher < $(file)

# Show running services
ps:
	docker-compose ps

# Show logs for specific service
logs-app:
	docker-compose logs -f app

logs-worker:
	docker-compose logs -f worker

logs-db:
	docker-compose logs -f db

# Run security checks
security:
	poetry run safety check
	poetry run bandit -r app/

# Generate API documentation
docs:
	@echo "API documentation available at: http://localhost:8000/docs"
	@echo "ReDoc documentation available at: http://localhost:8000/redoc"

# Performance test
perf-test:
	poetry run locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Run all checks (lint, test, security)
check: lint test security

# CI/CD pipeline
ci: install check

# Deploy to production (placeholder)
deploy-prod:
	@echo "Deploying to production..."
	@echo "This would typically involve:"
	@echo "1. Building production images"
	@echo "2. Pushing to container registry"
	@echo "3. Deploying to orchestration platform"
	@echo "4. Running health checks"

# Deploy to staging (placeholder)
deploy-staging:
	@echo "Deploying to staging..."
	@echo "This would typically involve:"
	@echo "1. Building staging images"
	@echo "2. Deploying to staging environment"
	@echo "3. Running integration tests"