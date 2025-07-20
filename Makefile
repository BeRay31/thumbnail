# Makefile for Thumbnail Service

.PHONY: help build up down logs clean restart shell test k8s-setup k8s-build k8s-deploy k8s-clean

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Docker Compose (Development):"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  logs      - Show logs for all services"
	@echo "  clean     - Remove all containers and volumes"
	@echo "  restart   - Restart all services"
	@echo ""
	@echo "Kubernetes (Production):"
	@echo "  k8s-setup   - Create Kind cluster"
	@echo "  k8s-build   - Build Docker images for K8s"
	@echo "  k8s-deploy  - Deploy to Kubernetes with Helm"
	@echo "  k8s-clean   - Delete Kind cluster"
	@echo "  k8s-all     - Complete K8s deployment (setup + build + deploy)"

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

# Kubernetes targets
k8s-setup:
	./scripts/kind-setup.sh

k8s-build:
	./scripts/build.sh

k8s-deploy:
	./scripts/kind-load-images.sh && ./scripts/deploy.sh

k8s-clean:
	kind delete cluster --name thumbnail-service

k8s-all: k8s-setup k8s-build k8s-deploy
