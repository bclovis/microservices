# 🔥 GUIDE BATTLE_SERVICE + CHAT_SERVICE (TES SERVICES)

> **Tu as fait** : battle_service, chat_service, Docker Compose, Nginx, Kubernetes  
> **Ce guide** : Maîtriser ces 2 services pour l'oral (15 min projet)

---

## 🎯 OBJECTIF

**À l'oral, tu dois pouvoir :**
1. Expliquer l'architecture des 2 services
2. Montrer le code clé (F(A), WebSocket, Kafka)
3. Justifier les choix techniques
4. Répondre aux questions pièges

**Temps de préparation recommandé : 2 jours (J5-J6)**

---

## ⚔️ SERVICE 1 : BATTLE_SERVICE

### Architecture du service

```
battle_service/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── routes/
│   │   └── battle.py        # Endpoints REST
│   ├── services/
│   │   ├── battle_engine.py # Logique F(A) et TYPE_CHART
│   │   └── kafka_service.py # Producer Kafka
│   ├── models/
│   │   └── battle.py        # SQLAlchemy (Battle, BattleTurn)
│   ├── schemas/
│   │   └── battle.py        # Pydantic validation
│   └── core/
│       ├── config.py        # Settings
│       └── database.py      # AsyncSession PostgreSQL
├── Dockerfile
└── requirements.txt
```

---

### Responsabilités principales

1. **Créer une bataille** (mode Draft/Constructed/Random)
2. **Gérer l'état** : en_attente → en_cours → termine
3. **Calculer F(A)** : Avantage de types avec TYPE_CHART
4. **Publier événements Kafka** : turn_played
5. **Forfait et fin de bataille**

---

### Endpoints REST (routes/battle.py)

#### 1. Créer une bataille

```python
POST /api/battle/battles
Body: {
  "player_red_id": "uuid",
  "player_blue_id": "uuid" (optionnel),
  "mode": "draft"
}

Response: {
  "id": "uuid",
  "player_red_id": "uuid",
  "player_blue_id": null,
  "status": "en_attente",  # ou "en_cours" si player_blue fourni
  "mode": "draft",
  "current_turn": 0
}
```

**Logique** :
- Si `player_blue_id` est fourni → status = "en_cours"
- Sinon → status = "en_attente" (salle ouverte)

**Code clé (simplifié)** :

```python
@router.post("/battles", response_model=BattleOut, status_code=status.HTTP_201_CREATED)
async def create_battle(payload: BattleCreate, db: AsyncSession = Depends(get_db)):
    status_initial = "en_cours" if payload.player_blue_id else "en_attente"
    battle = Battle(
        player_red_id=payload.player_red_id,
        player_blue_id=payload.player_blue_id,
        mode=payload.mode,
        status=status_initial,
    )
    db.add(battle)
    await db.commit()
    await db.refresh(battle)
    return battle
```

---

#### 2. Rejoindre une bataille (JOIN)

```python
POST /api/battle/battles/{battle_id}/join
Body: {
  "player_blue_id": "uuid"
}

Response: Battle avec status="en_cours"
```

**Validations** :
- ✅ Bataille doit être "en_attente"
- ✅ player_blue_id doit être null
- ✅ player_blue_id ≠ player_red_id (pas rejoindre sa propre salle)

**Code clé** :

```python
@router.post("/{battle_id}/join", response_model=BattleOut)
async def join_battle(battle_id: UUID, payload: BattleJoin, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status != "en_attente":
        raise HTTPException(status_code=400, detail="La salle n'est plus en attente")
    if battle.player_blue_id is not None:
        raise HTTPException(status_code=400, detail="La salle est déjà complète")
    if str(battle.player_red_id) == str(payload.player_blue_id):
        raise HTTPException(status_code=400, detail="Impossible de rejoindre sa propre salle")
    
    battle.player_blue_id = payload.player_blue_id
    battle.status = "en_cours"
    await db.commit()
    await db.refresh(battle)
    return battle
```

---

#### 3. Jouer un tour (TURN) - LE PLUS IMPORTANT

```python
POST /api/battle/battles/{battle_id}/turn
Body: {
  "pokemon_red": "Pikachu",
  "pokemon_blue": "Charizard",
  "types_red": ["Electrik"],
  "types_blue": ["Feu", "Vol"]
}

Response: {
  "turn_number": 1,
  "pokemon_red": "Pikachu",
  "pokemon_blue": "Charizard",
  "score_red": "3.0",
  "score_blue": "1.0",
  "result": "A"  # A = Rouge gagne, B = Bleu gagne, T = Égalité
}
```

**Logique** :
1. Calculer F(A) et F(B) avec `calc_advantage()`
2. Comparer : si F(A) > F(B) → result = "A"
3. Sauvegarder le tour en BDD
4. Incrémenter `current_turn`
5. Publier événement Kafka `turn_played`

**Code clé** :

```python
@router.post("/{battle_id}/turn", response_model=TurnResult)
async def play_turn(battle_id: UUID, payload: TurnPlay, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status == "termine":
        raise HTTPException(status_code=400, detail="La bataille est terminée")

    # Calculer F(A) et F(B)
    fa, fb = calc_advantage(payload.types_red, payload.types_blue)
    result = resolve_turn(payload.types_red, payload.types_blue)

    # Créer le tour en BDD
    turn_number = battle.current_turn + 1
    turn = BattleTurn(
        battle_id=battle_id,
        turn_number=turn_number,
        pokemon_red=payload.pokemon_red,
        pokemon_blue=payload.pokemon_blue,
        types_red=payload.types_red,
        types_blue=payload.types_blue,
        score_red=str(fa),
        score_blue=str(fb),
        result=result,
    )
    db.add(turn)
    battle.current_turn = turn_number
    await db.commit()
    await db.refresh(turn)

    # Publier sur Kafka
    await publish_battle_event("turn_played", {
        "battle_id": str(battle_id),
        "turn_number": turn_number,
        "pokemon_red": payload.pokemon_red,
        "pokemon_blue": payload.pokemon_blue,
        "score_red": str(fa),
        "score_blue": str(fb),
        "result": result,
    })

    return turn
```

---

### La formule F(A) (battle_engine.py)

**TYPE_CHART** = Table de multiplicateurs (18x18 types)

```python
TYPE_CHART = {
    "Feu": {
        "Plante": 2.0,   # Super efficace
        "Eau": 0.5,      # Peu efficace
        "Feu": 0.5,      # Peu efficace
        "Roche": 0.5,
        # ...
    },
    "Eau": {
        "Feu": 2.0,
        "Sol": 2.0,
        "Roche": 2.0,
        "Eau": 0.5,
        "Plante": 0.5,
        # ...
    },
    # ... 18 types au total
}
```

**Fonction calc_advantage()** :

```python
def calc_advantage(types_a: list[str], types_b: list[str]) -> tuple[float, float]:
    """
    Calcule F(A) et F(B) :
    Pour chaque type w de A, on multiplie get_multiplier(w, y) pour tous les
    types y de B, puis on additionne. Même chose en sens inverse pour fb.
    Fonctionne avec 1, 2 types ou plus — pas de doublement mono-type.
    """
    if not types_a or not types_b:
        return 0.0, 0.0

    fa = 0.0
    for w in types_a:
        val = 1.0
        for y in types_b:
            val *= get_multiplier(w, y)
        fa += val

    fb = 0.0
    for y in types_b:
        val = 1.0
        for w in types_a:
            val *= get_multiplier(y, w)
        fb += val

    return round(fa, 4), round(fb, 4)


def resolve_turn(types_a: list[str], types_b: list[str]) -> str:
    """Détermine le gagnant du tour"""
    fa, fb = calc_advantage(types_a, types_b)
    if fa > fb:
        return "A"    # Rouge gagne
    elif fb > fa:
        return "B"    # Bleu gagne
    else:
        return "draw"  # Égalité
```

**Exemple concret** :

Pikachu (Électrik) vs Gyarados (Eau, Vol)

```
types_a = ["Électrik"],  types_b = ["Eau", "Vol"]

F(A) — Pikachu attaque Gyarados :
  w = "Électrik" :
    get_multiplier("Électrik","Eau") = 2.0  (super efficace)
    get_multiplier("Électrik","Vol") = 2.0  (super efficace)
    val = 2.0 × 2.0 = 4.0
  fa = 4.0

F(B) — Gyarados attaque Pikachu :
  y = "Eau"  : get_multiplier("Eau","Électrik") = 1.0  (neutre) → fb += 1.0
  y = "Vol"  : get_multiplier("Vol","Électrik") = 1.0  (neutre) → fb += 1.0
  fb = 2.0

F(A) = 4.0 > F(B) = 2.0 → Rouge (Pikachu) gagne ! ⚡
```

---

### Kafka Producer (kafka_service.py)

**Publication d'événements** :

```python
import json
import logging
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await p.start()
        _producer = p
    return _producer


async def publish_battle_event(event_type: str, data: dict) -> None:
    global _producer
    try:
        producer = await get_producer()
        payload = {"type": event_type, **data}
        await producer.send_and_wait(settings.KAFKA_TOPIC_BATTLE, payload)
    except Exception as exc:
        # Kafka optionnel en dev — on reset le singleton et on log sans crasher
        _producer = None
        logger.warning("Kafka unavailable, event dropped: %s", exc)


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
```

**Topic Kafka** : `battle-events` (valeur de `settings.KAFKA_TOPIC_BATTLE`)

**Types d'événements** :
- `turn_played` : À chaque tour joué
- `battle_ended` : Fin de bataille
- `battle_started` : Début de bataille

---

#### 4. Forfait (FORFEIT)

```python
POST /api/battle/battles/{battle_id}/forfeit
Body: {
  "player_id": "uuid"
}

Response: {
  "detail": "Abandon enregistré",
  "winner": "blue"  # ou "red"
}
```

**Logique** :
- Si player_red abandonne → winner = "blue"
- Si player_blue abandonne → winner = "red"
- Status = "termine"

---

#### 5. Terminer la bataille (END)

```python
POST /api/battle/battles/{battle_id}/end

Response: {
  "winner": "red",  # "red", "blue", ou "draw"
  "wins_red": 4,
  "wins_blue": 2
}
```

**Logique** :
1. Compter les tours gagnés par chaque joueur
2. Le joueur avec le plus de tours gagnés = winner
3. Si égalité → "draw"

```python
@router.post("/{battle_id}/end")
async def end_battle(battle_id: UUID, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status == "termine":
        raise HTTPException(status_code=400, detail="Déjà terminée")

    # Compter les tours gagnés
    res = await db.execute(select(BattleTurn).where(BattleTurn.battle_id == battle_id))
    turns = res.scalars().all()

    if not turns:
        raise HTTPException(status_code=400, detail="Aucun tour joué")

    wins_red = sum(1 for t in turns if t.result == "A")
    wins_blue = sum(1 for t in turns if t.result == "B")

    if wins_red > wins_blue:
        battle.winner = "red"
    elif wins_blue > wins_red:
        battle.winner = "blue"
    else:
        battle.winner = "draw"

    battle.status = "termine"
    await db.commit()
    return {"winner": battle.winner, "wins_red": wins_red, "wins_blue": wins_blue}
```

---

### Modèles SQLAlchemy (models/battle.py)

```python
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Battle(Base):
    __tablename__ = "battles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_red_id = Column(UUID(as_uuid=True), nullable=False)
    player_blue_id = Column(UUID(as_uuid=True), nullable=True)
    mode = Column(String, nullable=False)  # "draft", "constructed", "random"
    status = Column(String, default="en_attente")  # "en_attente", "en_cours", "termine"
    winner = Column(String, nullable=True)  # "red", "blue", "draw"
    current_turn = Column(Integer, default=0)

class BattleTurn(Base):
    __tablename__ = "battle_turns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    battle_id = Column(UUID(as_uuid=True), ForeignKey("battles.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    pokemon_red = Column(String, nullable=False)
    pokemon_blue = Column(String, nullable=False)
    types_red = Column(JSON, nullable=False)  # ["Feu", "Vol"]
    types_blue = Column(JSON, nullable=False)
    score_red = Column(String, nullable=False)
    score_blue = Column(String, nullable=False)
    result = Column(String, nullable=False)  # "A", "B", "draw"
```

---

## 💬 SERVICE 2 : CHAT_SERVICE

### Architecture du service

```
chat_service/
├── app/
│   ├── main.py              # Point d'entrée + Kafka consumer loop
│   ├── routes/
│   │   └── chat.py          # WebSocket endpoints
│   ├── services/
│   │   └── chat_service.py  # Gestion connexions WS + broadcast
│   ├── models/
│   │   └── message.py       # SQLAlchemy (optionnel, historique)
│   ├── schemas/
│   │   └── message.py       # Pydantic
│   └── core/
│       ├── config.py
│       └── database.py
├── Dockerfile
└── requirements.txt
```

---

### Responsabilités principales

1. **WebSocket** : Connexion bidirectionnelle avec le frontend
2. **Chat en temps réel** : Messages entre joueurs
3. **Battle Log** : Afficher les événements de bataille
4. **Kafka Consumer** : Écouter `battle-events` et `chat-messages`
5. **Broadcast** : Envoyer les messages à tous les clients connectés

---

### WebSocket Endpoints (routes/chat.py)

#### 1. Chat par équipe

```python
ws://host/ws/chat/{team}?username=Betsaleel

Params:
- team: "red" ou "blue"
- username: Nom du joueur
```

**Logique** :
1. Valider que `team` est "red" ou "blue"
2. Connecter le WebSocket à la room correspondante
3. Écouter les messages du client
4. Publier sur Kafka pour que tous les clients reçoivent
5. Déconnecter proprement à la fin

**Code clé** :

```python
@router.websocket("/ws/chat/{team}")
async def chat_endpoint(
    websocket: WebSocket,
    team: str,
    username: str = Query(...)
):
    logger.info(f"New connection request: team={team}, username={username}")
    
    # Validation
    if team not in ("red", "blue"):
        logger.warning(f"Invalid team: {team}")
        await websocket.close(code=1003)
        return

    try:
        # Connexion
        await chat_service.connect(team, websocket)
        logger.info(f"Connected: {username} to {team}")
        
        # Boucle de réception
        while True:
            data = await websocket.receive_text()
            logger.info(f"Message from {username} ({team}): {data}")
            
            msg = {
                "author": username, 
                "content": data, 
                "is_bot": False, 
                "team": team
            }
            
            # Publier sur Kafka (tous les clients vont recevoir)
            await chat_service.publish_message(msg)
            
    except WebSocketDisconnect:
        logger.info(f"Disconnected: {username} from {team}")
        chat_service.disconnect(team, websocket)
    except Exception as e:
        logger.error(f"Error in chat_endpoint for {username}: {e}")
        chat_service.disconnect(team, websocket)
```

---

#### 2. Chat par bataille

```python
ws://host/ws/battle/{battle_id}?username=Betsaleel

Params:
- battle_id: UUID de la bataille
- username: Nom du joueur
```

**Logique** : Même principe mais la room = `battle_{battle_id}`

---

### Gestion des connexions (services/chat_service.py)

**Structure** :

```python
from fastapi import WebSocket
from typing import Dict, List

# Dictionnaire des connexions actives
# { "red": [ws1, ws2, ws3], "blue": [ws4, ws5], "battle_uuid": [ws6, ws7] }
active_connections: Dict[str, List[WebSocket]] = {}

async def connect(room: str, websocket: WebSocket):
    """Accepter la connexion et l'ajouter à la room"""
    await websocket.accept()
    if room not in active_connections:
        active_connections[room] = []
    active_connections[room].append(websocket)

def disconnect(room: str, websocket: WebSocket):
    """Retirer le WebSocket de la room"""
    if room in active_connections:
        active_connections[room].remove(websocket)
        if not active_connections[room]:
            del active_connections[room]

async def broadcast(room: str, message: dict):
    """Envoyer un message à tous les clients d'une room spécifique"""
    if room not in active_connections:
        return
    
    for connection in active_connections[room]:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Error broadcasting to {room}: {e}")

async def broadcast_all(message: dict):
    """Envoyer un message à TOUS les clients connectés (Battle Log)"""
    for room, connections in active_connections.items():
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to all: {e}")
```

---

### Kafka Consumer avec RETRY (main.py)

**LE PLUS IMPORTANT** : Le consumer doit être résilient !

```python
async def kafka_consumer_loop():
    """
    Boucle Kafka consumer avec retry automatique en cas de panne.
    Retry delay : 2s → 4s → 8s → 16s → 30s (max)
    """
    from aiokafka import AIOKafkaConsumer
    retry_delay = 2
    
    while True:
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,      # "battle-events"
            settings.KAFKA_TOPIC_CHAT,        # "chat-messages"
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,  # "kafka:29092"
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        
        try:
            await consumer.start()
            logger.info("[Kafka] Consumer connected to %s and %s", 
                       settings.KAFKA_TOPIC_BATTLE, settings.KAFKA_TOPIC_CHAT)
            retry_delay = 2  # Reset du délai après connexion réussie
            
            # Boucle de lecture des messages
            async for msg in consumer:
                event = msg.value
                topic = msg.topic
                
                # Traiter les événements de bataille
                if topic == settings.KAFKA_TOPIC_BATTLE:
                    etype = event.get("type", "")
                    
                    if etype == "turn_played":
                        result = event.get("result", "?")
                        turn = event.get("turn_number", "?")
                        winner = "Rouge" if result == "A" else ("Bleu" if result == "B" else "Égalité")
                        
                        notif = {
                            "author": "bot",
                            "content": f"Tour {turn} — {winner} remporte le tour !",
                            "is_bot": True
                        }
                        
                        logger.info("[Kafka] Battle Event -> broadcast_all")
                        await chat_service.broadcast_all(notif)
                
                # Traiter les messages de chat
                elif topic == settings.KAFKA_TOPIC_CHAT:
                    room = event.get("room")
                    if room:
                        await chat_service.broadcast(room, event)
                    else:
                        # Broadcast global pour le "Battle Log"
                        await chat_service.broadcast_all(event)

        except asyncio.CancelledError:
            # Arrêt propre
            await consumer.stop()
            return
        
        except Exception as e:
            # Erreur Kafka (ex: broker down) → retry avec backoff
            logger.warning("Kafka unavailable, retrying in %ds : %s", retry_delay, e)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)  # Doubler jusqu'à 30s max
        
        finally:
            try:
                await consumer.stop()
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Démarrer le consumer Kafka au lancement de l'app"""
    await init_db()
    
    # Lancer le consumer en arrière-plan
    task = asyncio.create_task(kafka_consumer_loop())
    
    yield  # Application running
    
    # Cleanup à l'arrêt
    task.cancel()
    await chat_service.stop_producer()
```

**Points clés** :
- ✅ Retry automatique avec backoff exponentiel (2s → 4s → 8s → ... → 30s)
- ✅ Reset du délai après connexion réussie
- ✅ Arrêt propre avec `asyncio.CancelledError`

---

### Kafka Producer (services/chat_service.py)

```python
import json
from aiokafka import AIOKafkaProducer
from app.core.config import settings

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await p.start()
        _producer = p
    return _producer


async def publish_message(message: dict):
    """Publier un message sur Kafka + sauvegarder en BDD."""
    # Sauvegarde en BDD (historique)
    try:
        async with AsyncSessionLocal() as db:
            db_msg = Message(
                room=message.get("room"),
                author=message.get("author"),
                content=message.get("content"),
                is_bot=message.get("is_bot", False),
                team=message.get("team")
            )
            db.add(db_msg)
            await db.commit()
    except Exception as e:
        logger.error(f"Error saving message to DB: {e}")

    # Publication sur Kafka
    try:
        producer = await get_producer()
        await producer.send_and_wait(settings.KAFKA_TOPIC_CHAT, message)
    except Exception as e:
        logger.warning(f"Kafka producer error: {e}")


async def stop_producer():
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
```

---

## 🎤 QUESTIONS PROBABLES À L'ORAL

### Sur battle_service

**Q1 : Expliquez comment fonctionne F(A).**

> "F(A) est la formule qui calcule l'avantage de types dans un combat Pokémon. Elle utilise une table TYPE_CHART de 18×18 types avec des multiplicateurs (2.0 = super efficace, 0.5 = peu efficace, 0 = aucun effet). Pour chaque type w de A, on multiplie tous les get_multiplier(w, y) pour chaque type y de B, et on additionne les produits — c'est F(A). On fait pareil en sens inverse pour F(B). Celui qui a le plus grand score remporte le tour. En cas d'égalité, resolve_turn() retourne 'draw'."

---

**Q2 : Pourquoi publier sur Kafka au lieu d'envoyer directement au frontend ?**

> "Kafka découple battle_service de chat_service. Battle_service publie l'événement 'turn_played' sans savoir qui l'écoute. Ça permet d'ajouter facilement d'autres services (ex: notifications_service, stats_service) sans modifier battle_service. De plus, Kafka garantit la livraison même si chat_service est temporairement down : les événements sont mis en file d'attente."

---

**Q3 : Comment gérer la concurrence si deux joueurs jouent en même temps ?**

> "On utilise des transactions PostgreSQL avec AsyncSession. Quand un joueur joue, la transaction verrouille la ligne Battle jusqu'au commit. Si un deuxième joueur essaie de jouer en même temps, il attend ou on peut retourner une erreur 409 Conflict. Dans notre implémentation actuelle, c'est le frontend qui gère le tour par tour, mais on pourrait améliorer avec un lock explicite en BDD."

---

### Sur chat_service

**Q4 : Comment fonctionne le WebSocket ?**

> "Le WebSocket est un protocole bidirectionnel qui maintient une connexion ouverte entre le client et le serveur. Contrairement à HTTP où le client doit demander les nouvelles données, ici le serveur peut envoyer des messages au client à tout moment. On l'utilise pour le chat temps réel : quand un joueur envoie un message, il est publié sur Kafka, le consumer le reçoit, et on broadcast via WebSocket à tous les clients connectés."

---

**Q5 : Pourquoi le retry avec backoff exponentiel ?**

> "Si Kafka est temporairement down (ex: redémarrage), on ne veut pas spammer les tentatives de reconnexion. Le backoff exponentiel (2s → 4s → 8s → 16s → 30s max) permet d'éviter de surcharger le système. Une fois Kafka de nouveau up, on se reconnecte automatiquement. Le délai est reset à 2s après une connexion réussie."

---

**Q6 : Différence entre broadcast() et broadcast_all() ?**

> "broadcast(room, msg) envoie le message à tous les clients d'une room spécifique (ex: 'red', 'blue', 'battle_uuid'). C'est utilisé pour les messages de chat privés entre équipes. broadcast_all(msg) envoie à TOUS les clients connectés, quelle que soit leur room. On l'utilise pour les événements de bataille qui doivent apparaître dans le Battle Log global visible par tout le monde."

---

## 🚀 AMÉLIORATIONS POSSIBLES (à mentionner à l'oral)

### Battle_service
1. **Circuit breaker** : Si pokedex_service est down, ne pas bloquer battle_service
2. **Rate limiting** : Limiter le nombre de tours par seconde pour éviter le spam
3. **Replay** : Sauvegarder tous les tours pour pouvoir rejouer une bataille
4. **Matchmaking** : Système d'appariement automatique par niveau

### Chat_service
5. **Persistence des messages** : Sauvegarder en BDD pour l'historique
6. **Modération** : Filtrer les messages offensants
7. **Rooms privées** : Chat direct entre 2 joueurs
8. **Typing indicator** : Afficher "X est en train d'écrire..."

---

## ✅ CHECKLIST DE MAÎTRISE

### Battle_service
- [ ] Je peux expliquer F(A) avec un exemple concret
- [ ] Je connais les 5 endpoints par cœur
- [ ] Je peux montrer le code de calc_advantage()
- [ ] Je sais pourquoi on utilise Kafka
- [ ] Je peux expliquer le flow : create → join → turn → end

### Chat_service
- [ ] Je peux expliquer WebSocket vs HTTP
- [ ] Je connais la différence entre broadcast et broadcast_all
- [ ] Je peux expliquer le retry loop du consumer
- [ ] Je sais comment un message Kafka arrive sur WebSocket
- [ ] Je peux montrer le code de chat_endpoint

---

## 🎯 SIMULATION ORALE (15 MIN)

### Structure de ta présentation

**Slide 1 : Vue d'ensemble (2 min)**
> "J'ai développé battle_service qui gère les combats Pokémon avec la formule F(A), et chat_service pour le chat temps réel et le Battle Log. Les deux communiquent via Kafka."

**Slide 2 : Battle_service (6 min)**
- Architecture (1 min)
- Endpoints principaux (2 min)
- Formule F(A) avec exemple (2 min)
- Kafka producer (1 min)

**Slide 3 : Chat_service (6 min)**
- WebSocket endpoints (2 min)
- Kafka consumer avec retry (2 min)
- Broadcast functions (1 min)
- Flow complet : battle → Kafka → WebSocket → frontend (1 min)

**Slide 4 : Conclusion (1 min)**
> "Ces 2 services montrent l'intérêt des microservices : découplage via Kafka, scalabilité indépendante, et résilience avec le retry automatique."

---

## 💪 MESSAGE FINAL

**TU AS FAIT LA PARTIE LA PLUS TECHNIQUE DU PROJET !**

- Battle_service = cœur métier (formule F(A))
- Chat_service = temps réel (WebSocket + Kafka consumer)
- Kafka = communication asynchrone
- Nginx = API Gateway
- Kubernetes = orchestration

**Avec ces 2 services maîtrisés, tu IMPRESSIONNES le prof. 🔥**

**Prépare-toi bien sur J5-J6, et tu passes FACILE ! 💪**
