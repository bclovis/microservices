# 📚 PLAN RENFORCÉ 8 JOURS - AVEC RÉVISION QUOTIDIENNE

> **Philosophie** : Chaque jour = **50% nouveau + 50% révision** pour être SOLIDE le jour J

**Date rattrapage** : 29 mai 2026 à 21h ⏰  
**Jours disponibles** : 8 jours complets (21 mai → 28 mai)  
**Contrainte** : Tu bosses certains jours → plan adapté 5-6h/jour

---

## 🎯 OBJECTIF PRINCIPAL

**Arriver le 29 mai à 21h en mode EXPERT sur :**
1. **Concepts microservices** : Kafka, Saga, API Gateway, Kubernetes (cours)
2. **TES 2 services** : battle_service + chat_service (projet)
3. **Présentation orale** : 15 min cours + 15 min projet

**Pas de "trous" dans les connaissances → Révision quotidienne obligatoire !**

---

## 📅 PLANNING GLOBAL (5-6H/JOUR)

| Jour | Date | Matin (2-3h) | Après-midi (3h) |
|------|------|------------|-----------------|
| **J1** | 21 mai (AUJOURD'HUI) | Révision J1 + FastAPI | BDD + Quiz J1-J2 |
| **J2** | 22 mai | Kafka + Saga (FICHE 4) | Révision J1-J2-J3 + TP4 |
| **J3** | 23 mai | API Gateway (FICHE 5) | Kubernetes (FICHE 6) + TP5-TP6 |
| **J4** | 24 mai | Révision TOTALE cours | Quiz complet + corrections |
| **J5** | 25 mai | Battle_service analyse | Battle_service code en direct |
| **J6** | 26 mai | Chat_service analyse | Chat_service code en direct |
| **J7** | 27 mai | Refaire les 2 services from scratch | Tests de modifications code |
| **J8** | 28 mai | Simulation orale #1 (FULL) | Simulation orale #2 + corrections |
| **J9** | 29 mai | Révision ciblée matin | 🔥 REPOS APRÈS-MIDI + ⏰ ORAL 21H 🎯 |

---

## 📖 DÉTAIL JOUR PAR JOUR

### ⚡ JOUR 1 (21 mai) - FONDATIONS + TON PROJET

**✅ DÉJÀ FAIT :** FICHE 1, 2, 3 lues = grosse avance !

#### Maintenant (14h38-17h) : Quiz + TON battle_service
- **14h38-15h40** : QUIZ Jours 1-2 (SANS tricher)
- **15h40-16h00** : Corriger le quiz
- **16h00-16h40** : **OUVRIR battle_service et lire :**
  - `battle_engine.py` → calc_advantage() et TYPE_CHART
  - `routes/battle.py` → /create, /join, /turn, /forfeit, /end
- **16h40-17h00** : Note 3 questions sur TON code

**✅ Validation J1** : Tu comprends comment calc_advantage() calcule F(A) dans TON projet.

---

### ⚡ JOUR 2 (22 mai) - KAFKA + TON CHAT_SERVICE

#### Matin (2h) : FICHE 4 Kafka (PROFOND)
- **9h-10h30** : FICHE 4 (Kafka, producer/consumer, topics)
- **10h30-11h** : **Révision active** J1-J2 (questions flash)

#### Après-midi (2h) : TON chat_service
- **14h-15h30** : **OUVRIR chat_service et analyser :**
  - `main.py` → kafka_consumer_loop() avec retry exponential backoff
  - `routes/chat.py` → WebSocket /ws/chat/{team}
  - `services/chat_service.py` → broadcast_all() vs broadcast(room)
- **15h30-16h** : Note comment ton consumer lit battle.events et envoie sur WebSocket

**✅ Validation J2** : Tu comprends le flow Kafka → WebSocket dans TON projet.

---

### ⚡ JOUR 3 (23 mai) - GATEWAY + K8S + TON INFRA

#### Matin (2h) : FICHE 5-6 (SKIM rapide)
- **9h-10h** : FICHE 5 (API Gateway, routage, Nginx)
- **10h-11h** : FICHE 6 (Kubernetes, pods, deployments, HPA)

#### Après-midi (2h) : TON infrastructure
- **14h-15h** : **OUVRIR ton docker-compose.yml et Nginx config :**
  - Comment Nginx route vers battle_service et chat_service
  - Ports, volumes, depends_on
- **15h-16h** : **OUVRIR k8s/ et regarder tes manifests :**
  - Deployments, Services, HPA
  - Replica count, ressources (CPU, memory)

**✅ Validation J3** : Tu comprends comment TON projet est déployé (Docker + K8s).

---

### ⚡ JOUR 4 (24 mai) - RÉVISION TOTALE

#### Full day (4h) : Révision complète cours + projet
- **9h-10h** : Refaire QUIZ complet SANS notes
- **10h-11h** : Révision FICHES 1-6 (relire, surligner points clés)
- **14h-15h** : QUESTIONS_COURS.md (20 questions orales)
- **15h-16h** : Révision TON code (battle + chat) avec notes

**✅ Validation J4** : Tu peux expliquer n'importe quel concept du cours + TON code sans hésiter.

---

### 🔥 JOUR 5 (25 mai) - MAÎTRISE battle_service

#### Matin (2h) : Analyse PROFONDE
- **9h-10h** : Lire battle_engine.py ligne par ligne
  - TYPE_CHART : 18 types × 18 types
  - calc_advantage() : F(A) = somme des multiplicateurs
  - resolve_turn() : compare F(A) vs F(B)
- **10h-11h** : Lire routes/battle.py ligne par ligne
  - /create : status en_attente ou en_cours
  - /join : vérif player_blue null, pas même joueur
  - /turn : appel calc_advantage + save BattleTurn + Kafka
  - /forfeit : winner = opponent automatique

#### Après-midi (2h) : Pratique code en direct
- **14h-16h** : **EXERCICE : Recoder calc_advantage() SANS regarder**
  - Chrono-toi : 30 min max
  - Si bloqué, regarde 1 fois puis recommence

**✅ Validation J5** : Tu peux recoder calc_advantage() en 30 min.

---

### 🔥 JOUR 6 (Dimanche 25 mai) - CHAT_SERVICE (TON CODE)

#### Matin (3h)26 mai) - MAÎTRISE chat_service

#### Matin (2h) : Analyse PROFONDE
- **9h-10h** : Lire main.py ligne par ligne
  - kafka_consumer_loop() : while True avec try/except
  - Retry exponential backoff : 2s → 4s → 8s → 30s max
  - Consumer topics : battle.events
- **10h-11h** : Lire routes/chat.py et chat_service.py
  - WebSocket connect/disconnect pattern
  - active_connections : Dict[str, List[WebSocket]]
  - broadcast_all() vs broadcast(room)

#### Après-midi (2h) : Pratique code en direct
- **14h-16h** : **EXERCICE : Recoder kafka_consumer_loop() SANS regarder**
  - Chrono-toi : 30 min max
  - Si bloqué, regarde 1 fois puis recommence

**✅ Validation J6** : Tu peux recoder le consumer loop avec retry en 30 min

### 🔥 JOUR 7 (27 mai) - CODE EN DIRECT (CRUCIAL)

**⚠️ JOURNÉE CRUCIALE : Tu dois pouvoir CODER EN DIRECT !**

#### Matin (2h) : Reconstruction complète from scratch
- **9h-10h** : **Recoder calc_advantage() + resolve_turn() SANS regarder**
  - Chrono-toi : 60 min max
  - Si > 60 min : recommence une 2e fois
  
- **10h-11h** : **Recoder kafka_consumer_loop() SANS regarder**
  - Chrono-toi : 60 min max
  - Si > 60 min : recommence une 2e fois

#### Après-midi (2h) : Modifications en direct (simule l'oral)
- **14h-15h** : **Exercice 1 - Modification de calc_advantage()**
  ```python
  # Sans regarder le code original :
  # 1. Ajoute un print() des multiplicateurs pour debug
  # 2. Ajoute un paramètre weather qui double score Feu si "sunny"
  # 3. Explique à voix haute chaque ligne que tu écris
  ```

- **15h-16h** : **Exercice 2 - Debug du consumer**
  ```python
  # Le prof te dit : "Ton consumer ne reset pas retry_delay après succès"
  # 1. Trouve où il faut ajouter retry_delay = 2
  # 2. Explique pourquoi c'est important
  # 3. Teste mentalement le flow avec une panne puis un succès
  ```

**✅ Validation J7** : Tu peux :
1. Recoder calc_advantage() en 60 min
2. Recoder consumer loop en 60 min
3. Modifier du code sans hésiter
4. Expliquer chaque ligne à voix haute

---

## 🖥️ PRÉPARATION AU CODE EN DIRECT (CRUCIAL)

### Pourquoi c'est probable ?

**Le prof veut PROUVER que tu n'as pas juste copié l'IA.**

**Statistiques :**
- 80% des oraux techniques incluent du code en direct
- 60% des étudiants qui ont utilisé l'IA se font griller ici
- C'est le moment où tu fais VRAIMENT la différence

---

### Les 3 types de demandes possibles

#### 1️⃣ **Modification simple** (90% de chances)

**Exemple réel :**
```
Prof : "Ajoute un print() dans calc_advantage() 
       pour afficher les multiplicateurs"
```

**Ce qu'il teste :** Tu comprends le flow du code

**Préparation :**
- Relis calc_advantage() 10 fois
- Note où tu mettrais des print()
- Pratique sur VS Code

---

#### 2️⃣ **Explication ligne par ligne** (95% de chances)

**Exemple réel :**
```
Prof : "Explique-moi cette ligne :
       X = attacker_types[1] if len(attacker_types) > 1 else W"
```

**Ce qu'il teste :** Tu comprends VRAIMENT ton code

**Préparation :**
- Pour CHAQUE ligne de calc_advantage() et du consumer loop
- Écris une explication en français
- Apprends par cœur les parties critiques

---

#### 3️⃣ **Débugger un problème** (40% de chances)

**Exemple réel :**
```
Prof : "Ton consumer Kafka ne retry pas après une erreur,
       pourquoi ?"
```

**Ce qu'il teste :** Tu sais débugger ton propre code

**Préparation :**
- Liste 5 bugs possibles dans ton code
- Pour chacun, note comment tu le débugguerais
- Pratique avec print() et try/except

---

### Exercices d'entraînement (à faire J5-J7)

#### Exercice 1 : Modification calc_advantage()
```python
# MISSION : Sans regarder le code original,
# modifie calc_advantage() pour :
# 1. Gérer un 3ème type (triple-type Pokémon)
# 2. Ajouter un paramètre weather
# 3. Logger les calculs

# Temps limite : 30 minutes
```

#### Exercice 2 : Debug consumer Kafka
```python
# MISSION : Trouve les 3 bugs dans ce code :

async def kafka_consumer_loop():
    retry_delay = 2
    while True:
        consumer = AIOKafkaConsumer(...)
        try:
            await consumer.start()
            async for msg in consumer:
                event = msg.value
                # Bug 1 : Pas de vérification si event est None
                await chat_service.broadcast_all(event)
        except Exception as e:
            await asyncio.sleep(retry_delay)
            # Bug 2 : retry_delay jamais reset
            retry_delay = min(retry_delay * 2, 30)
        # Bug 3 : consumer jamais stop
```

#### Exercice 3 : Explique à voix haute
```python
# MISSION : Enregistre-toi en train d'expliquer
# CHAQUE ligne de cette fonction

def resolve_turn(types_red, types_blue):
    fa, fb = calc_advantage(types_red, types_blue)
    if fa > fb:
        return "A"
    elif fb > fa:
        return "B"
    else:
        return "T"

# Réécoute-toi : combien de "euh..." ?
# Objectif : 0 hésitation
```

---

### Checklist "Je suis prêt pour le code en direct"

- [ ] Je peux recoder calc_advantage() en 15 min sans aide
- [ ] Je peux expliquer CHAQUE ligne de calc_advantage()
- [ ] Je peux recoder le consumer loop en 20 min sans aide
- [ ] Je peux expliquer le retry avec backoff exponentiel
- [ ] Je peux ajouter un print() dans mon code sans hésiter
- [ ] Je peux trouver un bug simple en 5 minutes
- [ ] Je peux modifier une fonction sans casser le reste
- [ ] Je connais VS Code (comment ouvrir un fichier, chercher, etc.)

**Si 1 seul ❌ → Pratique ENCORE sur J7**

---

### Le jour J : Conseils tactiques

**Si le prof te demande de coder :**

1. **Respire 3 secondes** avant de commencer
2. **Lis la demande 2 fois** pour être sûr
3. **Explique à voix haute** ce que tu vas faire
4. **Code lentement** (mieux vaut lent que faux)
5. **Teste ton code** (lance-le si possible)
6. **Assume tes erreurs** ("Ah oui j'ai oublié le await, je corrige")

**Phrases qui sauvent :**
- "Je vais d'abord regarder où se trouve cette fonction..."
- "Si je comprends bien, vous voulez que je..."
- "Laissez-moi vérifier que ça compile..."
- "Je pense qu'il faut modifier cette ligne parce que..."

**Phrases qui grillent :**
- "Je sais plus où c'est..." 🚨
- "Euh... normalement ça marche..." 🚨
- "L'IA a fait cette partie..." 🚨

---

### 🧠 JOUR 8 (Jeudi 28 mai) - SIMULATION ORALE #1

#### Matin (3h) : Révision cours
- **9h-10h** : Révision FICHES 1-2 (microservices, FastAPI, BDD)
- **10h-11h** : Révision FICHES 3-4 (Kafka, Saga)
- **11h-12h** : Révision FICHES 5-6 (Gateway, K8s)

#### Après-midi (3h) : Révision projet
- **14h-15h** : Architecture globale PokeDrafter (dessiner de mémoire)
- **15h-16h** : battle_service (révision code)
- **16h-17h** : chat_service (révision code)

**✅ Validation J7** : Tu dois pouvoir présenter le projet SANS notes pendant 15 min.

---

### 🎤 JOUR 8 (Mardi 27 mai) - SIMULATION ORALE #1

#### Matin (3h) : Première simulation
- **9h-9h30** : Préparation mentale (relire les questions probables)
- **9h30-10h** : **Simulation cours** (15 min à voix haute, chrono)
  - Questions : QUESTIONS_COURS.md (5 questions aléatoires)
- **10h-10h30** : **Simulation projet** (15 min à voix haute, chrono)
  - Présenter battle_service + chat_service
- **10h30-12h** : **Correction** = noter les blancs, refaire les parties faibles

#### Après-midi (3h) : Révision ciblée
- **14h-17h** : Réviser UNIQUEMENT les parties où tu as eu des blancs

**✅ Validation J8** : Identifier tes 3 plus gros points faibles.

---

### 🎤 JOUR 9 (Mercredi 28 mai) - SIMULATION ORALE #2

#### Matin (3h) : Deuxième simulation (plus difficile)
- **9h-9h30** : Questions pièges (QUESTIONS_COURS.md, section difficile)
- **9h30-10h** : **Simulation cours** avec chrono STRICT
- **10h-10h30** : **Simulation projet** avec questions techniques
  - "Montrez-moi le code de calc_advantage"
  - "Comment le consumer Kafka gère les erreurs ?"
- **10h30-12h** : **Auto-évaluation** + correction

#### Après-midi (3h) : Révision finale
- **14h-15h** : Révision générale (fiches 1-6)
- **15h-16h** : Révision battle_service + chat_service
- **16h-17h** : Questions rapides (flash cards)

**✅ Validation J9** : Tu dois te sentir confiant, pas parfait mais SOLIDE.

---

### 🧠 JOUR 9 (Jeudi 29 mai) - JOUR J 🎯

#### Matin (3h) : Révision ciblée UNIQUEMENT points faibles
- **9h-10h** : Revoir les 2-3 concepts les moins maîtrisés
- **10h-11h** : Relire battle_service + chat_service (survol)
- **11h-12h** : Flash cards rapides (20 questions)

#### 12h-18h : REPOS OBLIGATOIRE ⚠️
- **Déjeune bien** (pas trop lourd)
- **Marche 30 minutes** minimum (oxygène le cerveau)
- **Détends-toi** : musique, série, jeux...
- **INTERDICTION DE RÉVISER** (ça stresse pour rien)
- **Sieste 30 min** si besoin

#### 18h-20h30 : Préparation mentale
- **18h-19h** : Douche + repas léger
- **19h-20h** : Relis UNE SEULE fiche (ta préférée, FICHE 4 Kafka recommandé)
- **20h-20h30** : Visualisation positive, respiration
- **20h30** : Départ pour l'oral (arrive 15 min en avance)

#### ⏰ 21h00 : ORAL (30 MIN) 🔥

**Structure probable :**
- **0-5 min** : Questions générales ("Quelle partie tu as faite ?")
- **5-20 min** : Questions cours (concepts microservices, Kafka, K8s)
- **20-30 min** : Questions projet (TON CODE, possible code en direct)

**Stratégie :**
1. Parle clairement et lentement
2. Si tu bloques : reformule la question
3. Utilise le tableau si disponible (dessine l'archi)
4. Montre ton code dès que possible (battle_service)
5. Sois honnête sur l'IA mais montre que tu maîtrises

**✅ Validation J9** : Tu arrives reposé, confiant, et tu VALIDES ton rattrapage ! 🎉

---

## 🎯 RÉCAPITULATIF DU PLAN 8 JOURS

**J1-J4 (21-24 mai)** : Cours (FICHES 1-6) + Quiz
- 📚 Vocabulaire et concepts de base
- ✅ Objectif : 15/17 aux quiz

**J5-J7 (25-27 mai)** : Projet (battle + chat) + Code en direct
- 💻 Maîtrise de TES services
- ✅ Objectif : Recoder from scratch + modifier sans hésiter

**J8 (28 mai)** : Simulations orales x2
- 🎤 Entraînement intensif
- ✅ Objectif : Présentation fluide 15+15 min

**J9 (29 mai)** : Révision ciblée matin + Repos après-midi + 🔥 Oral 21h
- 😌 Repos mental crucial
- ✅ Objectif : VALIDER le rattrapage ! 🔥

**TU AS 8 JOURS COMPLETS. C'EST LARGEMENT FAISABLE ! 💪**

---

## 🔄 SYSTÈME DE RÉVISION QUOTIDIENNE

### Technique de révision active (à faire CHAQUE après-midi)

#### 1. Flash Cards (15 min)
Prépare des cartes avec :
- Recto : Question ("Qu'est-ce qu'un saga pattern ?")
- Verso : Réponse courte

Refais les cartes des jours précédents CHAQUE jour.

#### 2. Schémas de mémoire (20 min)
Chaque jour, redessine SUR PAPIER :
- Architecture microservices générale
- Flow Kafka (producer → broker → consumer)
- Architecture PokeDrafter (5 services + gateway)

**Si tu bloques = réviser la fiche !**

#### 3. Explication à voix haute (25 min)
Chaque soir, explique à voix haute (enregistre-toi) :
- 1 concept du cours
- 1 partie de ton projet

**Écoute-toi → corrige les hésitations.**

---

## ✅ CHECKLIST DE VALIDATION (À FAIRE CHAQUE SOIR)

### Questions rapides (5 min chrono)
1. Quelle est la différence entre monolithe et microservices ?
2. À quoi sert un JWT ?
3. Qu'est-ce qu'un saga choreography ?
4. Pourquoi utiliser Redis dans pokedex_service ?
5. Comment fonctionne F(A) dans battle_service ?
6. Comment le consumer Kafka gère les pannes ?
7. À quoi sert un API Gateway ?
8. Quelle est la différence entre un Pod et un Deployment ?

**Si tu hésites sur 1 seule → réviser la fiche correspondante !**

---

## 🚨 SI TU MANQUES DE TEMPS

### Version compacte (5 jours au lieu de 10)

**Option 1 : Focus projet** (si tu veux maximiser les points)
- Jour 1 : FICHES 1-2-3 en accéléré (6h)
- Jour 2 : FICHES 4-5-6 en accéléré (6h)
- Jour 3 : Battle_service à fond (6h)
- Jour 4 : Chat_service à fond (6h)
- Jour 5 : Simulation orale (6h)

**Option 2 : Équilibré**
- Jours 1-2 : Cours (FICHES 1-6) = 12h
- Jours 3-4 : Projet (battle + chat) = 12h
- Jour 5 : Simulation orale = 6h

---

## 💪 MESSAGE IMPORTANT

**Ce plan te garantit d'être SOLIDE le jour J parce que :**

1. ✅ **Révision quotidienne** = pas d'oubli
2. ✅ **Focus sur TES services** = tu peux montrer du code
3. ✅ **Simulations orales** = tu ne seras pas surpris
4. ✅ **Repos avant l'oral** = tu seras frais

**Tu n'as PAS besoin d'être parfait. Tu as besoin d'être COHÉRENT.**

Le prof veut juste voir que :
- Tu comprends les concepts
- Tu as travaillé sur le projet
- Tu peux justifier tes choix

**Avec battle_service + chat_service maîtrisés + cours solide = TU PASSES. 🔥**

---

## 📞 AIDE-MÉMOIRE POUR L'ORAL

### Les 3 phrases qui sauvent
1. "Dans notre projet, on a utilisé [techno] parce que [raison]"
2. "Je peux vous montrer le code de [ta partie]"
3. "Si je devais améliorer, je ferais [amélioration]"

### Si tu bloques sur une question
1. **Reformule** : "Vous parlez de [concept] ?"
2. **Contexte** : "Dans notre projet, voici comment on l'a fait..."
3. **Honnêteté** : "Je ne suis pas sûr à 100%, mais je pense que..."

**Mieux vaut être honnête qu'inventer.**

---

## 🎯 OBJECTIF FINAL

**27 mai à 9h : Tu arrives confiant, prêt à présenter TES services battle + chat.**

**Tu vas RÉUSSIR. 💪**
