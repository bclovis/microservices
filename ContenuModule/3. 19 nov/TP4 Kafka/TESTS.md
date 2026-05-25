# Scénarios de Test - TP Kafka

## 1. Commande Normale (Succès complet)

```bash
# Créer une commande
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod-1", "quantity": 2}'

# Attendre 2 sec puis voir les logs
sleep 2
docker logs notifications-service --tail 15
```

**Résultat attendu** :
- NEW ORDER CREATED
- INVENTORY RESERVED
- PAYMENT SUCCEEDED (si le paiement passe)

---

## 2. Stock Insuffisant

```bash
# Commander plus que le stock disponible
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod-1", "quantity": 10000}'

sleep 2
docker logs notifications-service --tail 10
```

**Résultat attendu** :
- NEW ORDER CREATED
- INVENTORY FAILED: insufficient stock
- Pas de paiement tenté

---

## 3. Échec Paiement + Compensation

```bash
# Faire plusieurs commandes pour avoir un échec
for i in {1..5}; do
  curl -s -X POST http://localhost:8001/orders \
    -H "Content-Type: application/json" \
    -d '{"product_id": "prod-2", "quantity": 1}'
  echo ""
done

sleep 3
docker logs notifications-service --tail 30
docker logs inventory-service --tail 20
```

**Résultat attendu** :
- Certaines commandes : PAYMENT FAILED
- Dans inventory : "Stock released for order X"

---

## 4. Vérifier l'État du Stock

```bash
# Entrer dans la BDD inventory
docker exec -it db-inventory psql -U user -d inventory_db -c "SELECT * FROM products;"
```

**Résultat attendu** :
```
 id | product_id | quantity 
----+------------+----------
  1 | prod-1     |       XX
  2 | prod-2     |       XX
  3 | prod-3     |       XX
```

---

## 5. Vérifier les Commandes Créées

```bash
# Entrer dans la BDD orders
docker exec -it db-orders psql -U user -d orders_db -c "SELECT * FROM orders ORDER BY id DESC LIMIT 5;"
```

---

## 6. Voir Tous les Topics Kafka

```bash
docker exec broker /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list
```

**Résultat attendu** :
```
order.created
inventory.updated
payment.succeeded
payment.failed
```

---

## 7. Lire les Messages d'un Topic

```bash
# Voir tous les messages order.created
docker exec broker /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic order.created \
  --from-beginning \
  --max-messages 5
```

---

## 8. Test de Charge Simple

```bash
# Créer 10 commandes rapidement
for i in {1..10}; do
  curl -s -X POST http://localhost:8001/orders \
    -H "Content-Type: application/json" \
    -d "{\"product_id\": \"prod-$((RANDOM % 3 + 1))\", \"quantity\": $((RANDOM % 5 + 1))}" &
done

wait
sleep 5
docker logs notifications-service --tail 50
```

---

## 9. Vérifier la Saga Complète

```bash
# Suivre les logs en temps réel
docker logs -f notifications-service
```

Dans un autre terminal :
```bash
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod-1", "quantity": 1}'
```

Observer le flow complet dans les logs.

---

## 10. Reset Complet

```bash
# Tout redémarrer avec clean slate
docker compose down -v
docker compose up --build -d
sleep 15

# Tester
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod-1", "quantity": 5}'
```
