#!/bin/bash

set -e

echo "Deploying Pokemon Drafter to Kubernetes..."

# Create namespace if it doesn't exist
kubectl create namespace pokemon-drafter --dry-run=client -o yaml | kubectl apply -f -

# Apply all Kubernetes configurations
echo "Applying database configuration..."
kubectl apply -f k8s/database.yaml -n pokemon-drafter

echo "Applying cache service configuration..."
kubectl apply -f k8s/cache-service.yaml -n pokemon-drafter

echo "Applying Kafka configuration..."
kubectl apply -f k8s/kafka.yaml -n pokemon-drafter

echo "Applying backend services..."
kubectl apply -f k8s/backends.yaml -n pokemon-drafter

echo "Applying frontend services..."
kubectl apply -f k8s/frontends.yaml -n pokemon-drafter

echo "Applying recommendation and encryption services..."
kubectl apply -f k8s/services.yaml -n pokemon-drafter

echo "Applying API gateway..."
kubectl apply -f k8s/api-gateway.yaml -n pokemon-drafter

echo ""
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n pokemon-drafter

echo ""
echo "Deployment complete!"
echo ""
echo "Services status:"
kubectl get pods -n pokemon-drafter
echo ""
kubectl get services -n pokemon-drafter
echo ""
echo "Access the application at:"
echo "  Main: http://pokemon-drafter.local"
echo "  Red Team: http://red.pokemon-drafter.local"
echo "  Blue Team: http://blue.pokemon-drafter.local"
echo ""
echo "Don't forget to add these entries to /etc/hosts:"
echo "  127.0.0.1 pokemon-drafter.local"
echo "  127.0.0.1 red.pokemon-drafter.local"
echo "  127.0.0.1 blue.pokemon-drafter.local"
