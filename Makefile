# Makefile for Thumbnail Service

.PHONY: help build up down logs clean restart shell test

# Default target
help:
	@echo "Available targets:"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  logs      - Show logs for all services"
	@echo "  clean     - Remove all containers and volumes"
	@echo "  restart   - Restart all services"
	@echo "  shell     - Open shell in server container"
	@echo "  test      - Run tests"

# Build Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Show logs
logs:
	docker-compose logs -f

# Clean up containers and volumes
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Restart services
restart: down up

# Open shell in server container
shell:
	docker-compose exec server bash

# Run tests
test:
	docker-compose exec server python -m pytest

# Development mode (with live reload)
dev:
	docker-compose up --build

# Check service status
status:
	docker-compose ps