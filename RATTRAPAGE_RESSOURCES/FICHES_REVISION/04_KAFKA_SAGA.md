# 📘 FICHE 4 : KAFKA ET EVENT-DRIVEN ARCHITECTURE

> **Source** : Kafka.pdf + TP Kafka.pdf (19/11/2025)

---

## 🎯 QU'EST-CE QUE KAFKA ?

**Apache Kafka** est une plateforme de **streaming d'événements** distribuée.

### Analogie simple
Kafka = **système de messagerie ultra-rapide** entre microservices.

Imagine :
- Un **Topic** = une file de messages (ex: "order.created")
- Un **Producer** = service qui publie des messages
- Un **Consumer** = service qui lit les messages

---

## 📬 COMMUNICATION SYNCHRONE vs ASYNCHRONE

### Synchrone (REST/HTTP)

```python
# OrderService appelle directement InventoryService
response = requests.post("http://inventory-service/reserve", json=data)
if response.status_code == 200:
    print("Stock réservé")
```

**Problème :**
- ❌ OrderService doit **attendre** la réponse
- ❌ Si InventoryService est down → échec total
- ❌ Couplage fort (dépendance directe)

### Asynchrone (Kafka)

```python
# OrderService publie un événement
kafka_producer.send("order.created", {"order_id": 123, "product_id": "prod-1"})
# OrderService continue sans attendre

# InventoryService écoute et traite quand il est prêt
@kafka_consumer("order.created")
def handle_order(event):
    reserve_stock(event["product_id"])
```

**Avantages :**
- ✅ OrderService n'attend pas (performance)
- ✅ Si InventoryService est down → messages en attente (résilience)
- ✅ Découplage total

---

## 🎮 EXEMPLE CONCRET : TON PROJET PokeDrafter

### Flow complet d'un tour de bataille

```
┌──────────────────┐
│ battle_service   │ POST /battles/{id}/turn
│                  │ → calc_advantage(types_red, types_blue)
│                  │ → Sauvegarde BattleTurn en BDD
│                  │ → PUBLIER event Kafka
└──────────────────┘
         │
         │ [battle-events] topic
         │ event: "turn_played"
         ▼
┌──────────────────┐
│ chat_service     │ Consumer Kafka
│                  │ → Reçoit event "turn_played"
│                  │ → Crée notification bot
│                  │ → broadcast_all() sur WebSocket
└──────────────────┘
         │
         ▼
    TOUS les joueurs connectés voient "Tour X — Rouge gagne !"
```

### Code réel : battle_service (PRODUCER)

```python
# battle_service/app/routes/battle.py

@router.post("/{battle_id}/turn", response_model=TurnResult)
async def play_turn(battle_id: UUID, payload: TurnPlay, db: AsyncSession = Depends(get_db)):
    # 1. Calculer F(A) et F(B)
    fa, fb = calc_advantage(payload.types_red, payload.types_blue)
    result = resolve_turn(payload.types_red, payload.types_blue)
    
    # 2. Sauvegarder en BDD
    turn = BattleTurn(
        battle_id=battle_id,
        turn_number=turn_number,
        score_red=str(fa),
        score_blue=str(fb),
        result=result,
    )
    db.add(turn)
    await db.commit()
    
    # 3. PUBLIER EVENT KAFKA (asynchrone)
    await publish_battle_event("turn_played", {
        "battle_id": str(battle_id),
        "turn_number": turn_number,
        "result": result,  # "A" ou "B" ou "draw"
    })
    
    return turn  # Retourne immédiatement SANS attendre chat_service
```

### Code réel : chat_service (CONSUMER)

```python
# chat_service/app/main.py

async def kafka_consumer_loop():
    retry_delay = 2  # Retry exponential backoff
    while True:
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,  # "battle-events"
            settings.KAFKA_TOPIC_CHAT,    # "chat-messages"
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        try:
            await consumer.start()
            retry_delay = 2  # Reset après succès
            
            # Écouter en continu
            async for msg in consumer:
                event = msg.value
                topic = msg.topic  # Routing selon le topic source
                
                if topic == settings.KAFKA_TOPIC_BATTLE:
                    if event.get("type") == "turn_played":
                        # Extraire les infos
                        result = event.get("result", "?")
                        turn = event.get("turn_number", "?")
                        winner = "Rouge" if result == "A" else ("Bleu" if result == "B" else "Egalité")
                        
                        # Créer notification bot
                        notif = {
                            "author": "bot",
                            "content": f"Tour {turn} — {winner} remporte le tour !",
                            "is_bot": True
                        }
                        
                        # Envoyer à TOUS les WebSocket connectés
                        await chat_service.broadcast_all(notif)
                
                elif topic == settings.KAFKA_TOPIC_CHAT:
                    room = event.get("room")
                    if room:
                        await chat_service.broadcast(room, event)
                    else:
                        await chat_service.broadcast_all(event)
                    
        except Exception as e:
            # Retry avec exponential backoff
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)  # 2s → 4s → 8s → ... → 30s max
        finally:
            await consumer.stop()
```

### Pourquoi asynchrone (Kafka) ici ?

**❌ Si on utilisait REST (synchrone) :**
```python
# battle_service devrait attendre que chat_service réponde
response = requests.post("http://chat-service/notify", json=data)
# Si chat_service est down → ERROR 500
# Si 100 joueurs connectés → lenteur
```

**✅ Avec Kafka (asynchrone) :**
```python
# battle_service publie et continue immédiatement
await publish_battle_event("turn_played", data)
# chat_service lit quand il est prêt
# Si chat_service down → messages en attente, pas de perte
```

---

## 🔄 RETRY EXPONENTIAL BACKOFF (TON CHAT_SERVICE)

**CRUCIAL À L'ORAL : Le prof peut te demander d'expliquer cette logique !**

### Problème
Si Kafka est temporairement indisponible, que faire ?

**❌ Mauvaise approche :** Retry immédiatement en boucle
```python
while True:
    try:
        await consumer.start()
    except Exception:
        continue  # ❌ Boucle infinie instantanée = CPU à 100%
```

**✅ Bonne approche :** Retry avec exponential backoff
```python
retry_delay = 2  # Commence à 2 secondes

while True:
    try:
        await consumer.start()
        retry_delay = 2  # ✅ Reset après succès
        async for msg in consumer:
            # Traiter les messages
            pass
    except Exception as e:
        await asyncio.sleep(retry_delay)  # Attendre avant retry
        retry_delay = min(retry_delay * 2, 30)  # ✅ Doubler, max 30s
```

### Fonctionnement détaillé

```
Tentative 1 : Kafka down → Attendre 2s    → retry
Tentative 2 : Kafka down → Attendre 4s    → retry (2 × 2)
Tentative 3 : Kafka down → Attendre 8s    → retry (4 × 2)
Tentative 4 : Kafka down → Attendre 16s   → retry (8 × 2)
Tentative 5 : Kafka down → Attendre 30s   → retry (min(16 × 2, 30))
Tentative 6 : Kafka down → Attendre 30s   → retry (plafond atteint)
...
Tentative N : Kafka UP ✅ → Reset retry_delay = 2s
```

### Pourquoi c'est important ?

1. **Évite la surcharge** : Ne pas bombarder Kafka avec des requêtes si down
2. **Laisse le temps** : Permet à Kafka de redémarrer proprement
3. **Économise les ressources** : CPU et réseau
4. **Résilience** : Le service continue à fonctionner même avec pannes temporaires

### Code exact de TON projet

```python
async def kafka_consumer_loop():
    retry_delay = 2  # 👈 IMPORTANT : Valeur initiale
    while True:      # 👈 IMPORTANT : Boucle infinie (lifespan)
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,   # 👈 "battle-events"
            settings.KAFKA_TOPIC_CHAT,     # 👈 "chat-messages" (2 topics !)
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        try:
            await consumer.start()
            logger.warning("[Kafka] Consumer connecté")
            
            retry_delay = 2  # 👈 IMPORTANT : Reset après succès
            
            async for msg in consumer:
                event = msg.value
                topic = msg.topic  # 👈 IMPORTANT : routing selon la source
                
                if topic == settings.KAFKA_TOPIC_BATTLE:
                    if event.get("type") == "turn_played":
                        result = event.get("result", "?")
                        turn = event.get("turn_number", "?")
                        winner = "Rouge" if result == "A" else ("Bleu" if result == "B" else "Egalité")
                        notif = {"author": "bot", "content": f"Tour {turn} — {winner} remporte le tour !", "is_bot": True}
                        await chat_service.broadcast_all(notif)
                
                elif topic == settings.KAFKA_TOPIC_CHAT:
                    room = event.get("room")
                    if room:
                        await chat_service.broadcast(room, event)
                    else:
                        await chat_service.broadcast_all(event)
                
        except asyncio.CancelledError:
            await consumer.stop()
            return  # 👈 IMPORTANT : Arrêt propre du service
            
        except Exception as e:
            logger.warning("Kafka indisponible, retry dans %ds : %s", retry_delay, e)
            await asyncio.sleep(retry_delay)  # 👈 IMPORTANT : Attendre
            retry_delay = min(retry_delay * 2, 30)  # 👈 IMPORTANT : Doubler, max 30s
            
        finally:
            try:
                await consumer.stop()  # 👈 IMPORTANT : Cleanup
            except Exception:
                pass
```

### Questions probables à l'oral

**Q1 : Pourquoi retry_delay = 2 dans le try après consumer.start() ?**
> "Pour reset le délai après une connexion réussie. Si Kafka était down puis revient, on ne veut pas attendre 30s au prochain problème temporaire."

**Q2 : Pourquoi min(retry_delay * 2, 30) ?**
> "Pour éviter d'attendre trop longtemps. Si Kafka est down 10 minutes, sans le min() on attendrait 2^10 = 1024 secondes (17 minutes), ce qui est trop. 30 secondes est un bon compromis."

**Q3 : Que fait asyncio.CancelledError ?**
> "C'est pour arrêter proprement le consumer quand le service FastAPI s'arrête. Le lifespan cancels la task, on catch l'erreur et on stop le consumer proprement."

**Q4 : Pourquoi while True ?**
> "Parce que le consumer doit tourner en continu pendant toute la vie du service. Il écoute les événements Kafka en permanence. C'est une task d'arrière-plan."

---

## 🏗️ ARCHITECTURE KAFKA

```
                    ┌─────────────┐
                    │   KAFKA     │
                    │   BROKER    │
                    └─────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
  ┌───────────┐    ┌───────────┐    ┌───────────┐
  │  Topic:   │    │  Topic:   │    │  Topic:   │
  │  orders   │    │ inventory │    │  payment  │
  └───────────┘    └───────────┘    └───────────┘
        │                 │                 │
    Producer          Consumer          Consumer
   (OrderSvc)       (InventorySvc)    (PaymentSvc)
```

### Composants

1. **Broker** : Serveur Kafka qui stocke les messages
2. **Topic** : Catégorie de messages (ex: "order.created")
3. **Producer** : Service qui publie des messages
4. **Consumer** : Service qui lit les messages
5. **Consumer Group** : Groupe de consumers (load balancing)

---

## 📝 TOPICS ET MESSAGES

### Créer un Topic

```bash
kafka-topics --create --topic order.created --bootstrap-server localhost:9092
```

### Structure d'un message

```json
{
  "event_type": "order.created",
  "timestamp": "2026-05-20T10:30:00Z",
  "data": {
    "order_id": 123,
    "user_id": 42,
    "product_id": "prod-1",
    "quantity": 5
  }
}
```

---

## 🚀 PRODUCER (Publier des événements)

### Configuration Python

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Publier un événement
producer.send('order.created', {
    "order_id": 123,
    "product_id": "prod-1",
    "quantity": 5
})

producer.flush()  # Assurer que le message est envoyé
```

### Exemple du TP4 - OrderService

```python
@app.post("/orders")
def create_order(product_id: str, quantity: int):
    # 1. Sauvegarder la commande en BDD
    order = Order(product_id=product_id, quantity=quantity, status="pending")
    db.add(order)
    db.commit()
    
    # 2. Publier l'événement
    producer.send('order.created', {
        "order_id": order.id,
        "product_id": product_id,
        "quantity": quantity
    })
    
    return {"order_id": order.id, "status": "pending"}
```

---

## 📨 CONSUMER (Écouter des événements)

### Configuration Python

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'order.created',  # Topic à écouter
    bootstrap_servers=['localhost:9092'],
    group_id='inventory-service',  # Consumer group
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Écouter en boucle infinie
for message in consumer:
    event = message.value
    print(f"Événement reçu: {event}")
    handle_order(event)
```

### Exemple du TP4 - InventoryService

```python
@kafka_consumer("order.created")
def handle_order_created(event):
    order_id = event["order_id"]
    product_id = event["product_id"]
    quantity = event["quantity"]
    
    # Vérifier le stock
    inventory = db.query(Inventory).filter_by(product_id=product_id).first()
    
    if inventory.quantity >= quantity:
        # Réserver le stock
        inventory.reserved += quantity
        db.commit()
        
        # Publier succès
        producer.send('inventory.reserved', {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity
        })
    else:
        # Publier échec
        producer.send('inventory.failed', {
            "order_id": order_id,
            "reason": "Insufficient stock"
        })
```

---

## 🔄 PATTERN SAGA (Chorégraphie)

### Problème
Comment gérer une transaction sur plusieurs services ?

**Exemple :** Créer une commande
1. OrderService crée la commande
2. InventoryService réserve le stock
3. PaymentService traite le paiement
4. Si paiement échoue → libérer le stock (compensation)

### Solution : Saga Chorégraphie

Chaque service écoute des événements et publie de nouveaux événements.

```
┌──────────────┐
│ OrderService │──[order.created]──▶ ┌─────────────────┐
└──────────────┘                      │InventoryService │
                                      └─────────────────┘
                                              │
                            [inventory.reserved] (70% succès)
                                              ▼
                                      ┌─────────────────┐
                                      │ PaymentService  │
                                      └─────────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
          [payment.succeeded] (70%)                   [payment.failed] (30%)
                       │                                             │
                       ▼                                             ▼
            ✅ Commande validée               ❌ Libérer le stock (compensation)
```

### Code complet du TP4

#### 1. OrderService (Création)

```python
@app.post("/orders")
def create_order(product_id: str, quantity: int):
    order = Order(product_id=product_id, quantity=quantity, status="pending")
    db.add(order)
    db.commit()
    
    producer.send('order.created', {
        "order_id": order.id,
        "product_id": product_id,
        "quantity": quantity
    })
    
    return {"order_id": order.id}
```

#### 2. InventoryService (Réservation)

```python
@kafka_consumer("order.created")
def handle_order_created(event):
    order_id = event["order_id"]
    product_id = event["product_id"]
    quantity = event["quantity"]
    
    inventory = db.query(Inventory).filter_by(product_id=product_id).first()
    
    if inventory.quantity >= quantity:
        inventory.reserved += quantity
        db.commit()
        
        producer.send('inventory.reserved', {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity
        })
    else:
        producer.send('inventory.failed', {
            "order_id": order_id,
            "reason": "Insufficient stock"
        })

# Compensation en cas d'échec du paiement
@kafka_consumer("payment.failed")
def handle_payment_failed(event):
    order_id = event["order_id"]
    product_id = event["product_id"]
    quantity = event["quantity"]
    
    # Libérer le stock réservé
    inventory = db.query(Inventory).filter_by(product_id=product_id).first()
    inventory.reserved -= quantity
    db.commit()
```

#### 3. PaymentService (Paiement avec 70% succès)

```python
import random

@kafka_consumer("inventory.reserved")
def handle_inventory_reserved(event):
    order_id = event["order_id"]
    
    # Simuler paiement (70% succès)
    if random.random() < 0.7:
        producer.send('payment.succeeded', {
            "order_id": order_id,
            "amount": 100.0
        })
    else:
        producer.send('payment.failed', {
            "order_id": order_id,
            "product_id": event["product_id"],
            "quantity": event["quantity"],
            "reason": "Insufficient funds"
        })
```

#### 4. NotificationsService (Logs)

```python
@kafka_consumer("order.created")
def log_order_created(event):
    print(f"✅ Order {event['order_id']} created")

@kafka_consumer("inventory.reserved")
def log_inventory_reserved(event):
    print(f"📦 Stock reserved for order {event['order_id']}")

@kafka_consumer("payment.succeeded")
def log_payment_succeeded(event):
    print(f"💰 Payment succeeded for order {event['order_id']}")

@kafka_consumer("payment.failed")
def log_payment_failed(event):
    print(f"❌ Payment failed for order {event['order_id']}")
```

---

## 🎤 QUESTIONS PROBABLES À L'ORAL

### Q1 : Qu'est-ce que Kafka ?
**Réponse type :**
> "Kafka est une plateforme de streaming d'événements qui permet la communication asynchrone entre microservices. Les services publient des événements dans des topics, et d'autres services les consomment. C'est plus résilient que REST car les messages sont persistés : si un service est down, il peut traiter les messages en retard quand il redémarre."

### Q2 : Quelle est la différence entre synchrone (REST) et asynchrone (Kafka) ?
**Réponse type :**
> "En synchrone (REST), le service appelant attend la réponse, ce qui crée du couplage. En asynchrone (Kafka), le service publie un événement et continue sans attendre. C'est plus résilient car si le consommateur est down, les messages sont en attente. Dans notre TP4, on utilise Kafka pour la saga de commande : order → inventory → payment."

### Q3 : C'est quoi une Saga ?
**Réponse type :**
> "Une Saga est un pattern pour gérer des transactions sur plusieurs services. Chaque service exécute sa partie et publie un événement. Si une étape échoue, on publie des événements de compensation pour annuler les étapes précédentes. Dans notre TP4, si le paiement échoue, on libère le stock réservé."

### Q4 : Expliquez le flux du TP4 Kafka
**Réponse type :**
> "1) OrderService crée une commande et publie 'order.created'. 2) InventoryService réserve le stock et publie 'inventory.reserved'. 3) PaymentService traite le paiement (70% succès) et publie 'payment.succeeded' ou 'payment.failed'. 4) Si échec, InventoryService libère le stock (compensation). C'est une saga chorégraphie : chaque service réagit aux événements."

### Q5 : Quels sont les avantages de Kafka ?
**Réponse type :**
> "1) Découplage total entre services, 2) Résilience (messages persistés si service down), 3) Scalabilité (consumer groups), 4) Traçabilité (log de tous les événements), 5) Rejouabilité (on peut relire les événements). C'est parfait pour l'event-driven architecture."

---

## 💡 CONCEPTS CLÉS À RETENIR

1. **Kafka** = système de messagerie pour événements
2. **Topic** = catégorie de messages
3. **Producer** = publie des événements
4. **Consumer** = lit des événements
5. **Saga** = pattern pour transactions distribuées
6. **Chorégraphie** = chaque service réagit aux événements
7. **Compensation** = annuler en cas d'échec (libérer le stock)

---

## ✅ AUTO-TEST

1. Quelle est la différence entre REST et Kafka ?
2. C'est quoi un Topic ? Un Producer ? Un Consumer ?
3. Expliquez le pattern Saga avec un exemple
4. Dans le TP4, que se passe-t-il si le paiement échoue ?
5. Pourquoi Kafka est plus résilient que REST ?

Si tu peux répondre → **✅ Fiche maîtrisée !**
