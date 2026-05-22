#!/bin/bash

set -e

echo "Cleaning up Pokemon Drafter deployment..."

# Delete all resources in namespace
kubectl delete namespace pokemon-drafter --ignore-not-found=true

echo "Deployment cleaned up successfully!"
