# 🎯 PLAN DE RÉVISION RATTRAPAGE - 10 JOURS

**Date limite : 27-30 mai**  
**Objectif : Valider le rattrapage et sauver l'année**

---

## 📊 ANALYSE DE LA SITUATION

### Ce qui a été fait
- ✅ TP4 : Architecture microservices avec Kafka (saga chorégraphie)
- ✅ TP5 : API Gateway avec sécurité et cache
- ✅ TP6 : Déploiement Kubernetes
- ✅ Projet PokeDrafter : Plateforme complète avec 5 microservices

### Points faibles identifiés
- ❌ Utilisation intensive de l'IA → compréhension superficielle
- ❌ Manque de maîtrise technique des choix
- ❌ Peur des questions théoriques

### Points forts à exploiter
- ✅ Projet fonctionnel réalisé
- ✅ TPs complets
- ✅ 10 jours pour préparer = largement suffisant avec méthode

---

## 🗓️ PLANNING DÉTAILLÉ (10 JOURS)

### **JOURS 1-2 : FONDAMENTAUX THÉORIQUES** ⚡
**Objectif : Maîtriser les bases du cours**

#### Jour 1 (20 mai) - Concepts de base
- ⏰ **Matin (3h)** : Microservices vs Monolithe
  - Lire la fiche "01_CONCEPTS_FONDAMENTAUX.md"
  - Faire un schéma personnel des 2 architectures
  - Noter 3 avantages/inconvénients de chaque
  
- ⏰ **Après-midi (3h)** : API REST et HTTP
  - Comprendre GET/POST/PUT/DELETE/PATCH
  - Lire les endpoints de TP5 (gateway) et PokeDrafter
  - Refaire les requêtes curl du TP4 en comprenant chaque ligne

- ⏰ **Soir (2h)** : Communication entre services
  - Synchrone (HTTP/REST) vs Asynchrone (Kafka)
  - Regarder le TP4 : comment les services communiquent
  - Dessiner le flux d'une commande dans le TP4

#### Jour 2 (21 mai) - Architecture technique
- ⏰ **Matin (3h)** : Docker et conteneurisation
  - Lire la fiche "02_DOCKER_CONTAINERS.md"
  - Comprendre Dockerfile, docker-compose.yml
  - Analyser le docker-compose du TP4 ligne par ligne

- ⏰ **Après-midi (3h)** : Bases de données et persistance
  - Comprendre PostgreSQL, Redis
  - Regarder les modèles de données (orders-service, inventory-service)
  - Comprendre pourquoi chaque service a SA base de données

- ⏰ **Soir (2h)** : Révision J1-J2 + quiz personnel
  - Faire le quiz "QUIZ_JOUR_1_2.md"
  - Refaire les schémas de mémoire

---

### **JOURS 3-4 : CONCEPTS AVANCÉS** 🚀
**Objectif : Maîtriser les patterns et Kubernetes**

#### Jour 3 (22 mai) - Patterns microservices
- ⏰ **Matin (3h)** : API Gateway
  - Lire la fiche "03_API_GATEWAY.md"
  - Comprendre le TP5 en profondeur
  - Expliquer à voix haute pourquoi on a besoin d'un gateway

- ⏰ **Après-midi (3h)** : Saga et Event-Driven
  - Lire la fiche "04_KAFKA_SAGA.md"
  - Comprendre la saga chorégraphie du TP4
  - Dessiner le flux complet : order → inventory → payment → notification

- ⏰ **Soir (2h)** : Sécurité
  - API Keys, JWT, authentification
  - Regarder auth_service de PokeDrafter
  - Comprendre comment protéger les endpoints

#### Jour 4 (23 mai) - Kubernetes
- ⏰ **Matin (4h)** : Kubernetes de base
  - Lire la fiche "05_KUBERNETES.md"
  - Comprendre : Pod, Deployment, Service, ReplicaSet
  - Analyser les fichiers k8s du TP6

- ⏰ **Après-midi (3h)** : Scalabilité et résilience
  - HPA (Horizontal Pod Autoscaler)
  - Readiness/Liveness probes
  - Load balancing

- ⏰ **Soir (1h)** : Quiz personnel jours 3-4

---

### **JOURS 5-7 : PROJET POKEDRAFTER EN PROFONDEUR** 🎮
**Objectif : Maîtriser AU MOINS 2 services du projet à fond**

#### Jour 5 (24 mai) - Vue d'ensemble du projet
- ⏰ **Matin (3h)** : Architecture globale
  - Lire instructions.md du projet
  - Dessiner l'architecture complète
  - Comprendre le rôle de chaque microservice

- ⏰ **Après-midi (4h)** : Choisir 2 services à maîtriser
  - **Recommandation : team_service + battle_service** (cœur métier)
  - OU **auth_service + pokedex_service** (plus simple)
  
  **Pour chaque service :**
  - Lire tout le code (main.py, models, routes)
  - Comprendre les endpoints
  - Tester manuellement avec curl/Postman

- ⏰ **Soir (1h)** : Noter les choix techniques faits

#### Jour 6 (25 mai) - Maîtrise approfondie service 1
- ⏰ **Toute la journée (8h)** : Service choisi #1
  - Refaire le service from scratch (sans copier-coller)
  - Expliquer chaque ligne de code à voix haute
  - Préparer 5 questions probables + réponses
  - Comprendre les dépendances (PostgreSQL, Kafka, Redis...)

#### Jour 7 (26 mai) - Maîtrise approfondie service 2
- ⏰ **Toute la journée (8h)** : Service choisi #2
  - Même méthode que le jour 6
  - Comprendre comment il communique avec les autres services
  - Tester l'intégration complète

---

### **JOURS 8-9 : PRÉPARATION ORALE** 🎤
**Objectif : Être prêt pour l'entretien**

#### Jour 8 (27 mai) - Questions de cours
- ⏰ **Matin (3h)** : Révision théorique complète
  - Relire toutes les fiches
  - Refaire tous les quiz
  - Identifier les 3 points faibles restants

- ⏰ **Après-midi (4h)** : Simulations de questions
  - Préparer 30 questions probables (voir QUESTIONS_ORAL.md)
  - Répondre à voix haute devant un miroir
  - Chronométrer : 15 min de réponses max

- ⏰ **Soir (2h)** : Présentation PowerPoint simple
  - 5-6 slides sur l'architecture du projet
  - Schémas clairs et professionnels
  - Anticiper les questions

#### Jour 9 (28 mai) - Présentation projet
- ⏰ **Matin (3h)** : Structurer la présentation (15 min)
  - Introduction (30s) : Contexte du projet
  - Architecture (3 min) : Schéma + explication
  - Services maîtrisés (8 min) : Détails techniques
  - Choix techniques (3 min) : Justifications
  - Conclusion (30s) : Retour d'expérience

- ⏰ **Après-midi (4h)** : Simulations complètes
  - S'enregistrer en vidéo (30 min complet)
  - Identifier les hésitations, tics de langage
  - Refaire jusqu'à être fluide

- ⏰ **Soir (2h)** : Anticiper les questions pièges
  - "Pourquoi avez-vous fait ce choix ?"
  - "Quelles sont les limites de votre architecture ?"
  - "Comment amélioreriez-vous le projet ?"

---

### **JOUR 10 : RÉVISION FINALE** 🔥
**Objectif : Confiance maximale**

- ⏰ **Matin (3h)** : Révision légère
  - Relire les fiches essentielles
  - Refaire les schémas clés
  - Relire le code des 2 services maîtrisés

- ⏰ **Après-midi (2h)** : Dernière simulation
  - Entretien complet 30 min
  - Avec un proche si possible

- ⏰ **Soir (1h)** : Préparation mentale
  - Se coucher tôt
  - Relire les notes "filet de sécurité"
  - Visualiser l'oral en mode positif

---

## 🎯 STRATÉGIE PENDANT L'ORAL

### 15 premières minutes (Questions de cours)
✅ **Si tu sais** : Réponds avec assurance, donne des exemples concrets
✅ **Si tu hésites** : Commence par ce que tu sais, puis construis logiquement
❌ **Si tu ne sais pas** : "Je ne suis pas sûr de la réponse exacte, mais voici ce que je pense..." → puis tente une réponse logique

**Mots clés à placer :**
- "Scalabilité", "Résilience", "Découplage"
- "Asynchrone", "Event-driven", "Saga"
- "Conteneurisation", "Orchestration"
- "Load balancing", "Circuit breaker"

### 15 dernières minutes (Présentation projet)
✅ **Structure imposée :**
1. "Le projet PokeDrafter est une plateforme de bataille Pokémon avec 5 microservices"
2. [MONTRER LE SCHÉMA] "Voici l'architecture globale"
3. "Je vais vous présenter en détail [service 1] et [service 2] que j'ai réalisés"
4. [EXPLIQUER LE CODE] avec des exemples concrets
5. "Les choix techniques ont été guidés par [scalabilité/sécurité/performance]"

✅ **Attitudes gagnantes :**
- Parler avec enthousiasme (même si stressé)
- Montrer le code et l'architecture visuellement
- Anticiper les questions : "Vous allez me demander pourquoi on a utilisé Kafka..."
- Être honnête : "Sur cette partie, j'ai collaboré avec l'équipe" (pas de mensonge)

❌ **À éviter absolument :**
- Lire ses notes
- Dire "J'ai utilisé l'IA donc je sais pas trop"
- Réponses trop courtes (développe toujours un minimum)
- Paniquer sur un blanc → respire, reformule la question, prends 5 secondes

---

## 📚 RESSOURCES CRÉÉES

1. **Fiches de révision** (dans `/FICHES_REVISION/`)
   - 01_CONCEPTS_FONDAMENTAUX.md
   - 02_DOCKER_CONTAINERS.md
   - 03_API_GATEWAY.md
   - 04_KAFKA_SAGA.md
   - 05_KUBERNETES.md

2. **Quiz d'entraînement** (dans `/QUIZ/`)
   - QUIZ_JOUR_1_2.md (bases)
   - QUIZ_JOUR_3_4.md (avancé)
   - QUIZ_FINAL.md (tout le programme)

3. **Questions probables oral** (dans `/ORAL/`)
   - QUESTIONS_COURS.md (30 questions types)
   - QUESTIONS_PROJET.md (20 questions projet)
   - REPONSES_TYPES.md (exemples de réponses)

4. **Schémas** (dans `/SCHEMAS/`)
   - architecture_pokedrafter.png
   - saga_tp4.png
   - gateway_tp5.png

---

## 🚨 RÈGLES D'OR

1. **Travaille tous les jours** (pas de jour off)
2. **Explique à voix haute** (apprentissage actif)
3. **Fais des schémas** (compréhension visuelle)
4. **Simule l'oral** (dès le jour 5)
5. **Dors suffisamment** (7-8h/nuit)
6. **Reste calme** (tu as le temps, c'est gérable)

---

## 💪 MESSAGE FINAL

**Tu as 10 jours = 80 heures de travail potentiel.**

Avec ce plan, tu vas :
- Comprendre les concepts du cours
- Maîtriser 2 services à fond
- Savoir défendre tes choix techniques
- Être capable de répondre aux questions probables

**Objectif réaliste : 12-14/20 au rattrapage → VALIDÉ ✅**

Le prof ne cherche pas à te piéger, il veut juste s'assurer que tu as compris les bases. Avec ce plan, tu vas largement y arriver.

**Courage, tu vas y arriver ! 🔥**
