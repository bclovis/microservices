#!/bin/bash

echo "Suppression de l'ancien load-generator s'il existe..."
kubectl delete pod load-generator 2>/dev/null || true

echo "Lancement du test de charge..."
kubectl run -i --tty load-generator \
 --rm --image=curlimages/curl:latest \
 --restart=Never -- /bin/sh -c '
while sleep 0.01; do
 curl -s -X POST "http://order-service:8000/orders?user_id=1&product_id=1" \
 -w "\nHTTP Status: %{http_code}\n"
done
'
