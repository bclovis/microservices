# S3 — BDD en Microservices : ACID, Cohérence éventuelle, Outbox, Saga

> Cours de Lalanne Raphaël — Séance du 19 novembre  
> Source : `BDD en Microservices (1).pdf`

---

## 1. Monolithe vs Microservices — Gestion des données

### Tableau comparatif du cours

| Critère | Architecture Monolithique | Architecture Microservices |
|---------|--------------------------|---------------------------|
| **Couplage** | Fort (tout dans une seule BDD) | Faible (chaque service = sa BDD) |
| **Cohérence** | ACID garantie globalement | Cohérence éventuelle |
| **Transactions** | Simples (tout ou rien) | Complexes (transactions distribuées) |
| **Évolution** | Difficile (tout change ensemble) | Indépendante par service |
| **Complexité** | Simple à gérer | Plus complexe |

---

## 2. ACID — Les propriétés des transactions

**ACID** = les 4 propriétés qu'une transaction en base de données doit respecter :

| Lettre | Propriété | Explication |
|--------|-----------|-------------|
| **A** | Atomicité | La transaction est tout ou rien. Si une étape échoue, tout est annulé (rollback). |
| **C** | Cohérence | La BDD passe d'un état valide à un autre état valide. Les contraintes sont toujours respectées. |
| **I** | Isolement | Les transactions concurrentes ne s'impactent pas entre elles. |
| **D** | Durabilité | Une transaction confirmée (commit) est définitivement sauvegardée, même en cas de crash. |

### Pourquoi les microservices cassent ACID ?

Avec des microservices, une opération métier peut impliquer plusieurs services et donc plusieurs bases de données **différentes**. Impossible d'avoir une transaction ACID globale entre deux BDD distinctes.

**Exemple concret :** Passer une commande  
→ Créer la commande (BDD orders)  
→ Réserver le stock (BDD inventory)  
→ Débiter le paiement (BDD payments)  

Ces 3 opérations sont dans 3 BDD différentes → pas de transaction globale possible.

---

## 3. Stratégies pour gérer les données en microservices

### 3.1 UUID comme identifiants stables

**Problème :** Les IDs auto-incrémentaux (1, 2, 3...) ne fonctionnent pas bien entre services car deux services peuvent générer le même ID.

**Solution :** Utiliser des **UUID** (Universally Unique Identifier)

```python
import uuid

# Générer un UUID
order_id = str(uuid.uuid4())
# Exemple : "550e8400-e29b-41d4-a716-446655440000"

# En SQLAlchemy
from sqlalchemy import Column, String
import uuid

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
```

**Pourquoi UUID ?** → Unique globalement → peut être généré côté client ou serveur → pas de collision entre services

### 3.2 Foreign Keys locales — Pas de FK cross-service

**Règle absolue :** On ne met **jamais** de foreign key qui référence une table d'un autre service.

```
❌ MAUVAIS — FK cross-service (crée un couplage fort) :
orders_service.Order.user_id → users_service.User.id

✅ BON — Stocker juste l'ID (string), pas de FK :
orders_service.Order.user_id = "user_uuid_here"  # simple string, pas de FK
```

**Pourquoi ?** Si le service `users` est down, le service `orders` ne doit pas être impacté.

### 3.3 Dénormalisation

En microservices, il est accepté de **dupliquer des données** entre services pour éviter les appels synchrones constants.

**Exemple :**  
Au lieu d'appeler `users_service` à chaque fois pour avoir le nom de l'utilisateur, le `orders_service` stocke `user_name` directement dans sa table orders.

**Trade-off :** Les données peuvent être légèrement désynchronisées → cohérence éventuelle.

### 3.4 Vues matérialisées (Read Models)

**Concept :** Créer une vue "lecture" qui agrège des données de plusieurs services. Cette vue est mise à jour de manière asynchrone (via événements Kafka).

```
Écriture → events Kafka → Read model mis à jour → Lecture rapide depuis le read model
```

---

## 4. Cohérence éventuelle (Eventual Consistency)

### Définition

En microservices, on accepte que les données **ne soient pas immédiatement cohérentes** entre tous les services, mais qu'elles le **deviendront éventuellement**.

**Analogy :** DNS — quand vous changez un DNS, ça prend jusqu'à 48h pour se propager partout. Pendant ce temps, certains voient l'ancien record, d'autres le nouveau. C'est de la cohérence éventuelle.

### Comment y parvenir ?

Le **message broker** (Kafka) fait le lien entre les BDD des différents services :

```
service A écrit dans sa BDD
    ↓ publie un événement dans Kafka
service B consomme l'événement
    ↓ met à jour SA BDD
cohérence éventuelle atteinte
```

### ⚠️ Règle du cours (CRITIQUE)

> **"Un message broker n'est PAS une BDD !"**

Kafka n'est pas conçu pour stocker des données de façon durable et interrogeable. Il est conçu pour transmettre des événements. Ne stockez jamais vos données uniquement dans Kafka.

> **"Ne stockez jamais de données utilisateur dans votre code en tant que variable"**

Les données doivent être dans une vraie BDD persistante (PostgreSQL, MySQL...), pas dans une variable Python en mémoire (ça disparaît au redémarrage).

---

## 5. Pattern Outbox — Garantir la publication des événements

### Problème sans Outbox

```python
# ❌ PROBLÈME : deux opérations non atomiques
db.add(new_order)
db.commit()              # ← si ça réussit...
kafka.send(event)        # ← mais ça échoue ? → incohérence !
```

Si la BDD est commitée mais que Kafka est down ou plante, l'événement est **perdu**. La commande existe en BDD mais aucun autre service ne le sait.

### Solution : Pattern Outbox

L'idée est de **stocker l'événement dans la même transaction** que la donnée métier, dans une table `outbox`. Un thread séparé lit cette table et publie les événements.

```
┌─────────────────────────────────────────┐
│  Transaction atomique (1 seule BDD)     │
│  ┌───────────────────┐                  │
│  │ INSERT orders     │                  │
│  │ INSERT outbox_events │               │
│  └───────────────────┘                  │
│  COMMIT (les deux ou rien)              │
└─────────────────────────────────────────┘
          ↓
  [Thread séparé toutes les 5s]
          ↓
  Lit les outbox_events non traités
          ↓
  Publie sur Kafka
          ↓
  Marque comme processed=1
```

### Code complet du Pattern Outbox (TP4)

```python
# models.py — Table Outbox
from sqlalchemy import Column, Integer, String, Text
from database import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    product_id = Column(String)
    quantity = Column(Integer)
    status = Column(String, default="pending")

class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String)     # ex: "order.created"
    payload = Column(Text)          # JSON stringifié
    processed = Column(Integer, default=0)  # 0 = à publier, 1 = publié
```

```python
# orders-service/main.py — Créer une commande avec pattern Outbox
import json
import threading

@app.post("/orders/")
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    # Créer la commande
    new_order = Order(
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        status="pending"
    )
    
    # Créer l'événement dans la table outbox
    outbox_event = OutboxEvent(
        event_type="order.created",
        payload=json.dumps({
            "order_id": new_order.id,
            "product_id": order_data.product_id,
            "quantity": order_data.quantity
        })
    )
    
    # ← ATOMIQUE : les deux sont dans la même transaction
    db.add(new_order)
    db.add(outbox_event)
    db.commit()              # Commit les deux ou rien
    
    return new_order

# Thread séparé qui publie les événements en attente
def process_outbox():
    while True:
        db = SessionLocal()
        try:
            # Récupérer tous les événements non traités
            events = db.query(OutboxEvent).filter(
                OutboxEvent.processed == 0
            ).all()
            
            for event in events:
                # Publier sur Kafka
                publish_event(event.event_type, json.loads(event.payload))
                # Marquer comme traité
                event.processed = 1
                db.commit()
        finally:
            db.close()
        time.sleep(5)  # Vérifier toutes les 5 secondes

# Démarrer le thread au lancement de l'application
threading.Thread(target=process_outbox, daemon=True).start()
```

**Avantages du Pattern Outbox :**
- ✅ Atomique : commande + événement commitées ensemble
- ✅ Fiable : même si Kafka est down, l'événement sera publié dès que Kafka revient
- ✅ Idempotent : si le thread redémarre, il republiera (il faut gérer les doublons côté consumer)

---

## 6. Pattern Saga — Transactions distribuées

### Problème : Transactions cross-services

Une commande nécessite :
1. Réserver le stock (inventory_service)
2. Débiter le paiement (payment_service)
3. Mettre à jour la commande (orders_service)

Ces 3 opérations **peuvent échouer** indépendamment. Comment gérer les échecs ?

### Deux types de Saga

| Type | Description | Quand utiliser |
|------|-------------|----------------|
| **Orchestration** | Un orchestrateur central coordonne tous les services | Logique complexe, besoin de visibilité centrale |
| **Chorégraphie** | Chaque service sait quoi faire et réagit aux événements | Architecture simple, services découplés |

### Saga par Chorégraphie (implémenté dans TP4)

```
orders-service crée la commande
    └─→ publie "order.created" sur Kafka

inventory-service consomme "order.created"
    ├─→ Si stock disponible → réserve, publie "inventory.updated" {status: "reserved"}
    └─→ Si stock insuffisant → publie "inventory.updated" {status: "insufficient_stock"}

payment-service consomme "inventory.updated"
    ├─→ Si status=reserved → tente paiement
    │   ├─→ Succès → publie "payment.succeeded"
    │   └─→ Échec → publie "payment.failed"
    └─→ Si status!=reserved → ignore

inventory-service consomme "payment.failed"
    └─→ COMPENSATION : libère le stock réservé

orders-service consomme "payment.succeeded" / "payment.failed"
    └─→ Met à jour le statut de la commande
```

### Schéma Saga TP4 (PlaceOrder)

```
[orders]  order.created
    ↓
[inventory] → reserved → inventory.updated{reserved}
    ↓                          ↓
[payment]          payment.succeeded / payment.failed
    ↓                    ↓              ↓
[orders]          order=confirmed   order=cancelled
                                        ↓
                              [inventory] ← COMPENSATION : libère le stock
```

### Transactions compensatoires

Si un service échoue, les services précédents doivent **défaire** ce qu'ils ont fait :

| Étape | Transaction directe | Transaction compensatoire |
|-------|--------------------|-----------------------------|
| Réserver stock | `stock -= quantité` | `stock += quantité` (libération) |
| Débiter paiement | `balance -= montant` | `balance += montant` (remboursement) |

---

## 7. Résumé des patterns de données

| Pattern | Problème résolu | Mécanisme |
|---------|----------------|-----------|
| **UUID** | Identifiants uniques cross-services | UUID généré localement |
| **FK locales** | Couplage fort entre services | Stocker juste l'ID string |
| **Dénormalisation** | Appels synchrones excessifs | Dupliquer les données nécessaires |
| **Outbox** | Événements perdus si Kafka down | Atomicité BDD + publication différée |
| **Saga chorégraphie** | Transaction multi-services | Événements Kafka + compensations |
| **Saga orchestration** | Coordination centralisée | Orchestrateur central |
| **Cohérence éventuelle** | Impossibilité d'ACID global | Accepter la désynchronisation temporaire |

---

## 8. Questions d'oral probables

**Q: Qu'est-ce qu'ACID et pourquoi les microservices le cassent ?**  
R: ACID = Atomicité, Cohérence, Isolement, Durabilité. Les microservices ont chacun leur propre BDD, donc impossible d'avoir une transaction ACID qui couvre plusieurs services. On passe à la cohérence éventuelle.

**Q: Qu'est-ce que le Pattern Outbox et pourquoi l'utiliser ?**  
R: Stocker l'événement Kafka dans la même transaction BDD que la donnée métier. Un thread séparé lit et publie les événements. Garantit qu'aucun événement n'est perdu même si Kafka est temporairement down.

**Q: Quelle est la différence entre Saga Orchestration et Chorégraphie ?**  
R: Orchestration = un service central coordonne les autres (il sait tout). Chorégraphie = chaque service réagit aux événements Kafka sans coordinateur central (couplage plus faible).

**Q: Pourquoi ne pas mettre de foreign keys entre services ?**  
R: Cela créerait un couplage fort. Si un service est down ou change son schéma, l'autre service serait impacté. On stocke juste l'UUID comme simple string.

**Q: Un message broker peut-il remplacer une BDD ?**  
R: Non ! "Un message broker n'est PAS une BDD." Kafka est fait pour transmettre des événements, pas pour stocker et interroger des données de façon durable.
