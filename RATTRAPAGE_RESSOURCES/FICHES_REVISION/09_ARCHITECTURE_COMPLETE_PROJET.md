# 🏗️ FICHE 09 : ARCHITECTURE COMPLÈTE DE POKEDRAFTER
> Basée à 100% sur `PokeDrafter_GitHub_Latest` — tout ce qui est dit ici existe dans le vrai code.

---

## 1. VUE D'ENSEMBLE — Ce qu'on a construit

### 1a. Flux vertical : Client → Nginx → Services → Stockage

```
     ┌──────────────────────────────────────────────────────────────────────┐
     │                       INTERNET / FRONTEND                             │
     └───────────────────────────────┬──────────────────────────────────────┘
                                     │ :80
     ┌───────────────────────────────▼──────────────────────────────────────┐
     │                        NGINX GATEWAY :80                              │
     │   /api/auth  /api/teams  /api/battle  /api/pokedex  /api/chat  /ws/  │
     │              (Routing uniquement — PAS de vérification JWT)          │
     └────┬──────────────┬──────────────┬──────────────┬──────────────┬─────┘
          │              │              │              │              │
          ▼              ▼              ▼              ▼              ▼
   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
   │    auth    │ │    team    │ │   battle   │ │  pokedex   │ │    chat    │
   │   :8001    │ │   :8002    │ │   :8003    │ │   :8004    │ │   :8005    │
   └──────┬─────┘ └──────┬──┬──┘ └──────┬─────┘ └───┬────┬───┘ └──────┬──┬─┘
          │              │  │           │            │    │            │  │
          ▼              ▼  │           ▼            │    ▼            │  ▼
      [auth_db]      [team_db]│      [battle_db]     │  [Redis]        │ [chat_db]
                             │                       │  (cache 24h)   │
                             └──── httpx REST ───────►                │
                                  (synchrone)      [pokeapi.co]       │
                                                                       │
                    ┌──────────────────────────────┐                  │
     Kafka producer │         KAFKA :29092          │ Kafka consumer   │
     (battle_svc) ──►   ● topic: battle-events      ├──────────────────┘
                    │   ● topic: chat-messages      │   (chat_svc lit les 2 topics,
                    └──────────────────────────────┘    route via msg.topic)

### 1b. Connexions inter-services (qui appelle qui)

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │ APPEL REST (synchrone — team_service a besoin de la réponse tout de suite) │
  └──────────────────────────────────────────────────────────────────────┘

     team_service ──── httpx GET ────► pokedex_service ──── httpx GET ────► pokeapi.co
        :8002                              :8004                            (API externe)
     "donne-moi                        "je cherche dans                  "voici les données
      des Pokémon"                      Redis d'abord,                    Pokémon brutes"
                                        sinon j'appelle
                                        pokeapi.co"


  ┌──────────────────────────────────────────────────────────────────────┐
  │ KAFKA (asynchrone — battle publie, chat consomme, ils se connaissent pas) │
  └──────────────────────────────────────────────────────────────────────┘

     battle_service ──► KAFKA :29092 ──► chat_service
        :8003          ┌─────────────┐      :8005
    "un tour a été      │battle-events│   "je reçois l'event,
     joué, je publie"   │chat-messages│    je regarde msg.topic,
                        └─────────────┘    je broadcast en WebSocket"

     chat_service ───► KAFKA :29092   (chat publie aussi sur chat-messages
        :8005          chat-messages   quand un user envoie un message)
```

---

## 2. LES 5 SERVICES — Rôle + Fichiers vrais

### Structure TYPE d'un service (ce qu'on retrouve dans TOUS les services)

```
api/[nom]_service/
├── app/
│   ├── main.py              ← Point d'entrée FastAPI (lifespan, routes, CORS)
│   ├── dependencies.py      ← JWT auth (get_current_user) + get_db
│   ├── core/
│   │   ├── config.py        ← Variables d'environnement (Settings Pydantic)
│   │   ├── database.py      ← Connexion SQLAlchemy async + init_db()
│   │   └── security.py      ← JWT encode/decode (auth_service uniquement)
│   ├── models/              ← Tables SQLAlchemy (ce qui est en BDD)
│   ├── schemas/             ← Pydantic (validation requête / réponse)
│   ├── routes/              ← Les endpoints FastAPI
│   └── services/            ← La logique métier (séparé des routes)
├── Dockerfile
└── requirements.txt
```

**Pourquoi cette structure ?**
> On sépare : "ce qui reçoit" (routes) de "ce qui calcule" (services) de "ce qui stocke" (models). Chaque couche a une responsabilité unique.

---

### 2.1 `auth_service` — Port 8001 — BDD `auth_db`

**Rôle :** Gérer les comptes et émettre des JWT.

**Fichiers clés :**
```
app/
├── core/security.py     ← bcrypt (hash mdp) + JWT (create/decode)
├── routes/auth.py       ← POST /api/auth/register, /login, /refresh, /me
├── models/user.py       ← Table users (id, username, email, hashed_password)
└── services/auth_service.py ← Logique register/login
```

**Ce qui est important :**
```python
# core/security.py — JWT avec python-jose
def create_access_token(subject: str) -> str:
    return _create_token({"sub": subject, "type": "access"},
                          timedelta(seconds=settings.JWT_EXPIRATION))  # 3600s

def create_refresh_token(subject: str) -> str:
    return _create_token({"sub": subject, "type": "refresh"},
                          timedelta(seconds=settings.JWT_REFRESH_EXPIRATION))  # 86400s
```

**Lifespan :**
```python
async def lifespan(app):
    await init_db()   # Crée les tables
    yield
```

---

### 2.2 `team_service` — Port 8002 — BDD `team_db`

**Rôle :** Gérer les équipes Pokémon des joueurs.

**Fichiers clés :**
```
app/
├── routes/team.py       ← GET/POST/PUT/DELETE /api/teams/
├── models/team.py       ← Table teams + table team_pokemon
├── services/team_service.py ← Logique + appel REST vers pokedex_service
└── core/config.py       ← POKEDEX_SERVICE_URL: "http://localhost:8004"
```

**Ce qui est important — appel inter-service REST :**
```python
# services/team_service.py — team_service appelle pokedex_service
async def complete_team(self, db, team_id, user_id):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.POKEDEX_SERVICE_URL}/api/pokedex/random/{slots_needed * 3}"
        )
        pool = resp.json()
    # Choisit les Pokémon depuis le pool retourné
```

**Pourquoi REST ici et pas Kafka ?**
> `team_service` a besoin de la réponse IMMÉDIATEMENT (compléter une équipe = l'utilisateur attend le résultat) → synchrone.

---

### 2.3 `battle_service` — Port 8003 — BDD `battle_db`

**Rôle :** Gérer les batailles, calculer les scores, publier dans Kafka.

**Fichiers clés :**
```
app/
├── routes/battle.py          ← 8 endpoints (open, create, join, turn, end, forfeit, get, history)
├── models/battle.py          ← Table Battle + Table BattleTurn
├── services/
│   ├── battle_engine.py      ← calc_advantage() + resolve_turn() (pur calcul, pas de BDD)
│   └── kafka_service.py      ← Producer Kafka (singleton _producer)
└── core/config.py            ← KAFKA_BOOTSTRAP_SERVERS: "kafka:29092", KAFKA_TOPIC_BATTLE: "battle-events"
```

**Ce qui est important — séparation des responsabilités :**
```python
# battle_engine.py = CALCUL PUR (aucune dépendance BDD ou Kafka)
def calc_advantage(types_a, types_b):
    fa, fb = 0.0, 0.0
    for w in types_a:
        val = 1.0
        for y in types_b:
            val *= get_multiplier(w, y)
        fa += val
    for y in types_b:
        val = 1.0
        for w in types_a:
            val *= get_multiplier(y, w)
        fb += val
    return round(fa, 4), round(fb, 4)

def resolve_turn(types_a, types_b):
    fa, fb = calc_advantage(types_a, types_b)
    if fa > fb: return "A"
    if fb > fa: return "B"
    return "draw"
```

**Lifespan :**
```python
async def lifespan(app):
    await init_db()   # Crée les tables Battle + BattleTurn
    yield
# PAS de Kafka ici — le producer est lazy (créé au 1er appel)
```

---

### 2.4 `pokedex_service` — Port 8004 — PAS de BDD → Redis uniquement

**Rôle :** Proxy vers l'API externe PokeAPI avec cache Redis.

**Fichiers clés :**
```
app/
├── routes/pokedex.py         ← GET /api/pokedex/{id}, /search, /random/{n}
├── core/cache.py             ← Singleton Redis async
└── services/pokeapi_service.py ← Appel httpx vers pokeapi.co + cache
```

**Ce qui est important — PAS de BDD :**
```python
# core/cache.py — Redis comme seul stockage
async def cache_get(key: str):
    data = await redis.get(key)
    return json.loads(data) if data else None

async def cache_set(key: str, value: Any, ttl: int = 86400):  # TTL 24h
    await redis.setex(key, ttl, json.dumps(value))
```

**Pourquoi Redis et pas PostgreSQL ?**
> Les données Pokémon sont en lecture seule et viennent d'une API externe. On n'a pas besoin de les modifier. Redis avec TTL 24h évite d'appeler PokeAPI à chaque requête.

**Lifespan :**
```python
async def lifespan(app):
    yield
    await close_redis()   # Ferme la connexion Redis proprement
# Pas de init_db() — pas de BDD
```

---

### 2.5 `chat_service` — Port 8005 — BDD `chat_db`

**Rôle :** WebSocket temps réel + Consumer Kafka (2 topics) + persistance des messages.

**Fichiers clés :**
```
app/
├── main.py                  ← lifespan (init_db + kafka_consumer_loop + stop_producer)
├── routes/chat.py           ← WebSocket /ws/{team}, GET /api/chat/history
├── models/message.py        ← Table Message (room, author, content, is_bot, team)
└── services/chat_service.py ← Producer Kafka + broadcast WebSocket + get_history()
```

**Ce qui est important — subscribe à 2 topics :**
```python
# main.py — consumer écoute battle-events ET chat-messages
consumer = AIOKafkaConsumer(
    settings.KAFKA_TOPIC_BATTLE,   # "battle-events"
    settings.KAFKA_TOPIC_CHAT,     # "chat-messages"
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    auto_offset_reset="latest",
)
async for msg in consumer:
    topic = msg.topic  # Routing selon la source
    if topic == settings.KAFKA_TOPIC_BATTLE:
        # Transformer l'event en notification bot
        await chat_service.broadcast_all(notif)
    elif topic == settings.KAFKA_TOPIC_CHAT:
        room = event.get("room")
        await chat_service.broadcast(room, event) if room else await chat_service.broadcast_all(event)
```

**Lifespan (le plus complet du projet) :**
```python
async def lifespan(app):
    await init_db()                                    # BDD chat_db
    task = asyncio.create_task(kafka_consumer_loop())  # Consumer en background
    yield
    task.cancel()                                      # Stop consumer
    await chat_service.stop_producer()                 # Ferme producer Kafka
```

---

## 3. L'INFRASTRUCTURE — Ce qui supporte les services

```
infra/
├── docker/docker-compose.yml   ← Tout en local (dev)
└── k8s/                        ← Kubernetes (prod)
    ├── namespace.yaml           ← namespace: pokedrafter
    ├── services.yaml            ← 5 Deployments + 5 Services (ClusterIP)
    ├── gateway.yaml             ← NodePort 30080
    └── kafka.yaml               ← Kafka + Zookeeper
```

### PostgreSQL — 4 BDD dans 1 instance (dev uniquement)
```yaml
postgres:
  environment:
    POSTGRES_MULTIPLE_DATABASES: auth_db,team_db,battle_db,chat_db
```
> En prod → chaque service aurait son PostgreSQL dédié. En dev on mutualise.

### Kafka — 2 topics, 1 broker
```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
# 29092 = réseau Docker interne (services entre eux)
# 9092  = exposé sur l'hôte (tests locaux)
```

---

## 4. LES 4 MODES DE COMMUNICATION DANS LE PROJET

| Mode | Qui → Qui | Pourquoi |
|------|-----------|----------|
| **REST sync** | Frontend → Nginx → Services | L'utilisateur attend la réponse |
| **REST sync** | `team_service` → `pokedex_service` | Besoin du résultat immédiatement |
| **Kafka async** | `battle_service` → `chat_service` | Notification non-critique, pas de blocage |
| **WebSocket** | `chat_service` → Frontend | Temps réel bidirectionnel |

---

## 5. LE JWT — Comment ça marche dans tout le projet

**Qui émet le JWT :** `auth_service` uniquement (via `core/security.py`)

**Qui vérifie le JWT :** Chaque service INDIVIDUELLEMENT via `dependencies.py`

```
Frontend
  │  POST /api/auth/login
  ▼
auth_service → retourne {access_token, refresh_token}

Frontend stocke le token, l'envoie dans chaque requête :
  Authorization: Bearer <token>

  ▼ Nginx (ne vérifie PAS le JWT — il route juste)
  ▼
battle_service/dependencies.py :
    async def get_current_user(credentials = Depends(bearer_scheme)):
        payload = decode_token(credentials.credentials)   # ← vérifie ici
        user_id = payload.get("sub")
        return await db.get(User, user_id)
```

**Pourquoi chaque service vérifie lui-même ?**
> Si Nginx vérifiait le JWT, il deviendrait un goulot d'étranglement. Chaque service est autonome et peut valider lui-même — cohérent avec le principe microservices.

---

## 6. LE FLOW COMPLET D'UNE BATAILLE (de A à Z)

```
1. CRÉER UN COMPTE
   POST /api/auth/register → auth_service → auth_db
   POST /api/auth/login    → auth_service → retourne JWT

2. CRÉER UNE ÉQUIPE
   POST /api/teams/        → team_service → team_db
   POST /api/teams/{id}/complete → team_service → httpx → pokedex_service
                                                         → pokeapi.co (ou Redis cache)

3. CRÉER UNE BATAILLE
   POST /api/battle/       → battle_service → battle_db (status="en_attente")

4. REJOINDRE
   POST /api/battle/{id}/join → battle_service → battle_db (status="en_cours")

5. JOUER UN TOUR
   POST /api/battle/{id}/turn
     → battle_service :
         1. calc_advantage(types_red, types_blue)   ← battle_engine.py
         2. resolve_turn()                           ← "A", "B" ou "draw"
         3. db.add(BattleTurn) ; await db.commit()  ← BDD AVANT Kafka
         4. publish_battle_event("turn_played", ...) ← Kafka
              │
              │ topic: battle-events
              ▼
         chat_service (consumer) :
              1. Reçoit event "turn_played"
              2. Formate notification bot
              3. broadcast_all() → WebSocket → tous les clients connectés

6. TERMINER LA BATAILLE
   POST /api/battle/{id}/end
     → battle_service :
         1. Compte wins_red / wins_blue / draw depuis les turns
         2. battle.winner = "red" ou "blue" ou "draw"
         3. battle.status = "termine"
         4. db.commit()
         (aucun event Kafka publié ici)
```

---

## 7. POURQUOI CES CHOIX — Justifications courtes

| Choix | Justification |
|-------|---------------|
| **5 services** | 1 responsabilité par service → Auth, Équipe, Bataille, Pokédex, Chat |
| **FastAPI** | Async natif (Python), auto-docs Swagger, Pydantic pour validation |
| **PostgreSQL** | Données relationnelles (users, teams, battles) — ACID nécessaire |
| **Redis** | Données read-only avec expiration naturelle (cache Pokédex 24h) |
| **Kafka** | Découplage battle→chat, résilience si chat down, event sourcing |
| **Nginx** | Point d'entrée unique, CORS centralisé, routing WebSocket |
| **4 BDD séparées** | Database-per-service : isolation, scalabilité, autonomie |
| **JWT dans chaque service** | Autonomie — pas de dépendance à auth_service pour valider |
| **httpx async** | Client HTTP async cohérent avec le reste du code FastAPI |
| **2 topics Kafka** | `battle-events` (battle→chat), `chat-messages` (chat→chat) — séparation des responsabilités |

---

## 8. CE QU'IL N'Y A PAS (à connaître pour l'oral)

| Ce qui manque | Pourquoi c'est absent | Amélioration possible |
|---------------|----------------------|----------------------|
| Healthchecks `pg_isready` | `depends_on` simple dans docker-compose | Ajouter `condition: service_healthy` |
| Event `battle_ended` dans Kafka | `end` route ne publie pas | Ajouter `publish_battle_event("battle_ended", ...)` |
| Rate limiting | Nginx n'a pas de `limit_req` | Ajouter dans nginx.conf |
| Auth centralisée dans Nginx | Chaque service valide son JWT | Acceptable en microservices |
| BDD propre à chaque service en prod | 1 PostgreSQL pour 4 BDD en dev | PostgreSQL dédié par service en prod |
