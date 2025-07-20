# Docker Development Guide

This guide covers running the Thumbnail Service using Docker and Docker Compose for local development.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB available memory
- 10GB available disk space

## Quick Start

### 1. Environment Setup

Create a `.env` file from the example:

```bash
cp .env.example .env
```

The default configuration works out of the box for local development:

```bash
# Database Configuration
POSTGRES_USER=thumbnail_user
POSTGRES_PASSWORD=thumbnail_pass
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_DB=thumbnail

# Redis Configuration  
REDIS_HOST=redis
REDIS_PORT=6379

# MinIO Configuration
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_ORIGINALS_BUCKET=raws
MINIO_THUMBNAILS_BUCKET=thumbnails
```

### 2. Start Services

```bash
# Start all services in background
make up

# Or using docker-compose directly
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check service status
make logs

# Test API health
curl http://localhost:8000/healthz
```

## Architecture Overview

The Docker Compose setup includes these services:

```yaml
services:
  server:      # FastAPI application server
  worker:      # Celery background workers (2 replicas)
  postgres:    # PostgreSQL database
  redis:       # Redis message broker
  minio:       # MinIO object storage
```

### Service Dependencies
<img src="system-design.svg" alt="system-design" width="800" height="800" />

## Service Details

### API Server (`server`)

- **Port**: `8000` (mapped to host)
- **Health**: `http://localhost:8000/healthz`
- **Docs**: `http://localhost:8000/docs`
- **Dependencies**: postgres, redis, minio

### Background Workers (`worker`)

- **Replicas**: 1 instances for parallel processing
- **Queue**: Celery with Redis backend
- **Dependencies**: postgres, redis, minio

### PostgreSQL Database (`postgres`)

- **Port**: `5432` (internal only)
- **Database**: `thumbnail`
- **Volume**: `postgres_data` for persistence
- **Health Check**: `pg_isready` command

### Redis (`redis`)

- **Port**: `6379` (internal only)  
- **Usage**: Task queue and caching
- **Volume**: `redis_data` for persistence
- **Health Check**: `redis-cli ping`

### MinIO Storage (`minio`)

- **API Port**: `9000` (internal only)
- **Console Port**: `9001` (mapped to host)
- **Console**: `http://localhost:9001` (admin/minioadmin)
- **Volumes**: `minio_data` for persistence
- **Health Check**: `mc ready` command

## Development Workflow

### Building Images

```bash
# Build all images
make build
```

### Starting Services

```bash
# Start all services
make up
```

### Viewing Logs

```bash
# All services
make logs
```

### Stopping Services

```bash
# Stop all services
make down

# Stop and remove volumes
make clean
```

## Image Build Process

### Multi-stage Builds

Both server and worker use optimized multi-stage builds:

#### Server Image (`Dockerfile.server`)

```dockerfile
# Stage 1: Dependencies
FROM python:3.11-slim as dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Application
FROM python:3.11-slim as runtime
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ /app/
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Worker Image (`Dockerfile.worker`)

```dockerfile
# Similar multi-stage pattern
# Optimized for background processing
CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]
```

### Build Optimization

- **Layer Caching**: Dependencies installed in separate stage
- **Size Optimization**: Using slim base images
- **Security**: Non-root user execution
- **Performance**: Pre-compiled Python packages

## Volume Management

### Data Persistence

```yaml
volumes:
  postgres_data:    # Database files
  redis_data:       # Redis persistence
  minio_data:       # Object storage files
```

### Development Data Reset

```bash
# Remove all data (destructive)
make clean
```

## Networking

### Internal Communication

Services communicate using Docker's internal DNS:

- `postgres:5432` - Database
- `redis:6379` - Message broker  
- `minio:9000` - Object storage

### External Access

- **API**: `localhost:8000`
- **MinIO Console**: `localhost:9001`

## Debugging

### Container Inspection

```bash
# View running containers
docker ps

# Inspect specific container
docker inspect <container>

# Execute commands in container
docker exec -it <container> bash
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it <pg-container> psql -U thumbnail_user -d thumbnail

# View tables
\dt

# Query jobs
SELECT id, status, created_at FROM jobs;
```

### Redis Inspection

```bash
# Connect to Redis
docker exec -it <redis-container> redis-cli

# View queues
KEYS *
LLEN celery

# Monitor commands
MONITOR
```

### MinIO Access

```bash
# Access MinIO CLI
docker exec -it <minio-container> mc

# List buckets
mc ls local

# View bucket contents
mc ls local/raws
mc ls local/thumbnails
```

## Testing

### API Testing

```bash
# Health check
curl http://localhost:8000/healthz

# Submit job
curl -X POST "http://localhost:8000/jobs" \
     -F "image=@test.jpg"

# List jobs
curl http://localhost:8000/jobs
```

## Configuration

### Environment Variables

All configuration through `.env` file:

```bash
# Edit configuration
nano .env

# Restart to apply changes
make restart
```

### Resource Limits

For development, you can add resource limits to `docker-compose.yml`:

```yaml
services:
  server:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## Common Issues

### Port Conflicts

```bash
# Check port usage
lsof -i :8000
lsof -i :9001

# Use different ports
# Edit docker-compose.yml port mappings
```
---
The Docker Compose setup works well as a development environment and lets you test everything locally before moving to Kubernetes.
