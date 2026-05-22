# PokeDrafter — Project Instructions

> **Repository:** [https://github.com/abdemeh/PokeDrafter](https://github.com/abdemeh/PokeDrafter)
> **Deadline:** 30 April 2026, 23:59
> **Team Size:** 3 people
> **Module:** Microservices — ICC ING3

---

## Table of Contents

1. [Project Summary](#-project-summary)
2. [High-Level Architecture](#-high-level-architecture)
3. [Folder Structure](#-folder-structure)
4. [Services Breakdown](#-services-breakdown)
5. [API Gateway & Endpoints](#-api-gateway--endpoints)
6. [Database Schema](#-database-schema)
7. [Kafka Events](#-kafka-events)
8. [Frontend Pages & Components](#-frontend-pages--components)
9. [Docker & Kubernetes](#-docker--kubernetes)
10. [Team Work Division](#-team-work-division)
12. [Packages & Dependencies](#-packages--dependencies)
13. [Environment Variables](#-environment-variables)
14. [How to Run](#-how-to-run)
15. [References](#-references)

---

## Project Summary

**PokeDrafter** is a real-time multiplayer Pokémon strategy game inspired by rock-paper-scissors. Two players — one on **Team Red**, the other on **Team Blue** — build teams of **6 Pokémon** and battle against each other in turn-based duels.

### How battles work

The advantage between two Pokémon is computed using **type matchup** from the official Pokémon type table, with the formula:

```
F(A) = 1 × (W/Y) × (W/Z) + 1 × (X/Y) × (X/Z)
F(B) = 1 × (Y/W) × (Y/X) + 1 × (Z/W) × (Z/X)
```

Where Pokémon A has types W·X and Pokémon B has types Y·Z. The Pokémon with the **lower F score** is knocked out. If equal, **both** are KO'd.

### Game Modes

| Mode | Description |
|------|-------------|
| **Constructed** | Each player brings a pre-built team |
| **Random** | Teams are randomly generated |
| **Draft** | Players take turns picking from 12 random Pokémon |

### Key Features

- User authentication (register, login, profile management)
- Team builder with CRUD operations
- Real-time chat between players
- Pokédex browsing (powered by PokéAPI)
- Turn-based battle engine with 90s timer
- AI-powered team recommendation ("Complete" button)
- Battle history & user statistics
- Admin log console

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB["Angular Frontend<br/>(web/)"]
    end

    subgraph "Gateway Layer"
        GW["Nginx API Gateway<br/>(infra/)"]
    end

    subgraph "Backend Services (api/)"
        AUTH["Auth Service<br/>:8001"]
        TEAM["Team Service<br/>:8002"]
        BATTLE["Battle Service<br/>:8003"]
        POKEDEX["Pokédex Service<br/>:8004"]
        CHAT["Chat Service<br/>:8005"]
    end

    subgraph "Message Broker"
        KAFKA["Apache Kafka<br/>+ Zookeeper"]
    end

    subgraph "Data Layer"
        PG_AUTH["PostgreSQL<br/>auth_db"]
        PG_TEAM["PostgreSQL<br/>team_db"]
        PG_BATTLE["PostgreSQL<br/>battle_db"]
        REDIS["Redis Cache<br/>(PokéAPI cache)"]
    end

    subgraph "External"
        POKEAPI["PokéAPI<br/>pokeapi.co"]
    end

    WEB -->|HTTP/WS| GW
    GW -->|/api/auth/*| AUTH
    GW -->|/api/teams/*| TEAM
    GW -->|/api/battle/*| BATTLE
    GW -->|/api/pokedex/*| POKEDEX
    GW -->|/api/chat/*| CHAT

    AUTH --> PG_AUTH
    TEAM --> PG_TEAM
    BATTLE --> PG_BATTLE
    POKEDEX --> REDIS
    POKEDEX -->|fetch & cache| POKEAPI

    BATTLE <-->|events| KAFKA
    CHAT <-->|messages| KAFKA
    TEAM -->|team-updates| KAFKA

    style WEB fill:#1976d2,color:#fff
    style GW fill:#ff9800,color:#fff
    style KAFKA fill:#e53935,color:#fff
    style REDIS fill:#43a047,color:#fff
```

### Request Flow

```mermaid
sequenceDiagram
    participant U as User (Angular)
    participant G as Nginx Gateway
    participant A as Auth Service
    participant B as Battle Service
    participant K as Kafka
    participant O as Opponent's Battle Service

    U->>G: POST /api/auth/login
    G->>A: Forward request
    A-->>G: JWT Token
    G-->>U: JWT Token

    U->>G: POST /api/battle/action (with JWT)
    G->>B: Forward + validate JWT
    B->>K: Publish battle-action event
    K->>O: Deliver to opponent's consumer
    O-->>K: Publish battle-result
    K-->>B: Receive result
    B-->>G: Turn result
    G-->>U: Update UI
```

### Inter-Backend Communication (Red ↔ Blue)

```mermaid
graph LR
    subgraph "Team Red"
        R_BACK["Red Backend<br/>:800x"]
        R_FRONT["Red Frontend<br/>:4200"]
    end

    subgraph "Kafka Cluster"
        TOPIC_RB["topic: battle-red-to-blue"]
        TOPIC_BR["topic: battle-blue-to-red"]
    end

    subgraph "Team Blue"
        B_BACK["Blue Backend<br/>:810x"]
        B_FRONT["Blue Frontend<br/>:4201"]
    end

    R_FRONT --> R_BACK
    R_BACK -->|"encrypted msg"| TOPIC_RB
    TOPIC_RB --> B_BACK
    B_BACK -->|"encrypted msg"| TOPIC_BR
    TOPIC_BR --> R_BACK
    B_FRONT --> B_BACK

    style TOPIC_RB fill:#e53935,color:#fff
    style TOPIC_BR fill:#1976d2,color:#fff
```

> **Important:** Red and Blue backends **never communicate directly**. All inter-team data flows through **Kafka** and is **encrypted with a private key**.

---

## Folder Structure

```
PokeDrafter/
│
├──  web/                          # FRONTEND — Angular 17
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/                # Singleton services, guards, interceptors
│   │   │   │   ├── guards/
│   │   │   │   │   └── auth.guard.ts
│   │   │   │   ├── interceptors/
│   │   │   │   │   └── jwt.interceptor.ts
│   │   │   │   ├── services/
│   │   │   │   │   ├── auth.service.ts
│   │   │   │   │   ├── team.service.ts
│   │   │   │   │   ├── battle.service.ts
│   │   │   │   │   ├── pokedex.service.ts
│   │   │   │   │   ├── chat.service.ts
│   │   │   │   │   └── websocket.service.ts
│   │   │   │   └── models/
│   │   │   │       ├── user.model.ts
│   │   │   │       ├── pokemon.model.ts
│   │   │   │       ├── team.model.ts
│   │   │   │       └── battle.model.ts
│   │   │   │
│   │   │   ├── features/            # Feature modules (lazy-loaded)
│   │   │   │   ├── auth/
│   │   │   │   │   ├── login/
│   │   │   │   │   └── register/
│   │   │   │   ├── dashboard/
│   │   │   │   │   └── dashboard-layout/
│   │   │   │   ├── battle/
│   │   │   │   │   ├── battle-arena/
│   │   │   │   │   ├── battle-card/
│   │   │   │   │   └── battle-timer/
│   │   │   │   ├── teams/
│   │   │   │   │   ├── team-list/
│   │   │   │   │   ├── team-builder/
│   │   │   │   │   └── team-card/
│   │   │   │   ├── pokedex/
│   │   │   │   │   ├── pokedex-list/
│   │   │   │   │   └── pokemon-detail/
│   │   │   │   ├── chat/
│   │   │   │   │   ├── chat-panel/
│   │   │   │   │   └── message-bubble/
│   │   │   │   └── profile/
│   │   │   │       ├── profile-view/
│   │   │   │       └── profile-edit/
│   │   │   │
│   │   │   ├── shared/              # Shared components, pipes, directives
│   │   │   │   ├── components/
│   │   │   │   │   ├── navbar/
│   │   │   │   │   ├── sidebar/
│   │   │   │   │   ├── pokemon-card/
│   │   │   │   │   └── loading-spinner/
│   │   │   │   ├── pipes/
│   │   │   │   └── directives/
│   │   │   │
│   │   │   ├── app.component.ts
│   │   │   ├── app.config.ts
│   │   │   └── app.routes.ts
│   │   │
│   │   ├── assets/
│   │   │   ├── images/
│   │   │   └── icons/
│   │   ├── environments/
│   │   │   ├── environment.ts
│   │   │   └── environment.prod.ts
│   │   ├── styles.css
│   │   └── index.html
│   │
│   ├── angular.json
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── nginx.conf                   # Serves built Angular + proxy to API
│
├──  api/                          # BACKEND — Python FastAPI
│   │
│   ├──  auth_service/             # Authentication microservice
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # FastAPI app entry point
│   │   │   ├── routes/
│   │   │   │   └── auth.py          # /register, /login, /me, /refresh
│   │   │   ├── schemas/
│   │   │   │   └── auth.py          # Pydantic models for request/response
│   │   │   ├── models/
│   │   │   │   └── user.py          # SQLAlchemy User model
│   │   │   ├── services/
│   │   │   │   └── auth_service.py  # Business logic (hash, JWT, etc.)
│   │   │   ├── core/
│   │   │   │   ├── config.py        # Settings from env vars
│   │   │   │   ├── security.py      # JWT encode/decode, password hashing
│   │   │   │   └── database.py      # Async DB session factory
│   │   │   └── dependencies.py      # Dependency injection (get_db, get_current_user)
│   │   ├── alembic/                 # Database migrations
│   │   │   └── versions/
│   │   ├── alembic.ini
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├──  team_service/             # Team management microservice
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   │   └── team.py          # CRUD /teams, /teams/{id}/complete
│   │   │   ├── schemas/
│   │   │   │   └── team.py
│   │   │   ├── models/
│   │   │   │   └── team.py          # SQLAlchemy Team + TeamPokemon models
│   │   │   ├── services/
│   │   │   │   ├── team_service.py  # CRUD logic
│   │   │   │   └── recommend.py     # AI recommendation engine
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   └── database.py
│   │   │   └── dependencies.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├──  battle_service/           # Battle engine microservice
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   │   └── battle.py        # /battle/start, /battle/{id}/action, /battle/{id}/forfeit
│   │   │   ├── schemas/
│   │   │   │   └── battle.py
│   │   │   ├── models/
│   │   │   │   └── battle.py        # SQLAlchemy Battle + BattleLog models
│   │   │   ├── services/
│   │   │   │   ├── battle_engine.py # The F(A)/F(B) formula calculation
│   │   │   │   └── kafka_service.py # Kafka producer/consumer for inter-team comms
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   ├── security.py      # Encrypt/decrypt inter-backend messages
│   │   │   │   └── database.py
│   │   │   └── dependencies.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├──  pokedex_service/          # Pokédex data microservice
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   │   └── pokedex.py       # /pokedex, /pokedex/{id}, /pokedex/search
│   │   │   ├── schemas/
│   │   │   │   └── pokemon.py
│   │   │   ├── services/
│   │   │   │   └── pokeapi_service.py  # Fetch from PokéAPI + Redis cache
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   └── cache.py         # Redis connection
│   │   │   └── dependencies.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├──  chat_service/             # Real-time chat microservice
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   │   └── chat.py          # WebSocket /ws/chat/{room_id}
│   │   │   ├── schemas/
│   │   │   │   └── message.py
│   │   │   ├── services/
│   │   │   │   └── chat_service.py  # Kafka-backed message distribution
│   │   │   ├── core/
│   │   │   │   └── config.py
│   │   │   └── dependencies.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └──  gateway/                  # API Gateway / Reverse Proxy config
│       ├── nginx.conf               # Routes /api/* to correct service
│       └── Dockerfile
│
├──  infra/                        # INFRASTRUCTURE — Docker & Kubernetes
│   │
│   ├──  docker/
│   │   ├── docker-compose.yml       # Full stack orchestration (dev)
│   │   ├── docker-compose.dev.yml   # Dev overrides (hot reload, debug)
│   │   └── .env.example             # Template for environment variables
│   │
│   ├──  k8s/                      # Kubernetes manifests
│   │   ├── namespace.yaml
│   │   ├──  deployments/
│   │   │   ├── auth-deployment.yaml
│   │   │   ├── team-deployment.yaml
│   │   │   ├── battle-deployment.yaml
│   │   │   ├── pokedex-deployment.yaml
│   │   │   ├── chat-deployment.yaml
│   │   │   ├── frontend-deployment.yaml
│   │   │   └── gateway-deployment.yaml
│   │   ├──  services/
│   │   │   ├── auth-service.yaml
│   │   │   ├── team-service.yaml
│   │   │   ├── battle-service.yaml
│   │   │   ├── pokedex-service.yaml
│   │   │   ├── chat-service.yaml
│   │   │   ├── frontend-service.yaml
│   │   │   └── gateway-service.yaml
│   │   ├──  stateful/
│   │   │   ├── postgres.yaml        # StatefulSet + PVC
│   │   │   ├── redis.yaml
│   │   │   ├── kafka.yaml
│   │   │   └── zookeeper.yaml
│   │   ├──  config/
│   │   │   ├── configmap.yaml       # Non-sensitive config
│   │   │   └── secrets.yaml         # Sensitive config (base64 encoded)
│   │   └──  ingress/
│   │       └── ingress.yaml         # External access rules
│   │
│   └──  scripts/
│       ├── init-db.sql              # Initial DB schema + seed data
│       ├── seed-users.sql           # Pre-existing test users
│       └── deploy.sh                # Deployment convenience script
│
├──  docs/                         # Documentation & assets
│   ├── architecture-diagram.png
│   ├── maquettes/                   # UI mockup scans
│   └── api-spec.yaml                # OpenAPI spec (auto-generated)
│
├── .gitignore
├── instructions.md                  # ← YOU ARE HERE
├── README.md                        # Quick start README
├── projet_micro.md                  # Original project specification
├── Projet Micro ICC 2026.pdf        # PDF specification
└── logo-square.png                  # Project logo
```

---

## Services Breakdown

### Service Architecture Overview

```mermaid
graph LR
    subgraph "Microservices"
        A[" Auth Service"]
        B[" Team Service"]
        C[" Battle Service"]
        D[" Pokédex Service"]
        E[" Chat Service"]
    end

    subgraph "Infrastructure"
        F[" PostgreSQL"]
        G[" Redis"]
        H[" Kafka"]
        I[" Nginx Gateway"]
    end

    A --- F
    B --- F
    C --- F
    C --- H
    D --- G
    E --- H
    I --> A & B & C & D & E
```

### 1. Auth Service (Port 8001)

**Responsibility:** User registration, login, JWT management, profile CRUD.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Create new user account |
| `POST` | `/api/auth/login` | Authenticate & return JWT |
| `POST` | `/api/auth/refresh` | Refresh expired JWT |
| `GET` | `/api/auth/me` | Get current user profile |
| `PUT` | `/api/auth/me` | Update profile (pseudo, color, avatar) |
| `GET` | `/api/auth/users/{id}` | Get public user profile |
| `POST` | `/api/auth/logout` | Invalidate token |

**Tech:** FastAPI, SQLAlchemy, PostgreSQL, bcrypt, PyJWT

---

### 2. Team Service (Port 8002)

**Responsibility:** CRUD operations on teams, AI-powered team completion.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/teams` | List all teams of current user |
| `POST` | `/api/teams` | Create a new team |
| `GET` | `/api/teams/{id}` | Get team details |
| `PUT` | `/api/teams/{id}` | Update a team |
| `DELETE` | `/api/teams/{id}` | Delete a team |
| `POST` | `/api/teams/{id}/complete` | AI: auto-fill remaining team slots |
| `GET` | `/api/teams/{id}/export` | Export team data |

**Tech:** FastAPI, SQLAlchemy, PostgreSQL, httpx (calls Pokédex service)

---

### 3. Battle Service (Port 8003)

**Responsibility:** Game lobby, matchmaking, turn-by-turn duel engine, scoring.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/battle/queue` | Join matchmaking queue |
| `POST` | `/api/battle/start` | Start a battle (with team selection) |
| `GET` | `/api/battle/{id}` | Get battle state |
| `POST` | `/api/battle/{id}/action` | Submit turn action (switch or keep Pokémon) |
| `POST` | `/api/battle/{id}/forfeit` | Forfeit the match |
| `GET` | `/api/battle/history` | Get user's battle history |
| `GET` | `/api/battle/{id}/log` | Get detailed battle log |
| `WS` | `/ws/battle/{id}` | WebSocket for real-time battle updates |

**Battle Engine — F(A) Formula:**

```python
def compute_advantage(types_a: list[str], types_b: list[str], type_chart: dict) -> float:
    """
    F(A) = Π(effectiveness of each of A's types against each of B's types)
    Using the formula:
    F(A) = 1*(W/Y)*(W/Z) + 1*(X/Y)*(X/Z)
    Where A = types W,X and B = types Y,Z
    """
    w, x = types_a[0], types_a[1] if len(types_a) > 1 else types_a[0]
    y, z = types_b[0], types_b[1] if len(types_b) > 1 else types_b[0]

    wy = type_chart.get((w, y), 1.0)
    wz = type_chart.get((w, z), 1.0)
    xy = type_chart.get((x, y), 1.0)
    xz = type_chart.get((x, z), 1.0)

    return 1 * wy * wz + 1 * xy * xz
```

**Tech:** FastAPI, SQLAlchemy, PostgreSQL, aiokafka, cryptography (Fernet)

---

### 4. Pokédex Service (Port 8004)

**Responsibility:** Proxy to PokéAPI with Redis caching. Serves Pokémon data.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/pokedex` | List Pokémon (paginated) |
| `GET` | `/api/pokedex/{id}` | Get Pokémon details |
| `GET` | `/api/pokedex/search` | Search by name, type1, type2 |
| `GET` | `/api/pokedex/types` | List all types + damage relations |
| `GET` | `/api/pokedex/types/{name}/chart` | Get type effectiveness chart |
| `GET` | `/api/pokedex/random/{count}` | Get N random Pokémon (for Draft mode) |

**Caching Strategy:**
```mermaid
graph LR
    REQ["Request /pokedex/25"] --> CHECK{"Redis Cache?"}
    CHECK -->|HIT| RET["Return cached data"]
    CHECK -->|MISS| FETCH["Fetch from PokéAPI"]
    FETCH --> STORE["Store in Redis (TTL: 24h)"]
    STORE --> RET
```

**Tech:** FastAPI, Redis (aioredis), httpx

---

### 5. Chat Service (Port 8005)

**Responsibility:** Real-time messaging via WebSocket, backed by Kafka for scaling.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `WS` | `/ws/chat/{room_id}` | WebSocket for real-time chat |
| `GET` | `/api/chat/{room_id}/history` | Get chat message history |
| `GET` | `/api/chat/rooms` | List available chat rooms |

**Tech:** FastAPI, WebSocket, aiokafka

---

### 6. Nginx API Gateway

**Responsibility:** Reverse proxy, routing, CORS, rate limiting, static file serving.

```nginx
# Simplified nginx.conf routing
upstream auth_service    { server auth:8001; }
upstream team_service    { server team:8002; }
upstream battle_service  { server battle:8003; }
upstream pokedex_service { server pokedex:8004; }
upstream chat_service    { server chat:8005; }

server {
    listen 80;

    # Frontend (Angular built files)
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API routing
    location /api/auth/    { proxy_pass http://auth_service; }
    location /api/teams/   { proxy_pass http://team_service; }
    location /api/battle/  { proxy_pass http://battle_service; }
    location /api/pokedex/ { proxy_pass http://pokedex_service; }
    location /api/chat/    { proxy_pass http://chat_service; }

    # WebSocket routing
    location /ws/ {
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_pass http://battle_service;
    }
}
```

---

## Database Schema

```mermaid
erDiagram
    USERS {
        uuid id PK
        string username UK
        string email UK
        string password_hash
        string first_name
        string last_name
        string color "RED or BLUE"
        string avatar_url
        int level
        int points
        timestamp created_at
        timestamp updated_at
    }

    TEAMS {
        uuid id PK
        uuid user_id FK
        string name
        timestamp created_at
        timestamp updated_at
    }

    TEAM_POKEMON {
        uuid id PK
        uuid team_id FK
        int pokemon_id "PokéAPI ID"
        string pokemon_name
        string type1
        string type2
        int slot "1-6"
    }

    BATTLES {
        uuid id PK
        uuid red_player_id FK
        uuid blue_player_id FK
        uuid winner_id FK
        string mode "constructed|random|draft"
        string status "pending|active|finished|forfeit"
        json red_team "snapshot of team at battle start"
        json blue_team "snapshot"
        int red_remaining
        int blue_remaining
        timestamp started_at
        timestamp finished_at
    }

    BATTLE_TURNS {
        uuid id PK
        uuid battle_id FK
        int turn_number
        int red_pokemon_id
        int blue_pokemon_id
        float red_score "F(A)"
        float blue_score "F(B)"
        string result "red_ko|blue_ko|both_ko"
        timestamp played_at
    }

    CHAT_MESSAGES {
        uuid id PK
        string room_id
        uuid user_id FK
        string content
        timestamp sent_at
    }

    USERS ||--o{ TEAMS : "owns"
    TEAMS ||--o{ TEAM_POKEMON : "contains"
    USERS ||--o{ BATTLES : "plays as red"
    USERS ||--o{ BATTLES : "plays as blue"
    BATTLES ||--o{ BATTLE_TURNS : "has turns"
    USERS ||--o{ CHAT_MESSAGES : "sends"
```

---

## Kafka Events

### Topics

| Topic | Producer | Consumer | Description |
|-------|----------|----------|-------------|
| `battle.action.red` | Red Battle Service | Blue Battle Service | Red player's action (encrypted) |
| `battle.action.blue` | Blue Battle Service | Red Battle Service | Blue player's action (encrypted) |
| `battle.result` | Battle Service | Frontend (via WS) | Turn result after calculation |
| `chat.messages` | Chat Service | Chat Service (all instances) | Chat message fan-out |
| `team.updates` | Team Service | Battle Service | Notifies when teams change |
| `user.events` | Auth Service | All services | User registration/update events |

### Message Encryption (Inter-Backend)

```mermaid
sequenceDiagram
    participant R as Red Backend
    participant K as Kafka
    participant B as Blue Backend

    R->>R: Serialize action to JSON
    R->>R: Encrypt with Fernet(SHARED_SECRET_KEY)
    R->>K: Publish encrypted payload to battle.action.red
    K->>B: Deliver message
    B->>B: Decrypt with Fernet(SHARED_SECRET_KEY)
    B->>B: Deserialize and process
```

---

## Frontend Pages & Components

### Page Map (from mockups)

```mermaid
graph TD
    A[" Login Page"] -->|Login| D[" Dashboard"]
    A -->|Sign Up| B[" Register Page"]
    B -->|Return| A
    B -->|Sign Up Success| D

    D --> E[" Battle Arena"]
    D --> F[" My Teams"]
    D --> G[" Pokédex"]
    D --> H[" Profile"]
    D --> I[" Mode Selection"]

    F --> F1["Team Builder"]
    G --> G1["Pokémon Detail"]
    H --> H1["Edit Profile"]
    I --> E

    D --> J[" Chat Panel (sidebar)"]
    D --> K[" Messages"]
```

### Mockup Analysis (from your paper wireframes)

#### Page 1 — Login & Register
- **Login:** Logo "PokeDrafter" + "Welcome to the game!" + Login/Password fields + "Forgot password?" link + LOGIN/SIGNUP buttons
- **Register:** "Join the squad" + Firstname/Lastname, Mail, Password, Username, Color picker + Return/Sign Up buttons

#### Page 2 — Main Dashboard (Opened Menu)
- **Left sidebar:** PokeDrafter logo, navigation items (Mode, Play, Teams, Dex), Username at bottom with avatar
- **Center:** Game area ("GAME HERE")
- **Right panel:** Messages/notifications
- **User popup:** Change username, Color, Avatar, History, Logout

#### Page 3 — Dashboard (Closed Menu)
- **Icons-only sidebar** (collapsed mode)
- **Same center game area + right messages panel**

#### Page 4 — Messages & Profile
- **Messages panel** on left
- **Game area** center
- **Profile popup:** Username, Color toggle, Level (99x), Points (999x)
- **Fullscreen** toggle button

#### Page 5 — Pokémon Card Design
- **Front:** Number (#002), Name (Pikachu), Sprite image, Points (2999 pts), Star badge
- **Back:** PokeDrafter logo + branding, Pokéball icon

### Angular Components Hierarchy

```
AppComponent
├── AuthModule (lazy)
│   ├── LoginComponent
│   └── RegisterComponent
│
└── DashboardLayoutComponent (lazy, guarded)
    ├── SidebarComponent (collapsible)
    │   ├── NavItemComponent
    │   └── UserPopupComponent
    ├── <router-outlet> (main content)
    │   ├── ModeSelectionComponent
    │   ├── BattleArenaComponent
    │   │   ├── BattleCardComponent
    │   │   ├── BattleTimerComponent (90s countdown)
    │   │   └── TurnLogComponent
    │   ├── TeamListComponent
    │   │   ├── TeamCardComponent
    │   │   └── TeamBuilderComponent
    │   │       └── PokemonSlotComponent (×6)
    │   ├── PokedexListComponent
    │   │   └── PokemonCardComponent
    │   │       └── PokemonDetailComponent (modal)
    │   └── ProfileComponent
    │       └── ProfileEditComponent
    ├── ChatPanelComponent (right sidebar)
    │   └── MessageBubbleComponent
    └── NotificationBarComponent
```

---

## Docker & Kubernetes

### Docker Compose (Development)

```yaml
# infra/docker/docker-compose.yml
version: '3.9'

services:
  # ─── FRONTEND ────────────────────────────────────
  frontend:
    build:
      context: ../../web
      dockerfile: Dockerfile
    ports:
      - "4200:80"
    depends_on:
      - gateway
    networks:
      - pokedrafter-net

  # ─── API GATEWAY ──────────────────────────────────
  gateway:
    build:
      context: ../../api/gateway
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - auth
      - team
      - battle
      - pokedex
      - chat
    networks:
      - pokedrafter-net

  # ─── AUTH SERVICE ──────────────────────────────────
  auth:
    build:
      context: ../../api/auth_service
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/auth_db
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=HS256
      - JWT_EXPIRATION=3600
    depends_on:
      - postgres
    networks:
      - pokedrafter-net

  # ─── TEAM SERVICE ──────────────────────────────────
  team:
    build:
      context: ../../api/team_service
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/team_db
      - JWT_SECRET=${JWT_SECRET}
      - POKEDEX_SERVICE_URL=http://pokedex:8004
    depends_on:
      - postgres
    networks:
      - pokedrafter-net

  # ─── BATTLE SERVICE ───────────────────────────────
  battle:
    build:
      context: ../../api/battle_service
      dockerfile: Dockerfile
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/battle_db
      - JWT_SECRET=${JWT_SECRET}
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - TEAM_COLOR=${TEAM_COLOR:-RED}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    depends_on:
      - postgres
      - kafka
    networks:
      - pokedrafter-net

  # ─── POKÉDEX SERVICE ──────────────────────────────
  pokedex:
    build:
      context: ../../api/pokedex_service
      dockerfile: Dockerfile
    ports:
      - "8004:8004"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - POKEAPI_BASE_URL=https://pokeapi.co/api/v2
    depends_on:
      - redis
    networks:
      - pokedrafter-net

  # ─── CHAT SERVICE ─────────────────────────────────
  chat:
    build:
      context: ../../api/chat_service
      dockerfile: Dockerfile
    ports:
      - "8005:8005"
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - kafka
    networks:
      - pokedrafter-net

  # ─── DATABASES & INFRA ────────────────────────────
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_MULTIPLE_DATABASES=auth_db,team_db,battle_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - pokedrafter-net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - pokedrafter-net

  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0
    environment:
      - ZOOKEEPER_CLIENT_PORT=2181
    networks:
      - pokedrafter-net

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    ports:
      - "9092:9092"
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
      - KAFKA_AUTO_CREATE_TOPICS_ENABLE=true
    depends_on:
      - zookeeper
    networks:
      - pokedrafter-net

volumes:
  postgres_data:
  redis_data:

networks:
  pokedrafter-net:
    driver: bridge
```

### Kubernetes Deployment

Deploy everything with a single command:

```bash
# Create namespace
kubectl create namespace pokedrafter

# Apply all manifests
kubectl apply -f infra/k8s/ -n pokedrafter

# Or use the convenience script
chmod +x infra/scripts/deploy.sh
./infra/scripts/deploy.sh
```

### Example Dockerfile (FastAPI Service)

```dockerfile
# api/auth_service/Dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Example Dockerfile (Angular Frontend)

```dockerfile
# web/Dockerfile
# Stage 1: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration=production

# Stage 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Team Work Division

### Team of 3

| Person | Role | Responsibilities |
|--------|------|-----------------|
| **Abdellatif** | **Frontend Developer** | Angular app, UI/UX, components, routing, services, WebSocket client, tests |
| **Alaa** | **Backend Developer — Core API** | Auth Service, Team Service, Pokédex Service, DB schema, JWT, Redis caching |
| **Betsaleel** | **Backend Developer — Game & Infra** | Battle Service, Chat Service, Kafka integration, Docker, Kubernetes, encryption |

### Detailed Breakdown

#### Abdellatif — Frontend (Angular)

**Branch:** `frontend/main`

| Week | Tasks |
|------|-------|
| **Week 1** | Project setup, routing, auth pages (login/register), shared components (sidebar, navbar, pokemon-card) |
| **Week 2** | Dashboard layout, team CRUD pages (list, builder), Pokédex page with search & filters |
| **Week 3** | Battle arena UI, timer component, real-time WebSocket integration, chat panel |
| **Week 4** | Profile page, polish animations, user popup menu, responsiveness, unit tests, bug fixes |

**Key deliverables:**
- All pages from mockups implemented
- JWT interceptor for authenticated requests
- WebSocket service for battle & chat
- Component unit tests (Jasmine/Karma)
- Responsive design

---

#### Alaa — Backend Core API (Python/FastAPI)

**Branch:** `backend/main`

| Week | Tasks |
|------|-------|
| **Week 1** | Project setup, Auth Service (register, login, JWT, bcrypt), PostgreSQL models with Alembic migrations |
| **Week 2** | Team Service (full CRUD), Pokédex Service (PokéAPI proxy + Redis cache), inter-service communication |
| **Week 3** | AI recommendation engine for "Complete" button, user profile endpoints, battle history endpoints |
| **Week 4** | API documentation (OpenAPI), seed data, integration tests, security hardening |

**Key deliverables:**
- Auth Service with JWT
- Team Service with CRUD + AI recommend
- Pokédex Service with Redis cache
- Database migrations (Alembic)
- API documentation

---

#### Betsaleel — Game Engine & Infrastructure

**Branch:** `infra/main`

| Week | Tasks |
|------|-------|
| **Week 1** | Docker setup (docker-compose.yml), Kafka + Zookeeper config, Battle Service skeleton, DB setup |
| **Week 2** | Battle Engine (F(A) formula), Kafka producer/consumer, inter-backend encryption (Fernet), WebSocket server |
| **Week 3** | Chat Service (WebSocket + Kafka fan-out), Kubernetes manifests (deployments, services, PVCs) |
| **Week 4** | Deploy script, k8s namespace config, end-to-end testing, monitoring/logs, admin log console endpoint |

**Key deliverables:**
- Full Docker Compose for local dev
- Kubernetes manifests for deployment
- Battle engine with type calculation
- Kafka event pipeline (encrypted)
- Chat service with WebSocket
- Deploy automation

---

### Collaboration Points

```mermaid
graph TD
    A["Abdellatif<br/>Frontend"] -->|"Consume API endpoints"| B["Alaa<br/>Backend Core"]
    A -->|"WebSocket events"| C["Betsaleel<br/>Game & Infra"]
    B -->|"Publish team.updates events"| C
    C -->|"Kafka topics & Docker networking"| B
    B ---|"Shared: JWT Secret, API contracts"| C

    style A fill:#1976d2,color:#fff
    style B fill:#388e3c,color:#fff
    style C fill:#e64a19,color:#fff
```

**Weekly sync meetings** recommended to align on:
- API contract changes (request/response schemas)
- WebSocket message format
- Kafka topic schemas
- Docker networking changes

---

## Packages & Dependencies

### Frontend (Angular — `web/package.json`)

```json
{
  "dependencies": {
    "@angular/animations": "^17.3.0",
    "@angular/common": "^17.3.0",
    "@angular/compiler": "^17.3.0",
    "@angular/core": "^17.3.0",
    "@angular/forms": "^17.3.0",
    "@angular/platform-browser": "^17.3.0",
    "@angular/platform-browser-dynamic": "^17.3.0",
    "@angular/router": "^17.3.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0",
    "zone.js": "~0.14.3",
    "socket.io-client": "^4.7.0"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^17.3.0",
    "@angular/cli": "^17.3.0",
    "@angular/compiler-cli": "^17.3.0",
    "@types/jasmine": "~5.1.0",
    "autoprefixer": "^10.4.0",
    "jasmine-core": "~5.1.0",
    "karma": "~6.4.0",
    "karma-chrome-launcher": "~3.2.0",
    "karma-coverage": "~2.2.0",
    "karma-jasmine": "~5.1.0",
    "karma-jasmine-html-reporter": "~2.1.0",
    "postcss": "^8.5.0",
    "tailwindcss": "^3.4.0",
    "typescript": "~5.4.0"
  }
}
```

### Backend (Python — per service `requirements.txt`)

#### Shared across all services
```txt
fastapi==0.111.0
uvicorn[standard]==0.30.0
pydantic==2.7.0
pydantic-settings==2.3.0
python-dotenv==1.0.1
httpx==0.27.0
```

#### Auth Service
```txt
sqlalchemy[asyncio]==2.0.31
asyncpg==0.29.0
alembic==1.13.0
bcrypt==4.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
```

#### Team Service
```txt
sqlalchemy[asyncio]==2.0.31
asyncpg==0.29.0
alembic==1.13.0
```

#### Battle Service
```txt
sqlalchemy[asyncio]==2.0.31
asyncpg==0.29.0
aiokafka==0.10.0
cryptography==42.0.0
websockets==12.0
```

#### Pokédex Service
```txt
aioredis==2.0.1
redis==5.0.0
```

#### Chat Service
```txt
aiokafka==0.10.0
websockets==12.0
```

---

## Environment Variables

Create `infra/docker/.env` from the template:

```env
# ─── GENERAL ────────────────────────────────
PROJECT_NAME=PokeDrafter
TEAM_COLOR=RED

# ─── JWT ─────────────────────────────────────
JWT_SECRET=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# ─── DATABASE ────────────────────────────────
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

AUTH_DB_NAME=auth_db
TEAM_DB_NAME=team_db
BATTLE_DB_NAME=battle_db

# ─── REDIS ───────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ─── KAFKA ───────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# ─── ENCRYPTION (Inter-Backend) ─────────────
ENCRYPTION_KEY=your-fernet-key-here

# ─── POKEAPI ─────────────────────────────────
POKEAPI_BASE_URL=https://pokeapi.co/api/v2
POKEAPI_CACHE_TTL=86400
```

---

## How to Run

### Prerequisites

- **Docker** & **Docker Compose** v2+
- **Node.js** 20+ & **npm** (for local frontend dev)
- **Python** 3.12+ (for local backend dev)
- **kubectl** (for Kubernetes deployment)

### Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/abdemeh/PokeDrafter.git
cd PokeDrafter

# 2. Copy environment template
cp infra/docker/.env.example infra/docker/.env
# → Edit .env with your secrets

# 3. Launch everything
cd infra/docker
docker compose up --build -d

# 4. Open in browser
# Frontend:  http://localhost:4200
# API Docs:  http://localhost:8001/docs  (Auth)
#            http://localhost:8002/docs  (Team)
#            http://localhost:8003/docs  (Battle)
#            http://localhost:8004/docs  (Pokédex)
```

### Local Development (without Docker)

```bash
# Frontend
cd web
npm install
ng serve
# → http://localhost:4200

# Backend (each service in separate terminal)
cd api/auth_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Repeat for each service...
```

### Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace pokedrafter

# Apply all config
kubectl apply -f infra/k8s/ -n pokedrafter

# Check status
kubectl get pods -n pokedrafter
kubectl get services -n pokedrafter

# View logs
kubectl logs -f deployment/battle-service -n pokedrafter
```

---

## References

### Official Documentation

| Resource | URL |
|----------|-----|
| **Angular 17** | https://angular.dev/overview |
| **FastAPI** | https://fastapi.tiangolo.com/ |
| **PokéAPI** | https://pokeapi.co/docs/v2 |
| **SQLAlchemy 2.0** | https://docs.sqlalchemy.org/en/20/ |
| **Alembic** | https://alembic.sqlalchemy.org/en/latest/ |
| **aiokafka** | https://aiokafka.readthedocs.io/ |
| **Apache Kafka** | https://kafka.apache.org/documentation/ |
| **Docker** | https://docs.docker.com/ |
| **Kubernetes** | https://kubernetes.io/docs/ |
| **Nginx** | https://nginx.org/en/docs/ |
| **Redis** | https://redis.io/docs/ |
| **Pydantic v2** | https://docs.pydantic.dev/latest/ |
| **WebSocket (FastAPI)** | https://fastapi.tiangolo.com/advanced/websockets/ |
| **Fernet Encryption** | https://cryptography.io/en/latest/fernet/ |
| **RxJS** | https://rxjs.dev/guide/overview |
| **Tailwind CSS** | https://tailwindcss.com/docs |

### Pokémon Type Chart

| Resource | URL |
|----------|-----|
| **PokéAPI Types Endpoint** | https://pokeapi.co/api/v2/type/ |
| **Type Damage Relations** | https://pokeapi.co/api/v2/type/{id}/ |
| **Pokémon List** | https://pokeapi.co/api/v2/pokemon?limit=151 |
| **Pokémon Detail** | https://pokeapi.co/api/v2/pokemon/{id}/ |
| **Pokémon Species** | https://pokeapi.co/api/v2/pokemon-species/{id}/ |

### Useful Tools

| Tool | Purpose |
|------|---------|
| **Postman / Insomnia** | API testing |
| **DBeaver** | Database GUI |
| **Kafdrop** | Kafka topic browser (add to docker-compose for debugging) |
| **Redis Commander** | Redis GUI |

---

> **Last updated:** 12 April 2026
> **Authors:** PokeDrafter Team
> **License:** Academic Project — ICC ING3
