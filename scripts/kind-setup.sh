#!/bin/bash
set -e

echo "Setting up Kind cluster for thumbnail service..."

CLUSTER_NAME="thumbnail-service"
KIND_NODE_IMAGE="kindest/node:v1.33.1"

# Check dependencies
if ! command -v kind &> /dev/null; then
    echo "Error: kind is not installed"
    echo "Install from: https://kind.sigs.k8s.io/docs/user/quick-start/"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed"  
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    echo "Install from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

echo "Pulling container images..."

# Infrastructure images needed for the service
images=(
    "$KIND_NODE_IMAGE"
    "postgres:15"
    "redis:7-alpine" 
    "minio/minio:latest"
    "minio/mc:latest"
)

for image in "${images[@]}"; do
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "  $image (cached)"
    else
        echo "  $image"
        docker pull "$image" || {
            echo "Failed to pull $image"
            exit 1
        }
    fi
done

# Check if cluster exists
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster '$CLUSTER_NAME' already exists"
    echo "Delete with: kind delete cluster --name $CLUSTER_NAME"
    kubectl config use-context "kind-${CLUSTER_NAME}"
    echo "Switched to existing cluster"
else
    echo "Creating cluster '$CLUSTER_NAME'..."
    
    cat <<EOF | kind create cluster --name "$CLUSTER_NAME" --image "$KIND_NODE_IMAGE" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
EOF

    kubectl config use-context "kind-${CLUSTER_NAME}"
    
    echo "Loading images into cluster..."
    
    # Skip kind node image since it's already used by the cluster
    for image in "${images[@]}"; do
        if [[ "$image" == "$KIND_NODE_IMAGE" ]]; then
            continue
        fi
        
        echo "  Loading $image..."
        kind load docker-image "$image" --name "$CLUSTER_NAME" || {
            echo "Warning: failed to load $image"
        }
    done
    
    echo "Cluster created successfully"
fi

echo
echo "Next steps:"
echo "  1. Build app images: ./scripts/build.sh"
echo "  2. Load app images: ./scripts/kind-load-images.sh"
echo "  3. Deploy: ./scripts/deploy.sh"
echo
echo "Cluster info:"
kubectl cluster-info --context "kind-${CLUSTER_NAME}"
