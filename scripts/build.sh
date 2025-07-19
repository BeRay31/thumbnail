#!/bin/bash
set -e
echo "🔨 Building Docker images for Thumbnail Service..."
echo "Building server image..."
docker build -f Dockerfile.server -t thumbnail-service-server:latest .

echo "Building worker image..."
docker build -f Dockerfile.worker -t thumbnail-service-worker:latest .

echo "✅ Docker images built successfully!"
echo "   - thumbnail-service-server:latest"
echo "   - thumbnail-service-worker:latest"

docker images | grep thumbnail-service
