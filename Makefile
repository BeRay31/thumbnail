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
