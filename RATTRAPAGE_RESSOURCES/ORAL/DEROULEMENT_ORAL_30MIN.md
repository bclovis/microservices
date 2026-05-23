# 📋 DÉROULEMENT DE L'ORAL - 30 MINUTES

> **Consigne officielle (Raphaël LALANNE) :**
> - 15 premières minutes : questions de cours + application dans des cas pratiques
> - 15 dernières minutes : tu présentes ta partie du projet + tu expliques tes choix
>
> **Tu passes : vendredi 29 mai à 20h**

---

## ⏱️ PARTIE 1 : THÉORIE (15 min)

### Ce que ça veut dire
Le prof te pose des questions sur les concepts du cours microservices. Il peut aussi inventer un cas pratique ("j'ai un service X et un service Y, comment tu fais ?"). Il n'y a pas de script prévu — il pose ce qu'il veut.

### Questions de cours à maîtriser

**Monolithe vs Microservices :**
- Monolithe = tout dans 1 seul processus → si ça plante, tout plante
- Microservices = 1 service = 1 responsabilité → scalabilité indépendante, isolation des pannes

**Kafka vs REST inter-service :**
- REST = synchrone, le service attend la réponse → couplage fort
- Kafka = asynchrone, le service publie et continue → découplage, résilience si l'autre est down

**Database-per-service :**
- Chaque service a SA BDD (auth_db, team_db, battle_db, chat_db)
- Pas de JOIN entre services → les services sont autonomes
- Inconvénient : pas de transactions distribuées faciles

**API Gateway :**
- Point d'entrée unique pour tous les clients
- Dans PokeDrafter : Nginx route vers les 5 services, gère CORS, WebSocket
- Ne vérifie PAS le JWT — chaque service le vérifie lui-même

**Kubernetes / scaling :**
- HPA (HorizontalPodAutoscaler) : crée des pods si CPU > seuil
- Le Service K8s fait le load balancing automatiquement entre les pods
- Namespace `pokedrafter` pour isoler les ressources

### Cas pratiques possibles

**"Ajoutez un service de notifications email"**
> Nouveau microservice `notification_service`, s'abonne au topic Kafka `battle-events`, envoie un email quand une bataille se termine, sa propre BDD pour l'historique.

**"Que se passe-t-il si chat_service est down ?"**
> L'event `turn_played` reste dans Kafka. Quand chat_service redémarre, il consomme les events en attente. C'est précisément pour ça qu'on utilise Kafka et pas un appel REST direct.

---

## 🖥️ PARTIE 2 : PROJET (15 min)

### Ce que ça veut dire
Tu présentes **ta partie** (battle, chat, docker, k8s) et tu expliques **pourquoi** tu as fait les choses comme ça. Pas de slides. Le prof regarde ton code avec toi et te pose des questions dessus.

---

### Ta partie selon les consignes officielles
> Battle Service, Chat Service, Kafka integration, Docker, Kubernetes

---

### Ce que tu dois être capable d'expliquer

#### battle_service — `routes/battle.py` → route `play_turn`

```python
# 1. Calcul des avantages de types
fa, fb = calc_advantage(types_red, types_blue)   # battle_engine.py
result = resolve_turn(types_red, types_blue)      # "A", "B" ou "draw"

# 2. Sauvegarde en BDD D'ABORD
db.add(BattleTurn(...))
await db.commit()

# 3. Kafka APRÈS
await publish_battle_event("turn_played", {...})
```

**Tes choix à justifier :**
- BDD avant Kafka → si Kafka fail, le tour est quand même enregistré
- `battle_engine.py` séparé des routes → calcul pur, testable seul, pas de dépendance BDD
- `kafka_service.py` avec producer lazy (singleton) → créé au 1er appel, pas au démarrage

---

#### chat_service — `main.py` → `kafka_consumer_loop`

```python
while True:                        # tourne en continu
    try:
        consumer = AIOKafkaConsumer(
            "battle-events",       # topic 1
            "chat-messages",       # topic 2
        )
        await consumer.start()
        retry_delay = 2            # reset après succès
        async for msg in consumer:
            if msg.topic == "battle-events": ...
            elif msg.topic == "chat-messages": ...
    except Exception:
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 30)  # 2→4→8→16→30s max
```

**Tes choix à justifier :**
- `while True` → le consumer doit tourner indéfiniment, c'est son rôle
- Retry exponentiel → si Kafka est temporairement down, on ne spam pas les reconnexions
- 2 topics dans 1 consumer → 1 seule boucle gère tout, routage via `msg.topic`
- `asyncio.create_task()` dans lifespan → tourne en arrière-plan sans bloquer le serveur HTTP

---

#### docker-compose

**Tes choix à justifier :**
- 4 BDD séparées (auth_db, team_db, battle_db, chat_db) → database-per-service, chaque service est autonome
- `depends_on` simple sans healthcheck → limitation connue, en prod on ajouterait `pg_isready`
- `restart: always` → si un service crash, Docker le redémarre automatiquement
- Kafka sur port `29092` en interne et `9092` exposé → réseau Docker interne vs accès depuis l'hôte

---

#### Kubernetes

**Tes choix à justifier :**
- Namespace `pokedrafter` → isolation des ressources du projet
- 5 Deployments + 5 Services ClusterIP → chaque service accessible uniquement en interne
- Gateway en NodePort `30080` → seul point d'entrée exposé vers l'extérieur
- Nginx comme gateway → routing centralisé, CORS, WebSocket

---

### Si le prof demande "qu'est-ce que vous changeriez ?"

| Ce qui manque | Ce que tu dirais |
|---------------|-----------------|
| Healthchecks | Ajouter `condition: service_healthy` + `pg_isready` dans docker-compose |
| Event `battle_ended` | Ajouter `publish_battle_event("battle_ended", ...)` dans la route `/end` |
| HPA Kubernetes | Ajouter un HorizontalPodAutoscaler sur battle_service (beaucoup de calculs CPU) |

---

## ✅ À FAIRE / ❌ À ÉVITER

| ✅ À FAIRE | ❌ À ÉVITER |
|-----------|------------|
| Dire "j'ai fait ça PARCE QUE..." | Inventer une réponse |
| Dire "je ne suis pas sûr mais je dirais que..." si tu bloques | Silence total |
| Parler lentement, prendre 5 secondes pour réfléchir | Critiquer ton propre code sans proposer d'amélioration |

---

## 🎓 CE QU'IL FAUT ABSOLUMENT MAÎTRISER

1. `play_turn()` dans `battle_service/routes/battle.py` — ligne par ligne
2. `kafka_consumer_loop()` dans `chat_service/main.py` — while True + retry + 2 topics
3. `docker-compose.yml` — 4 BDD + Kafka + pourquoi depends_on sans healthcheck
4. Kubernetes — namespace, Deployment, ClusterIP, NodePort 30080
5. Théorie — Kafka vs REST, database-per-service, monolithe vs microservices

---

## 💪 DERNIERS CONSEILS

- **Jeudi 28** : Relis battle.py et chat main.py à voix haute
- **Vendredi 29 matin** : Relis la fiche 01 (Introduction Microservices)
- **À 20h dans la salle** : Respire, parle lentement, c'est OK de réfléchir avant de répondre

**BON COURAGE ! 🚀**
