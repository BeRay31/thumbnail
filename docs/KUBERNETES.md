# Kubernetes Deployment Guide

This guide covers deploying the Thumbnail Service to Kubernetes using Helm charts, with detailed explanations of components, configurations, and operational procedures.

## Overview

The Kubernetes deployment uses a microservices architecture with separate components for API serving, background processing, and data storage. Each component is configured for production use with proper security contexts, resource management, and observability.

## Prerequisites

- Kubernetes cluster (1.20+)
- Helm (3.8+)
- kubectl configured for your cluster
- Docker images built and available

For local development with Kind:
- Kind (0.20+)
- Docker (20.10+)

## Quick Start

### Local Development (Kind)

```bash
# Complete setup
make k8s-all

# Or step by step:
make k8s-setup    # Create Kind cluster
make k8s-build    # Build Docker images  
make k8s-deploy   # Deploy with Helm
```

### Existing Cluster

```bash
# Build images
./scripts/build.sh

# Load to cluster (if using Kind)
./scripts/kind-load-images.sh

# Deploy with Helm
./scripts/deploy.sh
```

## Architecture

### Component Overview
<img src="system-design.svg" alt="system-design" width="800" height="800" />


### Helm Chart Structure

```
helm/
├── Chart.yaml                 # Chart metadata
├── values.yaml               # Default configuration
├── templates/
│   ├── _helpers.tpl          # Template helpers
│   ├── configmap.yaml        # Application configuration
│   ├── secret.yaml           # Sensitive configuration
│   ├── server-deployment.yaml # API server
│   ├── worker-deployment.yaml # Background workers
│   ├── service.yaml          # Service definitions
│   ├── service-nodeport.yaml # External access
│   ├── postgresql.yaml       # Database StatefulSet
│   ├── redis.yaml           # Cache Deployment
│   ├── minio.yaml           # Object storage StatefulSet
│   ├── minio-init-job.yaml  # Bucket initialization
│   └── minio-console-service.yaml # MinIO UI access
```

## Component Details

### Server Deployment

**Purpose**: Serves the REST API for job submission and status queries

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thumbnail-service-server
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
  template:
    spec:
      initContainers:
        - name: wait-for-postgresql    # Wait for database
        - name: wait-for-redis         # Wait for message broker
        - name: wait-for-minio         # Wait for storage
      containers:
        - name: server
          image: thumbnail-service-server:latest
          ports:
            - containerPort: 8000
          resources:
            limits:
              memory: 512Mi
              cpu: 500m
            requests:
              memory: 256Mi
              cpu: 250m
```

**Key Features**:
- **Init Containers**: Ensure dependencies are ready before starting
- **Health Checks**: Readiness and liveness probes
- **Resource Management**: CPU and memory limits
- **Security Context**: Non-root execution, read-only filesystem

### Worker Deployment

**Purpose**: Processes thumbnail generation jobs from the queue

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thumbnail-service-worker
spec:
  replicas: 2                    # Multiple workers for parallel processing
  template:
    spec:
      initContainers:            # Same dependency waiting as server
      containers:
        - name: worker
          image: thumbnail-service-worker:latest
          command: ["celery", "-A", "worker.celery_app", "worker"]
```

**Scaling**: 
- Default: 2 replicas
- Can scale based on queue depth
- Configurable via `worker.replicaCount` value

### PostgreSQL StatefulSet

**Purpose**: Persistent database for job metadata and status

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thumbnail-service-postgresql
spec:
  serviceName: thumbnail-service-postgresql
  replicas: 1
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

**Features**:
- **Persistent Storage**: Data survives pod restarts
- **Headless Service**: Direct pod-to-pod communication
- **Health Checks**: `pg_isready` validation
- **Backup Ready**: Volume can be snapshotted

### Redis Deployment

**Purpose**: Message broker for Celery task queue

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thumbnail-service-redis
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
```

**Configuration**:
- Single replica (suitable for development)
- Production: Consider Redis Cluster or Sentinel
- Persistent volume optional (queue data is transient)

### MinIO StatefulSet

**Purpose**: S3-compatible object storage for images and thumbnails

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thumbnail-service-minio
spec:
  serviceName: thumbnail-service-minio
  replicas: 1
  volumeClaimTemplates:
    - metadata:
        name: minio-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

**Features**:
- **Console Access**: Web UI on port 9001
- **Bucket Auto-creation**: Init job creates required buckets
- **Persistent Storage**: Images survive pod restarts
- **S3 Compatible**: Standard S3 API support

## Configuration Management

### Values.yaml Structure

```yaml
# Image configuration
image:
  server:
    repository: thumbnail-service-server
    tag: latest
    pullPolicy: Never
  worker:
    repository: thumbnail-service-worker
    tag: latest
    pullPolicy: Never

# Scaling configuration
server:
  replicaCount: 1
worker:
  replicaCount: 2

# Service configuration
service:
  type: ClusterIP
  port: 8000
  nodePort:
    enabled: true
    port: 30000

# Storage configuration
storage:
  persistence:
    enabled: true
    size: 10Gi
    storageClass: ""

# Database configuration
postgresql:
  enabled: true
  auth:
    username: admin
    password: admin
    database: thumbnail

# MinIO configuration
minio:
  enabled: true
  auth:
    accessKey: minioadmin
    secretKey: minioadmin
  buckets:
    originals: raws
    thumbnails: thumbnails
```
## Storage Management

### Persistent Volumes

#### PostgreSQL Storage
- **Type**: ReadWriteOnce PVC
- **Size**: 10Gi (configurable)
- **Purpose**: Database files, WAL logs
- **Backup**: Volume snapshots recommended

#### MinIO Storage  
- **Type**: ReadWriteOnce PVC
- **Size**: 10Gi (configurable)
- **Purpose**: Original images, generated thumbnails
- **Backup**: S3 replication or volume snapshots

### Storage Classes

#### Development (Kind)
```yaml
storageClassName: "standard"    # Default Kind storage class
```

#### Production
```yaml
storageClassName: "fast-ssd"    # High-performance storage
# or
storageClassName: "backup-enabled"  # Storage with automatic backups
```

## Networking

### Service Types

#### Internal Services (ClusterIP)
- **PostgreSQL**: `thumbnail-service-postgresql:5432`
- **Redis**: `thumbnail-service-redis:6379` 
- **MinIO API**: `thumbnail-service-minio:9000`
- **API Server**: `thumbnail-service-server:8000`

#### External Access (NodePort)
- **API Server**: `localhost:30000`
- **MinIO Console**: `localhost:30001`

### Kind Cluster Configuration

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000    # API server
    hostPort: 30000
  - containerPort: 30001    # MinIO console
    hostPort: 30001
- role: worker
- role: worker
```
## Monitoring and Observability

### Health Checks

#### Readiness Probes
```yaml
readinessProbe:
  httpGet:
    path: /healthz/detailed
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

#### Liveness Probes
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 20
```

### Metrics Collection

```bash
# View Prometheus metrics
curl http://localhost:30000/metrics

# Debug endpoints
curl http://localhost:30000/debug/info
curl http://localhost:30000/debug/config
```

### Log Aggregation

```bash
# View application logs
kubectl logs -l app.kubernetes.io/component=server -f

# View worker logs
kubectl logs -l app.kubernetes.io/component=worker -f

# All components
kubectl logs -l app.kubernetes.io/name=thumbnail-service -f
```

## Troubleshooting

### Common Issues

#### Pods Not Starting
```bash
# Check pod status
kubectl get pods

# Describe problematic pod
kubectl describe pod <pod-name>

# Check init container logs
kubectl logs <pod-name> -c wait-for-postgresql
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it deployment/thumbnail-service-server -- \
  python -c "from app.db.session import SessionLocal; SessionLocal()"

# Check database logs
kubectl logs statefulset/thumbnail-service-postgresql
```

#### Storage Issues
```bash
# Check PVC status
kubectl get pvc

# Check storage class
kubectl get storageclass

# Describe PVC
kubectl describe pvc postgres-data-thumbnail-service-postgresql-0
```

### Debug Commands

```bash
# Execute shell in server pod
kubectl exec -it deployment/thumbnail-service-server -- /bin/bash

# Port forward for direct access
kubectl port-forward service/thumbnail-service-server 8000:8000

# Check service endpoints
kubectl get endpoints
```
