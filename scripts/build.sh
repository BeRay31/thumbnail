#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

echo "Building images..."

docker build -f Dockerfile.server -t "$SERVER_IMAGE" .
docker build -f Dockerfile.worker -t "$WORKER_IMAGE" .

echo "Built:"
echo "  $SERVER_IMAGE"
echo "  $WORKER_IMAGE"

docker images | grep thumbnail-service
