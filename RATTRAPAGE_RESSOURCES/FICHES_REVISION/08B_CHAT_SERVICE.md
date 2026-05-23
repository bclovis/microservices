# 💬 FICHE 08B : chat_service — WebSocket + Kafka Consumer

> Basée sur le rapport (page 4) + ton vrai code.
> **Ce que tu dois dire = ce qui est dans le rapport, pas autre chose.**

---

## 🎯 PRÉSENTATION (à dire en 30 secondes)

> *"Le chat_service gère deux choses : le WebSocket pour la communication temps réel entre joueurs, et un consumer Kafka qui écoute les événements de bataille et les broadcast à tous les clients connectés. Le problème qu'on a rencontré : Kafka n'est pas prêt immédiatement au démarrage, donc le consumer plantait. On a mis en place une boucle de retry avec backoff exponentiel."*

---

## 1. Le problème qu'on a résolu (IMPORTANT pour l'oral)

**Ce qu'il faut dire (du rapport) :**
> *"La première version abandonnait le consumer dès le premier échec de connexion à Kafka. En pratique, au démarrage de la stack Docker Compose, Kafka met quelques secondes à être opérationnel, donc le consumer crashait systématiquement au boot."*

**La solution :**
> *"Une boucle while True avec backoff exponentiel (2s à 30s max) pour se reconnecter automatiquement. C'est un pattern classique pour les consumers Kafka dans un environnement où les services démarrent dans un ordre non garanti."*

---

## 2. Le code complet — `kafka_consumer_loop()`

**Fichier :** `api/chat_service/app/main.py`

```python
async def kafka_consumer_loop():
    retry_delay = 2         # Délai initial = 2 secondes
    
    while True:             # Tourne INDÉFINIMENT tant que le service est up
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,    # ← Topic 1 : events de bataille
            settings.KAFKA_TOPIC_CHAT,      # ← Topic 2 : messages du chat
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",     # Lit seulement les NOUVEAUX messages
        )
        try:
            await consumer.start()
            retry_delay = 2     # ← RESET après connexion réussie
            
            async for msg in consumer:      # Pour chaque message Kafka reçu
                event = msg.value           # Désérialisé automatiquement (JSON → dict)
                topic = msg.topic           # ← De quel topic vient ce message ?
                
                if topic == settings.KAFKA_TOPIC_BATTLE:
                    # Événement de bataille → notif dans le chat
                    etype = event.get("type", "")
                    if etype == "turn_played":
                        result = event.get("result", "?")
                        turn = event.get("turn_number", "?")
                        winner = "Rouge" if result == "A" else ("Bleu" if result == "B" else "Egalité")
                        notif = {
                            "author": "bot",
                            "content": f"Tour {turn} — {winner} remporte le tour !",
                            "is_bot": True
                        }
                        await chat_service.broadcast_all(notif)

                elif topic == settings.KAFKA_TOPIC_CHAT:
                    # Message de chat → broadcast dans la room ou global
                    room = event.get("room")
                    if room:
                        await chat_service.broadcast(room, event)   # Room ciblée
                    else:
                        await chat_service.broadcast_all(event)     # Broadcast global
        
        except asyncio.CancelledError:
            await consumer.stop()
            return                      # Arrêt propre si le serveur shutdown
        
        except Exception as e:
            logger.warning("Kafka unavailable, retrying in %ds : %s", retry_delay, e)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)    # ← Backoff exponentiel
        
        finally:
            try:
                await consumer.stop()   # Toujours fermer proprement
            except Exception:
                pass
```

### Pourquoi 2 topics ?

Le consumer écoute **deux topics en même temps** :
- `KAFKA_TOPIC_BATTLE` → reçoit les events du battle_service (ex: `turn_played`)
- `KAFKA_TOPIC_CHAT` → reçoit les messages de chat envoyés via Kafka

**`msg.topic`** permet de router le traitement selon la source du message.

---

## 3. Décortiquer le backoff exponentiel

### Progression des délais

```
1ère erreur  → attend 2s
2ème erreur  → attend 4s   (2 × 2)
3ème erreur  → attend 8s   (4 × 2)
4ème erreur  → attend 16s  (8 × 2)
5ème erreur  → attend 30s  (min(32, 30) = 30)
6ème erreur  → attend 30s  (min(60, 30) = 30)
... reste à 30s max
```

### Pourquoi ce pattern ?

**Sans backoff :**
```
Erreur → retry immédiat → erreur → retry → erreur → retry...
= 100 tentatives par seconde = logs illisibles + CPU gaspillé
```

**Avec backoff exponentiel :**
```
Erreur → attend → retry → si toujours down → attend plus longtemps
= laisse le temps à Kafka de démarrer + logs propres
```

### Pourquoi reset `retry_delay = 2` après succès ?

```python
await consumer.start()
retry_delay = 2   # ← ICI
```

> "Si la connexion a fonctionné une fois et qu'une erreur TEMPORAIRE se produit plus tard (ex: coupure réseau de 1 seconde), on ne veut pas attendre 30s. On repart de 2s pour les prochaines erreurs."

---

## 4. Le traitement d'un event Kafka

Quand battle_service envoie un event `"turn_played"`, voilà ce que reçoit chat :

```python
event = {
    "type": "turn_played",
    "battle_id": "abc-123",
    "turn_number": 3,
    "pokemon_red": "Dracaufeu",
    "pokemon_blue": "Bulbizarre",
    "score_red": "4.0",
    "score_blue": "1.25",
    "result": "A"
}
```

Chat transforme ça en notification lisible :
```python
winner = "Rouge"   # car result == "A"
notif = {
    "author": "bot",
    "content": "Tour 3 — Rouge remporte le tour !",
    "is_bot": True
}
await chat_service.broadcast_all(notif)   # Envoie à TOUS les WebSocket connectés
```

---

## 5. Le démarrage du consumer — `lifespan`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()                                      # Initialise la BDD chat
    task = asyncio.create_task(kafka_consumer_loop())    # Lance en arrière-plan
    yield                                                # L'app FastAPI tourne
    task.cancel()                                        # Stop propre à la fermeture
    await chat_service.stop_producer()                   # Ferme le producer Kafka
```

**Ce que ça fait :**
- `create_task` → lance `kafka_consumer_loop()` **en parallèle** de l'API
- L'API répond aux requêtes WebSocket ET consomme Kafka en même temps
- `task.cancel()` → à la fermeture du serveur, le consumer s'arrête proprement

**Question probable :** "Pourquoi `create_task` et pas `await` ?"
> "Avec `await`, l'app attendrait que `kafka_consumer_loop()` se termine (jamais, c'est un `while True`). Avec `create_task`, les deux tournent en parallèle dans la boucle asyncio."

---

## 6. WebSocket — c'est quoi et comment ça fonctionne

### Qu'est-ce qu'un WebSocket ?

**HTTP classique :** le client envoie une requête → le serveur répond → la connexion se ferme. Le serveur ne peut jamais envoyer quelque chose tout seul.

**WebSocket :** le client ouvre une connexion → elle **reste ouverte** → les deux côtés peuvent s'envoyer des messages à tout moment, sans nouvelle requête.

```
HTTP :    Client → [requête] → Serveur → [réponse] → connexion fermée

WebSocket: Client ←——— connexion persistante ———→ Serveur
                  ← push message à tout moment →
```

**Pourquoi on en a besoin ici :** le chat doit afficher les messages en temps réel. Sans WebSocket, le navigateur devrait poller (GET toutes les Xs) pour vérifier s'il y a de nouveaux messages — lent et inefficace.

---

### Comment ça fonctionne dans le projet

**URL de connexion :**
```
ws://localhost/ws/chat/red?username=Betsaleel
ws://localhost/ws/chat/blue?username=Betsaleel
```

- `red` ou `blue` = la "room" (salle de chat)
- `username` = query param (non vérifié — faille F3 de la fiche 10)

**Étapes :**

```
1. Angular ouvre : new WebSocket("ws://host/ws/chat/red?username=...")
2. Nginx route vers chat_service:8005
3. chat_service accepte la connexion → ajoute le WebSocket dans :
       _connections = { "red": [ws1, ws2, ...], "blue": [ws3, ...] }
4. Connexion reste ouverte indéfiniment
5. Quand un event arrive (message utilisateur OU event Kafka) :
       broadcast("red", message)  → envoie à TOUS les ws de la room "red"
       broadcast_all(message)     → envoie à TOUS les ws toutes rooms confondues
6. Quand l'utilisateur ferme l'onglet → WebSocket se ferme → retiré de _connections
```

**Les connexions sont stockées en mémoire (dans le processus Python) :**
```python
_connections: Dict[str, List[WebSocket]] = {}
```
C'est la **faille F6** — si on passe à 2 replicas K8s, chaque replica a ses propres `_connections`. Un message envoyé au replica 1 n'atteint pas les clients connectés au replica 2.

---

### Ce que fait chat_service côté WebSocket dans le code

```
Client envoie un message via WebSocket
    → chat_service reçoit
    → sauvegarde en chat_db (persistance)
    → publie dans Kafka topic "chat-messages"
    → kafka_consumer_loop reçoit l'event
    → broadcast à tous les connectés
```

**Le chat a SA propre BDD (`chat_db`) :**
Les messages sont persistés dans `chat_db` → l'historique survit aux redémarrages du service. `get_history()` lit depuis la BDD.

---

## 🔥 QUESTIONS PROBABLES SUR chat_service

| Question | Réponse courte |
|----------|---------------|
| "Expliquez `kafka_consumer_loop()`" | Boucle infinie, connexion Kafka, broadcast WebSocket, retry si erreur |
| "Pourquoi `while True` ?" | Service qui tourne en permanence, toujours à l'écoute |
| "C'est quoi le backoff exponentiel ?" | Délai croissant : 2s → 4s → 8s → 30s max pour ne pas spammer Kafka |
| "Pourquoi reset le délai après succès ?" | Pour ne pas pénaliser les prochaines erreurs temporaires |
| "chat_service a-t-il une BDD ?" | Oui — `chat_db`. `publish_message()` sauve en BDD avant Kafka. `get_history()` lit depuis la BDD. |
| "Que se passe-t-il quand Kafka envoie un event ?" | Le consumer le reçoit, formate la notif, broadcast à tous les WebSocket |
| "Pourquoi `auto_offset_reset="latest"` ?" | On veut seulement les NOUVEAUX events, pas rejouer l'historique au démarrage |
