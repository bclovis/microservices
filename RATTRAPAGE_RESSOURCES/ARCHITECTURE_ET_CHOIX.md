# 🏗️ ARCHITECTURE ET CHOIX TECHNIQUES - PokeDrafter

> **Pour l'oral :** Justifier tous les choix d'architecture et de communication

---

## 📚 TABLE DES MATIÈRES

1. [Pattern SAGA](#1-pattern-saga)
2. [Comment choisir ses services](#2-comment-choisir-ses-services)
3. [Pourquoi ces 5 services dans PokeDrafter](#3-pourquoi-ces-5-services-dans-pokedrafter)
4. [Moyens de communication](#4-moyens-de-communication)
5. [Justification complète de l'architecture](#5-justification-complète-de-larchitecture)

---

## 1. PATTERN SAGA

### 🎯 Qu'est-ce que SAGA ?

**Définition :** Pattern pour gérer des **transactions distribuées** sur plusieurs microservices.

**Le problème :**

En **monolithe**, tu as des transactions atomiques :
```python
# MONOLITHE - 1 base de données
def create_order(user_id, product_id, quantity):
    db.begin_transaction()
    try:
        order = db.insert_order(user_id, product_id)
        db.reserve_stock(product_id, quantity)
        db.charge_payment(user_id, order.total)
        db.commit()  # ✅ Tout ou rien (ACID)
    except:
        db.rollback()  # ❌ Annule TOUT
```

En **microservices**, **IMPOSSIBLE** :
```
OrderService → BDD orders
InventoryService → BDD inventory
PaymentService → BDD payments

❌ Pas de transaction globale entre 3 bases différentes !
```

---

### Les 2 types de SAGA

#### 1️⃣ SAGA Orchestration (Chef d'orchestre)

**Principe :** UN service central coordonne tout.

```
┌──────────────┐
│ OrderService │ (Orchestrateur)
└──────────────┘
       │
       ├─[1]─→ InventoryService.reserve() → OK
       │
       ├─[2]─→ PaymentService.charge() → OK
       │
       └─[3]─→ OrderService.complete() → ✅
```

**Code exemple :**
```python
# OrderService (orchestrateur)
async def create_order(product_id, quantity):
    # Étape 1 : Réserver stock
    response = await inventory_client.reserve(product_id, quantity)
    if not response.success:
        return "Stock insuffisant"
    
    # Étape 2 : Charger paiement
    response = await payment_client.charge(user_id, total)
    if not response.success:
        # COMPENSATION : libérer le stock
        await inventory_client.release(product_id, quantity)
        return "Paiement refusé"
    
    # Étape 3 : Confirmer commande
    return "Commande validée"
```

**✅ Avantages :**
- Contrôle centralisé (facile à comprendre)
- Facile à débugger (tout passe par l'orchestrateur)

**❌ Inconvénients :**
- OrderService doit connaître TOUT le flow
- Couplage fort (OrderService dépend de tous les autres)

---

#### 2️⃣ SAGA Choreography (Danse) ← **TON PROJET**

**Principe :** Chaque service écoute des **événements** et réagit de manière autonome.

```
┌──────────────┐
│ OrderService │ Publie "order.created" sur Kafka
└──────────────┘
       │
       │ Kafka: order.created
       ▼
┌──────────────┐
│ InventoryService │ Écoute "order.created"
│                  │ → Réserve stock
│                  │ → Publie "stock.reserved"
└──────────────┘
       │
       │ Kafka: stock.reserved
       ▼
┌──────────────┐
│ PaymentService │ Écoute "stock.reserved"
│                │ → Charge paiement
│                │ → Publie "payment.succeeded"
└──────────────┘
       │
       │ Kafka: payment.succeeded
       ▼
┌──────────────┐
│ OrderService │ Écoute "payment.succeeded"
│              │ → Marque commande "validée"
└──────────────┘
```

**Code exemple :**
```python
# OrderService (producer)
async def create_order(product_id, quantity):
    order = Order(product_id=product_id, status="pending")
    await db.save(order)
    
    # Publier événement
    await kafka_producer.send("order.created", {
        "order_id": order.id,
        "product_id": product_id,
        "quantity": quantity
    })
    return order

# InventoryService (consumer)
@kafka_consumer("order.created")
async def handle_order_created(event):
    if stock_available(event["product_id"], event["quantity"]):
        reserve_stock(event["product_id"], event["quantity"])
        await kafka_producer.send("stock.reserved", event)
    else:
        await kafka_producer.send("stock.failed", event)

# PaymentService (consumer)
@kafka_consumer("stock.reserved")
async def handle_stock_reserved(event):
    if charge_payment(event["user_id"], event["total"]):
        await kafka_producer.send("payment.succeeded", event)
    else:
        await kafka_producer.send("payment.failed", event)

# InventoryService (compensation)
@kafka_consumer("payment.failed")
async def handle_payment_failed(event):
    # COMPENSATION : Libérer le stock réservé
    release_stock(event["product_id"], event["quantity"])
```

**✅ Avantages :**
- Découplage total (chaque service autonome)
- Scalable (ajouter un service = écouter un topic)
- Résilient (si un service down, Kafka stocke les events)

**❌ Inconvénients :**
- Plus complexe à comprendre (flow distribué)
- Difficile à débugger (pas de point central)

---

### SAGA dans TON projet PokeDrafter

**Flow d'un tour de bataille :**

```
┌─────────────────┐
│ battle_service  │ (Producer)
│                 │ POST /battles/{id}/turn
│                 │   1. Calcule F(A) vs F(B)
│                 │   2. Sauvegarde BattleTurn en BDD
│                 │   3. Publie "turn_played" sur Kafka
└─────────────────┘
         │
         │ Kafka topic: "battle-events"
         │ Message: {"type": "turn_played", "result": "A", "turn_number": 3}
         ▼
┌─────────────────┐
│ chat_service    │ (Consumer)
│                 │ kafka_consumer_loop()
│                 │   1. Reçoit event "turn_played"
│                 │   2. Crée notification bot
│                 │   3. broadcast_all() sur WebSocket
└─────────────────┘
         │
         ▼
    Tous les joueurs connectés voient :
    "Tour 3 — Rouge remporte le tour !"
```

**C'est un SAGA Choreography simplifié :**
- battle_service publie un événement
- chat_service réagit automatiquement
- Pas d'orchestrateur central
- Si chat_service est down → Kafka stocke l'event, consommé plus tard

---

### 🎤 RÉPONSE POUR L'ORAL

**"C'est quoi le pattern SAGA ?"**

> "SAGA est un pattern pour gérer des transactions distribuées sur plusieurs microservices.
> 
> En monolithe, on a des transactions ACID atomiques. En microservices, impossible car chaque service a sa propre base de données.
> 
> Il existe 2 types :
> - **Orchestration** : un chef d'orchestre coordonne toutes les étapes
> - **Choreography** : chaque service écoute des événements et réagit de manière autonome
> 
> Dans PokeDrafter, on utilise Choreography : battle_service publie 'turn_played' sur Kafka, chat_service le consomme et broadcast sur WebSocket. C'est un SAGA simple sans compensation car si chat échoue, Kafka garde le message."

---

## 2. COMMENT CHOISIR SES SERVICES ?

### 🎯 Méthode en 5 étapes

#### Étape 1 : Identifier les **DOMAINES MÉTIER**

**Question :** Quelles sont les grandes fonctionnalités de l'application ?

**Méthode DDD (Domain-Driven Design) :**
- Chaque **domaine métier** = 1 service potentiel
- Un domaine = un ensemble de fonctionnalités cohérentes

**Exemple PokeDrafter :**
```
Domaines métier identifiés :
1. 👤 Authentification (register, login, JWT)
2. 🎮 Gestion d'équipes (créer, modifier, supprimer équipes)
3. ⚔️ Batailles (combat, calcul F(A), tours)
4. 💬 Chat (messages temps réel entre joueurs)
5. 📚 Pokédex (infos Pokémon, recherche)
```

**Chaque domaine devient un microservice.**

---

#### Étape 2 : Vérifier l'**INDÉPENDANCE DES DONNÉES**

**Question :** Ces domaines ont-ils des données indépendantes ?

**Règle :** Si 2 domaines partagent BEAUCOUP de données → peut-être 1 seul service.

**Exemple PokeDrafter :**

| Service | Tables BDD | Indépendant ? |
|---------|-----------|---------------|
| auth_service | users, sessions | ✅ Oui |
| team_service | teams, team_pokemons | ✅ Oui |
| battle_service | battles, battle_turns | ✅ Oui |
| chat_service | messages | ✅ Oui |
| pokedex_service | (cache Redis, pas de BDD) | ✅ Oui |

**Verdict :** Chaque service a ses propres données → **database per service pattern** ✅

**Contre-exemple :**
```
Si battle_service avait besoin de modifier les teams constamment
→ Fort couplage avec team_service
→ Peut-être fusionner en 1 seul service "game_service"
```

---

#### Étape 3 : Évaluer la **CHARGE** de chaque domaine

**Question :** Tous les services ont-ils la même charge ?

**Exemples de charge :**
- auth_service : login 1x/jour/user → Charge FAIBLE
- team_service : modifier équipe 10x/jour/user → Charge MOYENNE
- battle_service : 100 tours/bataille × 50 batailles → Charge ÉLEVÉE
- chat_service : 1000 messages/minute → Charge ÉLEVÉE
- pokedex_service : consulter Pokédex 50x/user → Charge MOYENNE

**Si charge différente → services séparés permettent de scaler indépendamment.**

**Exemple PokeDrafter :**
```
battle_service : Kubernetes HPA 2-10 pods (scale selon CPU)
auth_service : 1-2 pods fixes (peu de charge)
```

**Avantage microservices :** battle peut scaler sans scaler auth (économie de ressources).

---

#### Étape 4 : Identifier les **DÉPENDANCES**

**Question :** Quel service dépend de quel autre ?

**Exemple PokeDrafter :**

```
┌──────────────┐
│ auth_service │ (Aucune dépendance)
└──────────────┘
       ↓ Fournit JWT
┌──────────────┐
│ team_service │ Dépend de : auth (validation JWT)
└──────────────┘
       ↓ Fournit teams
┌──────────────┐
│ battle_service│ Dépend de : auth (JWT), team (teams)
└──────────────┘
       ↓ Publie events Kafka
┌──────────────┐
│ chat_service │ Dépend de : battle (events Kafka)
└──────────────┘

┌──────────────┐
│pokedex_service│ Dépend de : PokéAPI externe
└──────────────┘
```

**Règle :** Minimiser les dépendances circulaires (A → B → A).

**PokeDrafter :** Pas de dépendances circulaires ✅

---

#### Étape 5 : Définir les **MOYENS DE COMMUNICATION**

**Question :** Comment les services communiquent-ils ?

| Type | Quand l'utiliser | Exemple PokeDrafter |
|------|------------------|---------------------|
| **REST HTTP sync** | Requête-réponse immédiate | Frontend → auth_service (login) |
| **Kafka async** | Événements métier, pas besoin de réponse immédiate | battle → chat (turn_played) |
| **WebSocket** | Communication bidirectionnelle temps réel | chat_service ↔ Frontend |
| **gRPC** | Communication backend-backend haute performance | (pas utilisé ici) |

**Règle simple :**
- **Sync (REST)** : Quand tu as BESOIN de la réponse pour continuer
- **Async (Kafka)** : Quand tu PUBLIES un événement et tu t'en fous de la réponse

---

### 🎯 Arbre de décision

```
Mon application a plusieurs domaines métier ?
│
├─ OUI → Microservices potentiels
│  │
│  ├─ Les domaines ont des données indépendantes ?
│  │  │
│  │  ├─ OUI → Services séparés ✅
│  │  │
│  │  └─ NON → Peut-être 1 seul service
│  │
│  └─ Les domaines ont des charges différentes ?
│     │
│     ├─ OUI → Services séparés pour scaler indépendamment ✅
│     │
│     └─ NON → Monolithe modulaire OK
│
└─ NON → Monolithe simple
```

---

## 3. POURQUOI CES 5 SERVICES DANS POKEDRAFTER ?

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE PokeDrafter                  │
└─────────────────────────────────────────────────────────────┘

Frontend (Angular)
       │
       │ HTTP/WebSocket
       ▼
┌──────────────┐
│ Nginx Gateway│ Routage /api/*
└──────────────┘
       │
       ├────────────┬────────────┬────────────┬────────────┐
       ▼            ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   auth   │ │   team   │ │  battle  │ │   chat   │ │ pokedex  │
│ :8001    │ │ :8002    │ │ :8003    │ │ :8004    │ │ :8005    │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
     │            │            │            │            │
     ▼            ▼            ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│auth_db  │ │team_db  │ │battle_db│ │ (Kafka) │ │ Redis   │
│PostgreSQL│ │PostgreSQL│ │PostgreSQL│ │         │ │ Cache   │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
                                           │
                                           ▼
                                    ┌───────────┐
                                    │  PokéAPI  │
                                    │ (externe) │
                                    └───────────┘
```

---

### 1️⃣ auth_service (Authentification)

**Domaine métier :** Gestion des utilisateurs et sécurité

**Responsabilités :**
- Register (créer compte)
- Login (connexion + JWT)
- Validation JWT (middleware pour autres services)
- Gestion profil user

**Pourquoi service séparé ?**
- ✅ **Sécurité isolée** : Code sensible (hashing password, JWT) dans 1 seul endroit
- ✅ **Réutilisable** : Tous les autres services valident JWT via auth
- ✅ **Indépendant** : Données users totalement séparées des battles/teams

**Base de données :**
```sql
-- auth_db
users (id, username, email, password_hash, created_at)
sessions (id, user_id, token, expires_at)
```

**Communication :**
- REST sync : Frontend → auth_service (login, register)
- JWT : auth_service → autres services (validation token)

---

### 2️⃣ team_service (Gestion équipes)

**Domaine métier :** Construction et gestion des équipes Pokémon

**Responsabilités :**
- CRUD équipes (create, read, update, delete)
- Ajouter/retirer Pokémon d'une équipe
- Validation contraintes (max 6 Pokémon)
- Recommandation IA ("Complete" button)

**Pourquoi service séparé ?**
- ✅ **Domaine distinct** : Gérer équipes ≠ combattre
- ✅ **Données indépendantes** : teams table totalement séparée
- ✅ **Scalabilité** : Si beaucoup d'utilisateurs créent des équipes, on peut scaler team_service indépendamment

**Base de données :**
```sql
-- team_db
teams (id, user_id, name, created_at)
team_pokemons (id, team_id, pokemon_id, position)
```

**Communication :**
- REST sync : Frontend → team_service (CRUD équipes)
- REST sync : battle_service → team_service (récupérer équipe pour bataille)

---

### 3️⃣ battle_service (Moteur de combat) ← **TON SERVICE PRINCIPAL**

**Domaine métier :** Logique de combat et calcul avantages types

**Responsabilités :**
- Calcul F(A) vs F(B) (formule types)
- Gestion tours de bataille
- Routes /create, /join, /turn, /forfeit, /end
- Publication events Kafka "turn_played"

**Pourquoi service séparé ?**
- ✅ **Logique complexe** : calc_advantage() + TYPE_CHART = code spécialisé
- ✅ **Charge élevée** : Beaucoup de batailles simultanées → besoin de scaler
- ✅ **Événements métier** : Produit des événements (turn_played) pour d'autres services

**Base de données :**
```sql
-- battle_db
battles (id, player_red_id, player_blue_id, status, winner, created_at)
battle_turns (id, battle_id, turn_number, pokemon_red, pokemon_blue, 
              types_red, types_blue, score_red, score_blue, result)
```

**Communication :**
- REST sync : Frontend → battle_service (jouer tour, forfeit)
- Kafka async : battle_service → chat_service (événements turn_played)

**Code clé :**
```python
# battle_service/app/services/battle_engine.py
def calc_advantage(types_a, types_b):
    # Formule F(A) = 1×(W/Y)×(W/Z) + 1×(X/Y)×(X/Z)
    # Retourne (fa, fb)
    pass

# battle_service/app/routes/battle.py
@router.post("/{battle_id}/turn")
async def play_turn(battle_id, payload):
    fa, fb = calc_advantage(types_red, types_blue)
    # Sauvegarde BattleTurn
    # Publie Kafka
    await publish_battle_event("turn_played", {...})
```

---

### 4️⃣ chat_service (Chat temps réel) ← **TON 2E SERVICE PRINCIPAL**

**Domaine métier :** Communication temps réel entre joueurs

**Responsabilités :**
- WebSocket /ws/chat/{team} (chat d'équipe)
- Kafka consumer (écoute "turn_played")
- Broadcast notifications battle log à tous les joueurs
- Gestion connexions WebSocket (connect/disconnect)

**Pourquoi service séparé ?**
- ✅ **Technologie différente** : WebSocket ≠ REST (connexions persistantes)
- ✅ **Charge différente** : Chat = beaucoup de messages/seconde
- ✅ **Résilience** : Si chat crash, battle continue (grâce à Kafka)

**Base de données :**
- Aucune ! (messages éphémères, pas de persistance)
- Kafka stocke temporairement les events

**Communication :**
- WebSocket : Frontend ↔ chat_service (messages chat)
- Kafka async : battle_service → chat_service (événements battle)

**Code clé :**
```python
# chat_service/app/main.py
async def kafka_consumer_loop():
    retry_delay = 2
    while True:
        try:
            async for msg in consumer:  # S'abonne à : battle-events + chat-messages
                topic = msg.topic
                event = msg.value
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
        except Exception:
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)  # Exponential backoff
```

---

### 5️⃣ pokedex_service (Données Pokémon)

**Domaine métier :** Informations Pokémon (stats, types, sprites)

**Responsabilités :**
- Récupérer données PokéAPI (https://pokeapi.co)
- Cache Redis (éviter d'appeler PokéAPI à chaque fois)
- Routes /pokedex, /pokedex/{id}, /pokedex/search

**Pourquoi service séparé ?**
- ✅ **Source externe** : Appelle une API externe (PokéAPI)
- ✅ **Cache indépendant** : Redis uniquement pour le Pokédex
- ✅ **Scalabilité** : Si beaucoup de requêtes Pokédex, on peut scaler indépendamment

**Base de données :**
- Redis cache (key-value store)
- Pas de PostgreSQL (données viennent de PokéAPI)

**Communication :**
- REST sync : Frontend → pokedex_service (consulter Pokédex)
- HTTP externe : pokedex_service → PokéAPI (fetch données)

**Code clé :**
```python
# pokedex_service/app/services/pokeapi_service.py
async def get_pokemon(pokemon_id):
    # 1. Vérifier cache Redis
    cached = await redis.get(f"pokemon:{pokemon_id}")
    if cached:
        return json.loads(cached)
    
    # 2. Appeler PokéAPI
    response = await httpx.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
    data = response.json()
    
    # 3. Mettre en cache (TTL 1h)
    await redis.setex(f"pokemon:{pokemon_id}", 3600, json.dumps(data))
    
    return data
```

---

### Récapitulatif des choix

| Service | Pourquoi séparé | Scalabilité | Communication |
|---------|----------------|-------------|---------------|
| auth | Sécurité isolée, réutilisable | Faible → 1-2 pods | REST sync |
| team | Domaine distinct, données indépendantes | Moyenne → 2-3 pods | REST sync |
| battle | Logique complexe, charge élevée | Élevée → 2-10 pods HPA | REST + Kafka |
| chat | WebSocket, résilience | Élevée → 2-5 pods | WebSocket + Kafka |
| pokedex | API externe, cache Redis | Moyenne → 1-3 pods | REST + cache |

---

## 4. MOYENS DE COMMUNICATION

### Vue d'ensemble

```
┌──────────────────────────────────────────────────────────┐
│              MOYENS DE COMMUNICATION PokeDrafter          │
└──────────────────────────────────────────────────────────┘

1. REST HTTP (Synchrone)
   Frontend → auth_service : POST /login
   Frontend → team_service : GET /teams
   Frontend → battle_service : POST /battles/{id}/turn

2. Kafka (Asynchrone)
   battle_service → chat_service : "turn_played" event

3. WebSocket (Bidirectionnel temps réel)
   Frontend ↔ chat_service : Messages chat

4. HTTP externe
   pokedex_service → PokéAPI : Fetch Pokémon data
```

---

### 1️⃣ REST HTTP (Synchrone)

**Principe :** Client envoie requête → Serveur répond → Client attend la réponse

**Quand l'utiliser :**
- ✅ Tu as **BESOIN** de la réponse pour continuer
- ✅ Opération simple (CRUD)
- ✅ Latence acceptable (<1s)

**Exemples dans PokeDrafter :**

```python
# Frontend → auth_service
POST /api/auth/login
Body: {"username": "Alice", "password": "secret"}
Response: {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
→ Frontend ATTEND le token pour continuer

# Frontend → team_service
GET /api/teams/{id}
Response: {"id": 1, "name": "Dream Team", "pokemons": [...]}
→ Frontend ATTEND les données pour afficher

# Frontend → battle_service
POST /api/battles/{id}/turn
Body: {"types_red": ["Feu"], "types_blue": ["Eau"]}
Response: {"result": "B", "score_red": 0.5, "score_blue": 2.0}
→ Frontend ATTEND le résultat pour afficher
```

**Caractéristiques :**
- ⚡ Latence : 50-500ms
- 🔒 Couplage : Fort (si serveur down, client bloqué)
- 📊 Scalabilité : Limitée (1 requête = 1 thread)

---

### 2️⃣ Kafka (Asynchrone)

**Principe :** Producer publie événement → Kafka stocke → Consumer lit quand il veut

**Quand l'utiliser :**
- ✅ Tu publies un **événement métier** (pas une requête)
- ✅ Tu n'as PAS besoin de réponse immédiate
- ✅ Tu veux du **découplage** (producer ne connaît pas les consumers)
- ✅ Tu veux de la **résilience** (si consumer down, events stockés)

**Exemple dans PokeDrafter :**

```python
# battle_service (Producer)
@router.post("/{battle_id}/turn")
async def play_turn(battle_id, payload):
    # 1. Calculer résultat
    fa, fb = calc_advantage(types_red, types_blue)
    result = resolve_turn(types_red, types_blue)
    
    # 2. Sauvegarder en BDD
    turn = BattleTurn(...)
    await db.save(turn)
    
    # 3. Publier événement Kafka (asynchrone)
    await publish_battle_event("turn_played", {
        "battle_id": str(battle_id),
        "turn_number": 3,
        "result": "A"  # Rouge gagne
    })
    
    # 4. Retourner immédiatement (ne pas attendre chat_service)
    return turn  # ✅ Battle continue sans attendre chat

# chat_service (Consumer) — écoute 2 topics
async def kafka_consumer_loop():
    while True:
        try:
            async for msg in consumer:  # topics: battle-events + chat-messages
                event = msg.value
                topic = msg.topic
                if topic == settings.KAFKA_TOPIC_BATTLE:
                    if event.get("type") == "turn_played":
                        # Créer notification
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
        except Exception:
            # Retry avec exponential backoff
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)
```

**Pourquoi Kafka ici ?**

**❌ Si on utilisait REST (synchrone) :**
```python
# battle_service devrait attendre chat_service
response = await httpx.post("http://chat-service/notify", json=data)
# Problèmes :
# 1. Si chat down → ERROR 500, battle crash
# 2. Si chat lent (100ms) → battle ralenti
# 3. Couplage fort → battle dépend de chat
```

**✅ Avec Kafka (asynchrone) :**
```python
# battle_service publie et continue immédiatement
await publish_battle_event("turn_played", data)
# Avantages :
# 1. Si chat down → Kafka stocke, consomme plus tard
# 2. Battle ne ralentit pas (publish = 1-2ms)
# 3. Découplage total → battle ne sait même pas que chat existe
```

**Caractéristiques :**
- ⚡ Latence : 1-10ms (publish) + 10-100ms (consume)
- 🔒 Couplage : Faible (producer/consumer indépendants)
- 📊 Scalabilité : Très haute (millions de messages/seconde)
- 🛡️ Résilience : Excellente (store & forward)

---

### 3️⃣ WebSocket (Bidirectionnel temps réel)

**Principe :** Connexion persistante entre client et serveur, les 2 peuvent envoyer des messages

**Quand l'utiliser :**
- ✅ Communication **bidirectionnelle** (client ↔ serveur)
- ✅ **Temps réel** (latence <100ms)
- ✅ Serveur doit **push** des données au client sans que client demande

**Exemple dans PokeDrafter :**

```typescript
// Frontend (TypeScript)
const ws = new WebSocket('ws://localhost:8004/ws/chat/red');

// Envoyer message
ws.send(JSON.stringify({
    author: "Alice",
    content: "Salut l'équipe !",
    timestamp: Date.now()
}));

// Recevoir messages (push du serveur)
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log(`${message.author}: ${message.content}`);
};
```

```python
# Backend (Python)
@router.websocket("/ws/chat/{team}")
async def chat_endpoint(websocket: WebSocket, team: str):
    await websocket.accept()
    await chat_service.connect(team, websocket)
    
    try:
        while True:
            # Recevoir message du client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Publier sur Kafka (pour persistance)
            await kafka_producer.send("chat-messages", message)
            
            # Broadcast à tous les WebSocket de cette team
            await chat_service.broadcast(team, message)
            
    except WebSocketDisconnect:
        await chat_service.disconnect(team, websocket)
```

**Pourquoi WebSocket ici ?**

**❌ Si on utilisait HTTP long-polling :**
```typescript
// Client poll toutes les secondes
setInterval(async () => {
    const response = await fetch('/api/chat/messages');
    const messages = await response.json();
    // Problèmes :
    // 1. Latence élevée (jusqu'à 1s)
    // 2. Beaucoup de requêtes HTTP inutiles
    // 3. Charge serveur élevée
}, 1000);
```

**✅ Avec WebSocket :**
```typescript
// Connexion unique persistante
const ws = new WebSocket('ws://...');
ws.onmessage = (msg) => {
    // Reçoit messages instantanément (push)
    // Avantages :
    // 1. Latence très faible (<50ms)
    // 2. 1 seule connexion TCP
    // 3. Charge serveur optimisée
};
```

**Caractéristiques :**
- ⚡ Latence : <50ms
- 🔒 Couplage : Connexion persistante
- 📊 Scalabilité : Moyenne (1 connexion = 1 ressource)
- 🛡️ Résilience : Nécessite reconnexion si déconnexion

---

### 4️⃣ HTTP externe (vers PokéAPI)

**Principe :** Appeler une API externe pour récupérer des données

**Exemple dans PokeDrafter :**

```python
# pokedex_service appelle PokéAPI
async def get_pokemon(pokemon_id: int):
    # Vérifier cache Redis d'abord
    cached = await redis.get(f"pokemon:{pokemon_id}")
    if cached:
        return json.loads(cached)
    
    # Appeler API externe
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
        )
        data = response.json()
    
    # Mettre en cache (TTL 1h)
    await redis.setex(f"pokemon:{pokemon_id}", 3600, json.dumps(data))
    
    return data
```

**Pourquoi cache Redis ?**
- PokéAPI = externe, lent (200-500ms)
- Données Pokémon changent rarement
- Cache Redis = <5ms

---

### Tableau comparatif

| Moyen | Latence | Couplage | Scalabilité | Résilience | Usage PokeDrafter |
|-------|---------|----------|-------------|------------|-------------------|
| **REST HTTP** | 50-500ms | Fort | Moyenne | Faible | Frontend → services (CRUD) |
| **Kafka** | 1-100ms | Faible | Très haute | Excellente | battle → chat (events) |
| **WebSocket** | <50ms | Moyen | Moyenne | Moyenne | Frontend ↔ chat (temps réel) |
| **HTTP externe** | 200-500ms | Aucun | N/A | Faible | pokedex → PokéAPI |

---

## 5. JUSTIFICATION COMPLÈTE DE L'ARCHITECTURE

### 🎤 RÉPONSES POUR L'ORAL

#### Q1 : "Pourquoi microservices et pas monolithe ?"

**TA RÉPONSE :**
> "J'ai choisi microservices pour 4 raisons principales :
> 
> 1. **Scalabilité différenciée** : battle_service a beaucoup plus de charge que auth_service (100 tours/minute vs 10 logins/minute). Avec microservices, je peux scaler battle indépendamment avec Kubernetes HPA (2-10 pods selon CPU).
> 
> 2. **Résilience** : Si chat_service crash, battle_service continue à fonctionner. Kafka stocke les events 'turn_played' et chat les consomme quand il redémarre. En monolithe, tout crasherait.
> 
> 3. **Séparation domaines métier** : Authentification, gestion équipes, combat, chat sont des domaines distincts avec des données indépendantes (database per service). Chaque service a sa propre base PostgreSQL.
> 
> 4. **Travail en équipe** : On était 3 devs. Chacun pouvait travailler sur son service sans conflits Git. En monolithe, on aurait eu beaucoup de merge conflicts.
> 
> Le compromis c'est la complexité accrue (Docker, Kafka, Kubernetes), mais c'est acceptable pour un projet de cette envergure et ça correspond aux objectifs pédagogiques du cours."

---

#### Q2 : "Pourquoi Kafka entre battle et chat, et pas REST ?"

**TA RÉPONSE :**
> "J'ai choisi Kafka pour la communication battle → chat parce que :
> 
> 1. **Asynchrone** : battle_service publie 'turn_played' et continue immédiatement sans attendre chat. Avec REST, battle devrait attendre la réponse de chat (50-100ms), ce qui ralentirait le jeu.
> 
> 2. **Découplage** : battle ne connaît pas chat. Si on ajoute un service notification ou logs, il suffit qu'il écoute le même topic Kafka. Avec REST, il faudrait modifier battle pour appeler le nouveau service.
> 
> 3. **Résilience** : Si chat_service est down (déploiement, crash), Kafka stocke les events. Quand chat redémarre, il consomme tous les events manqués. Avec REST, ces events seraient perdus (ERROR 500).
> 
> 4. **Pattern standard** : Pour les événements métier ('turn_played', 'battle_ended'), Kafka est le standard en microservices. C'est du SAGA Choreography.
> 
> REST aurait été plus simple à implémenter, mais avec un couplage fort et sans résilience."

---

#### Q3 : "Pourquoi 5 services et pas 3 ou 10 ?"

**TA RÉPONSE :**
> "5 services c'est un compromis entre simplicité et bénéfices microservices :
> 
> **Pourquoi pas fusionner en 3 :**
> - Si je fusionne auth + team → Problème : team dépend de auth (JWT), mais auth ne dépend pas de team. Fusion créerait un service trop gros avec 2 domaines non liés.
> - Si je fusionne battle + chat → Problème : Battle = calculs lourds, Chat = WebSocket connexions persistantes. Technologies et charges trop différentes.
> 
> **Pourquoi pas découper en 10+ :**
> - On était 3 devs, 10 services = trop complexe à gérer
> - Overhead Docker/Kubernetes : chaque service = 1 deployment, 1 service K8s, 1 BDD
> - Latence réseau : Plus de services = plus d'appels réseau
> 
> **5 services = sweet spot :**
> - Chaque service a un domaine métier clair
> - Scalabilité indépendante là où c'est nécessaire (battle, chat)
> - Complexité gérable pour une équipe de 3
> - Résilience entre services critiques (battle ↔ chat)"

---

#### Q4 : "Pourquoi database per service et pas une seule BDD ?"

**TA RÉPONSE :**
> "Database per service pour 3 raisons :
> 
> 1. **Autonomie** : Chaque service gère ses propres données. battle_service peut changer son schéma BDD sans impacter team_service. C'est le principe microservices : indépendance totale.
> 
> 2. **Scalabilité** : battle_db peut être sur un serveur puissant (beaucoup d'écritures), auth_db sur un serveur moins cher (peu d'écritures). Avec 1 seule BDD, impossible d'optimiser séparément.
> 
> 3. **Résilience** : Si battle_db crash, team_service continue à fonctionner avec team_db. Avec 1 seule BDD, tout crashe.
> 
> **Inconvénient :** Pas de JOIN SQL entre tables de services différents. Par exemple, pour récupérer 'user.username + team.name', il faut 2 requêtes (auth puis team). C'est acceptable car ce pattern est rare dans notre projet.
> 
> **Alternative rejetée :** BDD partagée aurait créé un couplage fort au niveau des données, ce qui casse le principe microservices."

---

#### Q5 : "C'est pas overkill pour un projet étudiant ?"

**TA RÉPONSE :**
> "C'est un compromis conscient entre apprentissage et réalisme :
> 
> **Oui, c'est plus complexe qu'un monolithe :**
> - Docker Compose : 8 conteneurs (5 services + 3 infra)
> - Kubernetes : 15+ manifests YAML
> - Kafka : Broker + Zookeeper + gestion topics
> - Temps de développement : +30% vs monolithe
> 
> **Mais c'est justifié :**
> 1. **Objectif pédagogique** : Le cours s'appelle 'Microservices', pas 'Monolithe'. L'objectif est d'apprendre l'architecture distribuée.
> 2. **Réalisme industriel** : Les vrais jeux multijoueurs (League of Legends, Fortnite) utilisent cette architecture. C'est un projet portfolio.
> 3. **Compétences recherchées** : Docker, Kubernetes, Kafka sont dans 80% des offres d'emploi backend.
> 
> **On aurait pu simplifier :**
> - Fusionner en 3 services (auth+team, battle, chat+pokedex)
> - Utiliser REST partout (pas de Kafka)
> - Déployer sur 1 seul serveur (pas de K8s)
> 
> Mais on aurait perdu les bénéfices microservices (scalabilité, résilience) et l'apprentissage des outils standards."

---

### ✅ CHECKLIST FINALE "JE MAÎTRISE L'ARCHITECTURE"

- [ ] Je peux expliquer SAGA Choreography vs Orchestration
- [ ] Je peux justifier pourquoi 5 services et pas 3 ou 10
- [ ] Je peux expliquer pourquoi Kafka entre battle et chat
- [ ] Je peux expliquer pourquoi REST entre frontend et services
- [ ] Je peux expliquer pourquoi WebSocket pour le chat
- [ ] Je peux expliquer pourquoi database per service
- [ ] Je peux expliquer la méthode pour choisir ses services (5 étapes)
- [ ] Je peux citer des alternatives et pourquoi je les ai rejetées
- [ ] Je peux dessiner l'architecture complète de mémoire
- [ ] Je peux expliquer le flow d'un tour de bataille (battle → Kafka → chat → WebSocket)

**Si 1 seul ❌ → Relis les sections correspondantes**

---

## 📚 RESSOURCES COMPLÉMENTAIRES

### Pour approfondir SAGA
- **TP4 Kafka** : Flow complet order → inventory → payment avec compensation
- **FICHE 4** : Section SAGA avec exemples concrets

### Pour approfondir microservices
- **FICHE 1** : Monolithe vs Microservices, avantages/inconvénients
- **GUIDE_BATTLE_CHAT_SERVICES.md** : Détail technique de tes 2 services

### Pour approfondir Kafka
- **FICHE 4** : Producer/Consumer, topics, retry exponential backoff
- **TON CODE** : `chat_service/app/main.py` kafka_consumer_loop()

---

**🎯 Prochaine étape : Fais le QUIZ pour tester ta compréhension !** 💪
