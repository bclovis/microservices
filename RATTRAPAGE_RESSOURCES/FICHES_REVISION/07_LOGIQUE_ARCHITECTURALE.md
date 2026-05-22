# 🧠 FICHE 07 : LOGIQUE & RAISONNEMENT ARCHITECTURAL

## 🎯 OBJECTIF
Cette fiche t'apprend **COMMENT PENSER** face aux questions de l'oral, pas juste mémoriser des réponses.

---

## 📋 TYPE 1 : QUESTIONS "QUE SE PASSE-T-IL SI..." (Analyse de panne)

### 🔍 LA MÉTHODE EN 4 ÉTAPES

**Exemple :**
> "Que se passe-t-il si le chat_service est down quand battle_service envoie un event ?"

#### ÉTAPE 1 : Identifier le TYPE de communication
**Question à te poser :** Comment ces 2 services communiquent ?
- REST (synchrone) ?
- Kafka (asynchrone) ?
- WebSocket ?

**Dans ton projet :** battle → Kafka → chat = **ASYNCHRONE**

---

#### ÉTAPE 2 : Comprendre le COMPORTEMENT du mécanisme
**Question à te poser :** Que fait Kafka quand un consumer est down ?

**Réponse :**
- Kafka **stocke** les messages (persistance)
- Les messages restent dans le topic
- Aucun message n'est perdu

**Si c'était REST :** L'appel échouerait, erreur 500, message perdu

---

#### ÉTAPE 3 : Analyser la RÉCUPÉRATION
**Question à te poser :** Que se passe-t-il quand le service redémarre ?

**Réponse :**
- chat_service se reconnecte à Kafka
- Il consomme tous les events en attente (depuis son dernier offset)
- Les messages sont traités dans l'ordre

---

#### ÉTAPE 4 : Conclure avec le POURQUOI de l'architecture
**Question à te poser :** Pourquoi ce choix architectural ?

**Réponse :**
> "C'est exactement pour ça qu'on utilise Kafka et pas REST : la résilience. Le battle_service n'est pas bloqué, et aucun event n'est perdu."

---

### 🎯 TEMPLATE UNIVERSEL : "QUE SE PASSE-T-IL SI [SERVICE] EST DOWN ?"

```
1. TYPE DE COMM ? → Synchrone ou Asynchrone
2. COMPORTEMENT ? → Stockage ou Échec
3. RÉCUPÉRATION ? → Retry, Queue, Perte
4. POURQUOI ? → Justifier le choix architectural
```

---

### 🔥 EXEMPLES APPLIQUÉS

#### Question : "Que se passe-t-il si Kafka est down quand battle_service publie ?"

**ÉTAPE 1 :** Type de comm → battle publie dans Kafka  
**ÉTAPE 2 :** Comportement → La méthode `publish_battle_event()` lève une exception  
**ÉTAPE 3 :** Récupération → 
- L'event N'EST PAS enregistré
- Le tour est quand même sauvegardé en BDD (priorité = persistance)
- Pas de notification envoyée au chat

**ÉTAPE 4 :** Pourquoi → On priorise la sauvegarde du tour (donnée critique) sur la notification (non critique)

**Amélioration possible :**
- Ajouter un retry avec backoff dans `publish_battle_event()`
- Ou stocker les events non-publiés dans une table `outbox` pour retry ultérieur

---

#### Question : "Que se passe-t-il si auth_service est down ?"

**ÉTAPE 1 :** Type de comm → REST synchrone (API Gateway → auth_service)  
**ÉTAPE 2 :** Comportement → Timeout ou erreur 503 Service Unavailable  
**ÉTAPE 3 :** Récupération → 
- L'utilisateur ne peut pas se connecter
- Les requêtes authentifiées échouent (token non validé)

**ÉTAPE 4 :** Pourquoi → 
- L'auth est critique, pas de contournement possible
- Amélioration : mettre un cache sur la validation JWT (Redis) pour survivre à une panne courte

---

#### Question : "Que se passe-t-il si PostgreSQL du battle_service est down ?"

**ÉTAPE 1 :** Type de comm → Connexion BDD locale  
**ÉTAPE 2 :** Comportement → Toutes les routes qui font des queries échouent  
**ÉTAPE 3 :** Récupération → 
- Attendre que PostgreSQL redémarre
- Les autres services continuent de fonctionner (isolation)

**ÉTAPE 4 :** Pourquoi → 
- Database-per-service : si battle_db down, auth_db et team_db continuent
- Amélioration : réplication PostgreSQL (master-slave)

---

## 📋 TYPE 2 : QUESTIONS "COMMENT AJOUTER..." (Extension d'architecture)

### 🔍 LA MÉTHODE EN 5 ÉTAPES

**Exemple :**
> "Si je vous demande d'ajouter un service de notifications email, vous le feriez comment ?"

#### ÉTAPE 1 : Définir le RÔLE du nouveau service
**Question à te poser :** Qu'est-ce qu'il fait exactement ?

**Réponse :** 
- Envoie des emails quand un événement important se produit (bataille terminée, équipe créée, etc.)

---

#### ÉTAPE 2 : Identifier les SOURCES de données
**Question à te poser :** D'où viennent les infos dont il a besoin ?

**Réponse :**
- Événements de bataille → topic Kafka `battle-events`
- Infos utilisateur → REST call vers auth_service (pour récupérer l'email)

---

#### ÉTAPE 3 : Choisir le MODE de communication
**Question à te poser :** Synchrone ou asynchrone ?

**Règle d'or :**
- **Asynchrone (Kafka)** si :
  - L'opération peut échouer sans bloquer l'utilisateur
  - L'ordre des messages compte
  - Besoin de retry automatique
  
- **Synchrone (REST)** si :
  - L'utilisateur attend la réponse immédiatement
  - Besoin de données en temps réel

**Dans notre cas :** Asynchrone (Kafka) car l'utilisateur n'attend pas l'email

---

#### ÉTAPE 4 : Définir la STRUCTURE du service
**Question à te poser :** Comment il s'intègre dans l'archi ?

**Réponse :**
```
notification_service/
├── app/
│   ├── main.py              # Consumer Kafka
│   ├── email_sender.py      # Logique d'envoi (SMTP)
│   └── models.py            # Table notification_history
├── Dockerfile
└── requirements.txt
```

**Base de données :** `notification_db` avec une table `notification_history` (qui, quoi, quand)

---

#### ÉTAPE 5 : Planifier l'IMPLÉMENTATION
**Question à te poser :** Dans quel ordre je code ?

**Réponse :**
1. Créer le service vide avec consumer Kafka de base
2. S'abonner au topic `battle-events`
3. Parser les events et extraire les infos (battle_id, winner, loser)
4. Appeler auth_service pour récupérer les emails des joueurs
5. Envoyer l'email via SMTP (SendGrid, Mailgun, etc.)
6. Logger dans `notification_history`
7. Tester avec docker-compose

---

### 🎯 TEMPLATE UNIVERSEL : "COMMENT AJOUTER UN SERVICE [X] ?"

```
1. RÔLE ? → Quelle est sa responsabilité unique
2. SOURCES ? → D'où viennent les données
3. COMM ? → Synchrone ou Asynchrone
4. STRUCTURE ? → Fichiers, BDD, dépendances
5. IMPLÉMENTATION ? → Ordre des étapes
```

---

### 🔥 EXEMPLES APPLIQUÉS

#### Question : "Comment ajouter un service de statistiques ?"

**ÉTAPE 1 :** Rôle → Calculer des stats (nb de batailles par user, taux de victoire, etc.)

**ÉTAPE 2 :** Sources → 
- Events Kafka `battle-events` (pour collecter les données)
- Ou REST vers battle_service pour récupérer l'historique

**ÉTAPE 3 :** Comm → Asynchrone (Kafka) pour la collecte en temps réel

**ÉTAPE 4 :** Structure →
```
stats_service/
├── app/
│   ├── main.py              # Consumer Kafka
│   ├── aggregator.py        # Calcul des stats
│   ├── routes/
│   │   └── stats.py         # GET /users/{id}/stats
│   └── models.py            # Table user_stats
└── stats_db
```

**ÉTAPE 5 :** Implémentation →
1. Consumer Kafka écoute `battle-events`
2. À chaque event, met à jour `user_stats` (incrémente nb_battles, calcule win_rate)
3. Endpoint REST pour récupérer les stats d'un user

---

#### Question : "Comment ajouter un système de cache ?"

**ÉTAPE 1 :** Rôle → Réduire la charge sur PostgreSQL, accélérer les réponses

**ÉTAPE 2 :** Sources → Données fréquemment lues (pokedex_service, team_service)

**ÉTAPE 3 :** Comm → Synchrone (appel direct Redis)

**ÉTAPE 4 :** Structure →
- Ajouter un conteneur Redis dans docker-compose.yml
- Middleware de cache dans chaque service

**ÉTAPE 5 :** Implémentation →
```python
# Dans pokedex_service/routes/pokemon.py
@router.get("/{pokemon_id}")
async def get_pokemon(pokemon_id: int, redis: Redis = Depends(get_redis)):
    # 1. Check Redis
    cached = await redis.get(f"pokemon:{pokemon_id}")
    if cached:
        return json.loads(cached)
    
    # 2. Query PostgreSQL
    pokemon = await db.query(Pokemon).filter_by(id=pokemon_id).first()
    
    # 3. Store in Redis (TTL 1h)
    await redis.setex(f"pokemon:{pokemon_id}", 3600, json.dumps(pokemon))
    
    return pokemon
```

---

## 📋 TYPE 3 : QUESTIONS "OÙ MODIFIER..." (Localisation dans l'archi)

### 🔍 LA MÉTHODE EN 3 ÉTAPES

**Exemple :**
> "Si je vous demande d'ajouter un timeout sur Kafka, où vous le mettez ?"

#### ÉTAPE 1 : Identifier le COMPOSANT concerné
**Question à te poser :** Qui utilise Kafka ?

**Réponse :**
- **Producer** : battle_service (publie les events)
- **Consumer** : chat_service (consomme les events)

---

#### ÉTAPE 2 : Identifier le CÔTÉ à modifier
**Question à te poser :** Le timeout concerne quoi ?

**Réponse :**
- Timeout d'**envoi** (producer) → battle_service
- Timeout de **consommation** (consumer) → chat_service

**Ici :** Timeout d'envoi (le plus commun)

---

#### ÉTAPE 3 : Localiser le FICHIER précis
**Question à te poser :** Où est configuré le producer ?

**Réponse :**
```python
# battle_service/app/services/kafka_service.py
async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await p.start()
        _producer = p
    return _producer
```

---

### 🎯 TEMPLATE UNIVERSEL : "OÙ MODIFIER [X] ?"

```
1. COMPOSANT ? → Quel service est concerné
2. CÔTÉ ? → Producer, Consumer, API, BDD
3. FICHIER ? → Le fichier précis de config
```

---

### 🔥 EXEMPLES APPLIQUÉS

#### Question : "Où ajouter un logging de tous les events Kafka ?"

**ÉTAPE 1 :** Composant → battle_service (producer) + chat_service (consumer)

**ÉTAPE 2 :** Côté → Les deux côtés (avant publish + après consommation)

**ÉTAPE 3 :** Fichiers →
```python
# battle_service/app/services/kafka_service.py
async def publish_battle_event(event_type: str, data: dict) -> None:
    try:
        producer = await get_producer()
        payload = {"type": event_type, **data}
        await producer.send_and_wait(settings.KAFKA_TOPIC_BATTLE, payload)  # <-- ICI
    except Exception as exc:
        logger.warning("Kafka unavailable, event dropped: %s", exc)

# chat_service/app/main.py
async for msg in consumer:
    event = json.loads(msg.value)
    logger.info(f"Consumed event: {event}")  # <-- ICI
    # Traitement...
```

---

#### Question : "Où limiter le nombre de tours dans une bataille ?"

**ÉTAPE 1 :** Composant → battle_service (logique métier)

**ÉTAPE 2 :** Côté → Route `play_turn()` + table battles

**ÉTAPE 3 :** Fichiers →
```python
# 1. Ajouter la colonne dans models.py
class Battle(Base):
    __tablename__ = "battles"
    id = Column(UUID, primary_key=True)
    max_turns = Column(Integer, default=50)  # <-- ICI
    current_turn = Column(Integer, default=0)

# 2. Vérifier dans routes/battle.py
@router.post("/{battle_id}/turn")
async def play_turn(...):
    battle = await db.query(Battle).filter_by(id=battle_id).first()
    
    if battle.current_turn >= battle.max_turns:  # <-- ICI
        raise HTTPException(400, "Battle max turns reached")
    
    # Suite...
```

---

## 📋 TYPE 4 : QUESTIONS "POURQUOI..." (Justification de choix)

### 🔍 LA MÉTHODE EN 3 ÉTAPES

**Exemple :**
> "Pourquoi Kafka et pas REST entre battle et chat ?"

#### ÉTAPE 1 : Énoncer le PROBLÈME résolu
**Question à te poser :** Quel problème ça résout ?

**Réponse :**
- Battle_service ne doit pas être bloqué en attendant que chat envoie les notifications
- Si chat est down, les tours doivent quand même fonctionner

---

#### ÉTAPE 2 : Comparer les ALTERNATIVES
**Question à te poser :** Qu'est-ce qui ne marcherait pas avec l'autre solution ?

**Avec REST (synchrone) :**
- ❌ Battle bloqué en attendant chat (latence)
- ❌ Si chat down → erreur 500 dans battle
- ❌ Retry compliqué à gérer manuellement
- ❌ Couplage fort entre services

**Avec Kafka (asynchrone) :**
- ✅ Battle publie et continue (non-bloquant)
- ✅ Si chat down → events stockés, aucune perte
- ✅ Retry automatique par Kafka
- ✅ Découplage total (chat ne connaît pas battle)

---

#### ÉTAPE 3 : Conclure sur les AVANTAGES
**Question à te poser :** Quel est le gain principal ?

**Réponse :**
> "Kafka apporte la résilience et le découplage. Battle et chat évoluent indépendamment, et les pannes de l'un n'impactent pas l'autre."

---

### 🎯 TEMPLATE UNIVERSEL : "POURQUOI [CHOIX] ?"

```
1. PROBLÈME ? → Quelle contrainte ça résout
2. ALTERNATIVE ? → Pourquoi pas l'autre solution
3. AVANTAGE ? → Le gain principal
```

---

### 🔥 EXEMPLES APPLIQUÉS

#### Question : "Pourquoi database-per-service ?"

**ÉTAPE 1 :** Problème → Éviter les dépendances entre services

**ÉTAPE 2 :** Alternative (BDD unique) :
- ❌ Si BDD down → tous les services down
- ❌ Conflits de schéma entre équipes
- ❌ Impossible de scaler indépendamment
- ❌ Transactions complexes

**ÉTAPE 3 :** Avantage → 
- ✅ Chaque service scale indépendamment
- ✅ Isolation des pannes
- ✅ Liberté technologique (PostgreSQL, MongoDB, Redis selon les besoins)

---

#### Question : "Pourquoi async/await en FastAPI ?"

**ÉTAPE 1 :** Problème → Gérer de nombreuses requêtes concurrentes sans bloquer

**ÉTAPE 2 :** Alternative (synchrone) :
- ❌ Un thread par requête (lourd en mémoire)
- ❌ I/O bloquant (attente BDD, Kafka)
- ❌ Moins de requêtes simultanées

**ÉTAPE 3 :** Avantage → 
- ✅ Une seule boucle événementielle (léger)
- ✅ I/O non-bloquant (libère le CPU pendant les attentes)
- ✅ Meilleure performance sous charge

---

## 🎓 RÉSUMÉ : LES 4 TYPES DE QUESTIONS & TEMPLATES

| Type | Exemple | Template |
|------|---------|----------|
| **"Que se passe-t-il si..."** | Service down | 1. Type comm<br>2. Comportement<br>3. Récupération<br>4. Pourquoi |
| **"Comment ajouter..."** | Nouveau service | 1. Rôle<br>2. Sources<br>3. Comm<br>4. Structure<br>5. Implémentation |
| **"Où modifier..."** | Config, code | 1. Composant<br>2. Côté<br>3. Fichier |
| **"Pourquoi..."** | Justification | 1. Problème<br>2. Alternative<br>3. Avantage |

---

## 💪 EXERCICE PRATIQUE

**Entraîne-toi sur ces questions :**

1. "Que se passe-t-il si Redis (cache) est down ?"
2. "Comment ajouter un système d'authentification OAuth ?"
3. "Où ajouter une validation des types Pokémon avant battle ?"
4. "Pourquoi WebSocket dans chat_service et pas polling HTTP ?"

**Réponses à la fin de cette fiche** ⬇️

---

## ✅ RÉPONSES AUX EXERCICES

### 1. "Que se passe-t-il si Redis (cache) est down ?"

**Type comm :** Synchrone (appel direct Redis)  
**Comportement :** Erreur de connexion → fallback sur PostgreSQL  
**Récupération :** 
- Toutes les requêtes vont sur PostgreSQL (plus lent)
- Quand Redis redémarre, le cache se remplit progressivement
**Pourquoi :** L'architecture doit prévoir un fallback : Redis = optimisation, pas dépendance critique

---

### 2. "Comment ajouter un système d'authentification OAuth ?"

**Rôle :** Permettre login via Google/GitHub au lieu de JWT classique  
**Sources :** API Google OAuth, auth_service (pour créer le user)  
**Comm :** Synchrone (callback OAuth)  
**Structure :**
```
auth_service/
├── oauth_providers/
│   ├── google.py
│   └── github.py
└── routes/
    └── oauth.py  # GET /auth/google/callback
```
**Implémentation :**
1. Ajouter route `/auth/google` (redirige vers Google)
2. Callback `/auth/google/callback` (récupère le token)
3. Créer ou récupérer le user dans auth_db
4. Générer un JWT pour l'app
5. Retourner le JWT au client

---

### 3. "Où ajouter une validation des types Pokémon avant battle ?"

**Composant :** battle_service  
**Côté :** Route `create_battle()` (avant de créer la bataille)  
**Fichier :**
```python
# battle_service/app/routes/battle.py
@router.post("/")
async def create_battle(payload: BattleCreate, db: AsyncSession):
    # Validation
    valid_types = ["Fire", "Water", "Grass", "Electric", ...]
    
    for poke_type in payload.team_red_types + payload.team_blue_types:
        if poke_type not in valid_types:  # <-- ICI
            raise HTTPException(400, f"Invalid type: {poke_type}")
    
    # Création...
```

---

### 4. "Pourquoi WebSocket dans chat_service et pas polling HTTP ?"

**Problème :** Besoin de notifications temps réel (< 1s de latence)  

**Alternative (polling HTTP) :**
- ❌ Client fait GET /messages toutes les 2s (lourd)
- ❌ Latence de 0-2s selon le timing
- ❌ Beaucoup de requêtes inutiles (si pas de nouveau message)

**WebSocket :**
- ✅ Connexion persistante (pas de reconnexion)
- ✅ Push instantané du serveur vers client (0 latence)
- ✅ Moins de requêtes (juste les messages réels)

**Avantage :** WebSocket est le standard pour le temps réel (chat, notifications, jeux).

---

## 🚀 COMMENT UTILISER CETTE FICHE

**Jour 3-4 :** Lis cette fiche 2 fois, applique les templates sur les exemples  
**Jour 5-6 :** Entraîne-toi sur de nouvelles questions avec les templates  
**Jour 7 :** Relis juste les 4 templates, c'est tout

**Objectif :** Avoir les templates en tête pour l'oral. Le prof pose une question → tu identifies le type → tu déroules le template.

**BON COURAGE ! 🧠**
