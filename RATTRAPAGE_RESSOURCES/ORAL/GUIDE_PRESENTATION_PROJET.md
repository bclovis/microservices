# 🎤 GUIDE DE PRÉSENTATION - PROJET POKEDRAFTER (15 minutes)

> **Format** : 15 dernières minutes de l'oral = présentation de votre partie du projet

---

## 🎯 OBJECTIF DE CETTE PARTIE

Le prof veut vérifier que :
1. Tu as **réellement travaillé** sur le projet
2. Tu **comprends** ce que tu as fait
3. Tu peux **justifier** les choix techniques
4. Tu peux **expliquer** comment ton service fonctionne

**Pas besoin d'être expert sur tout**, mais maîtrise **AU MOINS 2 SERVICES à fond**.

---

## 📊 STRUCTURE DE LA PRÉSENTATION (15 MIN)

### ⏱️ Introduction (30 secondes)
"Je vais vous présenter PokeDrafter, une plateforme de bataille Pokémon multijoueur en temps réel que nous avons développée en architecture microservices."

### ⏱️ Vue d'ensemble du projet (2 minutes)
- Contexte et objectif
- Architecture globale (schéma)
- Technologies utilisées

### ⏱️ Services maîtrisés en profondeur (10 minutes)
- Service 1 : architecture, endpoints, logique métier (5 min)
- Service 2 : architecture, endpoints, logique métier (5 min)
- Communication entre services

### ⏱️ Choix techniques et retour d'expérience (2 minutes)
- Pourquoi ces choix ?
- Difficultés rencontrées
- Améliorations possibles

### ⏱️ Conclusion (30 secondes)
"Ce projet m'a permis de comprendre concrètement les défis des microservices, notamment la gestion de la communication asynchrone et la scalabilité."

---

## 🏗️ PARTIE 1 : VUE D'ENSEMBLE DU PROJET

### Slide 1 : Introduction

**À dire :**
> "PokeDrafter est une plateforme de bataille Pokémon stratégique en temps réel. Les joueurs créent des équipes de 6 Pokémon et s'affrontent dans 3 modes de jeu : Draft (pioche alternée), Constructed (équipes pré-construites), et Random (aléatoire). Le système de combat utilise une formule mathématique F(A) qui calcule les avantages de types pour déterminer le vainqueur de chaque tour."

**Points clés :**
- Jeu multijoueur temps réel
- 3 modes de jeu
- Formule de combat F(A)
- Architecture microservices

---

### Slide 2 : Architecture Globale

**Schéma à présenter :**

```
┌────────────────────────────────────────────────────────┐
│                  FRONTEND ANGULAR 17                   │
│              (Port 4200, Single Page App)              │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│               NGINX API GATEWAY (Port 80)              │
│       - Reverse Proxy - CORS - Load Balancing         │
└────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────────────┐
        │                 │                         │
        ▼                 ▼                         ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ auth_service │  │ team_service │  │ battle_service   │
│  (Port 8001) │  │  (Port 8002) │  │   (Port 8003)    │
│              │  │              │  │                  │
│ - JWT Auth   │  │ - CRUD Teams │  │ - Battle Engine  │
│ - Users      │  │ - AI Recomm  │  │ - Kafka Producer │
│              │  │              │  │ - F(A) Formula   │
│ PostgreSQL   │  │ PostgreSQL   │  │ PostgreSQL       │
└──────────────┘  └──────────────┘  └──────────────────┘
        │                 │                         │
        ▼                 ▼                         ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│pokedex_svc   │  │  chat_svc    │  │  KAFKA BROKER    │
│  (Port 8004) │  │  (Port 8005) │  │                  │
│              │  │              │  │ Topics:          │
│ - PokéAPI    │  │ - WebSocket  │  │ - battle.started │
│ - Redis Cache│  │ - Real-time  │  │ - turn.played    │
│              │  │   Chat       │  │ - battle.ended   │
│ Redis        │  │ PostgreSQL   │  └──────────────────┘
└──────────────┘  └──────────────┘
```

**À dire :**
> "L'architecture se compose de 5 microservices backend en FastAPI derrière une gateway Nginx. Le frontend Angular communique uniquement avec la gateway. Chaque service a sa propre base de données PostgreSQL, sauf pokedex_service qui utilise Redis comme cache. La communication synchrone se fait via REST, et l'asynchrone via Kafka pour les événements de bataille."

---

### Slide 3 : Technologies utilisées

**Stack technique :**

| Composant | Technologie | Pourquoi ? |
|-----------|-------------|------------|
| **Frontend** | Angular 17 + TypeScript | Framework moderne, composants réutilisables |
| **Backend** | FastAPI + Python 3.11 | Performance, async/await, documentation auto |
| **BDD Principale** | PostgreSQL 16 | Données relationnelles, ACID |
| **Cache** | Redis 7 | Cache ultra-rapide pour PokéAPI |
| **Message Broker** | Kafka 3.7 | Communication asynchrone, event-driven |
| **Gateway** | Nginx | Reverse proxy performant |
| **Conteneurisation** | Docker + Docker Compose | Déploiement uniforme |
| **Orchestration** | Kubernetes (optionnel) | Scalabilité, auto-healing |

**À dire :**
> "On a choisi FastAPI pour sa performance et sa documentation automatique. PostgreSQL pour les données relationnelles avec transactions ACID. Redis pour cacher les données de PokéAPI et éviter de surcharger l'API externe. Kafka pour les événements de bataille en temps réel, car il garantit la livraison des messages même si un service est temporairement down. Nginx comme gateway pour centraliser le CORS et la sécurité."

---

## 🔥 PARTIE 2 : SERVICES MAÎTRISÉS EN PROFONDEUR

### Stratégie de choix des services

**OPTION A : Cœur métier (Recommandé si tu aimes la technique)**
- **team_service** (gestion équipes + AI recommender)
- **battle_service** (engine de combat + Kafka)

**OPTION B : Plus simple (Recommandé si tu veux la sécurité)**
- **auth_service** (JWT, users)
- **pokedex_service** (cache Redis, proxy PokéAPI)

**OPTION C : Complet (Si tu es à l'aise)**
- **auth_service** (base solide)
- **team_service** (logique métier)

---

### 📦 SERVICE 1 : AUTH_SERVICE (Exemple détaillé)

#### Architecture du service

```
auth_service/
├── main.py          # Application FastAPI principale
├── models.py        # Modèles SQLAlchemy (User)
├── schemas.py       # Modèles Pydantic (validation)
├── database.py      # Connexion PostgreSQL
├── auth.py          # Logique JWT (create_token, verify_token)
└── requirements.txt # Dépendances
```

#### Responsabilités

1. **Inscription** (POST /register)
2. **Connexion** (POST /login) → Retourne JWT
3. **Vérification du token** (GET /me)
4. **Gestion des utilisateurs** (CRUD)

#### Endpoints principaux

```python
# 1. Inscription
POST /api/auth/register
Body: {
  "username": "player1",
  "email": "player1@example.com",
  "password": "securepass123"
}
Response: {
  "id": 1,
  "username": "player1",
  "email": "player1@example.com"
}

# 2. Connexion (retourne JWT)
POST /api/auth/login
Body: {
  "username": "player1",
  "password": "securepass123"
}
Response: {
  "access_token": "eyJhbGc....",
  "token_type": "bearer",
  "user": {"id": 1, "username": "player1"}
}

# 3. Vérifier le token
GET /api/auth/me
Headers: Authorization: Bearer eyJhbGc....
Response: {
  "id": 1,
  "username": "player1",
  "email": "player1@example.com"
}
```

#### Code clé à maîtriser : Génération JWT

```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    
    # Encoder le JWT
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return user_id
    except:
        return None
```

**À expliquer à l'oral :**
> "auth_service gère l'authentification avec JWT. Lors de la connexion, on vérifie le mot de passe hashé avec bcrypt, puis on génère un JWT contenant l'ID utilisateur. Ce token est valide 24h. Les autres services peuvent vérifier ce token pour authentifier les requêtes. On stocke les users dans PostgreSQL avec mot de passe hashé pour la sécurité."

#### Choix techniques

**Q : Pourquoi JWT et pas des sessions ?**
> "Les JWT sont stateless : le serveur n'a pas besoin de stocker les sessions. C'est parfait pour les microservices car n'importe quel service peut vérifier le token sans interroger auth_service. Chaque service a la clé secrète et peut décoder le JWT de manière indépendante."

**Q : Pourquoi hasher les mots de passe ?**
> "On utilise bcrypt pour hasher les mots de passe avant de les stocker. Même si la BDD est compromise, l'attaquant ne peut pas récupérer les mots de passe en clair. Bcrypt ajoute aussi un 'salt' unique par mot de passe."

---

### 📦 SERVICE 2 : TEAM_SERVICE (Exemple détaillé)

#### Architecture du service

```
team_service/
├── main.py          # Application FastAPI
├── models.py        # Team, TeamPokemon (SQLAlchemy)
├── schemas.py       # Validation Pydantic
├── database.py      # PostgreSQL connection
├── recommender.py   # AI Team Recommender
└── requirements.txt
```

#### Responsabilités

1. **CRUD Teams** : Créer, lire, modifier, supprimer des équipes
2. **Gestion des Pokémon** : Ajouter/retirer des Pokémon d'une équipe (max 6)
3. **AI Recommender** : Suggérer des Pokémon pour compléter une équipe
4. **Validation** : Vérifier les règles (max 6 Pokémon, pas de doublons)

#### Endpoints principaux

```python
# 1. Créer une équipe
POST /api/teams
Headers: Authorization: Bearer <JWT>
Body: {
  "name": "Team Thunder",
  "description": "Équipe électrique offensive"
}
Response: {
  "id": 1,
  "name": "Team Thunder",
  "user_id": 1,
  "pokemons": []
}

# 2. Ajouter un Pokémon à l'équipe
POST /api/teams/{team_id}/pokemons
Body: {
  "pokemon_id": 25,  # Pikachu
  "pokemon_name": "Pikachu",
  "pokemon_types": ["electric"]
}

# 3. Lister les équipes de l'utilisateur
GET /api/teams
Headers: Authorization: Bearer <JWT>
Response: [
  {
    "id": 1,
    "name": "Team Thunder",
    "pokemons": [
      {"pokemon_id": 25, "pokemon_name": "Pikachu", "types": ["electric"]},
      {"pokemon_id": 135, "pokemon_name": "Jolteon", "types": ["electric"]}
    ]
  }
]

# 4. AI Recommender (compléter l'équipe)
POST /api/teams/{team_id}/recommend
Response: {
  "recommendations": [
    {"id": 3, "name": "Venusaur", "types": ["grass", "poison"], "reason": "Couvre les faiblesses ground"},
    {"id": 6, "name": "Charizard", "types": ["fire", "flying"], "reason": "Ajoute diversity offensive"}
  ]
}
```

#### Code clé : AI Recommender (simplifié)

```python
def recommend_pokemon(team_pokemons: List[TeamPokemon]) -> List[dict]:
    # 1. Analyser les types de l'équipe actuelle
    current_types = set()
    for p in team_pokemons:
        current_types.update(p.pokemon_types)
    
    # 2. Identifier les faiblesses (types manquants)
    all_types = ["fire", "water", "grass", "electric", "ground", 
                 "flying", "psychic", "bug", "rock", "ghost", 
                 "dragon", "dark", "steel", "fairy", "fighting", "poison", "ice", "normal"]
    
    missing_types = set(all_types) - current_types
    
    # 3. Récupérer des Pokémon ayant ces types
    recommendations = []
    for missing_type in list(missing_types)[:3]:  # Top 3
        # Appel à pokedex_service pour trouver des Pokémon de ce type
        response = requests.get(f"http://pokedex-service:8004/pokemon/type/{missing_type}")
        pokemons = response.json()
        
        if pokemons:
            recommendations.append({
                "id": pokemons[0]["id"],
                "name": pokemons[0]["name"],
                "types": pokemons[0]["types"],
                "reason": f"Ajoute le type {missing_type} manquant"
            })
    
    return recommendations
```

**À expliquer à l'oral :**
> "team_service gère la création et modification d'équipes. Chaque équipe appartient à un utilisateur (vérifié via JWT). On a implémenté un AI Recommender qui analyse les types de l'équipe actuelle, identifie les faiblesses (types manquants), et suggère des Pokémon pour combler ces faiblesses. L'algorithme appelle pokedex_service pour récupérer des Pokémon par type. On stocke tout dans PostgreSQL avec une relation many-to-many entre Teams et Pokemons."

#### Choix techniques

**Q : Pourquoi séparer team_service de auth_service ?**
> "Chaque service a une responsabilité unique (Single Responsibility Principle). auth_service gère l'authentification, team_service gère la logique métier des équipes. Ça permet de scaler indépendamment : si beaucoup d'utilisateurs créent des équipes, on peut ajouter des instances de team_service sans toucher auth_service."

**Q : Comment le recommender fonctionne ?**
> "Il analyse les types actuels de l'équipe, identifie les types manquants, et suggère des Pokémon qui comblent ces lacunes. C'est une logique simplifiée, on pourrait améliorer en prenant en compte les stats, les faiblesses de types (ex: electric est faible contre ground), et les synergies. Mais ça donne déjà un bon point de départ pour les joueurs."

---

### 📦 SERVICE 3 : BATTLE_SERVICE (Optionnel - Si tu veux impressionner)

#### Responsabilités

1. **Créer une bataille** (Draft/Constructed/Random mode)
2. **Engine de combat** : Calculer F(A) pour chaque tour
3. **Publier événements Kafka** : `battle-events` topic
4. **Gérer l'état de la bataille** : tours, résultats, winner

#### Code clé : Formule F(A)

```python
def calc_advantage(types_a: list[str], types_b: list[str]) -> tuple[float, float]:
    """
    Double boucle : pour chaque type w de A, multiplie get_multiplier(w,y)
    pour chaque type y de B, puis additionne — c'est fa.
    Même chose en sens inverse pour fb.
    Fonctionne avec 1 ou 2 types sans logique spéciale.
    """
    if not types_a or not types_b:
        return 0.0, 0.0
    fa = 0.0
    for w in types_a:
        val = 1.0
        for y in types_b:
            val *= get_multiplier(w, y)
        fa += val
    fb = 0.0
    for y in types_b:
        val = 1.0
        for w in types_a:
            val *= get_multiplier(y, w)
        fb += val
    return round(fa, 4), round(fb, 4)
```

**À expliquer :**
> "battle_service implémente le moteur de combat. On utilise la formule F(A) qui calcule l'avantage en fonction des types avec une double boucle. Par exemple, si Pikachu (Électrik) attaque Gyarados (Eau/Vol) : F(A) = get_multiplier(Électrik,Eau) × get_multiplier(Électrik,Vol) = 2.0 × 2.0 = 4.0. À chaque tour, on publie un événement Kafka sur le topic `battle-events` pour que chat_service puisse afficher le résultat en temps réel via WebSocket."

---

## 🎯 PARTIE 3 : COMMUNICATION ENTRE SERVICES

### Communication Synchrone (REST)

**Exemple : team_service → pokedex_service**

```python
# team_service veut récupérer les infos d'un Pokémon
import requests

def get_pokemon_info(pokemon_id: int):
    response = requests.get(f"http://pokedex-service:8004/pokemon/{pokemon_id}")
    return response.json()
```

**À expliquer :**
> "Quand team_service a besoin des infos d'un Pokémon (nom, types, stats), il appelle pokedex_service via REST. C'est synchrone car team_service attend la réponse avant de continuer. pokedex_service fait lui-même office de proxy vers l'API externe PokéAPI et cache les résultats dans Redis pour éviter de surcharger l'API."

---

### Communication Asynchrone (Kafka)

**Exemple : battle_service → chat_service**

```python
# battle_service publie un événement (aiokafka)
from app.services.kafka_service import publish_battle_event

await publish_battle_event("turn_played", {
    "battle_id": str(battle_id),
    "turn_number": turn_number,
    "result": result,    # "A", "B" ou "draw"
})
# → envoyé sur settings.KAFKA_TOPIC_BATTLE = "battle-events"

# chat_service écoute (dans kafka_consumer_loop) :
# AIOKafkaConsumer abonné à settings.KAFKA_TOPIC_BATTLE + settings.KAFKA_TOPIC_CHAT
# À la réception d'un event "turn_played" → broadcast_all() via WebSocket
```

**À expliquer :**
> "Pour les événements de bataille, on utilise Kafka car c'est asynchrone et garantit la livraison. battle_service publie 'turn_played' sur le topic `battle-events` après chaque tour. chat_service a un consumer loop qui écoute ce topic et diffuse via WebSocket aux joueurs connectés. Même si chat_service est down pendant quelques secondes, les événements sont mis en file d'attente et seront traités au redémarrage."

---

## 💡 PARTIE 4 : CHOIX TECHNIQUES ET JUSTIFICATIONS

### Q : Pourquoi FastAPI ?

**Réponse :**
> "FastAPI offre plusieurs avantages : 1) Performance élevée grâce à async/await, 2) Documentation automatique (Swagger UI), 3) Validation automatique avec Pydantic, 4) Très bon support des WebSockets pour chat_service. C'est devenu le standard pour les microservices Python modernes."

---

### Q : Pourquoi Kafka et pas REST partout ?

**Réponse :**
> "Pour les événements de bataille temps réel, Kafka garantit la livraison même si un service est temporairement down. Les messages sont persistés. Avec REST, si chat_service est down, on perd l'événement. Kafka découple aussi complètement les services : battle_service ne sait pas qui écoute ses événements. On pourrait ajouter un notifications_service facilement."

---

### Q : Pourquoi Redis pour le cache ?

**Réponse :**
> "L'API externe PokéAPI a des rate limits (100 requêtes/minute). Sans cache, on atteindrait vite la limite. Redis est ultra-rapide (in-memory) et parfait pour ça. On cache les données avec un TTL de 24h. Ça réduit la latence de 500ms (appel PokéAPI) à 5ms (Redis)."

---

### Q : Difficultés rencontrées ?

**Réponse (sois honnête) :**
> "La partie la plus complexe était la gestion de la concurrence dans battle_service : s'assurer que deux joueurs ne peuvent pas jouer en même temps. On a résolu ça avec des transactions PostgreSQL et des locks. Aussi, debugger Kafka était difficile au début : comprendre pourquoi les messages n'arrivaient pas. On a utilisé Kafbat UI pour visualiser les topics."

---

### Q : Améliorations possibles ?

**Réponse (montre que tu réfléchis) :**
> "1) Ajouter une couche de cache Redis dans team_service pour les équipes fréquemment consultées. 2) Implémenter un circuit breaker pour gérer les pannes de pokedex_service. 3) Améliorer l'AI Recommender en prenant compte des synergies de types. 4) Déployer sur Kubernetes pour le scaling automatique en production. 5) Ajouter des tests end-to-end avec pytest."

---

## 🚨 QUESTIONS PIÈGES PROBABLES

### Q : "Vous avez utilisé l'IA pour le projet ?"

**Réponse honnête et professionnelle :**
> "Oui, on a utilisé GitHub Copilot et ChatGPT comme assistants de développement, notamment pour générer du code boilerplate et résoudre des bugs. Mais j'ai pris soin de comprendre chaque partie du code, et je peux expliquer en détail comment [service que tu maîtrises] fonctionne, depuis la base de données jusqu'aux endpoints. L'IA est un outil, mais la compréhension de l'architecture et des choix techniques reste humaine."

**Puis enchaîne immédiatement sur un point technique pour prouver que tu maîtrises :**
> "Par exemple, dans team_service, le recommender analyse les types actuels, identifie les faiblesses, et appelle pokedex_service pour suggérer des Pokémon. C'est une logique métier qu'on a conçue nous-mêmes."

---

### Q : "Quel est votre plus gros problème rencontré ?"

**Réponds avec un vrai problème technique et SA SOLUTION :**
> "Notre plus gros problème était la gestion des transactions distribuées. Par exemple, quand une bataille démarre, il faut : 1) Créer la bataille en BDD, 2) Vérifier que les équipes existent (team_service), 3) Publier l'événement Kafka. Si une étape échoue, il faut rollback. On a résolu ça avec une saga chorégraphie : si battle.started échoue, on publie battle.cancelled et chaque service compense."

---

### Q : "Comment testez-vous votre application ?"

**Réponse :**
> "On a plusieurs niveaux : 1) Tests unitaires avec pytest pour la logique métier (ex: la formule F(A)), 2) Tests d'intégration pour les endpoints avec TestClient de FastAPI, 3) Tests manuels via Swagger UI (/docs), 4) Tests end-to-end en lançant tout avec docker-compose et en testant des scénarios complets (créer équipe → lancer bataille). On pourrait automatiser plus avec Playwright pour le frontend."

---

## ✅ CHECKLIST AVANT L'ORAL

### Préparation technique
- [ ] Je peux dessiner l'architecture complète de mémoire
- [ ] Je maîtrise 2 services à 100% (code, endpoints, BDD)
- [ ] Je sais expliquer la communication sync vs async
- [ ] Je connais les choix techniques et leurs raisons
- [ ] J'ai préparé 3-4 améliorations possibles

### Préparation mentale
- [ ] J'ai répété ma présentation à voix haute (3 fois minimum)
- [ ] Je me suis enregistré en vidéo
- [ ] J'ai préparé des réponses aux questions pièges
- [ ] Je suis capable de coder en live un endpoint simple

### Matériel
- [ ] Slides avec schémas clairs (5-6 slides max)
- [ ] Code source ouvert (sur les parties que je maîtrise)
- [ ] Application fonctionnelle (docker-compose up)
- [ ] Postman ou Swagger pour démo live

---

## 🎤 SIMULATION D'ORAL

### Entraîne-toi avec ces questions :

1. "Expliquez-moi l'architecture de votre projet"
2. "Quelle partie avez-vous développée ?"
3. "Montrez-moi le code de [votre service]"
4. "Comment les services communiquent entre eux ?"
5. "Pourquoi avez-vous utilisé Kafka ?"
6. "Comment gérez-vous l'authentification ?"
7. "Quelles difficultés avez-vous rencontrées ?"
8. "Comment améliorer votre projet ?"

**Chronomètre-toi : tu dois pouvoir répondre en 15 minutes max.**

---

## 🔥 CONSEIL FINAL

**Le prof ne cherche PAS à te piéger. Il veut juste vérifier que :**
- Tu as vraiment travaillé sur le projet
- Tu comprends ce que tu as fait
- Tu peux justifier tes choix

**Stratégie gagnante :**
- Parle avec **enthousiasme** (même si tu stresses)
- Sois **honnête** (mieux vaut dire "je ne suis pas sûr" qu'inventer)
- **Montre le code** et l'application qui tourne
- **Anticipe** les questions en les posant toi-même

**Si tu maîtrises 2 services + l'architecture globale → tu passes ! 💪**
