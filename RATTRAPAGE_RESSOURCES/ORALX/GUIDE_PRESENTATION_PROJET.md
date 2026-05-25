# 🎤 GUIDE DE PRÉSENTATION - MA PARTIE DU PROJET (15 minutes)

> **Consigne exacte** : "Les 15 dernières minutes porteront sur votre rendu dont vous présenterez **la partie du projet que vous avez réalisée**, et expliquerez les choix que vous avez pris pour ce faire."

## 🎯 MES PARTIES — Ce que JE présente

| Partie | Ce que j'ai fait |
|--------|-----------------|
| **battle_service** | Moteur F(A), routes HTTP (create/join/turn/forfeit), Kafka producer |
| **chat_service** | WebSocket temps réel, Kafka consumer (battle-events), persistance BDD |
| **Docker Compose** | Orchestration des 10 services, depends_on, réseau interne |
| **Nginx (gateway)** | Reverse proxy, routing /api/*, upgrade WebSocket |
| **Kubernetes** | Deployments, Services, PVC, NodePort pour chaque service |

**Pas de WebSocket dans battle_service** — les WebSocket sont dans chat_service (`/ws/chat/{team}` et `/ws/battle/{battle_id}`). Battle_service est purement HTTP REST + Kafka producer.

---

## ⏱️ PLAN 15 MINUTES

| Temps | Contenu |
|-------|---------|
| 0–1 min | Intro : le projet en 3 phrases, mon périmètre |
| 1–6 min | **battle_service** : moteur F(A), routes HTTP, Kafka producer |
| 6–10 min | **chat_service** : WebSocket, Kafka consumer, broadcast |
| 10–13 min | **Infra** : Docker Compose, Nginx, Kubernetes |
| 13–15 min | Justification des choix techniques |

---

## 🗣️ INTRO (1 min)

> "PokeDrafter est une plateforme de bataille Pokémon multijoueur en temps réel, développée en architecture microservices FastAPI + Kafka + PostgreSQL.
> Ma partie couvre le **moteur de combat** (`battle_service`), le **chat temps réel** (`chat_service`), et toute l'**infrastructure** : Docker Compose, Nginx, et les manifests Kubernetes."

---

## 🥊 PARTIE 1 — BATTLE_SERVICE (5 min)

### Ce que j'ai fait
- Moteur de combat **F(A)** : calcul d'avantage par types
- 8 endpoints HTTP REST (create, join, turn, end, forfeit, history…)
- **Kafka producer** : publie sur le topic `battle-events` après chaque action
- BDD `battle_db` (PostgreSQL) : tables `Battle` et `BattleTurn`

### Endpoints à citer
```
GET  /api/battle/battles/open          → lister les salles ouvertes
POST /api/battle/battles/              → créer une bataille
POST /api/battle/battles/{id}/join     → rejoindre
POST /api/battle/battles/{id}/turn     → jouer un tour
POST /api/battle/battles/{id}/forfeit  → abandonner
POST /api/battle/battles/{id}/end      → terminer
GET  /api/battle/battles/{id}          → détails
GET  /api/battle/battles/history/{uid} → historique joueur
```

> ⚠️ **Pas de WebSocket ici** — battle_service est purement HTTP REST + Kafka producer.

### La formule F(A) — à expliquer clairement
```python
def calc_advantage(types_a, types_b):
    # Double boucle : pour chaque type de A contre chaque type de B
    # On multiplie les multiplicateurs (ex: Eau vs Feu → 2.0)
    # et on additionne pour obtenir fa (et fb en sens inverse)
    fa = 0.0
    for w in types_a:
        val = 1.0
        for y in types_b:
            val *= get_multiplier(w, y)  # table de types Pokémon
        fa += val
    fb = 0.0
    for y in types_b:
        val = 1.0
        for w in types_a:
            val *= get_multiplier(y, w)
        fb += val
    return round(fa, 4), round(fb, 4)
```

**À dire :**
> "La formule F(A) calcule l'avantage de type en double boucle. Si A = [Électrik] attaque B = [Eau, Vol] : fa = get_multiplier(Élec, Eau) × get_multiplier(Élec, Vol) = 2.0 × 2.0 = 4.0. On compare fa et fb : si fa > fb, le Pokémon A gagne le tour."

### Kafka producer — à expliquer
```python
# Dans routes/battle.py, après chaque action :
await publish_battle_event("turn_played", {
    "battle_id": str(battle_id),
    "turn_number": turn.turn_number,
    "result": result   # "A", "B" ou "draw"
})
# → publié sur settings.KAFKA_TOPIC_BATTLE = "battle-events"
```

**À dire :**
> "Après chaque tour, battle_service publie un event Kafka sur `battle-events`. C'est asynchrone : il n'attend pas que chat_service le lise. Le découplage est total."

### Questions probables

**Q : Pourquoi Kafka et pas un appel REST direct vers chat_service ?**
> "Kafka découple les services. Si chat_service est down, les événements sont mis en file et traités au redémarrage. Avec REST on perdrait les événements."

**Q : Comment on gère deux joueurs qui jouent en même temps ?**
> "PostgreSQL avec transactions et vérification de l'état de la bataille avant chaque tour. Si la bataille n'est pas en état 'active' ou si ce n'est pas le bon joueur, l'endpoint retourne une erreur."

---

## 💬 PARTIE 2 — CHAT_SERVICE (4 min)

### Ce que j'ai fait
- WebSocket `/ws/chat/{team}` — chat par équipe (red / blue)
- WebSocket `/ws/battle/{battle_id}` — chat de salle de combat
- **Kafka consumer loop** : écoute `battle-events`, broadcast aux clients WS connectés
- Persistance des messages en PostgreSQL (`chat_db`)
- `_connections = defaultdict(list)` — registre en mémoire des connexions actives

### Les deux WebSocket
```
WS /ws/chat/{team}           → chat d'équipe (red ou blue)
WS /ws/battle/{battle_id}    → chat de la salle de bataille
```

### Architecture du consumer Kafka
```python
# Dans main.py — démarre au lancement de l'app
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(kafka_consumer_loop())

async def kafka_consumer_loop():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_BATTLE,   # "battle-events"
        settings.KAFKA_TOPIC_CHAT,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
    )
    await consumer.start()
    async for msg in consumer:
        event = json.loads(msg.value)
        # Broadcast à tous les WebSocket connectés à cette bataille
        await broadcast_all(event["battle_id"], json.dumps(event))
```

### Broadcast et registre de connexions
```python
# defaultdict : clé = room_id, valeur = liste de WebSocket
_connections: dict[str, list[WebSocket]] = defaultdict(list)

async def broadcast_all(room_id: str, message: str):
    for ws in _connections[room_id]:
        await ws.send_text(message)
```

**À dire :**
> "chat_service maintient un registre en mémoire de toutes les connexions WebSocket actives, indexées par room_id. Quand Kafka reçoit un événement de bataille, on broadcast le message à tous les clients connectés à cette room. Le WebSocket est persistant : la connexion reste ouverte pendant toute la durée de la bataille."

### Questions probables

**Q : Que se passe-t-il si chat_service redémarre ?**
> "Les connexions WS sont perdues (elles sont en mémoire). Les clients doivent se reconnecter. C'est une limite de l'implémentation actuelle — on pourrait utiliser Redis Pub/Sub pour partager les connexions entre instances."

**Q : Pourquoi WebSocket et pas polling HTTP ?**
> "Le polling HTTP enverrait une requête toutes les X secondes même s'il n'y a rien de nouveau. WebSocket est bidirectionnel et persistant : le serveur pousse les données dès qu'elles arrivent, sans latence et sans surcharge."

---

## 🐳 PARTIE 3 — INFRA (3 min)

### Docker Compose (`infra/docker/docker-compose.yml`)

**10 services :** postgres, redis, zookeeper, kafka, auth-service, pokedex-service, team-service, battle-service, chat-service, gateway (nginx)

**Points clés à expliquer :**

```yaml
# Ordre de démarrage avec depends_on
battle-service:
  depends_on:
    kafka:
      condition: service_healthy
    postgres:
      condition: service_healthy

# Résolution DNS interne Docker
# Les services se parlent par nom : "http://battle-service:8003"
# Pas besoin d'IP, Docker gère le DNS sur le réseau interne
```

**À dire :**
> "Docker Compose orchestre les 10 services avec `depends_on` pour garantir l'ordre de démarrage. Kafka doit être healthy avant de démarrer battle-service. Docker crée un réseau interne où les services se résolvent par nom : battle_service appelle `http://postgres:5432` sans connaître l'IP."

### Nginx (`api/gateway/nginx.conf`)

```nginx
# Reverse proxy vers les microservices
location /api/battle/ {
    proxy_pass http://battle-service:8003;
}

location /api/chat/ {
    proxy_pass http://chat-service:8005;
}

# Upgrade WebSocket — CRUCIAL pour /ws/
location /ws/ {
    proxy_pass http://chat-service:8005;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

**À dire :**
> "Nginx est la gateway unique : le frontend ne connaît qu'une seule URL. Il route `/api/battle/` vers battle-service, `/api/chat/` vers chat-service. Pour les WebSocket, il faut absolument les headers `Upgrade` et `Connection: upgrade` — sans ça, la connexion WS est refusée par le proxy."

### Kubernetes (`infra/k8s/`)

**Fichiers :**
- `namespace.yaml` — namespace `pokedrafter`
- `postgres.yaml` — Deployment + Service + PVC
- `kafka.yaml` — Deployment Kafka + Zookeeper
- `redis.yaml` — Deployment Redis
- `services.yaml` — Deployments pour les 5 microservices
- `gateway.yaml` — Deployment Nginx + **Service NodePort 30080**

**Points clés :**
```yaml
# NodePort : exposer l'app à l'extérieur du cluster
apiVersion: v1
kind: Service
spec:
  type: NodePort
  ports:
    - port: 80
      nodePort: 30080   # accessible via http://localhost:30080

# PVC : stockage persistant pour PostgreSQL
kind: PersistentVolumeClaim
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
```

**À dire :**
> "Les manifests Kubernetes reprennent l'architecture Docker Compose en objets K8s : chaque microservice a un Deployment et un Service. La gateway est exposée en NodePort 30080. PostgreSQL a un PVC pour que les données survivent aux redémarrages de pods."

---

## 🤔 JUSTIFICATION DES CHOIX TECHNIQUES (2 min)

| Choix | Justification |
|-------|--------------|
| **Kafka** | Asynchrone, découplé, les events survivent si chat_service est down |
| **WebSocket dans chat_service** | Connexion persistante bidirectionnelle, pas de polling |
| **HTTP REST dans battle_service** | Logique transactionnelle, réponse synchrone nécessaire |
| **Redis (pokedex)** | Cache TTL 24h — évite de surcharger PokéAPI externe |
| **PostgreSQL par service** | Isolation des données, pas de couplage de schéma |
| **Zookeeper + Kafka 7.5.0** | Image `confluentinc/cp-kafka:7.5.0` nécessite Zookeeper (mode classique, pas KRaft) |
| **Nginx** | Gateway unique, gère CORS centralement, upgrade WS |

**À dire sur Kafka vs REST :**
> "On aurait pu faire un appel REST de battle_service vers chat_service après chaque tour, mais si chat_service est down on perd l'événement. Kafka garantit la livraison et découple complètement les services : battle_service ne sait même pas que chat_service existe."

**À dire sur WebSocket :**
> "Le WebSocket dans chat_service permet au serveur de pousser les événements Kafka directement aux clients sans qu'ils aient à poller. La connexion reste ouverte pendant toute la durée de la bataille."

---

## 🚨 QUESTIONS PIÈGES

**Q : "Il n'y a pas de WebSocket dans battle_service ?"**
> "Non, c'est volontaire. battle_service est purement REST : il reçoit des actions HTTP, calcule le résultat, et publie sur Kafka. C'est chat_service qui maintient les WebSocket et consomme Kafka pour broadcaster les résultats en temps réel."

**Q : "Pourquoi deux WebSocket différents dans chat_service ?"**
> "`/ws/chat/{team}` est pour le chat d'équipe (stratégie privée entre coéquipiers). `/ws/battle/{battle_id}` est pour les messages de la salle de combat visible par tous les participants d'une bataille."

**Q : "Comment Nginx sait qu'il doit upgrader la connexion WebSocket ?"**
> "Les headers `Upgrade: websocket` et `Connection: upgrade` dans nginx.conf. Sans ces deux headers, Nginx ferme la connexion au lieu de la laisser ouverte — c'est le protocole HTTP/1.1 pour l'upgrade vers WS."

**Q : "Vous avez utilisé l'IA pour coder ?"**
> "Oui, comme outil d'assistance (Copilot, ChatGPT) pour le boilerplate et les bugs. Mais j'ai compris et maîtrisé chaque partie : je peux expliquer la formule F(A), le consumer Kafka, le fonctionnement des WebSocket et les choix d'infrastructure ligne par ligne."
2. Tu **comprends** ce que tu as fait
3. Tu peux **justifier** les choix techniques
4. Tu peux **expliquer** comment ton service fonctionne

**Pas besoin d'être expert sur tout**, mais maîtrise **AU MOINS 2 SERVICES à fond**.

---

## 📊 STRUCTURE DE LA PRÉSENTATION (15 MIN)

### ⏱️ Introduction (30 secondes)
"Je vais vous présenter PokeDrafter, une plateforme de bataille Pokémon multijoueur en temps réel que nous avons développée en architecture microservices."

### ⏱️ Vue d'ensemble du projet (2 minutes)
- Contexte et objectif
- Architecture globale (schéma)
- Technologies utilisées

### ⏱️ Services maîtrisés en profondeur (10 minutes)
- Service 1 : architecture, endpoints, logique métier (5 min)
- Service 2 : architecture, endpoints, logique métier (5 min)
- Communication entre services

### ⏱️ Choix techniques et retour d'expérience (2 minutes)
- Pourquoi ces choix ?
- Difficultés rencontrées
- Améliorations possibles

### ⏱️ Conclusion (30 secondes)
"Ce projet m'a permis de comprendre concrètement les défis des microservices, notamment la gestion de la communication asynchrone et la scalabilité."

---

## 🏗️ PARTIE 1 : VUE D'ENSEMBLE DU PROJET

### Slide 1 : Introduction

**À dire :**
> "PokeDrafter est une plateforme de bataille Pokémon stratégique en temps réel. Les joueurs créent des équipes de 6 Pokémon et s'affrontent dans 3 modes de jeu : Draft (pioche alternée), Constructed (équipes pré-construites), et Random (aléatoire). Le système de combat utilise une formule mathématique F(A) qui calcule les avantages de types pour déterminer le vainqueur de chaque tour."

**Points clés :**
- Jeu multijoueur temps réel
- 3 modes de jeu
- Formule de combat F(A)
- Architecture microservices

---

### Slide 2 : Architecture Globale

**Schéma à présenter :**

```
┌────────────────────────────────────────────────────────┐
│                  FRONTEND ANGULAR 17                   │
│              (Port 4200, Single Page App)              │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│               NGINX API GATEWAY (Port 80)              │
│       - Reverse Proxy - CORS - Load Balancing         │
└────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────────────┐
        │                 │                         │
        ▼                 ▼                         ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ auth_service │  │ team_service │  │ battle_service   │
│  (Port 8001) │  │  (Port 8002) │  │   (Port 8003)    │
│              │  │              │  │                  │
│ - JWT Auth   │  │ - CRUD Teams │  │ - Battle Engine  │
│ - Users      │  │ - AI Recomm  │  │ - Kafka Producer │
│              │  │              │  │ - F(A) Formula   │
│ PostgreSQL   │  │ PostgreSQL   │  │ PostgreSQL       │
└──────────────┘  └──────────────┘  └──────────────────┘
        │                 │                         │
        ▼                 ▼                         ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│pokedex_svc   │  │  chat_svc    │  │  KAFKA BROKER    │
│  (Port 8004) │  │  (Port 8005) │  │                  │
│              │  │              │  │ Topics:          │
│ - PokéAPI    │  │ - WebSocket  │  │ - battle.started │
│ - Redis Cache│  │ - Real-time  │  │ - turn.played    │
│              │  │   Chat       │  │ - battle.ended   │
│ Redis        │  │ PostgreSQL   │  └──────────────────┘
└──────────────┘  └──────────────┘
```

**À dire :**
> "L'architecture se compose de 5 microservices backend en FastAPI derrière une gateway Nginx. Le frontend Angular communique uniquement avec la gateway. Chaque service a sa propre base de données PostgreSQL, sauf pokedex_service qui utilise Redis comme cache. La communication synchrone se fait via REST, et l'asynchrone via Kafka pour les événements de bataille."

---

### Slide 3 : Technologies utilisées

**Stack technique :**

| Composant | Technologie | Pourquoi ? |
|-----------|-------------|------------|
| **Frontend** | Angular 17 + TypeScript | Framework moderne, composants réutilisables |
| **Backend** | FastAPI + Python 3.11 | Performance, async/await, documentation auto |
| **BDD Principale** | PostgreSQL 16 | Données relationnelles, ACID |
| **Cache** | Redis 7 | Cache ultra-rapide pour PokéAPI |
| **Message Broker** | Kafka 3.7 | Communication asynchrone, event-driven |
| **Gateway** | Nginx | Reverse proxy performant |
| **Conteneurisation** | Docker + Docker Compose | Déploiement uniforme |
| **Orchestration** | Kubernetes (optionnel) | Scalabilité, auto-healing |

**À dire :**
> "On a choisi FastAPI pour sa performance et sa documentation automatique. PostgreSQL pour les données relationnelles avec transactions ACID. Redis pour cacher les données de PokéAPI et éviter de surcharger l'API externe. Kafka pour les événements de bataille en temps réel, car il garantit la livraison des messages même si un service est temporairement down. Nginx comme gateway pour centraliser le CORS et la sécurité."

---

## 🔥 PARTIE 2 : SERVICES MAÎTRISÉS EN PROFONDEUR

### Stratégie de choix des services

**OPTION A : Cœur métier (Recommandé si tu aimes la technique)**
- **team_service** (gestion équipes + AI recommender)
- **battle_service** (engine de combat + Kafka)

**OPTION B : Plus simple (Recommandé si tu veux la sécurité)**
- **auth_service** (JWT, users)
- **pokedex_service** (cache Redis, proxy PokéAPI)

**OPTION C : Complet (Si tu es à l'aise)**
- **auth_service** (base solide)
- **team_service** (logique métier)

---

### 📦 SERVICE 1 : AUTH_SERVICE (Exemple détaillé)

#### Architecture du service

```
auth_service/
├── main.py          # Application FastAPI principale
├── models.py        # Modèles SQLAlchemy (User)
├── schemas.py       # Modèles Pydantic (validation)
├── database.py      # Connexion PostgreSQL
├── auth.py          # Logique JWT (create_token, verify_token)
└── requirements.txt # Dépendances
```

#### Responsabilités

1. **Inscription** (POST /register)
2. **Connexion** (POST /login) → Retourne JWT
3. **Vérification du token** (GET /me)
4. **Gestion des utilisateurs** (CRUD)

#### Endpoints principaux

```python
# 1. Inscription
POST /api/auth/register
Body: {
  "username": "player1",
  "email": "player1@example.com",
  "password": "securepass123"
}
Response: {
  "id": 1,
  "username": "player1",
  "email": "player1@example.com"
}

# 2. Connexion (retourne JWT)
POST /api/auth/login
Body: {
  "username": "player1",
  "password": "securepass123"
}
Response: {
  "access_token": "eyJhbGc....",
  "token_type": "bearer",
  "user": {"id": 1, "username": "player1"}
}

# 3. Vérifier le token
GET /api/auth/me
Headers: Authorization: Bearer eyJhbGc....
Response: {
  "id": 1,
  "username": "player1",
  "email": "player1@example.com"
}
```

#### Code clé à maîtriser : Génération JWT

```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    
    # Encoder le JWT
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return user_id
    except:
        return None
```

**À expliquer à l'oral :**
> "auth_service gère l'authentification avec JWT. Lors de la connexion, on vérifie le mot de passe hashé avec bcrypt, puis on génère un JWT contenant l'ID utilisateur. Ce token est valide 24h. Les autres services peuvent vérifier ce token pour authentifier les requêtes. On stocke les users dans PostgreSQL avec mot de passe hashé pour la sécurité."

#### Choix techniques

**Q : Pourquoi JWT et pas des sessions ?**
> "Les JWT sont stateless : le serveur n'a pas besoin de stocker les sessions. C'est parfait pour les microservices car n'importe quel service peut vérifier le token sans interroger auth_service. Chaque service a la clé secrète et peut décoder le JWT de manière indépendante."

**Q : Pourquoi hasher les mots de passe ?**
> "On utilise bcrypt pour hasher les mots de passe avant de les stocker. Même si la BDD est compromise, l'attaquant ne peut pas récupérer les mots de passe en clair. Bcrypt ajoute aussi un 'salt' unique par mot de passe."

---

### 📦 SERVICE 2 : TEAM_SERVICE (Exemple détaillé)

#### Architecture du service

```
team_service/
├── main.py          # Application FastAPI
├── models.py        # Team, TeamPokemon (SQLAlchemy)
├── schemas.py       # Validation Pydantic
├── database.py      # PostgreSQL connection
├── recommender.py   # AI Team Recommender
└── requirements.txt
```

#### Responsabilités

1. **CRUD Teams** : Créer, lire, modifier, supprimer des équipes
2. **Gestion des Pokémon** : Ajouter/retirer des Pokémon d'une équipe (max 6)
3. **AI Recommender** : Suggérer des Pokémon pour compléter une équipe
4. **Validation** : Vérifier les règles (max 6 Pokémon, pas de doublons)

#### Endpoints principaux

```python
# 1. Créer une équipe
POST /api/teams
Headers: Authorization: Bearer <JWT>
Body: {
  "name": "Team Thunder",
  "description": "Équipe électrique offensive"
}
Response: {
  "id": 1,
  "name": "Team Thunder",
  "user_id": 1,
  "pokemons": []
}

# 2. Ajouter un Pokémon à l'équipe
POST /api/teams/{team_id}/pokemons
Body: {
  "pokemon_id": 25,  # Pikachu
  "pokemon_name": "Pikachu",
  "pokemon_types": ["electric"]
}

# 3. Lister les équipes de l'utilisateur
GET /api/teams
Headers: Authorization: Bearer <JWT>
Response: [
  {
    "id": 1,
    "name": "Team Thunder",
    "pokemons": [
      {"pokemon_id": 25, "pokemon_name": "Pikachu", "types": ["electric"]},
      {"pokemon_id": 135, "pokemon_name": "Jolteon", "types": ["electric"]}
    ]
  }
]

# 4. AI Recommender (compléter l'équipe)
POST /api/teams/{team_id}/recommend
Response: {
  "recommendations": [
    {"id": 3, "name": "Venusaur", "types": ["grass", "poison"], "reason": "Couvre les faiblesses ground"},
    {"id": 6, "name": "Charizard", "types": ["fire", "flying"], "reason": "Ajoute diversity offensive"}
  ]
}
```

#### Code clé : AI Recommender (simplifié)

```python
def recommend_pokemon(team_pokemons: List[TeamPokemon]) -> List[dict]:
    # 1. Analyser les types de l'équipe actuelle
    current_types = set()
    for p in team_pokemons:
        current_types.update(p.pokemon_types)
    
    # 2. Identifier les faiblesses (types manquants)
    all_types = ["fire", "water", "grass", "electric", "ground", 
                 "flying", "psychic", "bug", "rock", "ghost", 
                 "dragon", "dark", "steel", "fairy", "fighting", "poison", "ice", "normal"]
    
    missing_types = set(all_types) - current_types
    
    # 3. Récupérer des Pokémon ayant ces types
    recommendations = []
    for missing_type in list(missing_types)[:3]:  # Top 3
        # Appel à pokedex_service pour trouver des Pokémon de ce type
        response = requests.get(f"http://pokedex-service:8004/pokemon/type/{missing_type}")
        pokemons = response.json()
        
        if pokemons:
            recommendations.append({
                "id": pokemons[0]["id"],
                "name": pokemons[0]["name"],
                "types": pokemons[0]["types"],
                "reason": f"Ajoute le type {missing_type} manquant"
            })
    
    return recommendations
```

**À expliquer à l'oral :**
> "team_service gère la création et modification d'équipes. Chaque équipe appartient à un utilisateur (vérifié via JWT). On a implémenté un AI Recommender qui analyse les types de l'équipe actuelle, identifie les faiblesses (types manquants), et suggère des Pokémon pour combler ces faiblesses. L'algorithme appelle pokedex_service pour récupérer des Pokémon par type. On stocke tout dans PostgreSQL avec une relation many-to-many entre Teams et Pokemons."

#### Choix techniques

**Q : Pourquoi séparer team_service de auth_service ?**
> "Chaque service a une responsabilité unique (Single Responsibility Principle). auth_service gère l'authentification, team_service gère la logique métier des équipes. Ça permet de scaler indépendamment : si beaucoup d'utilisateurs créent des équipes, on peut ajouter des instances de team_service sans toucher auth_service."

**Q : Comment le recommender fonctionne ?**
> "Il analyse les types actuels de l'équipe, identifie les types manquants, et suggère des Pokémon qui comblent ces lacunes. C'est une logique simplifiée, on pourrait améliorer en prenant en compte les stats, les faiblesses de types (ex: electric est faible contre ground), et les synergies. Mais ça donne déjà un bon point de départ pour les joueurs."

---

### 📦 SERVICE 3 : BATTLE_SERVICE (Optionnel - Si tu veux impressionner)

#### Responsabilités

1. **Créer une bataille** (Draft/Constructed/Random mode)
2. **Engine de combat** : Calculer F(A) pour chaque tour
3. **Publier événements Kafka** : `battle-events` topic
4. **Gérer l'état de la bataille** : tours, résultats, winner

#### Code clé : Formule F(A)

```python
def calc_advantage(types_a: list[str], types_b: list[str]) -> tuple[float, float]:
    """
    Double boucle : pour chaque type w de A, multiplie get_multiplier(w,y)
    pour chaque type y de B, puis additionne — c'est fa.
    Même chose en sens inverse pour fb.
    Fonctionne avec 1 ou 2 types sans logique spéciale.
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
```

**À expliquer :**
> "battle_service implémente le moteur de combat. On utilise la formule F(A) qui calcule l'avantage en fonction des types avec une double boucle. Par exemple, si Pikachu (Électrik) attaque Gyarados (Eau/Vol) : F(A) = get_multiplier(Électrik,Eau) × get_multiplier(Électrik,Vol) = 2.0 × 2.0 = 4.0. À chaque tour, on publie un événement Kafka sur le topic `battle-events` pour que chat_service puisse afficher le résultat en temps réel via WebSocket."

---

## 🎯 PARTIE 3 : COMMUNICATION ENTRE SERVICES

### Communication Synchrone (REST)

**Exemple : team_service → pokedex_service**

```python
# team_service veut récupérer les infos d'un Pokémon
import requests

def get_pokemon_info(pokemon_id: int):
    response = requests.get(f"http://pokedex-service:8004/pokemon/{pokemon_id}")
    return response.json()
```

**À expliquer :**
> "Quand team_service a besoin des infos d'un Pokémon (nom, types, stats), il appelle pokedex_service via REST. C'est synchrone car team_service attend la réponse avant de continuer. pokedex_service fait lui-même office de proxy vers l'API externe PokéAPI et cache les résultats dans Redis pour éviter de surcharger l'API."

---

### Communication Asynchrone (Kafka)

**Exemple : battle_service → chat_service**

```python
# battle_service publie un événement (aiokafka)
from app.services.kafka_service import publish_battle_event

await publish_battle_event("turn_played", {
    "battle_id": str(battle_id),
    "turn_number": turn_number,
    "result": result,    # "A", "B" ou "draw"
})
# → envoyé sur settings.KAFKA_TOPIC_BATTLE = "battle-events"

# chat_service écoute (dans kafka_consumer_loop) :
# AIOKafkaConsumer abonné à settings.KAFKA_TOPIC_BATTLE + settings.KAFKA_TOPIC_CHAT
# À la réception d'un event "turn_played" → broadcast_all() via WebSocket
```

**À expliquer :**
> "Pour les événements de bataille, on utilise Kafka car c'est asynchrone et garantit la livraison. battle_service publie 'turn_played' sur le topic `battle-events` après chaque tour. chat_service a un consumer loop qui écoute ce topic et diffuse via WebSocket aux joueurs connectés. Même si chat_service est down pendant quelques secondes, les événements sont mis en file d'attente et seront traités au redémarrage."

---

## 💡 PARTIE 4 : CHOIX TECHNIQUES ET JUSTIFICATIONS

### Q : Pourquoi FastAPI ?

**Réponse :**
> "FastAPI offre plusieurs avantages : 1) Performance élevée grâce à async/await, 2) Documentation automatique (Swagger UI), 3) Validation automatique avec Pydantic, 4) Très bon support des WebSockets pour chat_service. C'est devenu le standard pour les microservices Python modernes."

---

### Q : Pourquoi Kafka et pas REST partout ?

**Réponse :**
> "Pour les événements de bataille temps réel, Kafka garantit la livraison même si un service est temporairement down. Les messages sont persistés. Avec REST, si chat_service est down, on perd l'événement. Kafka découple aussi complètement les services : battle_service ne sait pas qui écoute ses événements. On pourrait ajouter un notifications_service facilement."

---

### Q : Pourquoi Redis pour le cache ?

**Réponse :**
> "L'API externe PokéAPI a des rate limits (100 requêtes/minute). Sans cache, on atteindrait vite la limite. Redis est ultra-rapide (in-memory) et parfait pour ça. On cache les données avec un TTL de 24h. Ça réduit la latence de 500ms (appel PokéAPI) à 5ms (Redis)."

---

### Q : Difficultés rencontrées ?

**Réponse (sois honnête) :**
> "La partie la plus complexe était la gestion de la concurrence dans battle_service : s'assurer que deux joueurs ne peuvent pas jouer en même temps. On a résolu ça avec des transactions PostgreSQL et des locks. Aussi, debugger Kafka était difficile au début : comprendre pourquoi les messages n'arrivaient pas. On a utilisé Kafbat UI pour visualiser les topics."

---

### Q : Améliorations possibles ?

**Réponse (montre que tu réfléchis) :**
> "1) Ajouter une couche de cache Redis dans team_service pour les équipes fréquemment consultées. 2) Implémenter un circuit breaker pour gérer les pannes de pokedex_service. 3) Améliorer l'AI Recommender en prenant compte des synergies de types. 4) Déployer sur Kubernetes pour le scaling automatique en production. 5) Ajouter des tests end-to-end avec pytest."

---

## 🚨 QUESTIONS PIÈGES PROBABLES

### Q : "Vous avez utilisé l'IA pour le projet ?"

**Réponse honnête et professionnelle :**
> "Oui, on a utilisé GitHub Copilot et ChatGPT comme assistants de développement, notamment pour générer du code boilerplate et résoudre des bugs. Mais j'ai pris soin de comprendre chaque partie du code, et je peux expliquer en détail comment [service que tu maîtrises] fonctionne, depuis la base de données jusqu'aux endpoints. L'IA est un outil, mais la compréhension de l'architecture et des choix techniques reste humaine."

**Puis enchaîne immédiatement sur un point technique pour prouver que tu maîtrises :**
> "Par exemple, dans team_service, le recommender analyse les types actuels, identifie les faiblesses, et appelle pokedex_service pour suggérer des Pokémon. C'est une logique métier qu'on a conçue nous-mêmes."

---

### Q : "Quel est votre plus gros problème rencontré ?"

**Réponds avec un vrai problème technique et SA SOLUTION :**
> "Notre plus gros problème était la gestion des transactions distribuées. Par exemple, quand une bataille démarre, il faut : 1) Créer la bataille en BDD, 2) Vérifier que les équipes existent (team_service), 3) Publier l'événement Kafka. Si une étape échoue, il faut rollback. On a résolu ça avec une saga chorégraphie : si battle.started échoue, on publie battle.cancelled et chaque service compense."

---

### Q : "Comment testez-vous votre application ?"

**Réponse :**
> "On a plusieurs niveaux : 1) Tests unitaires avec pytest pour la logique métier (ex: la formule F(A)), 2) Tests d'intégration pour les endpoints avec TestClient de FastAPI, 3) Tests manuels via Swagger UI (/docs), 4) Tests end-to-end en lançant tout avec docker-compose et en testant des scénarios complets (créer équipe → lancer bataille). On pourrait automatiser plus avec Playwright pour le frontend."

---

## ✅ CHECKLIST AVANT L'ORAL

### Préparation technique
- [ ] Je peux dessiner l'architecture complète de mémoire
- [ ] Je maîtrise 2 services à 100% (code, endpoints, BDD)
- [ ] Je sais expliquer la communication sync vs async
- [ ] Je connais les choix techniques et leurs raisons
- [ ] J'ai préparé 3-4 améliorations possibles

### Préparation mentale
- [ ] J'ai répété ma présentation à voix haute (3 fois minimum)
- [ ] Je me suis enregistré en vidéo
- [ ] J'ai préparé des réponses aux questions pièges
- [ ] Je suis capable de coder en live un endpoint simple

### Matériel
- [ ] Slides avec schémas clairs (5-6 slides max)
- [ ] Code source ouvert (sur les parties que je maîtrise)
- [ ] Application fonctionnelle (docker-compose up)
- [ ] Postman ou Swagger pour démo live

---

## 🎤 SIMULATION D'ORAL

### Entraîne-toi avec ces questions :

1. "Expliquez-moi l'architecture de votre projet"
2. "Quelle partie avez-vous développée ?"
3. "Montrez-moi le code de [votre service]"
4. "Comment les services communiquent entre eux ?"
5. "Pourquoi avez-vous utilisé Kafka ?"
6. "Comment gérez-vous l'authentification ?"
7. "Quelles difficultés avez-vous rencontrées ?"
8. "Comment améliorer votre projet ?"

**Chronomètre-toi : tu dois pouvoir répondre en 15 minutes max.**

---

## 🔥 CONSEIL FINAL

**Le prof ne cherche PAS à te piéger. Il veut juste vérifier que :**
- Tu as vraiment travaillé sur le projet
- Tu comprends ce que tu as fait
- Tu peux justifier tes choix

**Stratégie gagnante :**
- Parle avec **enthousiasme** (même si tu stresses)
- Sois **honnête** (mieux vaut dire "je ne suis pas sûr" qu'inventer)
- **Montre le code** et l'application qui tourne
- **Anticipe** les questions en les posant toi-même

**Si tu maîtrises 2 services + l'architecture globale → tu passes ! 💪**
