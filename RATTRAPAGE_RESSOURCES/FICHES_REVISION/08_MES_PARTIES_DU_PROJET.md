# 🎯 FICHE 08 : MES PARTIES DU PROJET - EXPLIQUER ET JUSTIFIER

> ⚠️ Cette fiche est basée sur TON vrai code. C'est ce que tu dois maîtriser pour l'oral.
> Tu présentes TES parties : battle_service, chat_service, Docker Compose, Nginx, Kubernetes.

---

## 🥊 PARTIE 1 : battle_service

### 1.1 Le moteur F(A) — `calc_advantage()`

**Fichier :** `api/battle_service/app/services/battle_engine.py`

```python
def calc_advantage(types_a, types_b):
    # Si un des Pokémon n'a pas de types → avantages nuls
    if not types_a or not types_b:
        return 0.0, 0.0

    # Calcul du score de A contre B
    fa = 0.0
    for w in types_a:      # Pour chaque type de A
        val = 1.0
        for y in types_b:  # Contre chaque type de B
            val *= get_multiplier(w, y)   # Multiplie les effets
        fa += val          # Somme

    # Calcul du score de B contre A (symétrique)
    fb = 0.0
    for y in types_b:
        val = 1.0
        for w in types_a:
            val *= get_multiplier(y, w)
        fb += val

    return round(fa, 4), round(fb, 4)
```

**Ce que ça fait :**
- Calcule F(A) = puissance du Pokémon A contre B
- Calcule F(B) = puissance du Pokémon B contre A
- `get_multiplier("Feu", "Plante")` renvoie `2.0` (Feu fort contre Plante)

**Exemple concret :**
- Pokémon A = `["Feu"]`, Pokémon B = `["Plante", "Sol"]`
- F(A) : w="Feu" → get_multiplier("Feu","Plante")×get_multiplier("Feu","Sol") = 2.0×2.0 = 4.0
- F(B) : y="Plante" → get_multiplier("Plante","Feu") = 0.5 ; y="Sol" → get_multiplier("Sol","Feu") = 2.0
  fb = 0.5 + 2.0 = 2.5
- F(A) = 4.0 > F(B) = 2.5 → A gagne

**Avantage de la double boucle :**
> "On itère sur tous les types de l'attaquant contre tous les types du défenseur. Ça fonctionne naturellement avec 1, 2 ou plus de types, sans logique spéciale pour les mono-types."

---

### 1.2 `resolve_turn()` — Qui gagne le tour ?

```python
def resolve_turn(types_a, types_b):
    fa, fb = calc_advantage(types_a, types_b)  # Appelle calc_advantage
    if fa > fb:
        return "A"   # Rouge gagne
    if fb > fa:
        return "B"   # Bleu gagne
    return "draw"    # Égalité
```

**Simple :** Compare F(A) et F(B), retourne qui est plus fort.

---

### 1.3 Les routes de bataille

**Fichier :** `api/battle_service/app/routes/battle.py`

#### Route 1 : Créer une salle — `POST /battles/`

```python
@router.post("/", response_model=BattleOut)
async def create_battle(payload: BattleCreate, db: AsyncSession = Depends(get_db)):
    status_initial = "en_cours" if payload.player_blue_id else "en_attente"
    battle = Battle(
        player_red_id=payload.player_red_id,
        player_blue_id=payload.player_blue_id,
        status=status_initial,
    )
    db.add(battle)
    await db.commit()
    return battle
```

**Logique :**
- Si les 2 joueurs sont connus → `"en_cours"` directement
- Si le joueur bleu n'est pas encore là → `"en_attente"` (le 2e joueur rejoint après)

**Question probable :** "Pourquoi un statut en_attente ?"
> "Pour le mode multijoueur : le joueur rouge crée la salle, attend que quelqu'un la rejoigne via /join."

---

#### Route 2 : Rejoindre une salle — `POST /battles/{id}/join`

```python
@router.post("/{battle_id}/join", response_model=BattleOut)
async def join_battle(battle_id: UUID, payload: BattleJoin, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(404, "Bataille introuvable")
    if battle.status != "en_attente":
        raise HTTPException(400, "La salle n'est plus en attente")
    if battle.player_blue_id is not None:
        raise HTTPException(400, "La salle est déjà complète")
    if str(battle.player_red_id) == str(payload.player_blue_id):
        raise HTTPException(400, "Impossible de rejoindre sa propre salle")
    battle.player_blue_id = payload.player_blue_id
    battle.status = "en_cours"
    await db.commit()
    return battle
```

**Les 4 vérifications (à connaître) :**
1. La bataille existe
2. Elle est bien en attente (pas déjà commencée)
3. Le slot bleu n'est pas déjà pris
4. Le joueur ne peut pas jouer contre lui-même

**Question probable :** "Pourquoi vérifier que le joueur ne rejoint pas sa propre salle ?"
> "Règle métier de base : dans un jeu PvP, on ne peut pas jouer contre soi-même. C'est une protection côté serveur, même si l'interface l'interdit aussi."

---

#### Route 3 : Jouer un tour — `POST /battles/{id}/turn` (LA PLUS IMPORTANTE)

```python
@router.post("/{battle_id}/turn", response_model=TurnResult)
async def play_turn(battle_id: UUID, payload: TurnPlay, db: AsyncSession = Depends(get_db)):
    # 1. Vérifications
    battle = await db.get(Battle, battle_id)
    if not battle: raise HTTPException(404, ...)
    if battle.status == "termine": raise HTTPException(400, ...)

    # 2. Calcul du tour
    fa, fb = calc_advantage(payload.types_red, payload.types_blue)
    result = resolve_turn(payload.types_red, payload.types_blue)

    # 3. Sauvegarde en BDD
    turn_number = battle.current_turn + 1
    turn = BattleTurn(
        battle_id=battle_id,
        turn_number=turn_number,
        score_red=str(fa),
        score_blue=str(fb),
        result=result,
    )
    db.add(turn)
    battle.current_turn = turn_number
    await db.commit()

    # 4. Notification Kafka (APRÈS la BDD)
    await publish_battle_event("turn_played", {
        "battle_id": str(battle_id),
        "turn_number": turn_number,
        "result": result,
    })

    # 5. Retour au client
    return turn
```

**LES 5 ÉTAPES À MÉMORISER :**
1. **Vérifier** que la bataille existe et n'est pas terminée
2. **Calculer** les scores F(A) et F(B)
3. **Sauvegarder** le tour en BDD (AVANT Kafka !)
4. **Publier** l'event Kafka pour notifier le chat
5. **Retourner** le résultat au client

**Question clé :** "Pourquoi la BDD AVANT Kafka ?"
> "La donnée (le tour joué) est critique. Kafka sert à notifier le chat, qui est non-critique. Si Kafka est down, le tour est quand même sauvegardé et le jeu continue. L'inverse serait une erreur d'architecture."

---

### 1.4 Kafka Producer — `publish_battle_event()`

**Fichier :** `api/battle_service/app/services/kafka_service.py`

```python
async def publish_battle_event(event_type: str, data: dict) -> None:
    try:
        producer = await get_producer()
        payload = {"type": event_type, **data}
        await producer.send_and_wait(settings.KAFKA_TOPIC_BATTLE, payload)
    except Exception as exc:
        _producer = None  # Reset du singleton
        logger.warning("Kafka unavailable, event dropped: %s", exc)
        # PAS de raise → le tour continue quand même !
```

**Points importants :**
- `send_and_wait` → attend la confirmation que Kafka a reçu l'event
- Si Kafka fail → on log un warning et on continue (pas d'exception)
- `_producer = None` → force la reconnexion au prochain appel

**Question probable :** "Que se passe-t-il si Kafka est down ?"
> "La fonction attrape l'exception, la logue, et retourne sans planter. Le tour est déjà enregistré en BDD donc le jeu continue normalement, juste sans notification dans le chat."

---

## 💬 PARTIE 2 : chat_service

### 2.1 Consumer Kafka avec retry — `kafka_consumer_loop()`

**Fichier :** `api/chat_service/app/main.py`

```python
async def kafka_consumer_loop():
    retry_delay = 2    # Délai initial : 2 secondes
    while True:        # Tourne INDÉFINIMENT
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset="latest",   # Lit uniquement les NOUVEAUX messages
        )
        try:
            await consumer.start()
            logger.warning("[Kafka] Consumer connecté")
            retry_delay = 2    # RESET du délai après connexion réussie
            
            async for msg in consumer:   # Boucle sur chaque message
                event = msg.value
                if event.get("type") == "turn_played":
                    # Formater la notification
                    winner = "Rouge" if event["result"] == "A" else "Bleu"
                    notif = {
                        "author": "bot",
                        "content": f"Tour {event['turn_number']} — {winner} remporte le tour !",
                        "is_bot": True
                    }
                    # Envoyer à tous les clients WebSocket connectés
                    await chat_service.broadcast_all(notif)
        
        except asyncio.CancelledError:
            await consumer.stop()
            return    # Arrêt propre si le serveur shutdown
        
        except Exception as e:
            # Kafka down → attendre et réessayer
            logger.warning("Kafka indisponible, retry dans %ds", retry_delay)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)   # 2→4→8→16→30→30→30...
        
        finally:
            try:
                await consumer.stop()   # Toujours fermer proprement
            except Exception:
                pass
```

**Les 4 concepts à expliquer :**

| Concept | Code | Pourquoi |
|---------|------|---------|
| `while True` | Boucle infinie | Service qui tourne en permanence |
| `retry_delay = 2` | Reset après succès | Évite de punir les erreurs temporaires |
| `min(retry_delay * 2, 30)` | Backoff exponentiel | Ne spamme pas Kafka si down |
| `asyncio.CancelledError` | Arrêt propre | Fermer le consumer avant de couper |

**Question clé :** "Pourquoi l'exponential backoff ?"
> "Au démarrage de Docker Compose, Kafka prend 10-15 secondes à être prêt. Sans backoff, le consumer essaierait de se connecter 100 fois par seconde, saturant les logs. Avec backoff : 2s, 4s, 8s, 16s, 30s max. Ça évite de spammer et laisse le temps à Kafka de démarrer."

---

### 2.2 Démarrage du consumer — `lifespan`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(kafka_consumer_loop())  # Démarre le consumer
    yield                                               # L'app tourne
    task.cancel()                                      # Stop le consumer à la fermeture
```

**Question probable :** "Pourquoi un lifespan et pas directement dans `main()` ?"
> "Le lifespan FastAPI est le point officiel pour les tâches de fond qui doivent vivre toute la durée de l'app. `create_task` lance le consumer en parallèle sans bloquer l'API. À la fermeture, `task.cancel()` arrête proprement."

---

## 🐳 PARTIE 3 : Docker Compose

**Fichier :** `infra/docker/docker-compose.yml`

### Structure générale

```
Services démarrés :
├── postgres       → Base de données (3 BDD : auth_db, team_db, battle_db)
├── redis          → Cache (pour pokedex_service)
├── zookeeper      → Coordinateur de Kafka (obligatoire pour Kafka)
├── kafka          → Broker de messages
├── auth_service   → Port 8001
├── team_service   → Port 8002
├── battle_service → Port 8003 (dépend de postgres + kafka)
├── pokedex_service→ Port 8004 (dépend de redis)
├── chat_service   → Port 8005 (dépend de kafka)
└── gateway        → Port 80 (Nginx, dépend de tous les services)
```

### `depends_on` — L'ordre de démarrage

```yaml
battle_service:
  depends_on:
    - postgres
    - kafka

chat_service:
  depends_on:
    - kafka
```

**Question probable :** "Pourquoi `depends_on` ?"
> "Sans ça, Docker pourrait démarrer battle_service avant que PostgreSQL soit prêt, causant une erreur de connexion. `depends_on` garantit l'ordre."

**⚠️ Limite à connaître :** `depends_on` attend que le conteneur démarre, pas qu'il soit prêt. On a ajouté des healthchecks pour ça (`pg_isready`).

---

### Les variables d'environnement

```yaml
battle_service:
  environment:
    - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/battle_db
    - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
```

**Ce que ça fait :**
- `@postgres:5432` → `postgres` est le nom du service Docker (pas `localhost`)
- `kafka:29092` → pareil, le nom du service Docker
- Chaque service a SA propre database : `battle_db`, `auth_db`, `team_db` → **database-per-service**

**Question probable :** "Pourquoi `kafka:29092` et pas `localhost:9092` ?"
> "Dans Docker, les services communiquent via leurs noms de service (réseau interne Docker). `localhost` référencerait le conteneur lui-même. `kafka:29092` est le port interne, `9092` est exposé sur l'hôte pour les tests locaux."

---

## 🌐 PARTIE 4 : Nginx Gateway

**Fichier :** `api/gateway/nginx.conf`

```nginx
# Définition des services en amont
upstream auth_service    { server auth_service:8001; }
upstream team_service    { server team_service:8002; }
upstream battle_service  { server battle_service:8003; }
upstream pokedex_service { server pokedex_service:8004; }
upstream chat_service    { server chat_service:8005; }

server {
    listen 80;   # Seul port exposé à l'extérieur

    # Routing par préfixe d'URL
    location /api/auth    { proxy_pass http://auth_service/api/auth; }
    location /api/teams   { proxy_pass http://team_service/api/teams; }
    location /api/battle  { proxy_pass http://battle_service/api/battle; }
    location /api/pokedex { proxy_pass http://pokedex_service/api/pokedex; }
    location /api/chat    { proxy_pass http://chat_service/api/chat; }

    # WebSocket — configuration SPÉCIALE
    location /ws/ {
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;      # Header obligatoire
        proxy_set_header Connection "upgrade";        # Header obligatoire
        proxy_pass http://chat_service;
    }
}
```

### Le principe

```
Client (navigateur)
        ↓  POST /api/battle/battles/
     Nginx :80
        ↓  route vers battle_service:8003
  battle_service
        ↓
  Retour au client
```

**Pourquoi Nginx et pas exposer chaque service ?**
> "Sans gateway, le frontend devrait connaître l'adresse et le port de chaque service (8001, 8002, 8003...). Nginx centralise tout sur le port 80. C'est plus sécurisé (les services backend ne sont jamais exposés directement) et plus simple pour le client."

---

### ⚠️ La partie WebSocket — la difficulté rencontrée

```nginx
location /ws/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_pass http://chat_service;
}
```

**Pourquoi ces headers ?**

HTTP normal : `1.0` ou `1.1`, une requête → une réponse, connexion fermée.

WebSocket : Le client envoie un **handshake HTTP** spécial ("Je veux passer en WebSocket"), le serveur répond "OK" avec `Upgrade: websocket`, et la connexion reste **ouverte en permanence**.

Sans `proxy_set_header Upgrade $http_upgrade`, Nginx ne transmet pas ce header au service → le handshake échoue → WebSocket ne fonctionne pas.

**Question clé :** "Vous avez eu des difficultés avec le WebSocket ?"
> "Oui ! Le WebSocket ne fonctionnait pas à travers Nginx. Le problème venait des headers `Upgrade` et `Connection` que Nginx supprime par défaut lors du proxying. Il faut les réajouter explicitement avec `proxy_set_header`. Sans ça, le handshake WebSocket échoue et la connexion ne s'établit pas."

---

## ☸️ PARTIE 5 : Kubernetes

### Principe général

Docker Compose = développement local  
Kubernetes = production (plusieurs serveurs, scalabilité, haute dispo)

**Tes 6 fichiers YAML :**

| Fichier | Contenu |
|---------|---------|
| `namespace.yaml` | Crée l'espace de travail `pokedrafter` |
| `postgres.yaml` | Déploie PostgreSQL avec stockage persistant |
| `redis.yaml` | Déploie Redis avec stockage persistant |
| `kafka.yaml` | Déploie Zookeeper + Kafka Broker |
| `services.yaml` | Déploie les 5 microservices |
| `gateway.yaml` | Nginx exposé en NodePort :30080 |

---

### Les concepts K8s à connaître (les 4 essentiels)

#### 1. `Deployment`
Ce qui dit à K8s "lance X copies de ce container"

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: pokedrafter
spec:
  replicas: 1     # 1 instance
  selector:
    matchLabels:
      app: auth-service
  template:
    spec:
      containers:
        - name: auth-service
          image: pokedrafter/auth-service:latest
          ports:
            - containerPort: 8000
```

#### 2. `Service`
Ce qui permet à un pod d'être accessible par d'autres pods

```yaml
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: pokedrafter
spec:
  selector:
    app: auth-service   # Cible les pods avec ce label
  ports:
    - port: 8001        # Port accessible dans le cluster
      targetPort: 8000  # Port dans le container
```

#### 3. `Namespace`
Un espace isolé pour regrouper toutes les ressources du projet

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pokedrafter   # Toutes nos ressources sont dans cet espace
```

**Pourquoi un namespace ?**
> "Pour isoler le projet des autres applications qui tourneraient sur le même cluster. Comme un dossier qui groupe toutes nos ressources."

#### 4. `PersistentVolumeClaim (PVC)`
Pour que les données PostgreSQL/Redis survivent aux redémarrages

```yaml
# Dans postgres.yaml
volumeClaimTemplates:
  - spec:
      resources:
        requests:
          storage: 1Gi   # 1 gigabyte de stockage
```

**Pourquoi ?**
> "Par défaut les containers K8s sont éphémères. Si le pod PostgreSQL redémarre, toutes les données sont perdues. Le PVC monte un volume persistant qui survit aux redémarrages."

---

### Différence Docker Compose vs Kubernetes

| | Docker Compose | Kubernetes |
|-|----------------|-----------|
| Usage | Dev local | Production |
| Démarrage | `docker compose up` | `kubectl apply -f k8s/` |
| Scaling | Manuel (`--scale`) | Automatique (HPA) |
| Réseau | Réseau Docker | DNS interne K8s |
| Si un service crash | Restart si configuré | Restart automatique garanti |
| Multi-serveurs | Non (1 machine) | Oui (cluster) |

**Question probable :** "Pourquoi passer de Docker Compose à Kubernetes ?"
> "Docker Compose est parfait pour le dev : simple, rapide, une seule commande. Mais en production il faut de la haute disponibilité, du scaling automatique et la gestion de plusieurs serveurs. Kubernetes gère tout ça nativement."

---

## 🎯 RÉSUMÉ : CE QUE TU DOIS DIRE POUR CHAQUE PARTIE

### battle_service
> "J'ai implémenté le moteur F(A) qui calcule l'avantage de types entre deux Pokémon. Pour chaque tour, on calcule les scores, on sauvegarde en BDD, puis on publie un event Kafka pour que le chat soit notifié. La BDD est prioritaire sur Kafka : si Kafka est down, le jeu continue quand même."

### chat_service
> "J'ai implémenté le consumer Kafka avec une boucle infinie et un backoff exponentiel. Le problème qu'on a rencontré : au démarrage, Kafka n'est pas encore prêt, donc le consumer plantait. La solution : retry automatique avec délai croissant (2s → 4s → 8s → 30s max)."

### Docker Compose
> "J'ai orchestré l'ensemble des services avec Docker Compose. Chaque service a ses propres variables d'environnement, ses dépendances via `depends_on`, et sa propre base de données. Un seul `docker compose up` lance tout."

### Nginx
> "Nginx est le point d'entrée unique sur le port 80. Il route vers le bon service selon le préfixe d'URL. La difficulté : le WebSocket nécessite des headers spéciaux (`Upgrade`, `Connection`) que Nginx supprime par défaut."

### Kubernetes
> "J'ai créé les manifests YAML pour déployer sur cluster. Un namespace pour isoler le projet, des Deployments pour chaque service, des Services pour le réseau interne, et des PVC pour persister les données PostgreSQL et Redis."

---

## 📋 QUESTIONS PROBABLES SUR TES PARTIES

1. "Expliquez-moi `calc_advantage()` avec un exemple concret"
2. "Que se passe-t-il si Kafka est down pendant un tour ?"
3. "Pourquoi un `while True` dans le consumer ?"
4. "Comment les services se trouvent entre eux dans Docker ?"
5. "Pourquoi les headers `Upgrade` pour WebSocket ?"
6. "Quelle différence entre Docker Compose et Kubernetes ?"
7. "C'est quoi un PersistentVolumeClaim ?"
8. "Pourquoi `depends_on` ne suffit pas pour attendre que PostgreSQL soit prêt ?"
