#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

echo "Loading app images..."

if ! kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "Error: cluster not found"
    echo "Run ./scripts/kind-setup.sh first"
    exit 1
fi

images=("$SERVER_IMAGE" "$WORKER_IMAGE")

for image in "${images[@]}"; do
    echo "  $image"
    kind load docker-image "$image" --name "$CLUSTER_NAME" || exit 1
done

echo "Done"

# check they loaded
docker exec "${CLUSTER_NAME}-control-plane" crictl images | grep thumbnail-service || echo "Images loading..."
