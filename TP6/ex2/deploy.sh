#!/bin/bash

# 1. Configure Docker
eval $(minikube docker-env)

# 2. BUILD les images
cd user-service
docker build -t user-service:latest .
cd ../product-service
docker build -t product-service:latest .
cd ../order-service
docker build -t order-service:latest .
cd ..

# 3. DEPLOIE tout
kubectl apply -f k8s/user-deployment.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/product-deployment.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/order-deployment.yaml
kubectl apply -f k8s/order-service.yaml

# 4. APPLIQUE les HPA
kubectl apply -f k8s/user-hpa.yaml
kubectl apply -f k8s/product-hpa.yaml
kubectl apply -f k8s/order-hpa.yaml

# 5. AFFICHE le résultat
kubectl get pods
kubectl get hpa
