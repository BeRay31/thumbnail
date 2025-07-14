# Docker Deployment Guide

This guide explains how to run the Thumbnail Service using Docker.

## Prerequisites

- Docker Engine (>= 20.10)
- Docker Compose (>= 2.0)
- Make (optional, for convenience commands)

## Quick Start

1. **Clone the repository and navigate to the project directory**

2. **Copy the environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Build and start all services:**
   ```bash
   make up
   # or
   docker-compose up -d --build
   ```

4. **Check service status:**
   ```bash
   make status
   # or
   docker-compose ps
   ```

## Services

The Docker setup includes the following services:

- **server**: FastAPI application (port 8000)
- **worker**: Celery workers for background processing (2 instances)
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis for Celery broker (port 6379)
- **minio**: MinIO object storage (port 9000, console: 9001)

## Available Commands

Using the Makefile:

```bash
make build     # Build Docker images
make up        # Start all services
make down      # Stop all services
make logs      # Show logs for all services
make clean     # Remove all containers and volumes
make restart   # Restart all services
make shell     # Open shell in server container
make test      # Run tests
make dev       # Start in development mode with live reload
make status    # Check service status
```

## Configuration

Environment variables can be configured in the `.env` file:

- `POSTGRES_USER`: Database username (default: thumbnail_user)
- `POSTGRES_PASSWORD`: Database password (default: thumbnail_password)
- `POSTGRES_DB`: Database name (default: thumbnail_db)
- `MINIO_ACCESS_KEY`: MinIO access key (default: minioadmin)
- `MINIO_SECRET_KEY`: MinIO secret key (default: minioadmin)
- `MINIO_ORIGINALS_BUCKET`: Bucket for original images (default: raws)
- `MINIO_THUMBNAILS_BUCKET`: Bucket for thumbnails (default: thumbnails)

## Accessing Services

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (login with MINIO_ACCESS_KEY/MINIO_SECRET_KEY)

## Development

For development with live reload:

```bash
make dev
```

To access the server container shell:

```bash
make shell
```

## Scaling Workers

To scale the number of worker instances:

```bash
docker-compose up -d --scale worker=4
```

## Troubleshooting

1. **Check service logs:**
   ```bash
   make logs
   # or for specific service
   docker-compose logs server
   ```

2. **Reset everything:**
   ```bash
   make clean
   make up
   ```

3. **Check service health:**
   ```bash
   curl http://localhost:8000/healthz
   ```

## Production Considerations

For production deployment:

1. Use environment-specific `.env` files
2. Set secure passwords and keys
3. Consider using external managed services for PostgreSQL, Redis, and object storage
4. Implement proper logging and monitoring
5. Use Docker secrets for sensitive information
6. Set up reverse proxy (nginx) for the API server
7. Configure proper backup strategies for persistent data
