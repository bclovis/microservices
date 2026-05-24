# S3 — TP4 : Code complet Kafka + Saga Pattern

> TP du 19 novembre  
> Code source : `/TP4 Kafka/`

---

## 1. Architecture globale du TP4

### Services
```
┌─────────────────────────────────────────────────────────┐
│  CLIENT                                                  │
│  POST /orders/ → orders-service:8001                    │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │        KAFKA BROKER :29092           │
        │  Topics:                             │
        │  - order.created                     │
        │  - inventory.updated                 │
        │  - inventory.admin.updated           │
        │  - payment.succeeded                 │
        │  - payment.failed                    │
        └──┬────────────┬────────────┬────────┘
           │            │            │
    ┌──────▼──────┐ ┌───▼───────┐ ┌─▼──────────────────┐
    │  inventory  │ │  payment  │ │  notifications       │
    │  service    │ │  service  │ │  service             │
    │  :8002      │ │  (script) │ │  (script)            │
    └─────────────┘ └───────────┘ └────────────────────┘
```

### Flux Saga
```
orders → order.created
              ↓
inventory → inventory.updated {reserved / insufficient_stock}
              ↓
payment  → payment.succeeded / payment.failed
              ↓ (si failed)
inventory → libère le stock (compensation)
```

---

## 2. docker-compose.yml

```yaml
version: '3.8'

services:
  # ===== KAFKA =====
  zookeeper:
    image: confluentinc/cp-zookeeper:7.0.1
    hostname: zookeeper
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  broker:
    image: confluentinc/cp-kafka:7.0.1
    hostname: broker
    container_name: broker
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"         # Port externe (localhost)
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://broker:29092,PLAINTEXT_HOST://localhost:9092
      # broker:29092   = réseau interne Docker (entre containers)
      # localhost:9092 = réseau externe (machine hôte)
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  # ===== MICROSERVICES =====
  orders-service:
    build: ./orders-service
    ports:
      - "8001:8000"
    environment:
      KAFKA_BOOTSTRAP_SERVERS: broker:29092   # ← adresse interne Docker
      DATABASE_URL: sqlite:///./orders.db
    depends_on:
      - broker

  inventory-service:
    build: ./inventory-service
    ports:
      - "8002:8000"
    environment:
      KAFKA_BOOTSTRAP_SERVERS: broker:29092
    depends_on:
      - broker

  payment-service:
    build: ./payment-service
    environment:
      KAFKA_BOOTSTRAP_SERVERS: broker:29092
    depends_on:
      - broker

  notifications-service:
    build: ./notifications-service
    environment:
      KAFKA_BOOTSTRAP_SERVERS: broker:29092
    depends_on:
      - broker
```

---

## 3. orders-service — Pattern Outbox complet

### orders-service/main.py
```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import threading
import time
import json
import os

from database import SessionLocal, engine, Base
from kafka_producer import publish_event

app = FastAPI(title="Orders Service")
Base.metadata.create_all(bind=engine)

class OrderCreate(BaseModel):
    product_id: str
    quantity: int

@app.post("/orders/", status_code=201)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """
    Créer une commande avec Pattern Outbox.
    La commande ET l'événement sont créés dans la même transaction.
    """
    # Créer la commande
    new_order = Order(
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        status="pending"
    )
    
    # Créer l'entrée dans la table Outbox
    outbox_event = OutboxEvent(
        event_type="order.created",
        payload=json.dumps({
            "order_id": new_order.id,
            "product_id": order_data.product_id,
            "quantity": order_data.quantity
        })
    )
    
    # ← ATOMIQUE : commit les deux ensemble ou rien
    db.add(new_order)
    db.add(outbox_event)
    db.commit()
    db.refresh(new_order)
    
    return {"order_id": new_order.id, "status": "pending"}

# ===== THREAD OUTBOX =====
def process_outbox():
    """
    Thread qui tourne en continu et publie les événements non traités.
    S'exécute toutes les 5 secondes.
    """
    while True:
        db = SessionLocal()
        try:
            # Récupérer les événements non encore publiés
            events = db.query(OutboxEvent).filter(
                OutboxEvent.processed == 0
            ).all()
            
            for event in events:
                # Publier sur Kafka
                publish_event(
                    topic=event.event_type,          # ex: "order.created"
                    event=json.loads(event.payload)  # dict Python
                )
                # Marquer comme traité
                event.processed = 1
                db.commit()
                print(f"Published event: {event.event_type}")
        except Exception as e:
            print(f"Error in outbox processor: {e}")
        finally:
            db.close()
        time.sleep(5)  # Attendre 5 secondes avant la prochaine itération

# Démarrer le thread au lancement de l'app
# daemon=True : le thread s'arrête quand l'app principale s'arrête
threading.Thread(target=process_outbox, daemon=True).start()
```

### orders-service/kafka_producer.py
```python
from kafka import KafkaProducer
import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
    # Sérialise automatiquement les dict Python en bytes JSON
)

def publish_event(topic: str, event: dict):
    producer.send(topic, event)  # Envoi asynchrone
    producer.flush()              # Attendre la confirmation d'envoi
```

### orders-service/database.py
```python
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orders.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    product_id = Column(String)
    quantity = Column(Integer)
    status = Column(String, default="pending")

class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String)   # "order.created", etc.
    payload = Column(Text)         # JSON stringifié
    processed = Column(Integer, default=0)  # 0=non traité, 1=traité

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 4. inventory-service — Consumer + Saga

### inventory-service/consumer.py (Saga + Compensation)
```python
from kafka import KafkaConsumer, KafkaProducer
import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

# ===== CONSUMER — écoute order.created ET payment.failed =====
consumer = KafkaConsumer(
    'order.created',      # ← Saga step 1 : réserver le stock
    'payment.failed',     # ← Saga compensation : libérer le stock
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='inventory-service'
)

# ===== PRODUCER — publie inventory.updated =====
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Stock simulé (en production = base de données)
inventory = {
    "product_1": 100,
    "product_2": 50,
}

def handle_order_created(event: dict):
    """
    Réserver le stock pour une commande.
    Saga step 1 : après order.created
    """
    order_id = event['order_id']
    product_id = event['product_id']
    quantity = event['quantity']
    
    current_stock = inventory.get(product_id, 0)
    
    if current_stock >= quantity:
        # Réservation réussie
        inventory[product_id] -= quantity
        
        inventory_event = {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "status": "reserved"          # ← payment-service va consommer ça
        }
        producer.send('inventory.updated', inventory_event)
        print(f"Stock reserved for order {order_id}: {quantity} x {product_id}")
    else:
        # Pas assez de stock
        inventory_event = {
            "order_id": order_id,
            "product_id": product_id,
            "status": "insufficient_stock",
            "reason": f"Only {current_stock} available, {quantity} requested"
        }
        producer.send('inventory.updated', inventory_event)
        print(f"Insufficient stock for order {order_id}")
    
    producer.flush()

def handle_payment_failed(event: dict):
    """
    Transaction compensatoire : libérer le stock si paiement échoue.
    Saga compensation step
    """
    order_id = event['order_id']
    product_id = event.get('product_id')
    quantity = event.get('quantity')
    
    if product_id and quantity:
        inventory[product_id] = inventory.get(product_id, 0) + quantity
        print(f"Stock released for order {order_id}: {quantity} x {product_id}")

# ===== BOUCLE PRINCIPALE =====
print("Inventory service started, waiting for messages...")
for message in consumer:
    topic = message.topic
    event = message.value
    
    if topic == 'order.created':
        handle_order_created(event)
    elif topic == 'payment.failed':
        handle_payment_failed(event)
```

---

## 5. payment-service — Consumer + Producer

### payment-service/main.py
```python
from kafka import KafkaConsumer, KafkaProducer
import json
import os
import random

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

consumer = KafkaConsumer(
    'inventory.updated',   # ← Saga step 2 : après réservation stock
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='payment-service'
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def process_inventory_update(event: dict):
    order_id = event['order_id']
    status = event.get('status')
    
    # Ne traiter que si l'inventaire a été réservé avec succès
    if status != 'reserved':
        print(f"Order {order_id} was not reserved, skipping payment")
        return
    
    # Simuler un paiement (70% de succès, 30% d'échec)
    success = random.random() > 0.3
    
    if success:
        payment_event = {
            "order_id": order_id,
            "status": "succeeded",
            "amount": event['quantity'] * 10.0   # 10€ par item
        }
        producer.send('payment.succeeded', payment_event)
        print(f"Payment succeeded for order {order_id}: ${payment_event['amount']}")
    else:
        payment_event = {
            "order_id": order_id,
            "status": "failed",
            "reason": "card declined",
            # On renvoie les infos pour que inventory puisse compenser
            "product_id": event.get('product_id'),
            "quantity": event.get('quantity')
        }
        producer.send('payment.failed', payment_event)
        print(f"Payment failed for order {order_id}")
    
    producer.flush()

print("Payment service started, waiting for inventory updates...")
for message in consumer:
    process_inventory_update(message.value)
```

---

## 6. notifications-service — Observabilité

### notifications-service/main.py
```python
from kafka import KafkaConsumer
import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

# ← Écoute TOUS les topics pour avoir une vue complète du système
consumer = KafkaConsumer(
    'order.created',
    'inventory.updated',
    'inventory.admin.updated',
    'payment.succeeded',
    'payment.failed',
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='notifications-service'
    # ← group_id différent de payment-service et inventory-service
    # → lit les mêmes messages mais indépendamment
)

print("Notifications service started...")

for message in consumer:
    topic = message.topic
    event = message.value
    
    if topic == 'order.created':
        print(f"\n📦 NEW ORDER:")
        print(f"   Order ID : {event.get('order_id')}")
        print(f"   Product  : {event.get('product_id')}")
        print(f"   Quantity : {event.get('quantity')}")
    
    elif topic == 'inventory.updated':
        status = event.get('status')
        if status == 'reserved':
            print(f"\n✅ INVENTORY RESERVED:")
            print(f"   Order ID : {event.get('order_id')}")
        else:
            print(f"\n❌ INVENTORY FAILED:")
            print(f"   Reason: {event.get('reason')}")
    
    elif topic == 'payment.succeeded':
        print(f"\n💳 PAYMENT SUCCEEDED:")
        print(f"   Order ID : {event.get('order_id')}")
        print(f"   Amount   : ${event.get('amount')}")
    
    elif topic == 'payment.failed':
        print(f"\n🚫 PAYMENT FAILED:")
        print(f"   Order ID : {event.get('order_id')}")
        print(f"   Reason   : {event.get('reason')}")
    
    elif topic == 'inventory.admin.updated':
        print(f"\n🔧 ADMIN STOCK UPDATE:")
        print(f"   Product      : {event.get('product_id')}")
        print(f"   Old quantity : {event.get('old_quantity')}")
        print(f"   New quantity : {event.get('new_quantity')}")
```

---

## 7. Commandes pour lancer et tester le TP4

```bash
# Lancer tout avec Docker Compose
cd "TP4 Kafka"
docker-compose up --build

# Créer une commande
curl -X POST "http://localhost:8001/orders/" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "product_1", "quantity": 5}'

# Voir l'inventaire
curl http://localhost:8002/inventory/

# Mettre à jour le stock (admin)
curl -X PUT "http://localhost:8002/inventory/product_1" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 200}'

# Voir les logs de chaque service
docker logs notifications-service -f
docker logs payment-service -f
```

---

## 8. Points clés à retenir pour l'oral

1. **Pattern Outbox** = atomicité garantie entre BDD et Kafka
2. **Thread daemon** = s'arrête avec l'application principale
3. **group_id différents** = chaque service a son propre offset (indépendance)
4. **auto_offset_reset='earliest'** = rejouer depuis le début si nouveau consumer
5. **value_serializer/deserializer** = JSON automatique (plus besoin de json.dumps/loads manuel)
6. **producer.flush()** = attendre confirmation que le message est bien envoyé
7. **Compensation** = libérer le stock quand payment échoue (saga chorégraphie)
