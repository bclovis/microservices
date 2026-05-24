# S3 — Kafka : Théorie complète + kafka-python

> Cours de Lucas Pauzies — Séance du 19 novembre  
> Source : `Kafka (1) (1).pdf`

---

## 1. Présentation générale

**Apache Kafka** est une plateforme de **streaming d'événements distribuée**.

- Créé en **2011 par LinkedIn** pour gérer des flux de logs massifs
- Maintenu par **Apache Software Foundation** + LinkedIn
- Utilisé massivement : Netflix, Uber, Twitter, Airbnb...

### Caractéristiques clés
- **Haute disponibilité** : fonctionne en cluster (plusieurs brokers)
- **Haute performance** : millions de messages/seconde
- **Durabilité** : les messages sont stockés sur disque
- **Scalabilité horizontale** : ajouter des brokers = ajouter de la capacité
- **Ordre garanti** : FIFO à l'intérieur d'une partition

---

## 2. Concepts fondamentaux

### 2.1 Broker

Un **broker** = une instance Kafka (un serveur Kafka).

```
┌───────────────────────────────────────────────────────┐
│                     CLUSTER KAFKA                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Broker 1    │  │  Broker 2    │  │  Broker 3   │ │
│  │  (Leader)    │  │  (Replica)   │  │  (Replica)  │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
└───────────────────────────────────────────────────────┘
```

- Plusieurs brokers = **cluster** Kafka
- Plus de brokers = plus de résilience et de capacité
- En TP : un seul broker (docker-compose)

### 2.2 Topic

Un **topic** = un "canal" ou "sujet" de messages. C'est le regroupement logique de messages du même type.

```
Topic "order.created"    → tous les événements de création de commande
Topic "payment.succeeded" → tous les événements de paiement réussi
Topic "battle-events"    → tous les événements de combat Pokémon
```

**Règles :**
- 1 topic = 1 type de message (un contrat de données)
- Un broker peut avoir une **infinité** de topics
- Les topics persistent sur disque (configurable)

### 2.3 Partition

Une **partition** = une séquence immuable et ordonnée de messages dans un topic.

```
Topic "order.created" avec 3 partitions :

Partition 0 : [msg_0] → [msg_3] → [msg_6] → [msg_9]
Partition 1 : [msg_1] → [msg_4] → [msg_7] → [msg_10]
Partition 2 : [msg_2] → [msg_5] → [msg_8]

                                              ↑ Offset
```

**Propriétés des partitions :**
- **Immuable** : on ne peut que **ajouter** des messages, jamais modifier/supprimer
- **Ordonnée** : FIFO (First In, First Out) dans chaque partition
- **Unité de parallélisation** : chaque partition peut être consommée par un consumer différent
- **Réplicable** : une partition peut être répliquée sur plusieurs brokers pour la résilience

**Offset** = position d'un message dans une partition. Chaque consumer garde trace de son offset (jusqu'où il a lu).

### 2.4 Producer

Un **producer** = tout système qui **publie** des messages dans un topic.

```python
# Du cours (slides kafka-python) :
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='localhost:1234')
for _ in range(100):
    producer.send('foobar', b'some_message_bytes')
```

**Règles du producer :**
- Il **ne peut PAS supprimer** des messages
- Il écrit dans la partition **Leader** (Kafka gère la réplication)
- Il peut choisir la partition (via une clé de partitionnement) ou laisser Kafka choisir (round-robin)

### 2.5 Consumer

Un **consumer** = tout système qui **lit** des messages d'un topic.

```python
# Du cours (slides kafka-python) :
from kafka import KafkaConsumer

consumer = KafkaConsumer('my_favorite_topic')
for msg in consumer:
    print(msg)
```

**Propriétés du consumer :**
- Il lit sans **supprimer** les messages (les messages restent dans le topic)
- Plusieurs consumers peuvent lire **le même topic** indépendamment
- Les consumers peuvent être groupés en **consumer-group**

### 2.6 Consumer Group

Un **consumer-group** = plusieurs consumers qui coopèrent pour lire un topic.

```
Topic "order.created" avec 3 partitions

Consumer Group "inventory-service" :
├── Consumer A ← lit Partition 0
├── Consumer B ← lit Partition 1
└── Consumer C ← lit Partition 2

Consumer Group "notifications-service" :
└── Consumer D ← lit TOUTES les partitions (groupe à 1 consumer)
```

**Règles :**
- Dans un consumer-group, chaque partition est lue par **au plus 1 consumer**
- Si plus de consumers que de partitions → certains consumers sont inactifs
- Des consumer-groups différents sont **totalement indépendants** → ils reçoivent tous les messages

### 2.7 Message

Un **message** = l'unité de données transportée par Kafka.

**Propriétés :**
- C'est une **chaîne de caractères** (bytes en pratique)
- Doit être le **plus petit et concis possible** (performance)
- Doit assurer un **contrat d'interface** entre le producer et le consumer
  → Le producer et le consumer doivent s'accorder sur le format (JSON en général)

```python
# En pratique, on sérialise en JSON
import json
event = {
    "order_id": "uuid-123",
    "product_id": "pikachu_pack",
    "quantity": 2,
    "timestamp": "2024-01-15T10:30:00"
}
message_bytes = json.dumps(event).encode('utf-8')
```

---

## 3. kafka-python — Code du cours et TP

### Installation
```bash
pip install kafka-python
```

### KafkaProducer — Minimal (code du cours)
```python
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='localhost:1234')

# Envoyer 100 messages
for _ in range(100):
    producer.send('foobar', b'some_message_bytes')
```

### KafkaConsumer — Minimal (code du cours)
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer('my_favorite_topic')

for msg in consumer:
    print(msg)
```

### KafkaProducer — Production (TP4)
```python
from kafka import KafkaProducer
import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")
# En Docker : "broker:9092" (nom du service docker-compose)
# En local  : "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
    # value_serializer : sérialise automatiquement les dict Python en JSON bytes
)

def publish_event(topic: str, event: dict):
    producer.send(topic, event)    # event est sérialisé automatiquement
    producer.flush()               # Attendre que le message soit bien envoyé
```

### KafkaConsumer — Production (TP4 inventory-service)
```python
from kafka import KafkaConsumer, KafkaProducer
import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

consumer = KafkaConsumer(
    'order.created',        # Topic(s) à écouter (plusieurs possibles)
    'payment.failed',       # ← 2ème topic (compensation Saga)
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    # value_deserializer : désérialise automatiquement les bytes en dict Python
    auto_offset_reset='earliest',
    # 'earliest' : lire depuis le début si nouveau consumer
    # 'latest'   : lire seulement les nouveaux messages
    group_id='inventory-service'
    # group_id : identifiant du consumer-group
)

# Boucle principale d'écoute
for message in consumer:
    topic = message.topic      # "order.created" ou "payment.failed"
    event = message.value      # dict Python (déjà désérialisé)
    
    if topic == 'order.created':
        handle_order_created(event)
    elif topic == 'payment.failed':
        handle_payment_failed(event)  # ← compensation Saga
```

### KafkaConsumer — Notifications (TP4, écoute multi-topics)
```python
from kafka import KafkaConsumer
import json
import os

consumer = KafkaConsumer(
    'order.created',
    'inventory.updated',
    'inventory.admin.updated',
    'payment.succeeded',
    'payment.failed',
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092"),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='notifications-service'
)

for message in consumer:
    topic = message.topic
    event = message.value
    
    if topic == 'order.created':
        print(f"NEW ORDER: {event.get('order_id')} - Product: {event.get('product_id')}")
    
    elif topic == 'inventory.updated':
        status = event.get('status')
        if status == 'reserved':
            print(f"INVENTORY RESERVED: {event.get('order_id')}")
        else:
            print(f"INVENTORY FAILED: {event.get('reason')}")
    
    elif topic == 'payment.succeeded':
        print(f"PAYMENT OK: Order {event.get('order_id')} - ${event.get('amount')}")
    
    elif topic == 'payment.failed':
        print(f"PAYMENT FAILED: Order {event.get('order_id')} - {event.get('reason')}")
```

---

## 4. Docker Compose pour Kafka

Le fichier docker-compose du TP4 définit Kafka avec Zookeeper :

```yaml
version: '3.8'
services:
  # Zookeeper = coordinateur de cluster Kafka (obligatoire avec Kafka < 3.0)
  zookeeper:
    image: confluentinc/cp-zookeeper:7.0.1
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  # Kafka broker
  broker:
    image: confluentinc/cp-kafka:7.0.1
    depends_on: [zookeeper]
    ports:
      - "9092:9092"           # Port externe (localhost:9092)
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://broker:29092,PLAINTEXT_HOST://localhost:9092
      # broker:29092      = communication INTERNE Docker (entre containers)
      # localhost:9092    = communication EXTERNE (depuis la machine hôte)
```

**Points importants :**
- `broker:29092` = adresse interne Docker → utilisée dans les services Python (`KAFKA_BOOTSTRAP_SERVERS`)
- `localhost:9092` = adresse externe → depuis la machine hôte ou des tests
- Les variables d'env `KAFKA_BOOTSTRAP_SERVERS` permettent de configurer sans modifier le code

---

## 5. Topics utilisés dans les projets

### TP4 Kafka
```
order.created           → créé par orders-service
inventory.updated       → créé par inventory-service (reserved / insufficient_stock)
inventory.admin.updated → créé par inventory-service (admin change stock)
payment.succeeded       → créé par payment-service (70% de chance)
payment.failed          → créé par payment-service (30% de chance)
```

### PokeDrafter (Projet)
```
battle-events    → créé par battle_service lors des combats
chat-messages    → créé par chat_service lors des messages
```

---

## 6. Consumer Groups en pratique (TP4)

| Consumer Group | Topics écoutés | Rôle |
|---------------|---------------|------|
| `inventory-service` | `order.created`, `payment.failed` | Réserver/libérer stock |
| `payment-service` | `inventory.updated` | Traiter paiements |
| `notifications-service` | TOUS les topics | Logger tous les événements |

**Pourquoi des group_id différents ?**  
→ Chaque service a son propre offset. `payment-service` et `notifications-service` lisent tous les deux `inventory.updated` mais **indépendamment**. Si `payment-service` est down, il reprend depuis son dernier offset quand il redémarre — sans affecter `notifications-service`.

---

## 7. Flux Saga complet TP4 — avec les vrais topics

```
[Client] POST /orders/
    ↓
[orders-service]
    → INSERT orders + outbox_event dans BDD (atomique)
    → Thread publie: topic="order.created" {order_id, product_id, quantity}

[inventory-service] consomme "order.created"
    → Vérifie stock disponible
    → Si OK : stock -= quantity, publie "inventory.updated" {status: "reserved"}
    → Si KO : publie "inventory.updated" {status: "insufficient_stock", reason: "..."}

[payment-service] consomme "inventory.updated"
    → Si status == "reserved":
        → random.random() > 0.3 ? (70% succès)
        → Succès: publie "payment.succeeded" {order_id, amount}
        → Échec: publie "payment.failed" {order_id, reason: "card declined"}
    → Si status != "reserved": ignore

[inventory-service] consomme "payment.failed"
    → COMPENSATION : stock += quantity (libération)

[notifications-service] consomme TOUT
    → Log chaque événement (observabilité)
```

---

## 8. Questions d'oral probables

**Q: Qu'est-ce que Kafka et pourquoi l'utiliser dans les microservices ?**  
R: Kafka est une plateforme de streaming distribuée qui permet aux microservices de communiquer de manière asynchrone via des événements. Contrairement aux appels HTTP synchrones, Kafka découple les services — si un service est down, les événements sont stockés et seront traités à son redémarrage.

**Q: Quelle est la différence entre un topic et une partition ?**  
R: Un topic est un canal logique (ex: "order.created"). Une partition est une subdivision physique d'un topic — séquence immuable et ordonnée. Un topic peut avoir plusieurs partitions pour le parallélisme.

**Q: Pourquoi les messages Kafka sont-ils immuables ?**  
R: Pour garantir l'ordre et la cohérence. On ne peut qu'ajouter des messages, jamais modifier ou supprimer. Cela permet aussi le replay (rejouer les événements depuis le début).

**Q: Qu'est-ce qu'un consumer-group ?**  
R: Un groupe de consumers qui coopèrent pour lire un topic. Chaque partition est assignée à un seul consumer du groupe. Des groupes différents sont indépendants — ils reçoivent tous les mêmes messages.

**Q: Qu'est-ce que `auto_offset_reset='earliest'` ?**  
R: Si le consumer n'a pas d'offset sauvegardé (nouveau consumer ou groupe réinitialisé), il commencera à lire depuis le **début** du topic. Avec `'latest'`, il lirait seulement les nouveaux messages.

**Q: Quelle est la différence entre `broker:29092` et `localhost:9092` ?**  
R: `broker:29092` est l'adresse réseau interne Docker (utilisée entre containers). `localhost:9092` est l'adresse externe (depuis la machine hôte). Les services Python dans Docker utilisent `broker:29092`.
