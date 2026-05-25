# FICHE TP4 — Kafka : Architecture Event-Driven + Outbox + Saga

> **Séance :** 19 novembre | **Niveau :** Avancé  
> **Objectif TP :** Implémenter une architecture microservices event-driven avec Apache Kafka, 4 services (orders, inventory, notifications, payment), le pattern Outbox et la Saga chorégraphie

---

## 1. CONTEXTE DU TP — Ce qui était demandé

**Contexte métier :** Application de commandes en boutique en ligne.  
Un utilisateur commande un produit → l'inventaire est débité → le paiement est traité → des notifications sont envoyées.

### Phase 1 — 3 services de base
| Service | Rôle |
|---------|------|
| `orders-service` | Crée les commandes, publie `order.created` (Kafka) |
| `inventory-service` | Consomme `order.created`, vérifie/met à jour le stock, publie `inventory.updated` |
| `notifications-service` | Consomme les événements et affiche des logs console |

### Phase 2 — 4 services avec Saga
| Ajout | Rôle |
|-------|------|
| `payment-service` | Consomme `order.created`, vérifie si possible, publie `payment.succeeded` ou `payment.failed` |
| Inventaire (mise à jour) | Si `payment.failed` → libère la réservation |
| **Saga chorégraphie** | Séquence : `order.created` → `inventory.reserved` → `payment.succeeded/failed` → si échec : `inventory.unreserved` |

---

## 2. ARCHITECTURE EVENT-DRIVEN

```
[User] ──POST /orders──→ [orders-service]
                               │
                         publie order.created
                               │
              ┌────────────────┴────────────────┐
              ↓                                  ↓
    [inventory-service]              [payment-service]
    Consomme order.created           Consomme order.created
    Réserve le stock                 Vérifie si paiement possible
    Publie inventory.reserved        Publie payment.succeeded
              │                              │ (ou payment.failed)
              └──────────────┬───────────────┘
                             ↓
                  [notifications-service]
                  Consomme tout → logs console
```

**Flux Saga chorégraphie :**
```
order.created
    → inventory-service réserve → inventory.reserved
        → payment-service paie → payment.succeeded ✅
    → inventory-service réserve → inventory.reserved  
        → payment-service échoue → payment.failed
            → inventory-service libère ← payment.failed
```

---

## 3. DOCKER COMPOSE — Infrastructure

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ===== KAFKA BROKER (KRaft mode, sans Zookeeper) =====
  broker:
    image: apache/kafka:latest
    container_name: broker
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller        # Kafka en mode KRaft (auto-suffisant)
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://broker:9092  # Nom DNS interne Docker
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@broker:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0

  # ===== BASE DE DONNÉES COMMANDES =====
  db-orders:
    image: postgres:15
    container_name: db-orders
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: orders_db
    ports:
      - "5432:5432"
    volumes:
      - orders-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d orders_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ===== BASE DE DONNÉES INVENTAIRE =====
  db-inventory:
    image: postgres:15
    container_name: db-inventory
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: inventory_db
    ports:
      - "5433:5432"

  # ===== MICROSERVICES =====
  orders-service:
    build: ./orders-service
    ports:
      - "8001:8000"
    depends_on:
      db-orders:
        condition: service_healthy  # Attendre que la BDD soit prête
    environment:
      DATABASE_URL: postgresql://user:password@db-orders/orders_db
      KAFKA_BOOTSTRAP_SERVERS: broker:9092

  inventory-service:
    build: ./inventory-service
    ports:
      - "8002:8000"
    depends_on:
      - db-inventory
      - broker

  notifications-service:
    build: ./notifications-service
    depends_on:
      - broker

  payment-service:
    build: ./payment-service
    depends_on:
      - broker

volumes:
  orders-data:
  inventory-data:
```

**Concepts Docker Compose clés :**

| Concept | Explication |
|---------|-------------|
| `depends_on: condition: service_healthy` | Attendre le healthcheck avant de démarrer |
| `KAFKA_ADVERTISED_LISTENERS: broker:9092` | Nom DNS interne Docker (pas localhost !) |
| `volumes: orders-data:` | Volume persistant → données survivent aux redémarrages |
| `build: ./orders-service` | Construit l'image depuis le Dockerfile local |

---

## 4. orders-service — Le Pattern Outbox

### Le problème sans Outbox
```
1. Sauvegarder la commande en BDD  ✅
2. Publier l'événement Kafka        ❌ (Kafka down momentanément)
→ La commande est en BDD mais l'événement n'est jamais envoyé !
```

### La solution Outbox
```
1. Sauvegarder la commande en BDD      ✅
2. Sauvegarder l'événement en BDD      ✅  (dans la table outbox)
   → Dans la MÊME TRANSACTION → atomique !
3. Un thread en arrière-plan lit la table outbox et publie sur Kafka
4. Marque l'événement comme traité (processed=1)
```

### Code complet orders-service

```python
# orders-service/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import SessionLocal, Order, OutboxEvent
from kafka_producer import publish_event
import json, threading, time

app = FastAPI()

class OrderCreate(BaseModel):
    product_id: str
    quantity: int

@app.post("/orders")
def create_order(order: OrderCreate):
    db = SessionLocal()
    
    # 1. Créer la commande
    new_order = Order(
        product_id=order.product_id,
        quantity=order.quantity,
        status="pending"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    order_id = new_order.id
    
    # 2. Créer l'événement dans la table Outbox (même transaction)
    event_payload = {
        "order_id": order_id,
        "product_id": order.product_id,
        "quantity": order.quantity
    }
    outbox_event = OutboxEvent(
        event_type="order.created",
        payload=json.dumps(event_payload)
    )
    db.add(outbox_event)
    db.commit()  # Commit atomique : commande + outbox event
    
    db.close()
    return {"order_id": order_id, "status": "pending"}

# 3. Thread Outbox Processor : lit les événements non traités et les publie sur Kafka
def process_outbox():
    while True:
        db = SessionLocal()
        events = db.query(OutboxEvent).filter(OutboxEvent.processed == 0).all()
        
        for event in events:
            payload = json.loads(event.payload)
            publish_event(event.event_type, payload)  # Envoie sur Kafka
            event.processed = 1
            db.commit()
        
        db.close()
        time.sleep(5)  # Vérifie toutes les 5 secondes

# Lancer le thread au démarrage
threading.Thread(target=process_outbox, daemon=True).start()
```

### orders-service/database.py
```python
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db-orders/orders_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String)
    quantity = Column(Integer)
    status = Column(String, default="pending")  # pending, confirmed, cancelled

class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)        # "order.created"
    payload = Column(Text)             # JSON stringifié
    processed = Column(Integer, default=0)  # 0 = non traité, 1 = traité

Base.metadata.create_all(bind=engine)
```

### orders-service/kafka_producer.py
```python
from kafka import KafkaProducer
import json, os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def publish_event(topic: str, event: dict):
    producer.send(topic, event)
    producer.flush()  # Garantit l'envoi immédiat
```

---

## 5. inventory-service — Consumer Kafka + Saga

```python
# inventory-service/consumer.py
from kafka import KafkaConsumer
import json
from database import SessionLocal, Product
from kafka_utils import publish_event

reservations = {}  # Mémorise les réservations pour libérer si paiement échoue

def start_consumer():
    consumer = KafkaConsumer(
        'order.created',          # Topics écoutés
        'payment.failed',         # Pour la Saga : libérer si paiement échoue
        bootstrap_servers='broker:9092',
        group_id='inventory-service',           # Consumer group
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest'            # Relire depuis le début si redémarrage
    )
    
    for message in consumer:
        event_type = message.topic  # Quel topic ?
        data = message.value        # Payload JSON
        
        if event_type == 'order.created':
            handle_order_created(data)
        elif event_type == 'payment.failed':
            handle_payment_failed(data)

def handle_order_created(data):
    """Consomme order.created → réserve le stock → publie inventory.updated"""
    order_id = data['order_id']
    product_id = data['product_id']
    quantity = data['quantity']
    
    db = SessionLocal()
    product = db.query(Product).filter(Product.product_id == product_id).first()
    
    if product and product.quantity >= quantity:
        # Débit du stock
        product.quantity -= quantity
        db.commit()
        # Mémoriser la réservation (pour Saga)
        reservations[order_id] = {'product_id': product_id, 'quantity': quantity}
        
        # Publier l'événement de succès
        publish_event('inventory.updated', {
            'order_id': order_id,
            'product_id': product_id,
            'quantity': quantity,
            'status': 'reserved'
        })
    else:
        available = product.quantity if product else 0
        # Stock insuffisant → publier l'échec
        publish_event('inventory.updated', {
            'order_id': order_id,
            'product_id': product_id,
            'status': 'insufficient_stock',
            'available': available
        })
    db.close()

def handle_payment_failed(data):
    """Saga : si paiement échoue → libérer la réservation"""
    order_id = data.get('order_id')
    if order_id in reservations:
        res = reservations.pop(order_id)
        db = SessionLocal()
        product = db.query(Product).filter(Product.product_id == res['product_id']).first()
        if product:
            product.quantity += res['quantity']  # Libérer le stock
            db.commit()
        db.close()
        print(f"Stock libéré pour commande {order_id}")
```

---

## 6. notifications-service — Consumer Stateless

```python
# notifications-service/main.py
from kafka import KafkaConsumer
import json

def start_notifications_consumer():
    """Service stateless : écoute tout et affiche des logs"""
    consumer = KafkaConsumer(
        'order.created',
        'inventory.updated',
        'payment.succeeded',
        'payment.failed',
        bootstrap_servers='broker:9092',
        group_id='notifications-service',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest'
    )
    
    for message in consumer:
        event = message.value
        topic = message.topic
        
        if topic == 'order.created':
            print(f"📦 Nouvelle commande #{event['order_id']} : {event['quantity']}x {event['product_id']}")
        elif topic == 'inventory.updated':
            status = event.get('status')
            if status == 'reserved':
                print(f"✅ Stock réservé pour commande #{event['order_id']}")
            elif status == 'insufficient_stock':
                print(f"❌ Stock insuffisant pour commande #{event['order_id']}")
        elif topic == 'payment.succeeded':
            print(f"💳 Paiement réussi pour commande #{event['order_id']}")
        elif topic == 'payment.failed':
            print(f"💔 Paiement échoué pour commande #{event['order_id']}")

if __name__ == "__main__":
    start_notifications_consumer()
```

---

## 7. CONCEPTS KAFKA — Résumé essentiel

### Topics et partitions
```
Topic "order.created" :
  Partition 0 : [msg1, msg2, msg3, ...]
  Partition 1 : [msg4, msg5, msg6, ...]

Chaque message a un offset (position unique dans la partition)
```

### Consumer Groups
```
inventory-service (group_id='inventory-service')
    → consomme order.created
    → Kafka retient l'offset → si redémarrage, reprend là où il s'est arrêté

notifications-service (group_id='notifications-service')  
    → consomme aussi order.created INDÉPENDAMMENT
    → Chaque group reçoit tous les messages (pas de partage)
```

### bootstrap_servers
```python
# ⚠️ En Docker : utiliser le nom du service Docker, PAS localhost
bootstrap_servers='broker:9092'  ✅
bootstrap_servers='localhost:9092'  ❌ (ne fonctionne pas entre containers)
```

---

## 8. DOCKERFILE type

```dockerfile
# Dockerfile (identique pour chaque service)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

---

## 9. COMMANDES DE TEST

```bash
# Démarrer tout
docker compose up --build

# Créer une commande
curl -X POST "http://localhost:8001/orders" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod-001", "quantity": 2}'

# Voir l'état d'une commande
curl "http://localhost:8001/orders/1"

# Voir les logs (Kafka + services)
docker compose logs -f notifications-service

# Vérifier les topics Kafka
docker exec broker kafka-topics.sh --list --bootstrap-server localhost:9092
```

---

## 10. QUESTIONS D'ORAL POSSIBLES SUR CE TP

**Q : Qu'est-ce que le pattern Outbox et pourquoi est-il nécessaire ?**
> Sans Outbox : si Kafka est down au moment de publier l'événement, la commande est en BDD mais l'événement est perdu → incohérence entre services. Avec Outbox : la commande ET l'événement sont sauvegardés dans la **même transaction BDD** (atomique). Un thread séparé publie ensuite sur Kafka en retry. → Garantit qu'un événement sera **toujours** publié si la commande est créée.

**Q : C'est quoi un Consumer Group ?**
> Groupe de consumers qui se partagent les partitions d'un topic. Si 3 consumers dans le même groupe et 3 partitions → chaque consumer lit une partition. Si 2 groupes différents (inventory + notifications) → chaque groupe reçoit **tous** les messages indépendamment.

**Q : Qu'est-ce que la Saga chorégraphie ?**
> Pattern de gestion des transactions distribuées sans orchestrateur central. Chaque service **réagit** aux événements Kafka et publie ses propres événements. Si une étape échoue, des "événements de compensation" sont publiés pour annuler les étapes précédentes. Ex : `payment.failed` → inventory-service libère le stock.

**Q : Pourquoi `auto_offset_reset='earliest'` ?**
> Si le consumer redémarre et n'a pas d'offset sauvegardé, `earliest` relit tous les messages depuis le début du topic. `latest` = ignore les messages antérieurs au démarrage. En production, `latest` est souvent préféré pour éviter le retraitement.

**Q : Différence entre `producer.send()` et `producer.flush()` ?**
> `send()` est asynchrone — il place le message dans un buffer interne. `flush()` attend que tous les messages du buffer soient **effectivement envoyés** à Kafka. Sans `flush()`, les messages peuvent être perdus si le process s'arrête.

**Q : Pourquoi chaque service a sa propre BDD ?**
> Principe de l'isolation des données en microservices : chaque service est seul propriétaire de ses données. Pas de BDD partagée → pas de couplage fort. Un service ne lit pas directement la BDD d'un autre service : il publie/consomme des événements.
