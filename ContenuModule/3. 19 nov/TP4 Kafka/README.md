# TP Kafka - Microservices

## Architecture

- **orders-service** : Crée les commandes, les stocke en BDD, publie sur Kafka (pattern Outbox)
- **inventory-service** : Consomme order.created, vérifie le stock, publie inventory.updated, gère la libération en cas d'échec payment
- **payment-service** : Consomme inventory.updated, simule un paiement, publie payment.succeeded ou payment.failed
- **notifications-service** : Affiche les événements dans la console

## Lancer le projet

```bash
docker compose up --build
```

## Tester

Créer une commande :
```bash
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod-1", "quantity": 5}'
```

Vérifier une commande :
```bash
curl http://localhost:8001/orders/1
```

## Stock initial

- prod-1 : 100 unités
- prod-2 : 50 unités
- prod-3 : 75 unités

## Saga Chorégraphie

1. **Order Created** → inventory-service réserve le stock
2. **Inventory Reserved** → payment-service traite le paiement (70% succès)
3. **Payment Succeeded** → commande finalisée ✓
4. **Payment Failed** → inventory-service libère le stock

## Logs

Voir les notifications :
```bash
docker logs -f notifications-service
```

Voir l'inventaire :
```bash
docker logs -f inventory-service
```

Voir les paiements :
```bash
docker logs -f payment-service
```
