# Development Guide

This document will walk you through everything you need to know to get up and running with local development, from understanding the environment configuration to running tests and debugging.

## Table of Contents

- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Development Workflows](#development-workflows)
- [Understanding the Architecture](#understanding-the-architecture)
- [Working with Different Components](#working-with-different-components)
- [Testing and Debugging](#testing-and-debugging)
- [Common Development Tasks](#common-development-tasks)
- [Troubleshooting](#troubleshooting)

## Quick Start

The fastest way to get everything running locally:

```bash
# Clone and navigate
git clone <repository-url>
cd thumbnail-service

# Copy environment template
cp .env.example .env

# Start everything with Docker Compose
make up

# Check if everything is running
curl http://localhost:8000/healthz
```

That's it! Your development environment should be running. The API will be available at `http://localhost:8000`.

## Environment Configuration

### Understanding the Configuration Flow

The project uses a layered configuration approach that makes it easy to switch between different environments:

<img src="development-env.svg" alt="dev-env-flow" width="600" height="600" />


### Local Development Configuration

The `.env` file controls your local development environment. Here's what each variable does:

#### Database Settings
```bash
# PostgreSQL - Where we store job metadata and status
POSTGRES_USER=admin           # Database username
POSTGRES_PASSWORD=admin       # Database password (change for production!)
POSTGRES_SERVER=localhost     # Database host (localhost for local dev)
POSTGRES_DB=thumbnail         # Database name
POSTGRES_PORT=5432           # Standard PostgreSQL port
```

#### Object Storage Settings
```bash
# MinIO - S3-compatible storage for images
MINIO_ENDPOINT=localhost:9000    # MinIO server endpoint
MINIO_ACCESS_KEY=minioadmin      # Access key (like AWS access key)
MINIO_SECRET_KEY=minioadmin      # Secret key (like AWS secret key)
MINIO_ORIGINALS_BUCKET=raws      # Bucket for original uploaded images
MINIO_THUMBNAILS_BUCKET=thumbnails # Bucket for generated thumbnails
```

#### Message Queue Settings
```bash
# Redis - Message broker for Celery tasks
REDIS_HOST=localhost          # Redis server host
REDIS_PORT=6379              # Standard Redis port
```

### Kubernetes Configuration

For Kubernetes deployments, configuration is managed through `scripts/config.sh`:

```bash
# Cluster configuration
CLUSTER_NAME="thumbnail-service"    # Kind cluster name
NAMESPACE="default"                 # Kubernetes namespace

# Application images
SERVER_IMAGE="thumbnail-service-server:latest"
WORKER_IMAGE="thumbnail-service-worker:latest"

# External access
HOST_PORT="30000"                   # Port for accessing the API
```

You can customize these values before deploying to Kubernetes.

## Development Workflows

### Docker Compose Development

This is the recommended approach for local development as it matches the production environment closely:

```bash
# Start everything (detached mode)
make up

# View logs from all services
make logs

# Stop everything
make down

# Rebuild after code changes
make build && make up
```

**When to use**: For most development tasks, debugging, and testing new features.

**Pros**: Easy setup, matches production, isolated dependencies, consistent environment
**Cons**: Requires rebuilding containers for code changes

### Kubernetes Development

For testing Kubernetes-specific features or deployment configurations:

```bash
# Complete Kubernetes setup
make k8s-all

# Or step by step:
make k8s-setup    # Create Kind cluster
make k8s-build    # Build images
make k8s-deploy   # Deploy with Helm
```

**When to use**: When testing Helm charts, Kubernetes configurations, or production-like scenarios.

**Pros**: Production-like environment, tests actual deployment
**Cons**: Slower feedback loop, more complex setup

For detailed Kubernetes development, see the [Kubernetes Guide](KUBERNETES.md).

## Understanding the Architecture

### How Components Work Together

Let's trace through what happens when you upload an image:

1. **API Request**: You POST an image to `/jobs`
2. **Validation**: FastAPI validates the image format and size
3. **Storage**: Original image gets saved to MinIO (originals bucket)
4. **Job Creation**: A new job record is created in PostgreSQL
5. **Task Queue**: A Celery task is queued in Redis
6. **Processing**: A Celery worker picks up the task
7. **Thumbnail Generation**: Worker downloads image, creates 100x100 thumbnail
8. **Storage**: Thumbnail gets saved to MinIO (thumbnails bucket)
9. **Status Update**: Job status is updated to "completed" in PostgreSQL

### Component Responsibilities

**FastAPI Server** (`app/api/`):
- Handles HTTP requests
- Validates input data
- Manages job status
- Serves static files (thumbnails)

**Celery Worker** (`app/worker/`):
- Processes background tasks
- Generates thumbnails
- Handles retries and error cases

**PostgreSQL**:
- Stores job metadata
- Tracks processing status
- Handles concurrent access

**Redis**:
- Message queue for Celery
- Stores task states
- Handles job priorities

**MinIO**:
- Object storage for images
- S3-compatible API
- Bucket management

## Working with Different Components

### Developing API Endpoints

When adding new API endpoints, you'll mainly work in `app/api/routes/`:

```python
# Example: Adding a new endpoint
@router.get("/jobs/{job_id}/metadata")
async def get_job_metadata(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    # Your endpoint logic here
    pass
```

**Testing your endpoint**:
```bash
# If using Docker Compose
curl http://localhost:8000/jobs/{job_id}/metadata

# If running locally
curl http://localhost:8000/jobs/{job_id}/metadata
```

### Working with Background Tasks

Background tasks live in `app/worker/tasks.py`. When modifying task logic:

```python
@celery_app.task
def new_processing_task(job_id: str):
    # Your task logic here
    pass
```

**Testing tasks**:
```bash
# Monitor task execution
celery -A app.worker.celery_app events

# Check active tasks
celery -A app.worker.celery_app inspect active
```

### Database Changes

When you need to modify the database schema:

1. **Update the model** in `app/db/models/`
2. **The `init_db()` function will automatically handle migrations** when the application starts, creating new tables and applying schema changes as needed
3. **For manual migration control** (optional):
   ```bash
   # Generate migration explicitly
   docker-compose exec server alembic revision --autogenerate -m "your description"
   
   # Apply migration manually
   docker-compose exec server alembic upgrade head
   ```

The application handles database initialization automatically, so most schema changes will be applied when you restart the services.

## Testing and Debugging

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api/test_jobs.py

# Run tests with verbose output
pytest -v
```

### Debugging Tips

#### Checking Component Health

```bash
# API health check
curl http://localhost:8000/healthz

# Detailed health check (includes dependencies)
curl http://localhost:8000/healthz/detailed

# Check what's running
docker-compose ps
```

#### Viewing Logs

```bash
# All services
make logs

# Specific service
docker-compose logs -f server
docker-compose logs -f worker
docker-compose logs -f postgres
```

#### Database Debugging

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U admin -d thumbnail

# Common queries
SELECT * FROM jobs ORDER BY created_at DESC LIMIT 5;
SELECT status, COUNT(*) FROM jobs GROUP BY status;
```

#### Redis Debugging

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check queue status
KEYS *
LLEN celery
```

#### MinIO Debugging

Access the MinIO console at `http://localhost:9001` with credentials `minioadmin:minioadmin`.

Or use the command line:
```bash
# List buckets
docker-compose exec minio mc ls local

# List files in bucket
docker-compose exec minio mc ls local/raws
```

## Common Development Tasks

### Adding New Environment Variables

1. **Add to `.env.example`**:
   ```bash
   NEW_FEATURE_ENABLED=true
   ```

2. **Update configuration** in `app/core/config.py`:
   ```python
   class Settings(BaseSettings):
       new_feature_enabled: bool = False
   ```

3. **Use in your code**:
   ```python
   from app.core.config import settings
   
   if settings.new_feature_enabled:
       # Your feature code
   ```

### Working with Docker Images

```bash
# Build specific service
docker-compose build server

# Build without cache
docker-compose build --no-cache

# View image sizes
docker images | grep thumbnail
```

### Performance Testing

```bash
# Simple load test with curl
for i in {1..10}; do
    curl -X POST -F "file=@test-image.jpg" http://localhost:8000/jobs &
done
wait

# Check system resources
docker stats
```

## Docker-Specific Development

For detailed Docker development workflows, see the [Docker Guide](DOCKER.md). This covers:
- Container-specific debugging
- Volume management
- Multi-stage build optimization
- Docker Compose advanced features

## Kubernetes Development

For Kubernetes-specific development, see the [Kubernetes Guide](KUBERNETES.md). This covers:
- Helm chart development
- Local cluster management
- Resource configuration
- Production deployment patterns

## Troubleshooting

### Common Issues and Solutions

#### "Connection refused" errors
**Symptoms**: API requests fail with connection errors
**Solutions**:
1. Check if services are running: `docker-compose ps`
2. Check logs: `make logs`
3. Restart services: `make down && make up`

#### "Database connection failed"
**Symptoms**: Application can't connect to PostgreSQL
**Solutions**:
1. Check PostgreSQL logs: `docker-compose logs postgres`
2. Verify environment variables in `.env`
3. Ensure PostgreSQL container is healthy: `docker-compose ps postgres`

#### "Worker not processing jobs"
**Symptoms**: Jobs stuck in "pending" status
**Solutions**:
1. Check worker logs: `docker-compose logs worker`
2. Check Redis connection: `docker-compose exec redis redis-cli ping`
3. Check Celery task queue: `docker-compose exec redis redis-cli llen celery`

#### "MinIO bucket not found"
**Symptoms**: Upload fails with bucket errors
**Solutions**:
1. Check MinIO console: `http://localhost:9001`
2. Check if buckets exist: `docker-compose exec minio mc ls local`
3. Restart MinIO: `docker-compose restart minio`

### Getting Help

#### Debug Endpoints

The application provides several debug endpoints:

```bash
# System information
curl http://localhost:8000/debug/info

# Configuration dump
curl http://localhost:8000/debug/config

# Health check with dependencies
curl http://localhost:8000/debug/health
```

#### Log Analysis

```bash
# Search for errors in logs
docker-compose logs | grep -i error

# Follow logs for a specific service
docker-compose logs -f server | grep "ERROR\|WARN"
```

#### Resource Monitoring

```bash
# Monitor container resources
docker stats

# Check disk usage
docker system df

# Clean up unused resources
docker system prune
```

---

Happy coding! If you run into any issues not covered here, check the logs first, then consult the specific guides for [Docker](DOCKER.md) or [Kubernetes](KUBERNETES.md) development.
