# 🛡️ GUIDE DE DÉFENSE POUR L'ORAL

> **Objectif** : Justifier TES choix techniques et être prêt pour le code en direct

---

## 📋 CONSIGNES DU PROJET (À CONNAÎTRE PAR CŒUR)

### Sujet : PokeDrafter

**Description :** Jeu multijoueur Pokémon en temps réel. 2 joueurs (Team Red vs Team Blue) construisent des équipes de 6 Pokémon et combattent en tour par tour.

**Formule de combat :**
```
F(A) = 1 × (W/Y) × (W/Z) + 1 × (X/Y) × (X/Z)
F(B) = 1 × (Y/W) × (Y/X) + 1 × (Z/W) × (Z/X)

Où Pokémon A a les types W·X et Pokémon B a les types Y·Z
Le Pokémon avec le score F le plus BAS gagne
```

**TES RESPONSABILITÉS (Team Red) :**
- ✅ **battle_service** : Moteur de combat F(A), routes /turn, /join, /forfeit, Kafka producer
- ✅ **chat_service** : WebSocket chat, Kafka consumer avec retry exponential backoff
- ✅ **Infrastructure** : Docker Compose, Nginx (API Gateway), manifests Kubernetes

**Architecture imposée :**
- 5 microservices : auth, team, battle, chat, pokedex
- Communication Red ↔ Blue via Kafka (chiffrement obligatoire)
- Frontend Angular + Backend FastAPI
- Déploiement Docker + Kubernetes

---

## 🎯 PARTIE 1 : JUSTIFICATION DE TES CHOIX

### 1.1 Pourquoi FastAPI ?

**TA RÉPONSE :**
> "J'ai choisi FastAPI pour 3 raisons :
> 
> 1. **Performance** : FastAPI est un des frameworks Python les plus rapides, comparable à Node.js. Pour un jeu en temps réel, c'est crucial.
> 2. **Async natif** : Supporte async/await out-of-the-box, parfait pour les WebSocket et Kafka qui sont non-bloquants.
> 3. **Documentation automatique** : Génère Swagger UI automatiquement, très pratique pour tester les routes pendant le dev.
> 
> Alternativement j'aurais pu utiliser Flask, mais Flask n'a pas d'async natif et aurait nécessité des extensions supplémentaires."

---

### 1.2 Pourquoi PostgreSQL pour battle_service ?

**TA RÉPONSE :**
> "J'ai choisi PostgreSQL pour battle_service parce que :
> 
> 1. **ACID** : Les batailles nécessitent des transactions cohérentes. Si on sauvegarde un tour, il faut garantir que le score est bien enregistré avant de publier sur Kafka.
> 2. **Relations complexes** : J'ai une relation 1-N entre Battle et BattleTurn (une bataille a plusieurs tours). PostgreSQL gère très bien les relations.
> 3. **JSON natif** : PostgreSQL supporte les colonnes JSON, pratique pour stocker les types Pokémon comme arrays.
> 
> Alternativement j'aurais pu utiliser MySQL, mais PostgreSQL est plus standard en microservices et mieux supporté par SQLAlchemy async."

---

### 1.3 Pourquoi Kafka (et pas REST) entre battle et chat ?

**TA RÉPONSE :**
> "J'ai choisi Kafka pour la communication asynchrone entre battle_service et chat_service parce que :
> 
> 1. **Découplage** : battle_service ne dépend pas de la disponibilité de chat_service. Si chat est down, les events sont stockés et consommés plus tard.
> 2. **Performance** : battle_service publie l'event et continue immédiatement sans attendre de réponse. Ça évite de ralentir le jeu.
> 3. **Scalabilité** : Si on a 100 joueurs connectés, Kafka gère la distribution des messages efficacement.
> 
> Avec REST (synchrone), si chat_service était down, battle_service crasherait. Et avec 100 joueurs, on aurait des timeouts."

---

### 1.4 Pourquoi retry exponential backoff dans le consumer ?

**TA RÉPONSE :**
> "J'ai implémenté un retry avec exponential backoff (2s → 4s → 8s → 30s max) pour :
> 
> 1. **Résilience** : Si Kafka est temporairement indisponible (restart, maintenance), le consumer retry automatiquement sans crasher.
> 2. **Éviter la surcharge** : Sans backoff, le consumer bouclait infiniment à 100% CPU. Le backoff laisse le temps à Kafka de redémarrer.
> 3. **Best practice** : C'est un pattern standard en microservices pour gérer les pannes temporaires.
> 
> Le `min(retry_delay * 2, 30)` évite d'attendre trop longtemps (sans le min, après 10 échecs on attendrait 1024 secondes = 17 minutes)."

---

### 1.5 Pourquoi WebSocket (et pas HTTP long-polling) ?

**TA RÉPONSE :**
> "J'ai choisi WebSocket pour le chat parce que :
> 
> 1. **Bidirectionnel** : Le serveur peut envoyer des messages aux clients sans qu'ils demandent (push). Avec HTTP, il faudrait que le client poll toutes les secondes.
> 2. **Temps réel** : Latence très faible (<100ms). Crucial pour un jeu en temps réel où les joueurs doivent voir les résultats des tours immédiatement.
> 3. **Moins de ressources** : Une seule connexion TCP maintenue vs HTTP qui crée une nouvelle connexion à chaque requête.
> 
> HTTP long-polling aurait fonctionné mais avec beaucoup plus de latence et de charge serveur."

---

### 1.6 Pourquoi Docker Compose en dev ?

**TA RÉPONSE :**
> "J'ai utilisé Docker Compose pour le développement parce que :
> 
> 1. **Reproductibilité** : Tous les membres de l'équipe (Team Red) ont exactement le même environnement, évite les 'ça marche chez moi'.
> 2. **Isolation** : Chaque service tourne dans son conteneur avec ses dépendances isolées.
> 3. **Simplicité** : Un seul `docker-compose up` lance tous les services + PostgreSQL + Kafka. Sans Docker, il faudrait installer et configurer tout manuellement.
> 
> En production, on utilise Kubernetes, mais Docker Compose est parfait pour le dev local."

---

### 1.7 Pourquoi Kubernetes HPA (Horizontal Pod Autoscaler) ?

**TA RÉPONSE :**
> "J'ai configuré HPA sur battle_service parce que :
> 
> 1. **Scalabilité automatique** : Si la charge CPU dépasse 70%, Kubernetes ajoute automatiquement des pods (réplicas). Pendant les heures de pointe, on peut avoir 10 instances au lieu de 2.
> 2. **Économie** : En heures creuses (la nuit), HPA réduit automatiquement à 2 pods minimum. On ne paie que ce qu'on utilise.
> 3. **Résilience** : Si un pod crash, les autres continuent à servir les requêtes pendant que Kubernetes redémarre le pod crashé.
> 
> Sans HPA, on aurait un nombre fixe de pods, inefficace en termes de ressources."

---

### 1.8 Pourquoi Nginx comme API Gateway ?

**TA RÉPONSE :**
> "J'ai utilisé Nginx comme API Gateway parce que :
> 
> 1. **Routage** : Nginx route les requêtes vers le bon service (ex: `/api/battle/*` → battle_service:8003).
> 2. **Load balancing** : Si j'ai 3 instances de battle_service, Nginx distribue les requêtes équitablement (round-robin).
> 3. **Point d'entrée unique** : Le frontend n'a qu'une seule URL (`http://gateway/api/*`) au lieu de 5 URLs différentes.
> 
> Alternativement j'aurais pu utiliser Traefik ou Kong, mais Nginx est le plus standard et performant."

---

### 1.9 Pourquoi SQLAlchemy AsyncSession ?

**TA RÉPONSE :**
> "J'ai utilisé SQLAlchemy avec AsyncSession parce que :
> 
> 1. **Non-bloquant** : Avec `await db.execute()`, le serveur ne bloque pas pendant les requêtes BDD. Il peut traiter d'autres requêtes en parallèle.
> 2. **Cohérent avec FastAPI** : FastAPI est async par défaut, utiliser une BDD sync bloquerait le thread et casserait la performance.
> 3. **Scalabilité** : Sans async, FastAPI ne pourrait gérer qu'une requête à la fois par worker. Avec async, on peut gérer des centaines de requêtes simultanées.
> 
> La version sync de SQLAlchemy aurait fonctionné mais avec des performances désastreuses sous charge."

---

### 1.10 Pourquoi aiokafka (et pas kafka-python) ?

**TA RÉPONSE :**
> "J'ai utilisé aiokafka parce que :
> 
> 1. **Async natif** : aiokafka supporte `await consumer.start()` et `async for msg in consumer`. Cohérent avec FastAPI async.
> 2. **Non-bloquant** : Le consumer loop ne bloque pas le serveur FastAPI. Les deux tournent en parallèle.
> 3. **Performance** : kafka-python est synchrone et bloquerait le thread. aiokafka permet de consommer des messages Kafka pendant que FastAPI sert des requêtes HTTP.
> 
> kafka-python aurait nécessité de lancer un thread séparé, ce qui complique le code et la gestion des erreurs."

---

## 🔥 PARTIE 2 : TOP 10 ENDROITS OÙ LE PROF PEUT TE DEMANDER DE CODER

### 1️⃣ **Modifier calc_advantage() - TRÈS PROBABLE (90%)**

**Ce qu'il peut demander :**
```
"Ajoute un print() dans calc_advantage() pour afficher les multiplicateurs W/Y, W/Z, etc."
```

**Pourquoi c'est piégeux :**
- C'est TA fonction la plus importante
- Teste si tu comprends le flow et les variables

**Comment te préparer :**
```python
# EXERCICE : Ajoute ces 3 lignes dans calc_advantage() sans regarder le code

def calc_advantage(types_a, types_b):
    # ... ton code existant ...
    
    # AJOUTE ICI :
    print(f"[DEBUG] W={W}, X={X}, Y={Y}, Z={Z}")
    print(f"[DEBUG] W/Y={W_Y}, W/Z={W_Z}, X/Y={X_Y}, X/Z={X_Z}")
    print(f"[DEBUG] F(A)={fa}, F(B)={fb}")
```

**Entraînement (J5-J7) :**
- Recoder calc_advantage() en 30 min SANS regarder
- Ajouter un print() en 5 min chrono
- Expliquer CHAQUE ligne à voix haute

---

### 2️⃣ **Modifier le retry_delay - TRÈS PROBABLE (85%)**

**Ce qu'il peut demander :**
```
"Ton consumer ne reset pas retry_delay après succès. Corrige ça."
```

**Pourquoi c'est piégeux :**
- Teste si tu comprends le flow try/except
- Teste si tu sais où mettre `retry_delay = 2`

**Comment te préparer :**
```python
# EXERCICE : Trouve OÙ ajouter retry_delay = 2

async def kafka_consumer_loop():
    retry_delay = 2
    while True:
        consumer = AIOKafkaConsumer(...)
        try:
            await consumer.start()
            # AJOUTE ICI : retry_delay = 2  ✅
            
            async for msg in consumer:
                # Traiter messages
                pass
        except Exception as e:
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)
```

**Entraînement (J6-J7) :**
- Recoder kafka_consumer_loop() en 30 min
- Identifier la ligne à ajouter en 2 min

---

### 3️⃣ **Gérer un 3ème type Pokémon - PROBABLE (70%)**

**Ce qu'il peut demander :**
```
"Modifie calc_advantage() pour gérer des Pokémon triple-type (W, X, Y)."
```

**Pourquoi c'est piégeux :**
- Teste ta compréhension de la formule
- Teste si tu sais expliquer que le code ACTUEL gère déjà ça

**Bonne réponse :**
> "Notre implémentation utilise une double boucle `for w in types_a` / `for y in types_b`. Elle itère sur TOUS les types de la liste, quelle que soit sa taille. Un Pokémon mono-type donnera 1 itération, bi-type en donnera 2, triple-type en donnera 3. **Aucune modification n'est nécessaire** — le code supporte déjà le cas."

**Exemple mental pour Pokémon triple-type** (si jamais) :
```python
# types_a = ["Feu", "Vol", "Acier"]  →  3 itérations automatiques
# La boucle for w in types_a parcourt les 3 types naturellement

# Code actuel — PAS BESOIN de le modifier :
fa = 0.0
for w in types_a:       # fonctionne pour 1, 2 ou 3 types
    val = 1.0
    for y in types_b:
        val *= get_multiplier(w, y)
    fa += val
```

**Entraînement (J7) :**
- Tester mentalement avec Pikachu (Électrik-Vol-Acier) contre Bulbizarre [Plante, Poison]
- Expliquer pourquoi aucune modification n'est nécessaire en 2 min

---

### 4️⃣ **Ajouter un paramètre weather - PROBABLE (65%)**

**Ce qu'il peut demander :**
```
"Ajoute un paramètre 'weather' à calc_advantage(). Si weather='sunny', les Pokémon Feu ont F(A) × 2."
```

**Pourquoi c'est piégeux :**
- Teste si tu sais modifier une signature de fonction
- Teste si tu comprends où appliquer le bonus

**Comment te préparer :**
```python
# EXERCICE : Ajoute le paramètre weather

def calc_advantage(types_a, types_b, weather=None):
    # ... calcul normal de fa et fb ...
    
    # Appliquer le bonus weather APRÈS le calcul
    if weather == "sunny" and "Feu" in types_a:
        fa *= 2.0
    if weather == "sunny" and "Feu" in types_b:
        fb *= 2.0
    
    # Bonus rain pour Eau
    if weather == "rainy" and "Eau" in types_a:
        fa *= 1.5
    if weather == "rainy" and "Eau" in types_b:
        fb *= 1.5
    
    return round(fa, 4), round(fb, 4)
```

**Entraînement (J7) :**
- Ajouter ce paramètre en 10 min
- Expliquer où tu l'as mis et pourquoi

---

### 5️⃣ **Débugger broadcast_all() vs broadcast(room) - PROBABLE (60%)**

**Ce qu'il peut demander :**
```
"Explique la différence entre broadcast_all() et broadcast(room). Quand utiliser l'un ou l'autre ?"
```

**Pourquoi c'est piégeux :**
- Teste ta compréhension de la structure de données
- Teste si tu sais naviguer dans active_connections

**Comment te préparer :**
```python
# EXERCICE : Explique et code ces 2 fonctions

# Structure : active_connections = {"red": [ws1, ws2], "blue": [ws3]}

async def broadcast(room: str, message: dict):
    """Envoie à UNE room spécifique"""
    if room in active_connections:
        for ws in active_connections[room]:
            await ws.send_json(message)
    # Usage : Chat d'équipe (red ou blue seulement)

async def broadcast_all(message: dict):
    """Envoie à TOUTES les rooms"""
    for room in active_connections:
        for ws in active_connections[room]:
            await ws.send_json(message)
    # Usage : Battle Log (tout le monde voit les résultats)
```

**Entraînement (J6) :**
- Recoder ces 2 fonctions en 10 min
- Expliquer quand utiliser l'une ou l'autre

---

### 6️⃣ **Ajouter une route /battles/open - POSSIBLE (50%)**

**Ce qu'il peut demander :**
```
"Ajoute une route GET /battles/open qui retourne toutes les batailles avec status='en_attente'."
```

**Pourquoi c'est piégeux :**
- Teste si tu sais écrire une route FastAPI from scratch
- Teste si tu connais SQLAlchemy

**Comment te préparer :**
```python
# EXERCICE : Écris cette route en 10 min

@router.get("/open", response_model=List[BattleOut])
async def list_open_battles(db: AsyncSession = Depends(get_db)):
    """Liste des batailles en attente de joueur"""
    result = await db.execute(
        select(Battle).where(Battle.status == "en_attente")
    )
    battles = result.scalars().all()
    return battles
```

**Entraînement (J5) :**
- Écrire cette route en 10 min
- Expliquer query SQL équivalente : `SELECT * FROM battles WHERE status = 'en_attente'`

---

### 7️⃣ **Gérer le cas où event est None - POSSIBLE (45%)**

**Ce qu'il peut demander :**
```
"Ton consumer peut crasher si event est None. Ajoute une vérification."
```

**Pourquoi c'est piégeux :**
- Teste si tu sais ajouter des guards
- Teste ta compréhension du flow

**Comment te préparer :**
```python
# EXERCICE : Ajoute la vérification

async for msg in consumer:
    event = msg.value
    
    # AJOUTE ICI :
    if event is None:
        logger.warning("Event vide reçu, skip")
        continue
    
    etype = event.get("type", "")
    if etype == "turn_played":
        # ... traitement ...
```

**Entraînement (J6) :**
- Identifier les 3 endroits où il faut des guards (event None, type manquant, data invalide)

---

### 8️⃣ **Expliquer ligne par ligne resolve_turn() - TRÈS PROBABLE (80%)**

**Ce qu'il peut demander :**
```
"Explique-moi cette fonction ligne par ligne sans regarder le code."
```

**Pourquoi c'est piégeux :**
- Teste si tu COMPRENDS vraiment ton code
- Teste si tu peux expliquer sans hésitation

**Comment te préparer :**
```python
def resolve_turn(types_a, types_b):
    # Ligne 1 : Appelle calc_advantage pour obtenir F(A) et F(B)
    fa, fb = calc_advantage(types_a, types_b)
    
    # Ligne 2 : Compare les scores
    if fa > fb:
        # Si F(A) supérieur, Red gagne (Pokémon A plus fort)
        return "A"
    elif fb > fa:
        # Si F(B) supérieur, Blue gagne (Pokémon B plus fort)
        return "B"
    else:
        # Si égalité, aucun ne gagne (tie)
        return "draw"
```

**Entraînement (J5-J7) :**
- Enregistre-toi en train d'expliquer chaque ligne
- Objectif : 0 hésitation, 0 "euh..."

---

### 9️⃣ **Ajouter un log après publish_battle_event() - POSSIBLE (40%)**

**Ce qu'il peut demander :**
```
"Ajoute un logger.info() après publish_battle_event() pour logger l'event."
```

**Pourquoi c'est piégeux :**
- Teste si tu sais où se trouve cette fonction dans TON code
- Teste si tu connais la syntaxe du logger

**Comment te préparer :**
```python
# EXERCICE : Ajoute le log

await publish_battle_event("turn_played", {
    "battle_id": str(battle_id),
    "turn_number": turn_number,
    "result": result,
})

# AJOUTE ICI :
logger.info(f"[Kafka] Event 'turn_played' publié : battle={battle_id}, turn={turn_number}, result={result}")
```

**Entraînement (J5) :**
- Trouver ce code dans ton projet
- Ajouter le log en 2 min

---

### 🔟 **Créer un endpoint /health - FACILE (30%)**

**Ce qu'il peut demander :**
```
"Ajoute une route GET /health qui retourne {'status': 'ok', 'service': 'battle'}."
```

**Pourquoi c'est piégeux :**
- Teste si tu connais la syntaxe FastAPI basique
- Teste si tu sais où mettre la route

**Comment te préparer :**
```python
# EXERCICE : Écris cette route en 5 min

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "battle"}
```

**Entraînement (J5) :**
- Écrire cet endpoint en 5 min
- Expliquer à quoi sert un health check (monitoring Kubernetes)

---

## 💪 PARTIE 3 : ENTRAÎNEMENT INTENSIF (J5-J7)

### Planning d'entraînement

#### J5 (25 mai) - battle_service
```
9h-10h  → Lire battle_engine.py ligne par ligne (écris explication français)
10h-11h → Lire routes/battle.py ligne par ligne
14h-15h → EXERCICE 1 : Recoder calc_advantage() SANS regarder (30 min)
15h-16h → EXERCICE 2 : Ajouter print() et weather parameter (20 min)
```

#### J6 (26 mai) - chat_service
```
9h-10h  → Lire main.py kafka_consumer_loop() ligne par ligne
10h-11h → Lire chat_service.py ligne par ligne
14h-15h → EXERCICE 3 : Recoder consumer loop SANS regarder (30 min)
15h-16h → EXERCICE 4 : Fix retry_delay reset bug (10 min)
```

#### J7 (27 mai) - Code en direct FULL
```
9h-10h  → Recoder calc_advantage() + resolve_turn() (60 min max)
10h-11h → Recoder consumer loop (60 min max)
14h-15h → Prof simule : "Ajoute print dans calc_advantage" (5 min chrono)
15h-16h → Prof simule : "Explique cette ligne" (0 hésitation)
```

### Checklist "Je suis prêt"

- [ ] Je peux recoder calc_advantage() en 30 min
- [ ] Je peux expliquer CHAQUE ligne de calc_advantage()
- [ ] Je peux recoder consumer loop en 30 min
- [ ] Je peux expliquer retry exponential backoff
- [ ] Je peux ajouter un print() sans hésiter
- [ ] Je peux ajouter un paramètre weather en 10 min
- [ ] Je peux débugger le retry_delay en 5 min
- [ ] Je peux expliquer broadcast_all() vs broadcast(room)
- [ ] Je peux créer une route FastAPI en 5 min
- [ ] Je peux justifier TOUS mes choix techniques (10 questions ci-dessus)

**Si 1 seul ❌ → Pratique ENCORE**

---

## 🎯 PARTIE 4 : PHRASES QUI SAUVENT À L'ORAL

### Si le prof te demande de coder :

✅ **"Je vais d'abord regarder où se trouve cette fonction..."**  
→ Montre que tu connais la structure du projet

✅ **"Si je comprends bien, vous voulez que je..."**  
→ Reformule la demande pour être sûr

✅ **"Je vais faire ça en plusieurs étapes : d'abord..., ensuite..., enfin..."**  
→ Montre que tu as une méthode

✅ **"Laissez-moi tester mentalement avec un exemple : si Pikachu (Électrik) attaque Gyarados (Eau-Vol)..."**  
→ Montre que tu comprends la logique métier

✅ **"Ah oui, j'ai oublié le await ici, je corrige"**  
→ Assume tes erreurs proprement

### Phrases à ÉVITER :

❌ **"Euh... je sais plus..."**  
❌ **"L'IA m'a aidé pour cette partie..."**  
❌ **"J'ai copié ce code de Stack Overflow..."**  
❌ **"Je pense que... peut-être... je sais pas..."**  
❌ **"C'est compliqué, je vais pas réussir..."**

---

## 📊 PROBABILITÉ PAR TYPE DE QUESTION

| Type | Probabilité | Préparation nécessaire |
|------|-------------|----------------------|
| **Modifier calc_advantage()** | 90% | 3h (J5) |
| **Expliquer ligne par ligne** | 80% | 2h (J5-J7) |
| **Fix retry_delay** | 85% | 1h (J6) |
| **Gérer 3ème type** | 70% | 1h (J7) |
| **Ajouter weather** | 65% | 1h (J7) |
| **broadcast_all vs broadcast** | 60% | 30min (J6) |
| **Nouvelle route FastAPI** | 50% | 30min (J5) |
| **Guard event None** | 45% | 15min (J6) |
| **Ajouter logger** | 40% | 15min (J5) |
| **Route /health** | 30% | 10min (J5) |

**Total temps préparation critique : ~11h**  
**Tu as 32h disponibles → 3x plus que nécessaire 💪**

---

## 🔥 DERNIER CONSEIL

**Assume TOUT.** Même si l'IA a aidé, TU as fait les choix finaux. Dis :

> "J'ai choisi FastAPI parce que..." (pas "l'IA a choisi")  
> "J'ai implémenté retry backoff pour..." (pas "j'ai copié")  
> "J'ai décidé d'utiliser Kafka parce que..." (pas "c'était dans les consignes")

**Le prof sait que tu as utilisé l'IA. Il veut juste voir si TU COMPRENDS ce que tu as fait.**

---

**📍 Prochaine étape :** Imprime ce guide et fais les exercices J5-J7 ! 💪
