# INDEX — Fiches de Révision Contenu Module

> **Examen oral de rattrapage** — vendredi 29 mai 2026 à 20h  
> **Format** : 30 min (15 min théorie | 15 min présentation projet)  
> **Étudiant** : Betsaleel CLOVIS  
> **Parties projet** : battle_service, chat_service, Kafka, Docker Compose, Kubernetes

---

## Navigation rapide

| Fiche | Séance | Contenu principal |
|-------|--------|------------------|
| [S1_INTRO_MICROSERVICES.md](S1_INTRO_MICROSERVICES.md) | Séance 1 (5 nov) | Définition Martin Fowler, monolithe vs microservices, avantages/inconvénients |
| [S1_FASTAPI_BASES.md](S1_FASTAPI_BASES.md) | Séance 1 (5 nov) | Installation, Hello World, path/query/body params, exceptions, middlewares, CORS |
| [S2_FASTAPI_AVANCE.md](S2_FASTAPI_AVANCE.md) | Séance 2 (12 nov) | JWT, OAuth2, APIRouter, BackgroundTasks, TP2 complet, TP3 SQLAlchemy |
| [S3_BDD_MICROSERVICES.md](S3_BDD_MICROSERVICES.md) | Séance 3 (19 nov) | ACID, BDD par service, cohérence éventuelle, Outbox pattern, Saga |
| [S3_KAFKA_COMPLET.md](S3_KAFKA_COMPLET.md) | Séance 3 (19 nov) | Kafka théorie, Broker/Topic/Partition/Producer/Consumer, kafka-python code |
| [S3_TP4_KAFKA_CODE.md](S3_TP4_KAFKA_CODE.md) | Séance 3 (19 nov) | Code TP4 annoté : Outbox, producer, consumers, payment 70%, notifications |
| [S4_API_GATEWAY_ET_TP5.md](S4_API_GATEWAY_ET_TP5.md) | Séance 4 (3 déc) | Gateway définition, reverse proxy, rate limiting, cache, TP5 code complet |
| [S4_MICROSERVICES_REDESIGN.md](S4_MICROSERVICES_REDESIGN.md) | Séance 4 (3 déc) | Etsy/Netflix/Shopify — décomposition monolithes |
| [S5_KUBERNETES_ET_TP6.md](S5_KUBERNETES_ET_TP6.md) | Séance 5 (15 jan) | Deployment, Service, HPA, ConfigMap, Secret, Ingress, TP6 code complet |
| [S6_PROJET_POKEDRAFTER.md](S6_PROJET_POKEDRAFTER.md) | Projet final | Formule F(A), architecture, Kafka topics, battle_service, chat_service, Fernet |

---

## Stratégie de révision recommandée

### Pour les 15 minutes de théorie
Revoir dans l'ordre :
1. **Définition microservices** (S1_INTRO) — La définition de Martin Fowler + avantages/inconvénients
2. **FastAPI** (S1_FASTAPI_BASES + S2_FASTAPI_AVANCE) — Rapidement : JWT, APIRouter, Depends
3. **Kafka** (S3_KAFKA_COMPLET) — Broker, Topic, Producer, Consumer, Consumer Group
4. **API Gateway** (S4_API_GATEWAY_ET_TP5) — Définition, rôles, cache, rate limiting
5. **Kubernetes** (S5_KUBERNETES_ET_TP6) — Deployment vs Service, HPA, ConfigMap vs Secret

### Pour les 15 minutes de présentation projet
Maîtriser parfaitement :
1. **La formule F(A)** — Savoir l'expliquer avec un exemple (voir S6_PROJET_POKEDRAFTER)
2. **Architecture globale** — Qui fait quoi, sur quel port, quelle BDD
3. **battle_service** — Kafka producer (aiokafka), chiffrement Fernet, moteur de combat
4. **chat_service** — WebSocket, rooms par équipe, broadcast
5. **Docker Compose** — Comment démarrer le projet
6. **Kubernetes** — Manifests créés, HPA, Secrets pour clés API

---

## Points critiques à ne pas oublier

### FastAPI
- `pip install "fastapi[all]"` — avec les crochets !
- `uvicorn main:app --reload`
- `@app.middleware("http") async def mon_middleware(request: Request, call_next):`
- `raise HTTPException(status_code=404, detail="Not found")`

### Kafka (TP4)
- `KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=...)`
- `KafkaConsumer('topic', group_id='service-name', auto_offset_reset='earliest')`
- Pattern Outbox : créer Order ET OutboxEvent dans la même transaction DB, thread séparé publie sur Kafka

### API Gateway (TP5)
- `httpx.AsyncClient()` pour appels async entre services
- Rate limit : `{ip: datetime}` — vérifier que `elapsed < RATE_LIMIT_SECONDS`
- Cache : `{key: {"data": ..., "expires_at": datetime.now() + timedelta(minutes=10)}}`

### Kubernetes (TP6)
- `imagePullPolicy: Never` obligatoire pour images locales minikube
- `eval $(minikube docker-env)` avant de builder
- HPA exige `resources.requests` dans le deployment
- Noms de services K8s = DNS interne (`http://user-service:8000` pas `localhost:8001`)
- ConfigMap = non-sensible (URLs, params) vs Secret = sensible (passwords, tokens)

### Projet PokeDrafter
- Formule F(A) : somme des produits des multiplicateurs de types
- Chiffrement Fernet (AES symétrique) entre Red et Blue via Kafka
- `aiokafka` (async) pour battle_service et chat_service
- WebSocket FastAPI : `@router.websocket("/ws/chat/{team}")`

---

## Commandes utiles à connaître

```bash
# FastAPI
uvicorn main:app --reload --port 8000

# Kafka (TP4)
docker compose up -d
docker exec broker kafka-topics --list --bootstrap-server localhost:9092

# Kubernetes (TP6)
eval $(minikube docker-env)           # Pointer vers le Docker de minikube
kubectl apply -f k8s/                  # Déployer tout
kubectl get pods --watch               # Surveiller les pods
kubectl get hpa --watch                # Surveiller l'autoscaling
kubectl logs pod-name -f               # Logs en temps réel

# PokeDrafter
cd infra/docker && docker compose up --build -d
cd ../../web && npm start -- --port 4300
```
