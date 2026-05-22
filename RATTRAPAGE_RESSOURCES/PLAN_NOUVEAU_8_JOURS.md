# 🎯 PLAN SIMPLE 8 JOURS

**Examen** : 29 mai 21h  
**Principe** : Chaque jour je lis des trucs, point final.

---

## 📅 J1 (21 mai) - AUJOURD'HUI

**✅ Déjà fait :**
- FICHE 1, 2, 3 (au coiffeur)

**Maintenant (15h30-17h) :**

```
15h30-16h15 → FICHE 4 (Kafka/SAGA)
16h15-17h00 → FICHE 5 (API Gateway)
```

Si temps restant → GUIDE_DEFENSE_ORAL.md (partie battle/chat)

---

## 📅 J2 (22 mai)

**Matin :**
```
9h-10h → FICHE 6 (Kubernetes)
10h-11h → ARCHITECTURE_ET_CHOIX.md (tout lire)
11h-12h → GUIDE_DEFENSE_ORAL.md (partie justifications)
```

**Après-midi :**
```
14h-15h → Ouvre battle_engine.py, lis calc_advantage()
15h-16h → Ouvre main.py du chat, lis kafka_consumer_loop()
16h-17h → Note 5 questions que tu te poses sur ton code
```

---

## 📅 J3 (23 mai)

**Matin :**
```
9h-10h → Relis FICHE 1, 2, 3
10h-11h → Relis FICHE 4, 5, 6
11h-12h → QUIZ_JOUR_1_2.md (teste-toi)
```

**Après-midi :**
```
14h-15h → Cherche réponses à tes 5 questions sur ton code
15h-16h → Lis docker-compose.yml
16h-17h → Lis k8s/ (juste regarder)
```

---

## 📅 J4 (24 mai)

**Toute la journée :**
```
9h-11h → Explique calc_advantage() à voix haute
11h-13h → Explique kafka_consumer_loop() à voix haute
14h-16h → Pratique 10 questions orales de GUIDE_DEFENSE_ORAL
16h-17h → Essaie d'ajouter un print() dans calc_advantage()
```

---

## 📅 J5 (25 mai)

**Toute la journée :**
```
9h-11h → Simulation orale #1 (enregistre-toi)
11h-13h → Réécoute et note erreurs
14h-16h → Révise les erreurs
16h-17h → Simulation orale #2
```

---

## 📅 J6 (26 mai)

**Toute la journée :**
```
9h-11h → Relis TOUTES les fiches
11h-13h → Relis ton code battle + chat
14h-16h → Quiz complet 30 questions
16h-17h → Simulation orale #3
```

---

## 📅 J7 (27 mai)

**Toute la journée :**
```
9h-12h → Révision ciblée (tes points faibles)
14h-16h → Simulation orale #4 (la dernière)
16h-17h → Prépare 5 slides PowerPoint architecture
```

---

## 📅 J8 (28 mai)

**Matin :**
```
9h-11h → Relis tes notes personnelles
11h-12h → Détente (ne révise plus)
```

**Après-midi : REPOS TOTAL**

```
12h-20h30 → Mange, repose-toi, détends-toi
20h30 → Arrive à l'exam
21h → ORAL
```

---

## ✅ CE QU'IL FAUT RETENIR

**J1-J2** : Lire fiches + ton code  
**J3** : Quiz + infra  
**J4** : Pratique orale + code  
**J5-J7** : Simulations + révisions  
**J8** : Repos

**C'EST TOUT. PAS PLUS COMPLIQUÉ.**

---

## 🎯 MAINTENANT (15h30)

**Vas-y, lis FICHE 4 !**

**Programme aujourd'hui (15h30-17h) :**

```
15h30-16h30 → Lis FICHES 4, 5, 6 (survol)
16h30-17h00 → Regarde TON code battle_service (juste lire, pas coder)
```

**Comment lire les fiches :**
- Survole pour avoir une vue d'ensemble
- Note 1 concept par fiche que tu comprends pas
- Pas de pression, c'est une première lecture

**✅ Validation J1** : Tu as lu les 6 fiches au moins une fois.

---

### ⚡ J2 (22 mai) - THÉORIE + COMPRÉHENSION CODE

**Matin (9h-12h = 3h) : THÉORIE**

```
9h-10h30 → Relis FICHES 1, 2, 3 (approfondir)
10h30-12h → Relis FICHES 4, 5, 6 (approfondir)
```

**Méthode de lecture active :**
1. Lis une fiche
2. Ferme le document
3. Explique à voix haute ce que tu as compris
4. Rouvre si tu as oublié un truc
5. Recommence jusqu'à pouvoir expliquer sans regarder

**Après-midi (14h-17h = 3h) : TON CODE battle_service**

```
14h-15h30 → Lis battle_engine.py
              - Comprends calc_advantage()
              - Comprends TYPE_CHART
              
15h30-17h → Lis routes/battle.py
              - Comprends /turn
              - Comprends le flow complet
```

**Comment lire le code :**
- Lis ligne par ligne en expliquant à voix haute
- Note les parties que tu comprends PAS
- Cherche sur Google si besoin
- **PAS DE CODING**, juste de la LECTURE

**✅ Validation J2** : Tu peux expliquer calc_advantage() sans regarder le code.

---

### ⚡ J3 (23 mai) - THÉORIE + COMPRÉHENSION CODE 2

**Matin (9h-12h = 3h) : TON CODE chat_service**

```
9h-10h30 → Lis main.py (kafka_consumer_loop)
10h30-12h → Lis chat_service.py (broadcast_all vs broadcast)
```

**Questions à te poser :**
- Pourquoi retry_delay = 2 ?
- Que fait asyncio.CancelledError ?
- Comment un message Kafka devient un message WebSocket ?

**Après-midi (14h-17h = 3h) : INFRA (Docker, K8s, Nginx)**

```
14h-15h → Lis docker-compose.yml de TON projet
15h-16h → Lis k8s/ manifests
16h-17h → Lis ARCHITECTURE_ET_CHOIX.md (relecture)
```

**Focus :**
- Comprendre comment les services communiquent
- Comprendre HPA (Horizontal Pod Autoscaler)
- Comprendre Nginx routing

**✅ Validation J3** : Tu peux dessiner l'architecture complète de ton projet.

---

### ⚡ J4 (24 mai) - QUIZ + QUESTIONS ORALES

**Matin (9h-12h = 3h) : QUIZ**

```
9h-10h → QUIZ_JOUR_1_2.md (sans notes)
10h-11h → Corriger + réviser erreurs
11h-12h → QUIZ complet 30 questions (tout le programme)
```

**Après-midi (14h-17h = 3h) : QUESTIONS ORALES**

```
14h-17h → Pratique 20 questions orales
           (voir GUIDE_DEFENSE_ORAL.md partie 5 Q&A)
```

**Méthode :**
- Lis la question
- Chrono 2 min max pour répondre
- Enregistre-toi si possible
- Réécoute et améliore

**✅ Validation J4** : Tu peux répondre aux 20 questions principales.

---

### ⚡ J5 (25 mai) - PRATIQUE CODE (ciblée, pas from scratch)

**Matin (9h-12h = 3h) : EXERCICES calc_advantage()**

```
9h-10h → Explique calc_advantage() ligne par ligne à voix haute
10h-11h → Modifie calc_advantage() pour ajouter un print()
11h-12h → Modifie calc_advantage() pour gérer 3 types au lieu de 2
```

**Après-midi (14h-17h = 3h) : EXERCICES kafka_consumer_loop()**

```
14h-15h → Explique kafka_consumer_loop() ligne par ligne
15h-16h → Trouve et corrige le bug du retry_delay qui ne reset pas
16h-17h → Ajoute un log dans le consumer pour tracer les messages
```

**PAS BESOIN de recoder from scratch** - juste comprendre et modifier.

**✅ Validation J5** : Tu peux modifier ton code en 10-15 min.

---

### ⚡ J6 (26 mai) - SIMULATIONS ORALES

**Toute la journée (9h-17h = 8h) : SIMULATIONS**

```
9h-10h → Prépare 5 slides PowerPoint architecture
10h-11h → Simulation #1 (15 min cours + 15 min projet)
11h-12h → Analyse erreurs simulation #1

14h-15h → Révision points faibles
15h-16h30 → Simulation #2 (15 min cours + 15 min projet)
16h30-17h → Analyse simulation #2
```

**Simulations :**
- Enregistre-toi en vidéo
- Chronomètre 30 min exactement
- Réécoute et note les hésitations

**✅ Validation J6** : Zéro hésitation sur les 10 questions principales.

---

### ⚡ J7 (27 mai) - RÉVISION FINALE THÉORIE

**Matin (9h-12h = 3h) : FICHES**

```
9h-10h → Relis FICHES 1, 2, 3
10h-11h → Relis FICHES 4, 5, 6
11h-12h → Quiz flash (30 questions en 30 min)
```

**Après-midi (14h-17h = 3h) : PROJET**

```
14h-15h → Relis GUIDE_DEFENSE_ORAL.md
15h-16h → Relis ARCHITECTURE_ET_CHOIX.md
16h-17h → Simulation #3 (dernière)

**Matin (2h) :**

```
9h-10h30 (1h30) → Lire FICHE 4 Kafka (PROFOND)
10h30-11h (30min) → Questions flash J1-J2
```

**FICHE 4 - Points critiques :**
- Sync vs Async (REST vs Kafka)
- Producer/Consumer
- Topics (ex: "battle-events")
- Retry avec exponential backoff

**Après-midi (2h) :**

```
14h-16h → OUVRIR ton chat_service et analyser
```

**Ce que tu vas regarder dans chat_service :**

📂 **chat_service/app/main.py**
```python
# kafka_consumer_loop() - LA FONCTION CRITIQUE :

async def kafka_consumer_loop():
    retry_delay = 2  # Commence à 2 secondes
    while True:     # Boucle infinie (lifespan)
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,  # "battle-events"
            settings.KAFKA_TOPIC_CHAT,    # "chat-messages" (2 topics !)
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset="latest",
        )
        try:
            await consumer.start()
            retry_delay = 2  # Reset après succès
            
            async for msg in consumer:
                event = msg.value
                topic = msg.topic  # Routing selon le topic source
                
                if topic == settings.KAFKA_TOPIC_BATTLE:
                    if event.get("type") == "turn_played":
                        # Créer notification bot
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
                    room = event.get("room")
                    if room:
                        await chat_service.broadcast(room, event)
                    else:
                        await chat_service.broadcast_all(event)
                    
        except asyncio.CancelledError:
            await consumer.stop()
            return
        except Exception as e:
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)  # Double, max 30s
        finally:
            await consumer.stop()
```

**Retry Exponential Backoff - CRUCIAL :**
```
Tentative 1 : Erreur → attendre 2s
Tentative 2 : Erreur → attendre 4s
Tentative 3 : Erreur → attendre 8s
Tentative 4 : Erreur → attendre 16s
Tentative 5 : Erreur → attendre 30s (max)
Succès : Reset à 2s
```

📂 **chat_service/app/services/chat_service.py**
```python
# active_connections : Dict[str, List[WebSocket]]
# Exemple : {"red": [ws1, ws2], "blue": [ws3], "battle_123": [ws4, ws5]}

async def broadcast(room: str, message: dict):
    # Envoie à TOUS les WebSocket de cette room
    if room in active_connections:
        for ws in active_connections[room]:
            await ws.send_json(message)

async def broadcast_all(message: dict):
    # Envoie à TOUS les WebSocket connectés (toutes rooms)
    for room in active_connections:
        for ws in active_connections[room]:
            await ws.send_json(message)
```

**Questions à te poser (note les réponses) :**
1. Pourquoi retry_delay = 2 après succès ?
2. Que fait broadcast_all() vs broadcast(room) ?
3. Pourquoi while True dans le consumer ?
4. Comment l'event Kafka devient un message WebSocket ?

**✅ Validation J2** : Tu comprends le flow Kafka → WebSocket dans TON projet.

---

### ⚡ J3 (23 mai) - GATEWAY + K8S + TON INFRA

**Matin (2h) :**

```
9h-10h → FICHE 5 (API Gateway, Nginx)
10h-11h → FICHE 6 (Kubernetes, pods, HPA)
```

**Après-midi (2h) :**

```
14h-15h → OUVRIR ton docker-compose.yml
15h-16h → OUVRIR k8s/ manifests
```

**Ce que tu vas regarder dans ton infra :**

📂 **docker-compose.yml**
```yaml
# Comment tes services communiquent en local

services:
  battle-service:
    build: ./battle_service
    ports:
      - "8001:8000"
    depends_on:
      - postgres
      - kafka
    environment:
      DATABASE_URL: postgresql://...
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092

  chat-service:
    build: ./chat_service
    ports:
      - "8002:8000"
    depends_on:
      - kafka

  nginx:
    image: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - battle-service
      - chat-service
```

📂 **nginx.conf**
```nginx
# Comment Nginx route les requêtes

location /api/battle {
    proxy_pass http://battle-service:8000;
}

location /api/chat {
    proxy_pass http://chat-service:8000;
}

# Nginx = API Gateway qui dispatche vers les bons services
```

📂 **k8s/battle-service-deployment.yaml**
```yaml
# Comment Kubernetes déploie ton service

apiVersion: apps/v1
kind: Deployment
metadata:
  name: battle-service
spec:
  replicas: 3  # 3 instances pour la disponibilité
  template:
    spec:
      containers:
      - name: battle-service
        image: battle-service:latest
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
---
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    name: battle-service
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  # Si CPU > 70% → ajoute des pods automatiquement
```

**Questions à te poser :**
1. Comment Nginx sait vers quel service router ?
2. Pourquoi depends_on dans docker-compose ?
3. Que fait HPA si CPU > 70% ?
4. Différence entre replicas et HPA ?

**✅ Validation J3** : Tu comprends comment TON projet est déployé.

---

### ⚡ J4 (24 mai) - RÉVISION TOTALE

**Full day (4h) :**

```
9h-10h → QUIZ complet SANS notes (refaire)
10h-11h → Révision FICHES 1-6 (relire, surligner)
14h-15h → QUESTIONS_COURS.md (20 questions orales)
15h-16h → Révision TON code (notes clés)
```

**Checklist révision :**
- [ ] Microservices vs monolithe (FICHE 1)
- [ ] GET/POST/PUT/DELETE (FICHE 2)
- [ ] Pydantic models (FICHE 2)
- [ ] async/await (FICHE 2)
- [ ] Database per service (FICHE 3)
- [ ] Kafka producer/consumer (FICHE 4)
- [ ] Saga pattern (FICHE 4)
- [ ] Retry exponential backoff (FICHE 4)
- [ ] API Gateway routing (FICHE 5)
- [ ] Kubernetes pods, HPA (FICHE 6)
- [ ] **TON calc_advantage()**
- [ ] **TON kafka_consumer_loop()**

**✅ Validation J4** : Aucun blanc sur les concepts clés + ton code.

---

### 🔥 J5 (25 mai) - MAÎTRISE BATTLE_SERVICE

**Matin (2h) : Analyse ligne par ligne**

```
9h-10h → Lire battle_engine.py LENTEMENT
          Écris une explication en français de CHAQUE ligne

10h-11h → Lire routes/battle.py LENTEMENT
          Dessine le flow de /turn sur papier
```

**Après-midi (2h) : Code en direct**

```
14h-15h → EXERCICE : Recoder calc_advantage() SANS regarder
          Chrono-toi : 30 min max
          
15h-16h → EXERCICE : Modifier calc_advantage()
          Ajoute un print() des multiplicateurs
          Ajoute un paramètre weather (Feu ×2 si "sunny")
```

**✅ Validation J5** : Tu peux recoder calc_advantage() en 30 min.

---

### 🔥 J6 (26 mai) - MAÎTRISE CHAT_SERVICE

**Matin (2h) : Analyse ligne par ligne**

```
9h-10h → Lire kafka_consumer_loop() LENTEMENT
         Écris une explication en français de CHAQUE ligne

10h-11h → Lire chat_service.py (WebSocket)
          Dessine le flow d'un message Kafka → WS
```

**Après-midi (2h) : Code en direct**

```
14h-15h → EXERCICE : Recoder kafka_consumer_loop() SANS regarder
          Chrono-toi : 30 min max
          
15h-16h → EXERCICE : Debug le consumer
          "Le retry_delay ne reset pas après succès, corrige"
```

**✅ Validation J6** : Tu peux recoder le consumer avec retry en 30 min.

---

### 🔥 J7 (27 mai) - RECONSTRUCTION COMPLÈTE

**Matin (2h) : From scratch**

```
9h-10h → Recoder calc_advantage() + resolve_turn() SANS regarder
10h-11h → Recoder kafka_consumer_loop() SANS regarder
```

**Après-midi (2h) : Modifications**

```
14h-15h → Prof te dit : "Ajoute un print dans calc_advantage"
          Fais-le en 5 min chrono

15h-16h → Prof te dit : "Explique cette ligne du consumer"
          Explique à voix haute CHAQUE ligne
```

**✅ Validation J7** : Tu peux coder et expliquer sans hésiter.

---

### 🎤 J8 (28 mai) - SIMULATIONS ORALES

**Simulation #1 (Matin 2h)**

```
9h-9h15 → Préparation mentale
9h15-9h30 → COURS (15 min enregistré) :
            "Expliquez Kafka et saga pattern"
            "Différence sync vs async"
            "Pourquoi Kubernetes HPA"
            
9h30-9h45 → PROJET (15 min enregistré) :
            "Expliquez battle_service"
            "Comment calc_advantage fonctionne"
            "Pourquoi Kafka entre battle et chat"
            
9h45-11h → Réécoute + note hésitations
```

**Simulation #2 (Après-midi 2h)**

```
14h-14h15 → Révision points faibles simulation #1
14h15-14h45 → ORAL COMPLET #2 (enregistré)
14h45-16h → Réécoute + perfectionne
```

**✅ Validation J8** : Zéro hésitation, tu parles avec assurance.

---

### 🎯 J9 (29 mai) - JOUR J

**Matin (3h) : Révision ciblée**

```
9h-10h → Relire notes clés battle_service + chat_service
10h-11h → Refaire calc_advantage() une dernière fois
11h-12h → Questions probables (QUESTIONS_COURS.md)
```

**Après-midi : REPOS**

```
12h-20h30 → REPOS COMPLET
            - Mange bien
            - Douche
            - Détente
            - NE RÉVISE PLUS
```

**Soir : EXAMEN**

```
20h30 → Arrive 30 min avant
21h00 → ORAL 🎯
```

---

## 🎯 CHECKLIST "JE SUIS PRÊT"

**Cours (30%) :**
- [ ] Je peux expliquer sync vs async avec exemples
- [ ] Je peux expliquer Kafka producer/consumer
- [ ] Je peux expliquer saga pattern choreography
- [ ] Je peux expliquer API Gateway (Nginx)
- [ ] Je peux expliquer Kubernetes HPA

**Projet (70%) :**
- [ ] Je peux recoder calc_advantage() en 30 min
- [ ] Je peux expliquer CHAQUE ligne de calc_advantage()
- [ ] Je peux recoder kafka_consumer_loop() en 30 min
- [ ] Je peux expliquer le retry exponential backoff
- [ ] Je peux dessiner l'architecture complète du projet
- [ ] Je peux expliquer le flow d'un tour de bataille
- [ ] Je peux expliquer comment Kafka → WebSocket
- [ ] Je peux modifier calc_advantage() en direct
- [ ] Je peux débugger le consumer si le prof me montre un bug

**Si 1 seul ❌ → Pratique encore**

---

## 💡 CONSEILS TACTIQUES POUR L'ORAL

### Si le prof te demande de coder :

1. **Respire 3 secondes** avant de commencer
2. **Lis la demande 2 fois** pour être sûr
3. **Explique à voix haute** ce que tu vas faire
4. **Code lentement** (mieux vaut lent que faux)
5. **Assume tes erreurs** ("Ah oui j'ai oublié le await, je corrige")

### Phrases qui sauvent :

- "Je vais d'abord regarder où se trouve cette fonction..."
- "Si je comprends bien, vous voulez que je..."
- "Laissez-moi vérifier que ça fonctionne..."
- "Je pense qu'il faut modifier cette ligne parce que..."

### Phrases à éviter :

- ❌ "Euh... je sais plus"
- ❌ "L'IA m'a aidé pour ça"
- ❌ "J'ai copié ce code"
- ❌ "Je pense que... peut-être... je sais pas"

---

## 🔥 TU AS 32H DISPONIBLES, IL FAUT 14H MINIMUM

**Marge de sécurité : 2.3x** 💪

Tu peux :
- Skiper 2-3 jours complets et QUAND MÊME réussir
- Prendre des pauses
- Dormir suffisamment

**Pas de stress, tu as le temps.** Concentre-toi sur ton code (battle + chat) et le cours viendra naturellement.

---

**🎯 MAINTENANT : Commence le QUIZ (14h38) !**

Fichier : `QUIZ/QUIZ_JOUR_1_2.md`
