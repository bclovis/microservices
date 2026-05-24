# S6 — Projet Final : PokeDrafter

> Projet : ICC ING3 Microservices — 2026  
> Deadline originale : 30 avril 2026  
> Équipe : Abdellatif, Alaa, **Betsaleel**  
> Repository : https://github.com/abdemeh/PokeDrafter  
> Sujet : `Projet Micro ICC 2026.pdf`

---

## 1. Description du projet

**PokeDrafter** est un jeu de stratégie Pokémon multijoueur en temps réel. Deux joueurs — une équipe **Rouge** et une équipe **Bleue** — construisent des équipes de 6 Pokémon et s'affrontent dans des duels au tour par tour.

L'avantage entre deux Pokémon est calculé par **correspondance de types** selon la formule F(A).

### Modes de jeu

| Mode | Description |
|------|-------------|
| **Constructed** | Chaque joueur amène une équipe pré-construite |
| **Random** | Les équipes sont générées aléatoirement |
| **Draft** | Les joueurs choisissent à tour de rôle parmi 12 Pokémon |

---

## 2. La formule F(A) — Cœur du jeu

### Définition mathématique (du cours/projet)

$$F(A) = \sum_{w \in A} \left[\prod_{y \in B} \text{get\_multiplier}(w, y)\right]$$

Pour deux Pokémon avec respectivement des types :
- **A** : types W et X (ou W·W si mono-type)
- **B** : types Y et Z (ou Y·Y si mono-type)

$$F(A) = 1 \times \text{mult}(W/Y) \times \text{mult}(W/Z) + 1 \times \text{mult}(X/Y) \times \text{mult}(X/Z)$$

$$F(B) = 1 \times \text{mult}(Y/W) \times \text{mult}(Y/X) + 1 \times \text{mult}(Z/W) \times \text{mult}(Z/X)$$

**Résultat :**
- Si F(A) > F(B) → B est KO
- Si F(B) > F(A) → A est KO
- Si F(A) = F(B) → les deux sont KO ("draw")

### Exemple du cours
Dracaufeu (Feu/Vol) vs Laggron (Eau/Sol) :  
F(Dracaufeu) = 1.5, F(Laggron) = 2.0 → Dracaufeu est KO

### Code réel : `battle_service/app/services/battle_engine.py`

```python
# get_multiplier : récupère le multiplicateur du tableau des types
def get_multiplier(atk, defense):
    row = TYPE_CHART.get(atk)
    if row is None:
        return 1.0
    return row.get(defense, 1.0)


def calc_advantage(types_a, types_b):
    """
    Calcule F(A) et F(B) selon la formule du projet.
    Si mono-type, le type est doublé : [type1, type1]
    """
    if not types_a or not types_b:
        return 0.0, 0.0

    # Mono-type → dupliquer le type
    ta = types_a if len(types_a) == 2 else [types_a[0], types_a[0]]
    tb = types_b if len(types_b) == 2 else [types_b[0], types_b[0]]

    fa = 0.0
    for w in ta:
        val = 1.0
        for y in tb:
            val *= get_multiplier(w, y)   # Multiplier chaque type de B
        fa += val                          # Additionner pour chaque type de A

    fb = 0.0
    for y in tb:
        val = 1.0
        for w in ta:
            val *= get_multiplier(y, w)
        fb += val

    return round(fa, 4), round(fb, 4)


def resolve_turn(types_a, types_b):
    """
    Retourne "A", "B" ou "draw" selon F(A) vs F(B)
    """
    fa, fb = calc_advantage(types_a, types_b)
    if fa > fb:
        return "A"
    if fb > fa:
        return "B"
    return "draw"
```

---

## 3. Architecture complète

```
┌─────────────────────────────────────────────┐
│  CLIENT LAYER                                │
│  Angular 17 Frontend (Port 4300)             │
└──────────────────────┬──────────────────────┘
                       │ HTTP / WebSocket
         ┌─────────────▼─────────────┐
         │     NGINX API GATEWAY      │
         │         Port 80            │
         │  /api/auth/*  → :8001      │
         │  /api/teams/* → :8002      │
         │  /api/battle/*→ :8003      │
         │  /api/pokedex/*→:8004      │
         │  /api/chat/* → :8005       │
         └──────────────┬────────────┘
                        │
    ┌──────┬────────┬───┴────┬──────────┐
    │      │        │        │          │
  :8001  :8002    :8003    :8004      :8005
  AUTH   TEAM   BATTLE   POKEDEX     CHAT
  (JWT)  (CRUD) (Engine) (Redis+API) (WS+Kafka)
    │      │        │                   │
 auth_db team_db battle_db   Redis   (Kafka)
                              │
                         PokéAPI externe
                      (pokeapi.co)

KAFKA Cluster (Apache Kafka + Zookeeper)
    ← battle_service (producer + consumer)
    ← chat_service (fan-out)
    ← team_service (team.updates)
    ← auth_service (user.events)
```

### Communication inter-backends (Rouge ↔ Bleu)
```
Red Backend
    │ Sérialise action en JSON
    │ Chiffre avec Fernet(SHARED_SECRET_KEY)
    ▼
Kafka topic: battle.action.red
    │
    ▼
Blue Backend
    │ Déchiffre avec Fernet(SHARED_SECRET_KEY)
    │ Traite l'action
    ▼
Kafka topic: battle.action.blue
    │
    ▼
Red Backend (reçoit la réponse chiffrée)
```

> **⚠️ Contrainte critique :** Les backends Rouge et Bleu ne communiquent JAMAIS directement. Tout transite par Kafka et est **chiffré avec Fernet**.

---

## 4. Services — Description détaillée

### Auth Service (Port 8001) — Alaa
- **Responsabilité** : Inscription, connexion, JWT
- **BDD** : `auth_db` (PostgreSQL)
- **Routes** : POST /register, POST /login, GET /me, PUT /profile
- **Technos** : JWT (python-jose), bcrypt, SQLAlchemy

### Team Service (Port 8002) — Alaa
- **Responsabilité** : CRUD équipes + recommandations IA
- **BDD** : `team_db` (PostgreSQL)
- **Routes** : GET/POST/PUT/DELETE /teams, POST /teams/{id}/complete
- **Event Kafka** : publie `team.updates` quand une équipe change

### Battle Service (Port 8003) — **Betsaleel**
- **Responsabilité** : Moteur de combat F(A), orchestration des tours, gestion des sessions de battle
- **BDD** : `battle_db` (PostgreSQL)
- **Routes** : POST /battle/start, POST /battle/action, GET /battle/{id}
- **Kafka** : Producteur + Consommateur pour `battle.action.red` / `battle.action.blue` / `battle.result`
- **Chiffrement** : Messages chiffrés avec Fernet avant publication Kafka

### Pokédex Service (Port 8004) — Alaa
- **Responsabilité** : Proxy vers PokéAPI externe + mise en cache Redis
- **BDD** : Redis (cache)
- **Routes** : GET /pokemon, GET /pokemon/{id}, GET /types
- **Pattern** : Check Redis → si pas en cache → appel PokéAPI → mise en cache

### Chat Service (Port 8005) — **Betsaleel**
- **Responsabilité** : Chat temps réel par WebSocket, groupé par équipe
- **WebSocket** : `ws://host/ws/chat/{team}?username=...`
- **Kafka** : Fan-out des messages (scalabilité)
- **Connexions** : Gérées en mémoire par dictionnaire `{team: [WebSocket, ...]}`

---

## 5. Topics Kafka du projet

| Topic | Producteur | Consommateur | Description |
|-------|-----------|-------------|-------------|
| `battle.action.red` | Red Battle Service | Blue Battle Service | Action du joueur Rouge (chiffrée) |
| `battle.action.blue` | Blue Battle Service | Red Battle Service | Action du joueur Bleu (chiffrée) |
| `battle.result` | Battle Service | Frontend (via WS) | Résultat d'un tour |
| `chat.messages` | Chat Service | Chat Service (toutes instances) | Fan-out messages chat |
| `team.updates` | Team Service | Battle Service | Notification changement d'équipe |
| `user.events` | Auth Service | Tous les services | Événements inscription/MAJ utilisateur |

---

## 6. Code clé de Betsaleel

### battle_service : Kafka Producer (aiokafka)

```python
# battle_service/app/services/kafka_service.py
import json
import logging
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)
_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    """Singleton producer — créé une fois au démarrage"""
    global _producer
    if _producer is None:
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            # Sérialiser automatiquement en bytes JSON
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await p.start()   # Connexion async au broker Kafka
        _producer = p
    return _producer


async def publish_battle_event(event_type: str, data: dict) -> None:
    """Publier un événement de combat sur Kafka"""
    global _producer
    try:
        producer = await get_producer()
        payload = {"type": event_type, **data}  # Merge type + données
        # send_and_wait = attend confirmation de la réception par Kafka
        await producer.send_and_wait(settings.KAFKA_TOPIC_BATTLE, payload)
    except Exception as exc:
        # Si Kafka est down → on log sans crasher le service
        _producer = None
        logger.warning("Kafka unavailable, event dropped: %s", exc)


async def stop_producer() -> None:
    """Fermer proprement le producer au shutdown"""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
```

### chat_service : WebSocket + rooms par équipe

```python
# chat_service/app/services/chat_service.py
from collections import defaultdict
from typing import Dict, List
from fastapi import WebSocket

# Connexions groupées par équipe ("red" ou "blue")
_connections: Dict[str, List[WebSocket]] = defaultdict(list)


async def connect(team: str, ws: WebSocket):
    """Accepter et enregistrer une connexion WebSocket"""
    await ws.accept()
    _connections[team].append(ws)


def disconnect(team: str, ws: WebSocket):
    """Supprimer une connexion de la liste"""
    try:
        _connections[team].remove(ws)
    except ValueError:
        pass


async def broadcast(team: str, message: dict):
    """Envoyer un message JSON à tous les clients d'une équipe"""
    if team not in _connections:
        return
    dead = []
    for ws in _connections[team]:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)         # Connexion morte
    for ws in dead:
        disconnect(team, ws)        # Nettoyer les connexions mortes


async def broadcast_all(message: dict):
    """Envoyer à TOUTES les équipes (rouge + bleu)"""
    for team in ["red", "blue"]:
        await broadcast(team, message)
```

### chat_service : Routes WebSocket

```python
# chat_service/app/routes/chat.py
@router.websocket("/ws/chat/{team}")
async def chat_endpoint(team: str, username: str, websocket: WebSocket):
    """
    WebSocket : ws://host/ws/chat/red?username=Toto
    Connecte et broadcast les messages à l'équipe
    """
    if team not in ("red", "blue"):
        await websocket.close(code=1003)   # 1003 = données non acceptables
        return

    await chat_service.connect(team, websocket)
    
    # Message de bienvenue
    await chat_service.broadcast(team, {
        "author": "bot",
        "content": f"{username} a rejoint le chat",
        "is_bot": True
    })

    try:
        while True:
            data = await websocket.receive_text()    # Écouter en boucle
            msg = {"author": username, "content": data, "is_bot": False, "team": team}
            await chat_service.broadcast(team, msg)  # Broadcaster à l'équipe
    except WebSocketDisconnect:
        chat_service.disconnect(team, websocket)
        await chat_service.broadcast(team, {
            "author": "bot",
            "content": f"{username} a quitté le chat",
            "is_bot": True
        })
```

### battle_service : Application principale

```python
# battle_service/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.routes.battle import router as battle_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook : initialise la DB au démarrage"""
    await init_db()
    yield          # ← Le serveur tourne ici

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,  # ← Utiliser le nouveau système lifespan (FastAPI ≥ 0.93)
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.include_router(battle_router, prefix="/api/battle")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "battle"}
```

---

## 7. Chiffrement inter-backends avec Fernet

**Fernet** = chiffrement symétrique AES (bibliothèque `cryptography`).

```python
from cryptography.fernet import Fernet

# Générer une clé (à stocker dans un Secret Kubernetes)
key = Fernet.generate_key()   # ex: b'ZmDfcTF7_60GrrY167zsiPd_GbM4yXL0CfA...='
fernet = Fernet(key)

# Chiffrer avant d'envoyer sur Kafka
plaintext = json.dumps({"action": "attack", "pokemon_id": 5}).encode()
encrypted = fernet.encrypt(plaintext)   # → bytes

# Déchiffrer après réception de Kafka
decrypted = fernet.decrypt(encrypted)   # → bytes
data = json.loads(decrypted.decode())
```

**Pourquoi chiffrer ?**  
→ Red et Blue sont des équipes **séparées** avec leurs propres serveurs.  
→ Les données de battle ne doivent pas être lisibles par un tiers qui écouterait le topic Kafka.  
→ Contrainte explicite du sujet : "data chiffrée entre backends"

---

## 8. Démarrage du projet (Docker Compose)

```bash
# Depuis infra/docker/
cd infra/docker
docker compose up --build -d

# Démarrer le frontend Angular
cd ../../web
npm install
npm start -- --port 4300
```

**Accès :**
- Dashboard : http://localhost:4300
- API Docs (Swagger) : http://localhost:80/docs

### Utilisateurs préexistants (README)

| Pseudo | Couleur | Email | Password |
|--------|---------|-------|----------|
| `red_trainer` | Rouge | red@pokedrafter.com | `RedTeam123!` |
| `blue_trainer` | Bleu | blue@pokedrafter.com | `BlueTeam123!` |
| `admin` | — | admin@pokedrafter.com | `Admin123!` |

---

## 9. Contraintes critiques du sujet

| Contrainte | Implémentation |
|-----------|---------------|
| Front + back différents par couleur | Angular (port 4300/4301), backends séparés (rouge/bleu) |
| Data chiffrée entre backends | Fernet (AES symétrique) sur tous les messages Kafka inter-team |
| Logs accessibles admin | Endpoint admin dans les services + console de logs |
| BDD persistante (volumes) | Volumes Docker dans docker-compose.yml |
| Tests frontend | Jasmine/Karma sur components Angular |
| Users préexistants dans README | ✅ (voir tableau ci-dessus) |

---

## 10. Stack technique résumée

| Couche | Technologie |
|--------|------------|
| Frontend | Angular 17, TailwindCSS, RxJS |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 |
| Messagerie | Apache Kafka (aiokafka) |
| Base de données | PostgreSQL 16, Redis 7 |
| Gateway | Nginx |
| Conteneurs | Docker Compose, Kubernetes |
| Auth | JWT (python-jose), bcrypt |
| Chiffrement | Fernet (cryptography) |
| Source données | PokéAPI (pokeapi.co) |

---

## 11. Répartition du travail de Betsaleel

| Semaine | Tâches |
|---------|--------|
| Semaine 1 | Docker setup (docker-compose.yml), Kafka + Zookeeper config, Battle Service skeleton, DB setup |
| Semaine 2 | Battle Engine (formule F(A)), Kafka producer/consumer, chiffrement Fernet, WebSocket server |
| Semaine 3 | Chat Service (WebSocket + Kafka fan-out), Kubernetes manifests (deployments, services, PVCs) |
| Semaine 4 | Deploy script, k8s namespace config, tests end-to-end, monitoring/logs, endpoint admin |

**Livrables de Betsaleel :**
- Docker Compose complet pour le dev local
- Manifests Kubernetes pour le déploiement
- Battle engine avec calcul de types F(A)
- Pipeline Kafka events (chiffrée)
- Chat service avec WebSocket
- Automatisation du déploiement

---

## 12. Questions d'oral probables

**Q: Expliquez la formule F(A) du projet.**  
R: Pour chaque type du Pokémon A, on multiplie les multiplicateurs contre chaque type de B, puis on additionne. Si mono-type, on duplique le type. Le Pokémon avec le F le plus bas est KO. Si égalité, les deux sont KO.

**Q: Pourquoi utiliser Kafka entre les backends Rouge et Bleu ?**  
R: Les deux backends sont déployés séparément (deux équipes différentes). Kafka permet une communication asynchrone sans couplage direct. De plus, les messages sont chiffrés avec Fernet avant publication, ce qui garantit que même si quelqu'un lit le topic Kafka, les données de battle restent confidentielles.

**Q: Comment fonctionne le Chat Service ?**  
R: WebSocket Python avec FastAPI. Les connexions sont regroupées par équipe dans un dictionnaire `{team: [WebSocket, ...]}`. Quand un message arrive, il est broadcasté à tous les WebSockets de l'équipe. Kafka est utilisé pour la scalabilité (fan-out entre plusieurs instances du service).

**Q: Quelle est la différence entre aiokafka et kafka-python ?**  
R: `aiokafka` est asynchrone (async/await, compatible FastAPI). `kafka-python` est synchrone. Pour FastAPI, on préfère `aiokafka` pour ne pas bloquer la boucle d'événements.

**Q: Pourquoi utiliser `lifespan` dans FastAPI au lieu de `@app.on_event("startup")` ?**  
R: `@app.on_event` est déprécié depuis FastAPI 0.93. `lifespan` avec `asynccontextmanager` est la nouvelle approche recommandée. Le code avant `yield` = startup, après `yield` = shutdown.

**Q: Comment est géré le chiffrement Fernet dans le projet ?**  
R: Les deux backends partagent une même clé symétrique (`SHARED_SECRET_KEY`) stockée dans un Secret Kubernetes. Avant d'envoyer sur Kafka, le backend sérialise l'action en JSON puis chiffre avec `Fernet.encrypt()`. L'autre backend déchiffre avec `Fernet.decrypt()`.
