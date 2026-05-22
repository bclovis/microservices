<p align="center">
  <img src="logo-square.png" alt="PokeDrafter Logo" width="250"/>
</p>

<h1 align="center">PokeDrafter</h1>

<p align="center">
  <strong>A real-time multiplayer Pokémon strategy game built with microservices</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Angular-17-dd0031?logo=angular" alt="Angular 17"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Kafka-3.7-231f20?logo=apachekafka" alt="Kafka"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169e1?logo=postgresql" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker" alt="Docker"/>
  <img src="https://img.shields.io/badge/Kubernetes-1.29-326ce5?logo=kubernetes" alt="Kubernetes"/>
</p>

---

## About

PokeDrafter is a turn-based Pokémon strategy game where two teams — **Red** and **Blue** — battle using type-based matchups (calculated with the `F(A)` formula). Features include real-time chat, team building, Pokédex browsing, and three game modes: Constructed, Random, and Draft.

> **Full documentation:** See [`instructions.md`](instructions.md) for architecture, API endpoints, branching strategy, and team work division.

---

## Features

- **Strategic Turn-Based Battles**: Real-time combat using the F(A) type-calculating engine.
- **Global Battle Log & Chat**: Persistent right sidebar for real-time turn results and team communication across all views.
- **Team Builder**: Create and manage your 6-Pokémon squads with real-time stats.
- **Integrated Pokédex**: Browse the entire library with advanced search and detailed stats.
- **Multi-Microservice Architecture**: Decoupled services for Auth, Teams, Battles, Chat, and Pokedex.

---

## Architecture

```
PokeDrafter/
├── web/              # Angular 17+ Frontend (Port 4300)
├── api/              # Python FastAPI Microservices
│   ├── auth_service/       # Authentication (JWT, Port 8001)
│   ├── team_service/       # Team CRUD + Recommender (Port 8002)
│   ├── battle_service/     # Battle Engine + Kafka (Port 8003)
│   ├── pokedex_service/    # PokéAPI Proxy + Redis (Port 8004)
│   ├── chat_service/       # Real-time Chat (WebSocket, Port 8005)
│   └── gateway/            # Nginx Reverse Proxy (Port 80)
├── infra/            # Deployment Configurations
│   ├── docker/             # docker-compose.yml
│   ├── k8s/                # Kubernetes manifests
│   └── scripts/            # Database init & helper scripts
└── shared_lib/       # Common Python utilities for services
```

---

## Quick Start

### Prerequisites

- **Docker Desktop** (v24+)
- **Node.js** (v20+) & **npm**

### Launching the App (Docker)

1. **Spin up the backend & infrastructure**:

   ```bash
   cd infra/docker
   docker compose up --build -d
   ```

2. **Start the frontend**:

   ```bash
   cd ../../web
   npm install
   npm start -- --port 4300
   ```

3. **Access the application**:
   - **Game Dashboard**: [http://localhost:4300](http://localhost:4300)
   - **API Documentation**: [http://localhost:80/docs](http://localhost:80/docs)

---

## Team

| Role | Focus |
|------|-------|
| **Frontend Dev** | Angular UI, components, WebSocket client |
| **Backend Core** | Auth, Teams, Pokédex, DB, JWT |
| **Game & Infra** | Battle engine F(A), Kafka, WebSocket PvP, Docker, K8s |

---

## Branching

```
main ← develop ← frontend/main ← frontend/feat/*
                ← backend/main  ← backend/feat/*
                ← infra/main    ← infra/feat/*
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 17, TailwindCSS, RxJS |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 |
| Messaging | Apache Kafka (aiokafka) |
| Database | PostgreSQL 16, Redis 7 |
| Gateway | Nginx |
| Container | Docker, Kubernetes |
| Auth | JWT (python-jose), bcrypt |
| Data Source | [PokéAPI](https://pokeapi.co/) |

---

## Test Users

| Pseudo | Color | Email | Password |
|--------|-------|-------|----------|
| `red_trainer` | Red | <red@pokedrafter.com> | `RedTeam123!` |
| `blue_trainer` | Blue | <blue@pokedrafter.com> | `BlueTeam123!` |
| `admin` | — | <admin@pokedrafter.com> | `Admin123!` |

---

## License

Academic project — ICC ING3 Microservices Module — 2026
