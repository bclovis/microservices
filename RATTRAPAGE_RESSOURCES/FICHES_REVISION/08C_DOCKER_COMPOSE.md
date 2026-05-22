# 🐳 FICHE 08C : Docker Compose — Infrastructure locale

> Basée sur le rapport (page 4-5) + ton vrai fichier `infra/docker/docker-compose.yml`.
> **Ce que tu dois dire = ce qui est dans le rapport, pas autre chose.**

---

## 🎯 PRÉSENTATION (à dire en 30 secondes)

> *"Docker Compose garantit que tout le monde travaille dans le même environnement, quelle que soit la machine. Un seul `docker compose up` démarre les cinq services, PostgreSQL, Redis, Kafka et Nginx. On a ajouté des healthchecks pour éviter que les services démarrent avant que la base soit prête — c'est un problème classique qu'on a rencontré au début."*

---

## 1. La structure complète du fichier

**Fichier :** `infra/docker/docker-compose.yml`

```
Services lancés :
├── INFRASTRUCTURE
│   ├── postgres     → Base de données (3 BDD dans 1 instance)
│   ├── redis        → Cache (pour pokedex_service)
│   ├── zookeeper    → Coordinateur Kafka (obligatoire)
│   └── kafka        → Broker de messages
│
└── APPLICATIFS
    ├── auth_service     → Port 8001  (dépend de postgres)
    ├── team_service     → Port 8002  (dépend de postgres)
    ├── battle_service   → Port 8003  (dépend de postgres + kafka)
    ├── pokedex_service  → Port 8004  (dépend de redis)
    ├── chat_service     → Port 8005  (dépend de kafka)
    └── gateway          → Port 80    (dépend de tous les services)
```

---

## 2. PostgreSQL — 3 bases en 1 conteneur

```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_MULTIPLE_DATABASES: auth_db,team_db,battle_db
  volumes:
    - postgres_data:/var/lib/postgresql/data        # Persistance
    - ../scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql  # Création des BDD
```

**Pourquoi 3 BDD dans 1 instance PostgreSQL ?**
> "En dev, on mutualise PostgreSQL pour simplifier. En production, chaque service aurait son propre PostgreSQL. Mais le principe reste : chaque service n'accède QU'À SA base (`battle_service` → `battle_db` uniquement)."

**Le `POSTGRES_MULTIPLE_DATABASES` :**
- C'est une variable personnalisée traitée par le script `init-db.sql`
- Ce script crée les 3 bases au premier démarrage

---

## 3. Kafka — Zookeeper obligatoire

```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181

kafka:
  image: confluentinc/cp-kafka:7.5.0
  depends_on:
    - zookeeper          # Kafka NE PEUT PAS démarrer sans Zookeeper
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

**Pourquoi Zookeeper ?**
> "Kafka utilisait Zookeeper pour gérer les métadonnées du cluster (qui est le leader, quels topics existent, etc.). C'est une dépendance obligatoire dans Kafka 7.5. Les versions récentes de Kafka peuvent fonctionner sans (KRaft mode) mais on a gardé la configuration classique."

**Les 2 listeners :**
- `kafka:29092` → pour les services DANS Docker (battle_service, chat_service)
- `localhost:9092` → pour les tests depuis la machine hôte

---

## 4. `depends_on` — L'ordre de démarrage

```yaml
battle_service:
  depends_on:
    - postgres
    - kafka
```

**Ce que ça fait :**
- Docker attend que le conteneur `postgres` soit **démarré** avant de lancer `battle_service`

**⚠️ La limite (à connaître pour l'oral) :**
> *"On a ajouté des healthchecks `pg_isready` sur PostgreSQL avec `depends_on: condition: service_healthy` pour éviter que les services démarrent avant que la base soit prête — un problème classique qu'on a rencontré au début."* (rapport page 4)

**La différence :**
- `depends_on` simple → attend que le conteneur DÉMARRE (postgres peut démarrer en 1s, être prêt en 5s)
- `depends_on: condition: service_healthy` → attend que postgres RÉPONDE à `pg_isready`

---

## 5. Variables d'environnement — Réseau Docker

```yaml
battle_service:
  environment:
    - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/battle_db
    - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
```

**Pourquoi `@postgres:5432` et pas `@localhost:5432` ?**
> "Dans Docker, les services communiquent via leurs **noms de service** (réseau interne Docker). `localhost` référencerait le conteneur lui-même, pas le conteneur postgres. `postgres` est le nom du service défini dans docker-compose, Docker le résout automatiquement."

**Tableau des BDD par service :**

| Service | Database URL | Base |
|---------|-------------|------|
| auth_service | `@postgres:5432/auth_db` | auth_db |
| team_service | `@postgres:5432/team_db` | team_db |
| battle_service | `@postgres:5432/battle_db` | battle_db |
| pokedex_service | `redis://redis:6379` | Redis (pas PostgreSQL) |
| chat_service | *(pas de BDD)* | Mémoire uniquement |

---

## 6. Les volumes — Persistance des données

```yaml
volumes:
  postgres_data:   # Les données PostgreSQL survivent au restart
  redis_data:      # Le cache Redis aussi
```

**Sans volumes :**
- `docker compose down` → toutes les données perdues
- À chaque `docker compose up` : base vide, plus d'utilisateurs, plus de batailles

**Avec volumes :**
- Les données persistent entre les redémarrages

---

## 7. La gateway au dernier

```yaml
gateway:
  depends_on:
    - auth_service
    - team_service
    - battle_service
    - pokedex_service
    - chat_service
```

**Pourquoi gateway dépend de TOUT ?**
> "Nginx doit démarrer en dernier car il route vers les services. Si un service n'est pas encore up quand Nginx démarre, les premières requêtes échoueraient."

---

## 🔥 QUESTIONS PROBABLES SUR Docker Compose

| Question | Réponse courte |
|----------|---------------|
| "Pourquoi Docker Compose ?" | Même environnement partout, 1 commande pour tout lancer |
| "Pourquoi `depends_on` ?" | Garantit l'ordre de démarrage |
| "Pourquoi `depends_on` ne suffit pas ?" | Il attend le démarrage, pas la disponibilité → healthchecks pour ça |
| "Comment les services se parlent ?" | Via noms de service (réseau interne Docker), pas localhost |
| "Pourquoi `kafka:29092` ?" | Port interne Docker, distinct du port 9092 exposé sur l'hôte |
| "Pourquoi Zookeeper ?" | Dépendance obligatoire de Kafka pour gérer les métadonnées du cluster |
| "Pourquoi des volumes ?" | Persister les données PostgreSQL/Redis entre les redémarrages |
| "Quelle difficulté rencontrée ?" | Race condition au démarrage : services up avant que PostgreSQL soit prêt → healthchecks |
