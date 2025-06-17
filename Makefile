# File Stats API Makefile
# Provides convenient commands for development and deployment

.PHONY: help build deploy deploy-prod deploy-traefik status logs stop restart cleanup test dev install

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "File Stats API - Available Commands"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Commands
install: ## Install dependencies locally
	pip install -r requirements.txt

dev: ## Run development server locally
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests (placeholder)
	@echo "No tests configured yet. Add your test framework here."
	# pytest tests/ -v

# Docker Commands
build: ## Build Docker image
	./deploy.sh build

deploy: ## Deploy using Docker Compose
	./deploy.sh deploy

deploy-prod: ## Deploy with production configuration
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

deploy-traefik: ## Deploy with Traefik reverse proxy
	./deploy.sh deploy-traefik

# Management Commands
status: ## Show service status
	./deploy.sh status

logs: ## Show service logs
	./deploy.sh logs

stop: ## Stop all services
	./deploy.sh stop

restart: ## Restart services
	./deploy.sh restart

cleanup: ## Clean up containers and images
	./deploy.sh cleanup

# Utility Commands
shell: ## Open shell in running container
	docker compose exec file-stats-api /bin/bash

inspect: ## Inspect the API container
	docker compose exec file-stats-api ps aux
	docker compose exec file-stats-api df -h

health: ## Check API health
	@echo "Checking API health..."
	@curl -f http://localhost:8000/ || echo "API is not responding"
	@echo "\nChecking API docs..."
	@curl -f http://localhost:8000/docs > /dev/null && echo "API docs accessible" || echo "API docs not accessible"

# Development Utilities
format: ## Format code with black (if installed)
	@command -v black >/dev/null 2>&1 && black main.py || echo "Black not installed. Run: pip install black"

lint: ## Lint code with flake8 (if installed)
	@command -v flake8 >/dev/null 2>&1 && flake8 main.py || echo "Flake8 not installed. Run: pip install flake8"

# Production Commands
backup: ## Backup application data
	@echo "Creating backup..."
	@mkdir -p backups
	@tar -czf backups/data-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/
	@echo "Backup created in backups/ directory"

update: ## Update and redeploy
	git pull
	$(MAKE) stop
	$(MAKE) build
	$(MAKE) deploy

# Quick start command
quick-start: ## Quick start: build and deploy
	$(MAKE) build
	$(MAKE) deploy
	@echo "Waiting for service to be ready..."
	@sleep 10
	$(MAKE) health 