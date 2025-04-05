#!/bin/bash

set -e

APP_NAME="vector-store"
DOCKERFILE_PATH="docker_store/Dockerfile"
HELM_CHART_PATH="./vector-store"
PORT_LOCAL=8080
PORT_CONTAINER=8000

echo "🚀 [1/6] Starting Minikube (if it's not running)..."
minikube status >/dev/null 2>&1 || minikube start

echo "🐳 [2/6] Using Minikube's Docker..."
eval $(minikube docker-env)

echo "📦 [3/6] Building Docker image 'vector-store'..."
docker build -t vector-store -f Dockerfile .

echo "📦 [4/6] Helm upgrade/install chart..."
helm upgrade --install $APP_NAME $HELM_CHART_PATH

echo "⌛ Waiting for the pod to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=$APP_NAME --timeout=120s

echo "🌐 [5/6] Getting pod name..."
POD_NAME=$(kubectl get pods -l "app.kubernetes.io/name=$APP_NAME" -o jsonpath="{.items[0].metadata.name}")

echo "🌍 [6/6] Port-forwarding to http://localhost:$PORT_LOCAL ..."
echo "🔁 Use Ctrl+C to stop local access."

kubectl port-forward $POD_NAME $PORT_LOCAL:$PORT_CONTAINER
