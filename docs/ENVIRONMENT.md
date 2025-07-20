# Environment Variables Guide

This document explains all environment variables used by the Thumbnail Service, their purposes, and how they relate to different deployment scenarios.

## Overview

The service uses environment-based configuration to support different deployment environments (development, testing, production) without code changes. All sensitive values are managed through Kubernetes secrets.

## Core Application Variables

### Database Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `POSTGRES_USER` | Database username | - | Yes | `thumbnail_user` |
| `POSTGRES_PASSWORD` | Database password | - | Yes | `secure_password_123` |
| `POSTGRES_SERVER` | Database hostname | - | Yes | `thumbnail-service-postgresql` |
| `POSTGRES_PORT` | Database port | `5432` | No | `5432` |
| `POSTGRES_DB` | Database name | - | Yes | `thumbnail` |
| `DATABASE_URL` | Complete connection string | Auto-generated | No | `postgresql+psycopg2://user:pass@host:5432/db` |

### Redis Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `REDIS_HOST` | Redis server hostname | - | Yes | `thumbnail-service-redis` |
| `REDIS_PORT` | Redis server port | `6379` | No | `6379` |

### MinIO Storage Configuration

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `MINIO_ENDPOINT` | MinIO server endpoint | - | Yes | `thumbnail-service-minio:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | - | Yes | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | - | Yes | `minioadmin` |
| `MINIO_ORIGINALS_BUCKET` | Bucket for original images | `raws` | No | `original-images` |
| `MINIO_THUMBNAILS_BUCKET` | Bucket for thumbnails | `thumbnails` | No | `generated-thumbnails` |

## Deployment-Specific Configuration

### Docker Compose Development

For local development with Docker Compose, variables are set in `.env` file:

```bash
# Database
POSTGRES_USER=thumbnail_user
POSTGRES_PASSWORD=thumbnail_pass
POSTGRES_SERVER=postgres
POSTGRES_DB=thumbnail

# Redis
REDIS_HOST=redis

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### Kubernetes

In Kubernetes, variables are managed through:

#### ConfigMap (Non-sensitive data)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: thumbnail-service-config
data:
  POSTGRES_USER: "admin"
  POSTGRES_SERVER: "thumbnail-service-postgresql"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "thumbnail"
  REDIS_HOST: "thumbnail-service-redis"
  REDIS_PORT: "6379"
  MINIO_ENDPOINT: "thumbnail-service-minio:9000"
  MINIO_ORIGINALS_BUCKET: "raws"
  MINIO_THUMBNAILS_BUCKET: "thumbnails"
```

#### Secret (Sensitive data)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: thumbnail-service-secret
type: Opaque
data:
  POSTGRES_PASSWORD: <base64-encoded-password>
  MINIO_ACCESS_KEY: <base64-encoded-access-key>
  MINIO_SECRET_KEY: <base64-encoded-secret-key>
```

## Variable Usage in Code

### Configuration Loading

The application uses Pydantic Settings for type-safe configuration loading:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    DATABASE_URL: str = ""
    
    # Auto-generate DATABASE_URL if not provided
    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
```

## Security Considerations

### Sensitive Variables

The following variables contain sensitive information and must be stored in Kubernetes Secrets:

- `POSTGRES_PASSWORD`
- `MINIO_ACCESS_KEY`  
- `MINIO_SECRET_KEY`

### Non-sensitive Variables

These can be stored in ConfigMaps:

- All hostnames and ports
- Database and bucket names
- Non-authentication configuration

## Kubernetes with Helm

When deploying to Kubernetes, I use Helm charts to manage configuration across different environments. Helm provides a clean way to template Kubernetes manifests and separate configuration from deployment logic.

#### How Helm Works with values.yaml

Helm uses a values.yaml file to define configuration that gets injected into template files. The chart is designed to handle different deployment scenarios, from local development to production clusters. Here's how the actual values.yaml is structured:

**values.yaml (Complete structure):**
```yaml
# Image configuration - assumes images are built and loaded manually
image:
  server:
    repository: thumbnail-service-server
    tag: latest
    pullPolicy: Never  # For local development with Kind
  worker:
    repository: thumbnail-service-worker
    tag: latest
    pullPolicy: Never

# Service configuration with NodePort for local access
service:
  type: ClusterIP
  port: 8000
  nodePort:
    enabled: true
    port: 30000  # Access the API at localhost:30000

# Separate deployment configuration for server and worker
server:
  replicaCount: 1
worker:
  replicaCount: 2  # More workers for thumbnail processing

# Resource allocation per component
resources:
  server:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi
  worker:  # Workers need more resources for image processing
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi

# PostgreSQL with embedded chart
postgresql:
  enabled: true
  database: thumbnail
  auth:
    username: admin
    password: admin
  persistence:
    enabled: true
    size: 8Gi

# External PostgreSQL option
externalPostgresql:
  host: ""
  port: 5432
  database: thumbnail

# Redis with embedded chart
redis:
  enabled: true

# External Redis option
externalRedis:
  host: ""
  port: 6379

# MinIO with embedded chart and console access
minio:
  enabled: true
  auth:
    accessKey: minioadmin
    secretKey: minioadmin
  buckets:
    originals: raws
    thumbnails: thumbnails
  persistence:
    enabled: true
    size: 10Gi
  console:
    nodePort:
      enabled: true
      port: 30001  # Access MinIO console at localhost:30001

# External MinIO option
externalMinio:
  endpoint: ""

# Security contexts for both components
securityContext:
  server:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  worker:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000

# Health checks for the server
healthChecks:
  server:
    liveness:
      path: /healthz
      initialDelaySeconds: 30
      periodSeconds: 10
    readiness:
      path: /healthz/detailed
      initialDelaySeconds: 5
      periodSeconds: 10
```

This structure gives me several deployment options:

**1. All-in-one local development** (default):
- All dependencies run inside the cluster
- NodePort services for easy access
- Minimal resource requirements

**2. Hybrid deployments**:
- Use external databases for persistence
- Keep some services internal for development

**3. Production deployments**:
- External managed services
- Proper resource limits
- Security contexts enforced

#### Helm Templates Transform Values into Kubernetes Resources

The magic happens in the template files. Helm takes the values and generates actual Kubernetes manifests. Here's how the chart transforms my values.yaml into environment variables:

**ConfigMap Template (templates/configmap.yaml):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "thumbnail-service.fullname" . }}-config
data:
  # Database configuration from postgresql section
  {{- if .Values.postgresql.enabled }}
  POSTGRES_SERVER: {{ include "thumbnail-service.postgresql.fullname" . | quote }}
  POSTGRES_USER: {{ .Values.postgresql.auth.username | quote }}
  POSTGRES_DB: {{ .Values.postgresql.database | quote }}
  {{- else }}
  POSTGRES_SERVER: {{ .Values.externalPostgresql.host | quote }}
  POSTGRES_USER: {{ .Values.externalPostgresql.username | quote }}
  POSTGRES_DB: {{ .Values.externalPostgresql.database | quote }}
  {{- end }}
  POSTGRES_PORT: {{ .Values.postgresql.port | default "5432" | quote }}
  
  # Redis configuration
  {{- if .Values.redis.enabled }}
  REDIS_HOST: {{ include "thumbnail-service.redis.fullname" . | quote }}
  {{- else }}
  REDIS_HOST: {{ .Values.externalRedis.host | quote }}
  {{- end }}
  REDIS_PORT: {{ .Values.redis.port | default "6379" | quote }}
  
  # MinIO configuration
  {{- if .Values.minio.enabled }}
  MINIO_ENDPOINT: {{ printf "%s:9000" (include "thumbnail-service.minio.fullname" .) | quote }}
  {{- else }}
  MINIO_ENDPOINT: {{ .Values.externalMinio.endpoint | quote }}
  {{- end }}
  MINIO_ORIGINALS_BUCKET: {{ .Values.minio.buckets.originals | quote }}
  MINIO_THUMBNAILS_BUCKET: {{ .Values.minio.buckets.thumbnails | quote }}
```

**Secret Template (templates/secret.yaml):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "thumbnail-service.fullname" . }}-secret
type: Opaque
data:
  {{- if .Values.postgresql.enabled }}
  POSTGRES_PASSWORD: {{ .Values.postgresql.auth.password | b64enc | quote }}
  {{- else }}
  POSTGRES_PASSWORD: {{ .Values.externalPostgresql.password | b64enc | quote }}
  {{- end }}
  
  {{- if .Values.minio.enabled }}
  MINIO_ACCESS_KEY: {{ .Values.minio.auth.accessKey | b64enc | quote }}
  MINIO_SECRET_KEY: {{ .Values.minio.auth.secretKey | b64enc | quote }}
  {{- else }}
  MINIO_ACCESS_KEY: {{ .Values.externalMinio.accessKey | b64enc | quote }}
  MINIO_SECRET_KEY: {{ .Values.externalMinio.secretKey | b64enc | quote }}
  {{- end }}
```

The templates are smart enough to handle both embedded services (when `*.enabled: true`) and external services. This means I can start with everything running in-cluster for development, then gradually move to external managed services for production without changing the application code.

#### Environment-Specific Deployments

The beauty of this Helm chart is its flexibility. You can customize any configuration value without changing the templates themselves. Here are the main ways to override values:

**Using command-line flags:**
```bash
# Override individual values
helm install thumbnail ./helm \
  --set postgresql.enabled=false \
  --set externalPostgresql.host=my-external-db.com \
  --set server.replicaCount=3
```

**Using custom values files:**
```bash
# Create custom-values.yaml with your overrides
cat > custom-values.yaml << EOF
postgresql:
  enabled: false
externalPostgresql:
  host: my-database-server.com
  username: my_user
  password: my_password
server:
  replicaCount: 2
worker:
  replicaCount: 4
EOF

# Deploy with custom configuration
helm install thumbnail ./helm -f custom-values.yaml
```

**Combining both approaches:**
```bash
# Use a base custom file plus additional overrides
helm install thumbnail ./helm \
  -f custom-values.yaml \
  --set minio.console.nodePort.enabled=false
```

#### How Templates and Values Work Together

Here's the step-by-step process of how Helm transforms my values.yaml into actual Kubernetes resources:

1. **values.yaml provides the data** - All the configuration options I want to customize
2. **Templates define the structure** - How that data should be formatted into Kubernetes manifests
3. **Helm processes templates** - Replaces `{{ .Values.something }}` with actual values
4. **Conditional logic handles flexibility** - Different templates based on what services are enabled
5. **Generated manifests get applied** - Creates real ConfigMaps, Secrets, and Deployments
6. **Pods start with environment variables** - The application sees standard env vars regardless of how they were generated

**Example transformation flow:**

When I have this in values.yaml:
```yaml
postgresql:
  enabled: true
  auth:
    username: admin
    password: secret123
```

The template processes it like this:
```yaml
# Template with conditional logic
{{- if .Values.postgresql.enabled }}
POSTGRES_SERVER: {{ include "thumbnail-service.postgresql.fullname" . | quote }}
POSTGRES_USER: {{ .Values.postgresql.auth.username | quote }}
{{- end }}
```

And generates this final ConfigMap:
```yaml
apiVersion: v1
kind: ConfigMap
data:
  POSTGRES_SERVER: "thumbnail-service-postgresql"
  POSTGRES_USER: "admin"
```

The application then receives `POSTGRES_SERVER=thumbnail-service-postgresql` as an environment variable, exactly what it expects. The magic is that I can change `postgresql.enabled: false` and provide `externalPostgresql.host: my-db.com`, and the template will generate `POSTGRES_SERVER: "my-db.com"` instead - same environment variable, different source.

This approach gives me incredible flexibility. I can start simple with everything in-cluster, then gradually move to external services by just changing values. The application code never needs to change because it always sees the same environment variable interface.

## Validation and Defaults

### Required Variables

The application will fail to start if these variables are missing:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD` 
- `POSTGRES_SERVER`
- `POSTGRES_DB`
- `REDIS_HOST`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`

### Optional Variables with Defaults

- `POSTGRES_PORT` → `5432`
- `REDIS_PORT` → `6379`
- `MINIO_ORIGINALS_BUCKET` → `raws`
- `MINIO_THUMBNAILS_BUCKET` → `thumbnails`

### Auto-Generated Variables

- `DATABASE_URL` → Constructed from individual database variables if not provided

## Debugging Configuration

### Viewing Current Configuration

Use the debug endpoint to see current (non-sensitive) configuration:

```bash
curl http://localhost:30000/debug/config
```

### Common Configuration Issues

1. **Database Connection Fails**
   - Check `POSTGRES_*` variables match database setup
   - Verify network connectivity between components

2. **Redis Connection Fails**
   - Confirm `REDIS_HOST` and `REDIS_PORT` are correct
   - Check Redis service is running

3. **MinIO Access Denied**
   - Verify `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`
   - Confirm bucket names exist and are accessible

4. **Application Won't Start**
   - Check required variables are set
   - Review logs for specific missing variables
