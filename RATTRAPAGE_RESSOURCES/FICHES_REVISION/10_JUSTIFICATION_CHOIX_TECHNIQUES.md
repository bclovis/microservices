# 🛡️ FICHE 10 — JUSTIFICATION DE TOUS LES CHOIX TECHNIQUES

> **Objectif :** Pour chaque ligne de code ou décision d'architecture dans tes parties, savoir répondre "pourquoi ?" en moins de 30 secondes.
> **Source de vérité :** `PokeDrafter_GitHub_Latest` — tout est vérifié sur le vrai code.

---

## PARTIE A — BATTLE SERVICE

### A1 — `battle_engine.py` est un fichier SÉPARÉ des routes

**Code réel :**
```python
# routes/battle.py
from app.services.battle_engine import calc_advantage, resolve_turn
```

**Question :** "Pourquoi vous n'avez pas mis le calcul directement dans la route ?"

**Réponse :**
- `battle_engine.py` = fonction **pure** (entrée → sortie, zéro dépendance BDD ou Kafka)
- Testable tout seul : `assert resolve_turn(["Feu"], ["Plante"]) == "A"`
- Si on change la formule, on touche UNE seule ligne dans UN seul fichier
- Les routes restent lisibles — elles orchestrent, elles ne calculent pas

---

### A2 — La formule `calc_advantage` — ce qu'elle fait exactement

**Code réel :**
```python
def calc_advantage(types_a, types_b):
    fa = 0.0
    for w in types_a:       # chaque type de A
        val = 1.0
        for y in types_b:   # multiplié contre chaque type de B
            val *= get_multiplier(w, y)
        fa += val
    # idem fb avec B attaquant A
    return round(fa, 4), round(fb, 4)
```

**Question :** "Comment vous calculez l'avantage de type ?"

**Réponse :**
- Pour chaque type de A, on calcule le produit des multiplicateurs contre tous les types de B
- On somme ces produits → `fa`
- On fait pareil dans l'autre sens → `fb`
- Si `fa > fb` → A gagne (`"A"`), si `fb > fa` → B gagne (`"B"`), sinon draw
- Exemple : Feu contre Plante → `get_multiplier("Feu", "Plante") = 2.0` → `fa = 2.0 > fb = 0.5` → résultat `"A"`

---

### A3 — BDD AVANT Kafka dans `play_turn`

**Code réel (ordre exact) :**
```python
# 1. CALCUL
fa, fb = calc_advantage(payload.types_red, payload.types_blue)
result = resolve_turn(...)

# 2. SAUVEGARDE BDD D'ABORD
turn = BattleTurn(...)
db.add(turn)
battle.current_turn = turn_number
await db.commit()
await db.refresh(turn)

# 3. KAFKA APRÈS
await publish_battle_event("turn_played", {...})
```

**Question :** "Pourquoi vous sauvegardez en BDD avant d'envoyer sur Kafka ?"

**Réponse :**
- Si Kafka est down au moment du `publish_battle_event`, le tour est **quand même enregistré** en BDD
- L'inverse (Kafka d'abord) serait dangereux : event publié mais BDD non commitée si crash → état incohérent
- Le tour existe → c'est la priorité. Le chat peut manquer un event, c'est gérable. Perdre un tour de bataille, non.

---

### A4 — Le producer Kafka est un **singleton lazy**

**Code réel (`kafka_service.py`) :**
```python
_producer: AIOKafkaProducer | None = None

async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:           # créé au 1er appel seulement
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await p.start()
        _producer = p
    return _producer
```

**Question :** "Pourquoi le producer n'est pas créé au démarrage dans le lifespan ?"

**Réponse :**
- **Lazy init** : le producer est créé seulement quand un premier event est publié
- Si Kafka est down au démarrage, le service démarre quand même — pas de crash au boot
- En dev, ça évite de bloquer le démarrage si Kafka n'est pas lancé
- Contrastez avec `chat_service` qui lui démarre le consumer **dès le démarrage** (obligatoire, il doit écouter en continu)

---

### A5 — Kafka optionnel : on ne crash pas si Kafka fail

**Code réel :**
```python
async def publish_battle_event(event_type: str, data: dict) -> None:
    global _producer
    try:
        producer = await get_producer()
        await producer.send_and_wait(settings.KAFKA_TOPIC_BATTLE, payload)
    except Exception as exc:
        _producer = None        # reset le singleton pour le prochain appel
        logger.warning("Kafka unavailable, event dropped: %s", exc)
        # PAS de raise → la route répond quand même 200
```

**Question :** "Que se passe-t-il si Kafka est down quand un tour est joué ?"

**Réponse :**
- L'exception est **catchée** — la route `play_turn` répond normalement (le client voit un succès)
- L'event est perdu (dropped) mais la partie continue — on log un warning
- On reset `_producer = None` pour que le prochain appel retente la connexion
- **Choix conscient** : le chat est "nice to have" en temps réel, pas bloquant pour la bataille

---

### A6 — Il n'y a PAS d'event `battle_ended`

**Code réel (route `/end`) :**
```python
@router.post("/{battle_id}/end")
async def end_battle(...):
    # compte les tours
    wins_red = sum(1 for t in turns if t.result == "A")
    wins_blue = sum(1 for t in turns if t.result == "B")
    # détermine le winner
    battle.winner = "red" | "blue" | "draw"
    battle.status = "termine"
    await db.commit()
    return {"winner": battle.winner, ...}
    # ⚠️ AUCUN publish_battle_event ici
```

**Question :** "Vous ne publiez pas d'event quand la bataille se termine ?"

**Réponse honnête :**
- Non, c'est une **limitation du code actuel** — la route `/end` ne publie rien sur Kafka
- Seul `turn_played` est publié (dans `/turn`)
- Ce qu'on améliorerait : ajouter `await publish_battle_event("battle_ended", {"winner": battle.winner, ...})` à la fin de `end_battle`
- En l'état, le chat peut afficher les tours en temps réel mais pas la fin de la partie

---

### A7 — La route `forfeit` — pourquoi elle existe

**Code réel :**
```python
@router.post("/{battle_id}/forfeit")
async def forfeit(battle_id: UUID, player_id: UUID, ...):
    if str(battle.player_red_id) == str(player_id):
        battle.winner = "blue"
    elif str(battle.player_blue_id) == str(player_id):
        battle.winner = "red"
    else:
        raise HTTPException(403, "Joueur pas dans cette bataille")
```

**Question :** "Pourquoi une route forfeit séparée de end ?"

**Réponse :**
- `/end` calcule le winner par compte des tours gagnés (logique normale)
- `/forfeit` déclare le winner DIRECTEMENT sans compter — un joueur abandonne, l'autre gagne automatiquement
- Sécurité : vérification que `player_id` est bien dans la bataille (HTTP 403 sinon)

---

## PARTIE B — CHAT SERVICE

### B1 — Le `while True` dans `kafka_consumer_loop`

**Code réel :**
```python
async def kafka_consumer_loop():
    retry_delay = 2
    while True:                     # ← boucle infinie
        consumer = AIOKafkaConsumer(...)
        try:
            await consumer.start()
            ...
        except asyncio.CancelledError:
            await consumer.stop()
            return                  # ← seule sortie propre
        except Exception as e:
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)
        finally:
            try:
                await consumer.stop()
            except Exception:
                pass
```

**Question :** "Pourquoi une boucle infinie ?"

**Réponse :**
- Le consumer Kafka DOIT tourner en permanence — c'est son rôle de service
- Si Kafka drop la connexion, on doit **reconnecter automatiquement** → ça nécessite un while True
- La seule sortie propre est `CancelledError` → levé par `task.cancel()` dans le lifespan shutdown
- Sans `while True`, une erreur Kafka tue le consumer définitivement

---

### B2 — Le retry exponentiel

**Code réel :**
```python
except Exception as e:
    logger.warning("Kafka unavailable, retrying in %ds : %s", retry_delay, e)
    await asyncio.sleep(retry_delay)
    retry_delay = min(retry_delay * 2, 30)  # 2→4→8→16→30→30→30...
```

**Question :** "Pourquoi pas un retry toutes les secondes ?"

**Réponse :**
- Si Kafka est complètement down, retry chaque seconde = spam de connexions inutiles
- Backoff exponentiel : on attend de plus en plus longtemps → laisse le temps à Kafka de redémarrer
- Cap à 30s : on ne patiente pas indéfiniment entre deux tentatives
- Le `retry_delay = 2` est **reseté après chaque connexion réussie** — les erreurs passées ne pénalisent pas la suite

---

### B3 — Reset du `retry_delay` après succès

**Code réel :**
```python
await consumer.start()
logger.info("[Kafka] Consumer connected ...")
retry_delay = 2         # ← reset ICI, après start() réussi
async for msg in consumer:
    ...
```

**Question :** "Pourquoi vous remettez le delay à 2 ?"

**Réponse :**
- Si la connexion a réussi, la prochaine déconnexion sera peut-être temporaire → on repart de zéro
- Sans ce reset, après 5 déconnexions le delay serait à 30s même pour une micro-coupure réseau de 1s
- C'est une **politique de retry pragmatique** : punir les crashes répétés, pas les coupures isolées

---

### B4 — 1 seul consumer pour 2 topics

**Code réel :**
```python
consumer = AIOKafkaConsumer(
    settings.KAFKA_TOPIC_BATTLE,   # "battle-events"
    settings.KAFKA_TOPIC_CHAT,     # "chat-messages"
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    ...
)
...
async for msg in consumer:
    if msg.topic == settings.KAFKA_TOPIC_BATTLE:
        # traitement battle → broadcast_all avec message bot
    elif msg.topic == settings.KAFKA_TOPIC_CHAT:
        # traitement chat → broadcast room ou broadcast_all
```

**Question :** "Pourquoi pas un consumer par topic ?"

**Réponse :**
- aiokafka supporte plusieurs topics dans un seul consumer → 1 boucle suffit
- 2 consumers = 2 coroutines = 2 tâches asyncio à gérer, à annuler, à reconnecter
- Le routage via `msg.topic` est simple et lisible
- Moins de connexions vers Kafka = moins de ressources

---

### B5 — `asyncio.create_task()` dans le lifespan

**Code réel :**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(kafka_consumer_loop())   # ← tâche en background
    yield                                                # ← le serveur HTTP démarre
    task.cancel()                                        # ← shutdown propre
    await chat_service.stop_producer()
```

**Question :** "Pourquoi `create_task` et pas `await kafka_consumer_loop()` ?"

**Réponse :**
- `await kafka_consumer_loop()` = on attend que la fonction se termine → JAMAIS (c'est un `while True`)
- Le serveur HTTP ne démarrerait jamais, bloqué sur la boucle Kafka
- `create_task` = la coroutine tourne **en arrière-plan** sans bloquer le lifespan
- Au shutdown, `task.cancel()` lève `CancelledError` → la boucle se termine proprement

---

### B6 — `auto_offset_reset="latest"`

**Code réel :**
```python
consumer = AIOKafkaConsumer(
    ...
    auto_offset_reset="latest",   # ← pas "earliest"
)
```

**Question :** "Pourquoi `latest` et pas `earliest` ?"

**Réponse :**
- `"latest"` = on consomme les events arrivés DEPUIS que le consumer s'est connecté
- `"earliest"` = on rejouerait TOUS les events depuis le début → au redémarrage on afficherait des centaines de vieux messages
- Pour un chat en temps réel, c'est normal de ne pas rejouer l'historique au redémarrage
- Si on voulait de la persistance totale, il faudrait `"earliest"` + stocker l'offset en BDD

---

### B7 — `finally: consumer.stop()`

**Code réel :**
```python
        except asyncio.CancelledError:
            await consumer.stop()
            return
        except Exception as e:
            ...
        finally:
            try:
                await consumer.stop()
            except Exception:
                pass
```

**Question :** "Pourquoi stop() à deux endroits ?"

**Réponse :**
- `CancelledError` : sortie propre → `stop()` puis `return`
- `finally` : exécuté dans TOUS les autres cas (Exception normale) → garantit que le consumer est bien stoppé avant la reconnexion
- Sans `finally`, un consumer zombie pourrait rester ouvert côté Kafka entre deux tentatives

---

## PARTIE C — DOCKER COMPOSE

### C1 — 1 seul postgres avec 4 BDD (pas 4 containers postgres)

**Code réel :**
```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_MULTIPLE_DATABASES: auth_db,team_db,battle_db,chat_db
  volumes:
    - ../scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
```

**Question :** "Vous avez un seul postgres mais 4 bases de données — c'est du database-per-service ?"

**Réponse :**
- Techniquement, le principe database-per-service = chaque service a une BDD **isolée** (schéma séparé, pas de partage)
- En prod, on aurait 4 instances postgres séparées (ou 4 pods K8s séparés)
- En dev/démo, 1 instance avec 4 databases isolées = **compromis pragmatique** → moins de RAM, setup plus rapide
- Les services n'ont PAS accès aux bases des autres (chaque connection string pointe sur sa propre DB)

---

### C2 — `depends_on` simple sans healthcheck

**Code réel :**
```yaml
battle_service:
  depends_on:
    - postgres
    - kafka
```

**Question :** "Comment vous êtes sûr que postgres est prêt quand battle_service démarre ?"

**Réponse honnête :**
- On ne l'est pas — c'est une **limitation connue**
- `depends_on` simple attend juste que le container postgres soit **démarré** (processus lancé), pas qu'il soit **prêt** (accepte des connexions)
- SQLAlchemy async retente la connexion, donc en pratique ça marche
- En prod, on ajouterait :
```yaml
depends_on:
  postgres:
    condition: service_healthy
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
```

---

### C3 — Kafka sur deux ports : `29092` interne et `9092` externe

**Code réel :**
```yaml
kafka:
  ports:
    - "9092:9092"
  environment:
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
```

**Question :** "Pourquoi deux ports pour Kafka ?"

**Réponse :**
- `kafka:29092` = listener **interne** au réseau Docker → les services (battle_service, chat_service) l'utilisent avec `KAFKA_BOOTSTRAP_SERVERS=kafka:29092`
- `localhost:9092` = listener **externe** → pour tester depuis l'hôte avec un client Kafka local (kafkacat, Kafka UI)
- Les deux ne peuvent pas être le même port car les clients Docker et hôte ont des résolutions DNS différentes
- `kafka:29092` fonctionne seulement à l'intérieur du réseau Docker bridge

---

### C4 — Zookeeper requis pour Kafka

**Code réel :**
```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181

kafka:
  depends_on:
    - zookeeper
  environment:
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
```

**Question :** "Pourquoi vous avez besoin de Zookeeper ?"

**Réponse :**
- Confluent Platform 7.5 (version utilisée) nécessite Zookeeper pour la coordination du broker Kafka
- Zookeeper gère : l'élection du leader, la liste des brokers, les métadonnées des topics
- Kafka 3.x+ (KRaft mode) peut fonctionner sans Zookeeper, mais pas la version 7.5 Confluent
- En prod on pourrait migrer vers KRaft pour simplifier l'infra

---

### C5 — `restart: always` sur tous les services

**Code réel :**
```yaml
auth_service:
  restart: always

battle_service:
  restart: always
```

**Question :** "Pourquoi `restart: always` ?"

**Réponse :**
- Si un service crash (exception non catchée, OOM, etc.), Docker le redémarre automatiquement
- Sans ça, un crash = service mort jusqu'à intervention manuelle
- `always` = redémarre même après `docker-compose stop` (différent de `unless-stopped`)
- En prod on utiliserait Kubernetes pour ça, mais en dev Docker Compose c'est la bonne pratique

---

### C6 — Les ports exposés (8001-8005) en dev

**Code réel :**
```yaml
auth_service:
  ports:
    - "8001:8000"    # hôte:container
battle_service:
  ports:
    - "8003:8000"
```

**Question :** "Pourquoi exposer les ports des services si vous avez un gateway ?"

**Réponse :**
- En **production**, on n'exposerait PAS ces ports — tout passerait par le gateway (port 80)
- En **développement**, exposer 8001-8005 permet de tester chaque service directement (Swagger UI, curl)
- C'est un choix délibéré pour faciliter le debug — en prod, ces ports seraient supprimés ou bloqués par firewall

---

## PARTIE D — KUBERNETES

### D1 — Namespace `pokedrafter`

**Code réel (`namespace.yaml`) :**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pokedrafter
```

**Question :** "Pourquoi un namespace dédié ?"

**Réponse :**
- Isole les ressources du projet des autres dans le cluster
- `kubectl get pods -n pokedrafter` ne montre que les pods PokeDrafter
- RBAC possible : donner accès à un namespace sans exposer le reste du cluster
- Évite les collisions de noms (deux projets peuvent avoir un service appelé `gateway` dans des namespaces différents)

---

### D2 — ClusterIP (par défaut) pour les services internes

**Code réel (`services.yaml`) :**
```yaml
kind: Service
metadata:
  name: battle-service
  namespace: pokedrafter
spec:
  # type: ClusterIP ← par défaut (non écrit = ClusterIP)
  selector:
    app: battle-service
  ports:
    - port: 8003
      targetPort: 8000
```

**Question :** "C'est quoi le type de vos services K8s ?"

**Réponse :**
- `ClusterIP` = accessible uniquement **depuis l'intérieur du cluster** — c'est le défaut quand `type:` n'est pas spécifié
- Les services métier (auth, team, battle, pokedex, chat) ne sont PAS exposés à l'extérieur
- Seul le gateway est en NodePort pour être accessible depuis l'hôte
- C'est le pattern correct : exposition minimale, tout passe par le gateway

---

### D3 — NodePort `30080` sur le gateway seulement

**Code réel (`gateway.yaml`) :**
```yaml
kind: Service
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
```

**Question :** "Comment vous accédez à l'application depuis l'extérieur ?"

**Réponse :**
- `NodePort` ouvre le port `30080` sur **chaque nœud** du cluster → `http://<node-ip>:30080`
- En local (Minikube) : `http://$(minikube ip):30080`
- Le gateway (Nginx) reçoit la requête et la route vers le bon service interne (ClusterIP)
- En prod cloud, on utiliserait un `LoadBalancer` ou un `Ingress` à la place de NodePort

---

### D4 — `replicas: 1` pour tous les services

**Code réel :**
```yaml
spec:
  replicas: 1
```

**Question :** "Pourquoi une seule réplique ? C'est scalable ça ?"

**Réponse honnête :**
- Non, `replicas: 1` = pas de haute disponibilité
- C'est un choix de **simplicité pour le projet** — pas d'overhead de gestion de plusieurs pods
- Pour un vrai contexte prod :
  - `battle_service` : 2-3 replicas (calculs CPU, fort trafic)
  - `pokedex_service` : 2-3 replicas (nombreuses requêtes GET)
  - `auth_service` : 2 replicas minimum (critique, doit être toujours up)
- On aurait ajouté un **HPA** pour scale automatiquement selon la charge CPU

---

### D5 — Même variable `kafka:29092` en K8s qu'en Docker

**Code réel (`services.yaml`) :**
```yaml
- name: KAFKA_BOOTSTRAP_SERVERS
  value: kafka:29092
```

**Question :** "Comment battle_service trouve Kafka en K8s ?"

**Réponse :**
- En K8s, le service Kafka a pour `metadata.name: kafka` dans le même namespace
- Kubernetes DNS résout `kafka` → IP du Service Kafka automatiquement
- La variable d'env est identique à Docker Compose (`kafka:29092`) → cohérence totale, zéro changement de config
- Le port `29092` = port interne du container Kafka, exposé via le Service K8s sur le même port

---

## PARTIE E — QUESTIONS TRANSVERSALES

### E1 — Pourquoi async/await partout ?

**Question :** "Pourquoi vous utilisez `async def` et non des fonctions synchrones ?"

**Réponse :**
- FastAPI + Uvicorn = serveur **ASGI** → supporte le vrai async Python
- `await db.commit()` = ne bloque pas le thread pendant l'IO BDD → le serveur peut traiter d'autres requêtes en attendant
- `await producer.send_and_wait()` = idem pour Kafka
- Avec des fonctions synchrones, chaque requête bloquerait le thread → throughput très limité
- 1 worker Uvicorn peut gérer des centaines de requêtes simultanées grâce à l'async

---

### E2 — Pourquoi Kafka entre battle_service et chat_service ?

**Question :** "Vous auriez pu faire un appel HTTP de battle_service vers chat_service. Pourquoi Kafka ?"

**Réponse :**
- **Découplage** : `battle_service` ne connaît pas l'existence de `chat_service` — il publie juste un event
- **Résilience** : si chat_service est down, l'event reste dans Kafka et sera consommé au redémarrage. Avec HTTP, l'event est perdu ou il faut gérer le retry manuellement
- **Extensibilité** : demain on peut ajouter `notification_service` qui s'abonne aussi à `battle-events` sans toucher à battle_service
- **Asynchrone** : battle_service n'attend pas la réponse de chat_service → pas de latence ajoutée sur play_turn

---

### E3 — JWT : chaque service vérifie lui-même

**Question :** "Qui vérifie le JWT dans votre architecture ?"

**Réponse :**
- **Chaque service** vérifie le JWT dans son propre `dependencies.py` via `python-jose`
- Nginx (gateway) ne vérifie PAS le JWT — il route seulement
- **Avantage** : pas de SPOF (Single Point of Failure) sur la validation auth
- **Inconvénient** : le secret JWT doit être partagé entre tous les services (variable d'env `SECRET_KEY`)
- `auth_service` CRÉE les tokens (`security.py`), les autres les VÉRIFIENT uniquement

---

### E4 — `battle_engine.py` : le commentaire `# TODO: optimiser ce dict`

**Dans le code réel :**
```python
# TODO: optimiser ce dict, c'est un peu sale
# import random  # utilisé pour debug, à enlever plus tard
TYPE_CHART = { ... }
```

**Question :** "Je vois des TODO dans votre code, vous ne les avez pas traités ?"

**Réponse honnête :**
- Le `TYPE_CHART` est un gros dictionnaire qui fonctionne correctement mais qui n'est pas optimisé pour la lisibilité
- On pourrait le charger depuis un fichier JSON externe ou une matrice numpy pour les calculs
- Le `import random` commenté est un artefact de debug — à supprimer en prod
- C'est du code fonctionnel avec des pistes d'amélioration identifiées — le TODO honnête vaut mieux que cacher le problème

---

## RÉCAP RAPIDE — LES 10 CHOIX LES PLUS PROBABLES À L'ORAL

| # | Question | Réponse en 1 phrase |
|---|---------|---------------------|
| 1 | BDD avant Kafka ? | Si Kafka fail, le tour est quand même sauvegardé |
| 2 | Pourquoi Kafka pas REST ? | Découplage + résilience si chat down |
| 3 | Pourquoi while True ? | Consumer doit tourner en permanence + auto-reconnect |
| 4 | Retry exponentiel ? | Évite de spammer Kafka si il est down, reset après succès |
| 5 | Producer lazy ? | Service démarre même si Kafka down, créé au 1er besoin |
| 6 | depends_on sans healthcheck ? | Limitation connue, restart:always + SQLAlchemy retente |
| 7 | kafka:29092 vs 9092 ? | 29092 = interne Docker, 9092 = accès depuis l'hôte |
| 8 | ClusterIP + NodePort 30080 ? | Services internes jamais exposés, tout passe par gateway |
| 9 | battle_engine.py séparé ? | Fonction pure, testable seul, routes lisibles |
| 10 | 1 postgres 4 BDD ? | Compromis dev : isolation des données, moins de RAM |
