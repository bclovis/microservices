#!/bin/bash

echo "Configuration de l'environnement Docker de Minikube..."
eval $(minikube docker-env)

echo "Construction des images Docker..."
cd user-service
docker build -t user-service:latest .
cd ../product-service
docker build -t product-service:latest .
cd ../order-service
docker build -t order-service:latest .
cd ..

echo "Deploiement sur Kubernetes..."
kubectl apply -f k8s/user-deployment.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/product-deployment.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/order-deployment.yaml
kubectl apply -f k8s/order-service.yaml

echo "Attente du demarrage des pods..."
sleep 10

echo "Verification des deploiements..."
kubectl get deployments
kubectl get services
kubectl get pods

echo "Deploiement termine"
echo "order-service accessible sur: http://$(minikube ip):30000"
