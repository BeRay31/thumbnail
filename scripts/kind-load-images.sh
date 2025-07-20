#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

echo "Loading images to cluster..."

if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "Error: cluster not found"
    echo "Run ./scripts/kind-setup.sh first"
    exit 1
fi

echo "Pulling infrastructure images..."

# infrastructure images
infra_images=(
    "$POSTGRES_IMAGE"
    "$REDIS_IMAGE" 
    "$MINIO_IMAGE"
    "$MINIO_MC_IMAGE"
)

for image in "${infra_images[@]}"; do
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "  $image (cached)"
    else
        echo "  $image"
        docker pull "$image" || exit 1
    fi
done

echo "Loading infrastructure images to cluster..."
for image in "${infra_images[@]}"; do
    echo "  $image"
    kind load docker-image "$image" --name "$CLUSTER_NAME" || true
done

echo "Loading app images..."

app_images=("$SERVER_IMAGE" "$WORKER_IMAGE")

for image in "${app_images[@]}"; do
    echo "  $image"
    kind load docker-image "$image" --name "$CLUSTER_NAME" || exit 1
done

echo "All images loaded"

# verify images are available
echo "Verifying images in cluster..."
docker exec "${CLUSTER_NAME}-control-plane" crictl images | grep -E "(thumbnail-service|postgres|redis|minio)" || echo "Images may still be loading..."
