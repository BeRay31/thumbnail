#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

echo "Deploying to k8s..."

# check tools
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "Error: helm not found"
    exit 1
fi

# check cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: cannot connect to cluster"
    exit 1
fi

echo "Connected to:"
kubectl cluster-info | head -1

# deploy
echo "Installing chart..."
helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
    --namespace "$NAMESPACE" \
    --wait \
    --timeout 10m

echo "Deployed"

# show status
echo
kubectl get pods -l app.kubernetes.io/name=thumbnail-service
echo
kubectl get services -l app.kubernetes.io/name=thumbnail-service

echo
echo "Access:"
echo "  http://localhost:$HOST_PORT"
echo "  curl http://localhost:$HOST_PORT/healthz"

echo
echo "Commands:"
echo "  kubectl logs -l app.kubernetes.io/component=server"
echo "  helm uninstall $RELEASE_NAME"
echo "  kubectl port-forward service/thumbnail-service-server 8000:8000"
