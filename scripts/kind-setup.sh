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

echo "Pulling Kind node image..."
if docker image inspect "$KIND_NODE_IMAGE" >/dev/null 2>&1; then
    echo "  $KIND_NODE_IMAGE (cached)"
else
    echo "  $KIND_NODE_IMAGE"
    docker pull "$KIND_NODE_IMAGE" || exit 1
fi

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
  - containerPort: 30001
    hostPort: 30001
    protocol: TCP
- role: worker
- role: worker
EOF

    kubectl config use-context "kind-${CLUSTER_NAME}"
    
    echo "Cluster ready"
fi

echo
echo "Cluster ready! Next steps:"
echo "  ./scripts/build.sh              # Build application images"
echo "  ./scripts/kind-load-images.sh   # Load all images to cluster"
echo "  ./scripts/deploy.sh             # Deploy to cluster"
echo
kubectl cluster-info --context "kind-${CLUSTER_NAME}" | head -1
