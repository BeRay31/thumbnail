#!/bin/bash
# Configuration for thumbnail service deployment

CLUSTER_NAME="thumbnail-service"
KIND_NODE_IMAGE="kindest/node:v1.33.1"

RELEASE_NAME="thumbnail-service"
NAMESPACE="default"
CHART_PATH="./helm"

SERVER_IMAGE="thumbnail-service-server:latest"
WORKER_IMAGE="thumbnail-service-worker:latest"

POSTGRES_IMAGE="postgres:15"
REDIS_IMAGE="redis:7-alpine"
MINIO_IMAGE="minio/minio:latest"
MINIO_MC_IMAGE="minio/mc:latest"

HOST_PORT="30000"
CONTAINER_PORT="30000"
