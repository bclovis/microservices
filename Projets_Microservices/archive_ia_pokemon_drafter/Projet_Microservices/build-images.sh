#!/bin/bash

set -e

echo "Building Pokemon Drafter Docker images..."

# Build backend images
echo "Building backend-red..."
docker build -t pokemon-drafter/backend-red:latest ./backend-red

echo "Building backend-blue..."
docker build -t pokemon-drafter/backend-blue:latest ./backend-blue

# Build frontend images
echo "Building frontend-red..."
docker build -t pokemon-drafter/frontend-red:latest ./frontend-red

echo "Building frontend-blue..."
docker build -t pokemon-drafter/frontend-blue:latest ./frontend-blue

# Build service images
echo "Building recommendation service..."
docker build -t pokemon-drafter/recommendation:latest ./recommendation

echo "Building encryption service..."
docker build -t pokemon-drafter/encryption:latest ./encryption

echo "Building API gateway..."
docker build -t pokemon-drafter/api-gateway:latest ./api-gateway

echo "All images built successfully!"
echo ""
echo "Available images:"
docker images | grep pokemon-drafter
