#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

echo "Setting up kind cluster..."

# dependency checks
if ! command -v kind &> /dev/null; then
    echo "Error: kind not found"
    echo "Install: https://kind.sigs.k8s.io/docs/user/quick-start/"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Error: docker not found"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found"
    exit 1
fi

echo "Pulling images..."

# images we need
images=(
    "$KIND_NODE_IMAGE"
    "$POSTGRES_IMAGE"
    "$REDIS_IMAGE" 
    "$MINIO_IMAGE"
    "$MINIO_MC_IMAGE"
)

for image in "${images[@]}"; do
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "  $image (cached)"
    else
        echo "  $image"
        docker pull "$image" || exit 1
    fi
done

# create cluster if needed
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster '$CLUSTER_NAME' exists"
    kubectl config use-context "kind-${CLUSTER_NAME}"
else
    echo "Creating cluster..."
    
    cat <<EOF | kind create cluster --name "$CLUSTER_NAME" --image "$KIND_NODE_IMAGE" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: $CONTAINER_PORT
    hostPort: $HOST_PORT
    protocol: TCP
EOF

    kubectl config use-context "kind-${CLUSTER_NAME}"
    
    echo "Loading infrastructure images..."
    for image in "${images[@]}"; do
        [[ "$image" == "$KIND_NODE_IMAGE" ]] && continue
        echo "  $image"
        kind load docker-image "$image" --name "$CLUSTER_NAME" || true
    done
    
    echo "Cluster ready"
fi

echo
echo "Next:"
echo "  ./scripts/build.sh"
echo "  ./scripts/kind-load-images.sh"
echo "  ./scripts/deploy.sh"
echo
kubectl cluster-info --context "kind-${CLUSTER_NAME}" | head -1
