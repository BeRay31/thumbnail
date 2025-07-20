# Thumbnail Service

A production-ready microservice for generating 100x100 pixel thumbnails from uploaded images. Built for Cogent Labs to support custom emoji creation workflows with solid reliability and security.

**Author**: Reyvan Irsandy

## Overview

This service provides a REST API for asynchronous image thumbnail generation that can handle high-volume processing workloads in an on-premises Kubernetes environment. The system processes images through a distributed task queue, ensuring scalability and fault tolerance.

### Key Features

- **Asynchronous Processing**: Long-running job support via Celery task queue
- **Scalable Architecture**: Microservices design with horizontal scaling capabilities  
- **Production Security**: Read-only filesystems, non-root containers, proper security contexts
- **Observability**: Structured logging, health checks, debug endpoints, and Prometheus metrics
- **High Availability**: StatefulSet persistence, multiple worker replicas, proper resource management

## Quick Start

### Prerequisites

- Docker (latest)
- kubectl (v1.20+)
- Helm (v3.8+)
- Kind (v0.20+)

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd thumbnail-service
   ```

2. **Configuration (Optional)**
   
   The deployment uses a centralized configuration file at `scripts/config.sh` that contains all the key variables like cluster name, image names, and deployment settings. You can customize these settings before deployment:
   
   ```bash
   # Edit configuration
   vim scripts/config.sh
   
   # Key variables you can change:
   # CLUSTER_NAME="thumbnail-cluster"     # Kind cluster name
   # NAMESPACE="default"                  # Kubernetes namespace
   # SERVER_IMAGE="thumbnail-service-server"
   # WORKER_IMAGE="thumbnail-service-worker"
   # API_PORT="30000"                     # External API port
   ```

3. **Helm Configuration**

   The current `helm/values.yaml` works well for development and staging environments. For production deployments, you'll want to review and adjust several settings:

   **Key production considerations**:
   - **Scaling**: Increase `server.replicaCount` and `worker.replicaCount` based on your load
   - **Storage**: Configure appropriate `storageClass` and increase storage sizes
   - **Security**: Update default passwords in the values file or use external secrets
   - **Resources**: Set proper CPU/memory limits for your environment
   - **NodePort**: Disable `service.nodePort.enabled` and set up proper ingress instead

   **For production**, create a custom values file:

4. **Complete Deployment (Recommended)**
   ```bash
   make k8s-all
   ```
   This will:
   - Create Kind cluster
   - Build Docker images
   - Load images to cluster
   - Deploy with Helm using default values

5. **Step-by-Step Deployment**
   ```bash
   # Setup cluster
   make k8s-setup
   
   # Build images
   make k8s-build
   
   # Deploy to cluster (with custom values if needed)
   make k8s-deploy
   # Or for production: helm install thumbnail-service ./helm -f helm/values-prod.yaml
   ```

### Usage

Once deployed, the API is available at `http://localhost:30000`

#### Submit a Job
```bash
curl -X POST "http://localhost:30000/jobs" \
     -F "image=@your-image.jpg"
```

#### Check Job Status
```bash
curl "http://localhost:30000/jobs/{job_id}"
```

#### Download Thumbnail
```bash
curl "http://localhost:30000/thumbnails/{job_id}" > thumbnail.png
```

#### List All Jobs
```bash
curl "http://localhost:30000/jobs"
```

### API Documentation

Interactive API docs available at: `http://localhost:30000/docs`

## Architecture

### Design Philosophy

The architecture prioritizes **reliability**, **scalability**, and **maintainability** over complexity. I chose a microservices approach with clear separation of concerns to support future extensibility while maintaining operational simplicity.

### System Components

![System Architecture](docs/system-design.svg)

The service follows a microservices architecture with clear separation of responsibilities:

**Application Layer:**
- **API Server (FastAPI)**: Handles HTTP requests, validates uploads, manages job status, serves thumbnails
- **Celery Workers**: Process background thumbnail generation tasks, handle retries and error cases

**Data Layer:**
- **PostgreSQL**: Stores job metadata, tracks processing status, handles concurrent access
- **Redis**: Message queue for Celery tasks, stores task states, handles job priorities
- **MinIO**: S3-compatible object storage for original images and generated thumbnails

### Technology Choices

#### **FastAPI** for API Layer
- **Why**: Easy to develop with excellent developer experience, superior performance, automatic OpenAPI documentation, excellent type safety
- **Alternative Considered**: Flask (rejected due to lack of async support and manual documentation)

#### **Celery + Redis** for Task Queue
- **Why**: Simple setup for development and proven at scale, excellent monitoring, supports complex workflows
- **Production Note**: For production battle-ready systems, consider upgrading to Kafka or proper message queue systems with better persistence guarantees and advanced features like Dead Letter Queues (DLQ)
- **Alternative Considered**: RQ (rejected due to limited scaling features)

#### **PostgreSQL** for Metadata
- **Why**: ACID compliance, excellent JSON support, proven reliability
- **Alternative Considered**: MongoDB (rejected due to consistency requirements)

#### **MinIO** for Object Storage
- **Why**: S3-compatible, on-premises deployment, excellent performance
- **Alternative Considered**: File system storage (rejected due to scaling limitations)

#### **Kubernetes + Helm** for Orchestration
- **Why**: Selected to meet the specific requirement for on-premises Kubernetes deployment


### Security Design

- **Non-root containers**: All processes run as unprivileged users
- **Read-only filesystems**: Prevents runtime modifications
- **Capability dropping**: Removes unnecessary system capabilities
- **Resource limits**: Prevents resource exhaustion attacks
- **Network policies**: Implicit through Kubernetes service mesh

**Important Security Note**: The current deployment uses NodePort (port 30000) for easy access during development. For production environments, disable NodePort and use proper ingress controllers with TLS termination to avoid exposing services directly.

## Implementation Details

### Request Flow

1. **Image Upload**: Client POSTs image to `/jobs` endpoint
2. **Validation**: Server validates image format and dimensions
3. **Storage**: Original image saved to MinIO (S3-compatible storage)
4. **Job Creation**: Database record created with "processing" status
5. **Task Queuing**: Celery task queued via Redis
6. **Processing**: Worker retrieves image, generates 100x100 thumbnail
7. **Completion**: Thumbnail saved to MinIO, job status updated to "succeeded"

### Error Handling

- **Validation Errors**: Immediate rejection with descriptive messages
- **Storage Failures**: Automatic cleanup of partial uploads
- **Processing Failures**: Exponential backoff retry (3 attempts)
- **System Failures**: Graceful degradation with proper error responses

### Monitoring & Debugging

- **Health Endpoints**: `/healthz` for basic checks, `/healthz/detailed` for detailed status
- **Debug Endpoints**: `/debug/*` for system information, connectivity, and logs
- **Metrics**: `/metrics` with Prometheus-compatible format
- **Structured Logging**: JSON format with correlation IDs

## Trade-offs and Limitations

### Conscious Decisions

#### **Chosen**: Synchronous Image Validation
- **Why**: Immediate feedback improves user experience
- **Trade-off**: Slightly higher API latency
- **Future**: Could move to async validation for very large files

#### **Chosen**: Fixed 100x100 Thumbnail Size
- **Why**: Meets current requirements, simplifies implementation
- **Trade-off**: Less flexibility
- **Future**: Parameterizable dimensions with reasonable limits

#### **Chosen**: File-based Logging
- **Why**: Simple debugging, standard Kubernetes patterns
- **Trade-off**: Log rotation required for long-term operation
- **Future**: Centralized logging with ELK stack or similar

### What's Left Out (Time Constraints)

#### **Comprehensive Testing Suite**
- **Status**: Currently only manual testing has been performed
- **Production Need**: Automated unit tests, integration tests, and end-to-end testing
- **Components**: API endpoint tests, worker task tests, database model tests, error handling validation
- **Future**: Complete test coverage with CI/CD integration

#### **Enhanced Message Queue System**
- **Status**: Currently using basic Redis + Celery setup
- **Production Need**: High Availability message queue with proper persistence, Dead Letter Queues (DLQ), and message durability guarantees
- **Future**: Kafka cluster or RabbitMQ with clustering for production workloads

#### **Disaster Recovery**
- **Status**: Basic persistence only
- **Risk**: Data loss in catastrophic failures
- **Solution**: Cross-region backup strategies, automated failover procedures, point-in-time recovery capabilities
- **Components**: Database backups, object storage replication

#### **Rate Limiting**
- **Status**: Not implemented
- **Risk**: Potential resource exhaustion
- **Solution**: Redis-based rate limiting per client IP

#### **Image Format Optimization**
- **Status**: Basic PNG output only
- **Improvement**: WebP support, format negotiation based on client capabilities

#### **Batch Processing**
- **Status**: Single image per request
- **Enhancement**: Bulk upload endpoints for efficiency

#### **Advanced Monitoring**
- **Status**: Basic metrics only
- **Enhancement**: Distributed tracing, APM integration

## Production Readiness

### Current Production Features

✅ **High Availability**: Multiple worker replicas, StatefulSet persistence  
✅ **Security**: Security contexts, non-root execution, capability restrictions  
✅ **Observability**: Health checks, metrics, structured logging  
✅ **Scalability**: Horizontal pod autoscaling ready  
✅ **Resource Management**: CPU/memory limits and requests  
✅ **Configuration Management**: Environment-based config with secrets  

### Additional Productionization Steps

#### **Infrastructure & Operations**

1. **Persistent Storage Classes**
   - Configure appropriate storage classes for PostgreSQL and MinIO
   - Implement backup strategies for data persistence
   - Set up cross-AZ replication for high availability

2. **Networking & Security**
   - Implement NetworkPolicies for pod-to-pod communication
   - Set up ingress controllers with TLS termination
   - Configure service mesh (Istio/Linkerd) for advanced traffic management

3. **Monitoring & Alerting**
   - Deploy Prometheus for metrics collection
   - Configure Grafana dashboards for visualization
   - Set up alerting rules for system health
   - Implement log aggregation (ELK/EFK stack)

#### **Application Enhancements**

1. **Performance Optimization**
   - Implement connection pooling for database and Redis
   - Add caching layer for frequently accessed metadata
   - Optimize image processing pipeline with streaming

2. **Reliability Improvements**
   - Circuit breakers for external dependencies
   - Graceful shutdown handling for worker processes
   - Dead letter queues for failed jobs

3. **Security Hardening**
   - Implement proper authentication and authorization
   - Add request signing for API security
   - Vulnerability scanning in CI/CD pipeline

### Scaling Considerations

#### **Horizontal Scaling**
- **Workers**: Can scale to dozens of replicas based on queue depth
- **API Servers**: Stateless design supports unlimited horizontal scaling
- **Database**: Read replicas for query scaling, partitioning for write scaling

#### **Vertical Scaling**
- **Memory**: Processing large images requires memory tuning
- **CPU**: Thumbnail generation is CPU-intensive, optimized for multi-core

#### **Storage Scaling**
- **MinIO**: Supports distributed mode for petabyte-scale storage
- **PostgreSQL**: Supports table partitioning for metadata scaling

## Development

### Local Development Setup

See [Development Guide](docs/DEVELOPMENT.md) for detailed setup instructions.

### Environment Configuration

See [Environment Variables Guide](docs/ENVIRONMENT.md) for all configuration options.

### Docker Development

See [Docker Guide](docs/DOCKER.md) for container-based development.

### Kubernetes Development

See [Kubernetes Guide](docs/KUBERNETES.md) for cluster-based development.

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check init container logs for dependency readiness
2. **API not accessible**: Verify NodePort services and Kind port mappings
3. **Jobs stuck in processing**: Check worker logs and Redis connectivity
4. **Storage issues**: Verify MinIO bucket creation and credentials

### Debug Commands

```bash
# Check all components
kubectl get all

# View API logs
kubectl logs -l app.kubernetes.io/component=server -f

# View worker logs  
kubectl logs -l app.kubernetes.io/component=worker -f

# Check system health
curl http://localhost:30000/healthz/detailed
```

## Disclaimer

This project is developed as part of the Cogent Labs technical assessment.

**Contact**: For questions about this implementation, please include relevant logs and system information from the debug endpoints.
