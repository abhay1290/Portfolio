# Financial Services Microservices Makefile

.PHONY: help build up down logs clean restart status health test

# Default target
help:
	@echo "Financial Services Microservices Management"
	@echo ""
	@echo "Available commands:"
	@echo "  build          - Build all services"
	@echo "  up             - Start all services"
	@echo "  down           - Stop all services"
	@echo "  restart        - Restart all services"
	@echo "  logs           - Show logs for all services"
	@echo "  logs-equity    - Show logs for equity service"
	@echo "  logs-fi        - Show logs for fixed income service"
	@echo "  status         - Show status of all services"
	@echo "  health         - Check health of all services"
	@echo "  clean          - Remove all containers and volumes"
	@echo "  test           - Run tests for both services"
	@echo "  db-migrate     - Run database migrations"
	@echo "  shell-equity   - Open shell in equity service"
	@echo "  shell-fi       - Open shell in fixed income service"

# Build all services
build:
	@echo "Building all services..."
	docker-compose build --no-cache

# Start all services
up:
	@echo "Starting all services..."
	docker-compose up -d

# Start with build
up-build:
	@echo "Building and starting all services..."
	docker-compose up -d --build

# Stop all services
down:
	@echo "Stopping all services..."
	docker-compose down

# Restart all services
restart: down up

# Show logs for all services
logs:
	docker-compose logs -f

# Show logs for equity service
logs-equity:
	docker-compose logs -f equity-service equity-celery-worker

# Show logs for fixed income service
logs-fi:
	docker-compose logs -f fixed-income-service fixed-income-celery-worker

# Show status of all services
status:
	docker-compose ps

# Check health of all services
health:
	@echo "Checking service health..."
	@echo "Equity Service:"
	@curl -s http://localhost:8001/health | jq . || echo "Equity service not responding"
	@echo ""
	@echo "Fixed Income Service:"
	@curl -s http://localhost:8002/health | jq . || echo "Fixed Income service not responding"

# Clean up everything
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Run tests
test:
	@echo "Running tests for equity service..."
	docker-compose exec equity-service python -m pytest tests/ -v
	@echo "Running tests for fixed income service..."
	docker-compose exec fixed-income-service python -m pytest tests/ -v

# Run database migrations
db-migrate:
	@echo "Running database migrations for equity service..."
	docker-compose exec equity-service alembic upgrade head
	@echo "Running database migrations for fixed income service..."
	docker-compose exec fixed-income-service alembic upgrade head

# Open shell in equity service
shell-equity:
	docker-compose exec equity-service /bin/bash

# Open shell in fixed income service
shell-fi:
	docker-compose exec fixed-income-service /bin/bash

# Development commands
dev-up:
	@echo "Starting services in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production commands
prod-up:
	@echo "Starting services in production mode..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor services
monitor:
	@echo "Monitoring services..."
	watch -n 2 'docker-compose ps && echo "" && docker stats --no-stream'

# Backup databases
backup:
	@echo "Creating database backups..."
	@mkdir -p backups
	docker-compose exec equity-postgres pg_dump -U $(EQUITY_DB_USER) $(EQUITY_DB_NAME) > backups/equity_backup_$(shell date +%Y%m%d_%H%M%S).sql
	docker-compose exec fixed-income-postgres pg_dump -U $(FIXED_INCOME_DB_USER) $(FIXED_INCOME_DB_NAME) > backups/fixed_income_backup_$(shell date +%Y%m%d_%H%M%S).sql

# Scale services
scale-equity:
	docker-compose up -d --scale equity-service=2 --scale equity-celery-worker=2

scale-fi:
	docker-compose up -d --scale fixed-income-service=2 --scale fixed-income-celery-worker=2