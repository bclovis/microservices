.PHONY: help build deploy clean dev-up dev-down test lint

help:
	@echo "Pokemon Drafter - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up          Start development environment (Docker Compose)"
	@echo "  make dev-down        Stop development environment"
	@echo ""
	@echo "Production:"
	@echo "  make build           Build all Docker images"
	@echo "  make deploy          Deploy to Kubernetes"
	@echo "  make clean           Clean Kubernetes deployment"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests"
	@echo "  make lint            Run linters"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs            Show Kubernetes logs"
	@echo "  make status          Show deployment status"

# Development
dev-up:
	docker-compose up -d
	@echo ""
	@echo "Development environment started!"
	@echo "  Frontend Red:  http://localhost:4201"
	@echo "  Frontend Blue: http://localhost:4202"
	@echo "  Backend Red:   http://localhost:8001"
	@echo "  Backend Blue:  http://localhost:8002"
	@echo "  API Gateway:   http://localhost:8080"

dev-down:
	docker-compose down

dev-logs:
	docker-compose logs -f

# Production
build:
	./build-images.sh

deploy:
	./deploy.sh

clean:
	./cleanup.sh

# Testing
test:
	@echo "Running backend tests..."
	cd backend-red && python -m pytest || true
	cd backend-blue && python -m pytest || true
	@echo ""
	@echo "Running frontend tests..."
	cd frontend-red && npm test -- --watch=false || true
	cd frontend-blue && npm test -- --watch=false || true

test-backend:
	cd backend-red && python -m pytest -v
	cd backend-blue && python -m pytest -v

test-frontend:
	cd frontend-red && npm test -- --watch=false
	cd frontend-blue && npm test -- --watch=false

# Linting
lint:
	@echo "Linting backend..."
	cd backend-red && pylint main.py || true
	cd backend-blue && pylint main.py || true
	@echo ""
	@echo "Linting frontend..."
	cd frontend-red && ng lint || true
	cd frontend-blue && ng lint || true

# Utilities
logs:
	kubectl logs -f -l app=backend-red -n pokemon-drafter --tail=50

status:
	@echo "Deployment Status:"
	@kubectl get pods -n pokemon-drafter
	@echo ""
	@echo "Services:"
	@kubectl get services -n pokemon-drafter

describe:
	kubectl describe pods -n pokemon-drafter

# Database
db-shell:
	kubectl exec -it deployment/database -n pokemon-drafter -- psql -U pokemon_user -d pokemon_db

db-migrate:
	kubectl exec -i deployment/database -n pokemon-drafter -- psql -U pokemon_user -d pokemon_db < database/schema.sql

# Quick setup
setup:
	@echo "Setting up Pokemon Drafter..."
	@echo "1. Building images..."
	make build
	@echo ""
	@echo "2. Deploying to Kubernetes..."
	make deploy
	@echo ""
	@echo "Setup complete! Check status with: make status"

# Install dependencies
install-backend:
	cd backend-red && pip install -r requirements.txt
	cd backend-blue && pip install -r requirements.txt
	cd recommendation && pip install -r requirements.txt
	cd encryption && pip install -r requirements.txt

install-frontend:
	cd frontend-red && npm install
	cd frontend-blue && npm install

install: install-backend install-frontend
	@echo "All dependencies installed!"
