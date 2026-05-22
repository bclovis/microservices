# 📘 FICHE 3 : BASES DE DONNÉES EN MICROSERVICES

> **Source** : BDD en Microservices.pdf (19/11/2025)

---

## 🎯 PRINCIPE FONDAMENTAL : DATABASE PER SERVICE

### La règle d'or
**Chaque microservice possède SA PROPRE base de données.**

```
❌ MAUVAIS : Base de données partagée
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Service  │   │ Service  │   │ Service  │
│  Users   │───┤  Orders  │───┤ Products │
└──────────┘   └──────────┘   └──────────┘
      │             │              │
      └─────────────┴──────────────┘
              │
        ┌─────────────┐
        │ BDD UNIQUE  │
        └─────────────┘

✅ BON : Database per service
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Service  │   │ Service  │   │ Service  │
│  Users   │   │  Orders  │   │ Products │
│    │     │   │    │     │   │    │     │
│ ┌──────┐│   │ ┌──────┐ │   │ ┌──────┐ │
│ │DB usr││   │ │DB ord│ │   │ │DB prd│ │
│ └──────┘│   │ └──────┘ │   │ └──────┘ │
└──────────┘   └──────────┘   └──────────┘
```

### Pourquoi ?

1. **Découplage** : Les services sont indépendants
2. **Scalabilité** : Chaque BDD peut scaler séparément
3. **Choix technologique** : PostgreSQL pour users, Redis pour cache, MongoDB pour logs
4. **Isolation des pannes** : Si une BDD tombe, les autres continuent

---

## 🗄️ TYPES DE BASES DE DONNÉES

### 1. PostgreSQL (Relationnel)
**Usage :** Données structurées avec relations

```python
# Exemple : Users avec Orders
class User:
    id: int
    name: str
    email: str

class Order:
    id: int
    user_id: int  # Foreign key
    product_id: int
    quantity: int
```

**Avantages :**
✅ ACID (Atomicité, Cohérence, Isolation, Durabilité)
✅ Relations entre tables (JOIN)
✅ Transactions complexes

**Cas d'usage dans le projet :**
- `auth_service` : Stockage des utilisateurs
- `team_service` : Gestion des équipes Pokémon
- `battle_service` : Historique des combats

### 2. Redis (Cache en mémoire)
**Usage :** Cache rapide, sessions, données temporaires

```python
# Exemple : Cache des Pokémon
redis.set("pokemon:25", json.dumps({"name": "Pikachu", "type": "Electric"}))
pokemon = redis.get("pokemon:25")  # Super rapide !
```

**Avantages :**
✅ Extrêmement rapide (en mémoire)
✅ Expire automatiquement les clés
✅ Structures de données avancées (lists, sets, sorted sets)

**Cas d'usage dans le projet :**
- `pokedex_service` : Cache des données PokéAPI (évite de rappeler l'API externe)
- Sessions utilisateur

### 3. MongoDB (NoSQL Document)
**Usage :** Données non-structurées, logs, documents JSON

```python
# Exemple : Logs de bataille
{
  "battle_id": "abc123",
  "timestamp": "2026-05-20T10:30:00",
  "turns": [
    {"attacker": "Pikachu", "defender": "Bulbasaur", "damage": 45},
    {"attacker": "Bulbasaur", "defender": "Pikachu", "damage": 30}
  ]
}
```

**Avantages :**
✅ Schéma flexible (pas de structure fixe)
✅ Bonne performance pour les écritures massives
✅ Stockage de documents complexes

**Cas d'usage :**
- Logs d'événements
- Historiques de parties

---

## 🔄 COMMENT RÉCUPÉRER DES DONNÉES D'UN AUTRE SERVICE ?

### Problème
Si chaque service a sa BDD, comment `OrderService` récupère les infos d'un utilisateur stockées dans `UserService` ?

### ❌ Solution INTERDITE : Accès direct à la BDD
```python
# ❌ NE JAMAIS FAIRE ÇA !
from user_service.database import User

user = db.query(User).filter(User.id == user_id).first()
```

**Pourquoi c'est interdit ?**
- Crée un couplage fort
- Viole l'encapsulation
- Rend les services non-indépendants

### ✅ Solution 1 : Appel API REST (Synchrone)
```python
# ✅ OrderService appelle UserService via API
import requests

response = requests.get(f"http://user-service:8001/users/{user_id}")
user = response.json()
```

**Avantages :**
✅ Simple à implémenter
✅ Réponse immédiate

**Inconvénients :**
❌ Le service doit être disponible (couplage temporel)
❌ Latence (chaque appel prend du temps)

### ✅ Solution 2 : Events (Asynchrone via Kafka)
```python
# UserService publie un événement quand un user est créé
kafka_producer.send("user.created", {
    "user_id": 123,
    "name": "Alice",
    "email": "alice@example.com"
})

# OrderService écoute et stocke une copie locale
@kafka_consumer("user.created")
def handle_user_created(event):
    # Sauvegarder une copie dans la BDD locale
    local_users_cache[event["user_id"]] = event
```

**Avantages :**
✅ Découplage total
✅ Pas de latence au moment de la commande
✅ Résilience (retry automatique)

**Inconvénients :**
❌ Eventual consistency (les données ne sont pas immédiatement à jour)
❌ Plus complexe à implémenter

### ✅ Solution 3 : Duplication de données
Chaque service garde une **copie locale** des données dont il a besoin.

```python
# OrderService a sa propre table "users_cache"
class UserCache:
    user_id: int
    name: str
    email: str
    # Synchronisé via Kafka
```

**Avantages :**
✅ Pas de dépendance réseau
✅ Performance maximale

**Inconvénients :**
❌ Duplication de données
❌ Consistency complexe

---

## 🔁 TRANSACTIONS DISTRIBUÉES

### Problème
Comment gérer une transaction qui touche plusieurs services ?

**Exemple :** Créer une commande
1. Vérifier l'utilisateur (UserService)
2. Vérifier le stock (InventoryService)
3. Créer la commande (OrderService)
4. Débiter le compte (PaymentService)

### ❌ Solution impossible : Transaction ACID classique
Les transactions SQL (BEGIN...COMMIT) ne fonctionnent PAS entre plusieurs BDD.

### ✅ Solution : Pattern SAGA

Voir **FICHE 4 : KAFKA** pour les détails des Sagas.

---

## 📦 EXEMPLE CONCRET : TP4 KAFKA

### Architecture BDD du TP4

```
┌─────────────────────┐
│  orders-service     │
│  ┌───────────────┐  │
│  │ PostgreSQL    │  │
│  │ - orders      │  │
│  └───────────────┘  │
└─────────────────────┘

┌─────────────────────┐
│ inventory-service   │
│  ┌───────────────┐  │
│  │ PostgreSQL    │  │
│  │ - inventory   │  │
│  └───────────────┘  │
└─────────────────────┘

┌─────────────────────┐
│  payment-service    │
│  (pas de BDD)       │
│  (simulation)       │
└─────────────────────┘
```

### Code OrderService - Modèle BDD

```python
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, completed, failed
    
    # Pas de foreign key vers users ou products !
    # Chaque service a sa propre BDD
```

### Code InventoryService - Modèle BDD

```python
class Inventory(Base):
    __tablename__ = "inventory"
    
    product_id = Column(String, primary_key=True)
    quantity = Column(Integer, nullable=False)
    reserved = Column(Integer, default=0)
```

---

## 🎤 QUESTIONS PROBABLES À L'ORAL

### Q1 : Pourquoi chaque service a sa propre base de données ?
**Réponse type :**
> "C'est le principe 'database per service'. Ça permet de découpler les services, de scaler chaque BDD indépendamment, de choisir le type de BDD adapté (PostgreSQL, Redis, MongoDB...), et d'isoler les pannes. Si une BDD tombe, les autres services continuent de fonctionner."

### Q2 : Comment un service récupère des données d'un autre service ?
**Réponse type :**
> "On ne doit JAMAIS accéder directement à la BDD d'un autre service. On utilise soit des appels API REST pour les besoins synchrones, soit des événements Kafka pour les besoins asynchrones. Par exemple, dans notre TP4, order-service publie un événement 'order.created' que inventory-service écoute."

### Q3 : Quels types de BDD avez-vous utilisés dans le projet ?
**Réponse type :**
> "On a utilisé PostgreSQL pour les données relationnelles (users, teams, battles), Redis comme cache pour les données du Pokédex (évite de rappeler l'API externe à chaque fois), et potentiellement MongoDB pour les logs d'événements. Chaque service choisit la BDD la plus adaptée à son besoin."

### Q4 : C'est quoi l'eventual consistency ?
**Réponse type :**
> "C'est quand les données ne sont pas immédiatement cohérentes entre tous les services, mais le deviennent après un court délai. Par exemple, si on utilise Kafka : quand un user est créé dans auth_service, il faut quelques millisecondes pour que team_service reçoive l'événement et mette à jour son cache local. Pendant ce délai, les données sont 'eventually consistent'."

### Q5 : Comment gérer les transactions sur plusieurs services ?
**Réponse type :**
> "On ne peut pas utiliser les transactions SQL classiques car elles ne traversent pas les services. On utilise le pattern Saga : une série d'événements qui se compensent en cas d'échec. Par exemple dans le TP4, si le paiement échoue, on publie un événement 'payment.failed' et inventory-service libère le stock réservé."

---

## 💡 CONCEPTS CLÉS À RETENIR

1. **Database per service** = chaque service a SA BDD
2. **Pas d'accès direct** = on passe par les API ou Kafka
3. **PostgreSQL** = données relationnelles structurées
4. **Redis** = cache rapide en mémoire
5. **MongoDB** = documents flexibles, logs
6. **Eventual consistency** = les données deviennent cohérentes avec un délai
7. **Saga** = pattern pour les transactions distribuées

---

## ✅ AUTO-TEST

1. Pourquoi on ne partage PAS une BDD entre tous les services ?
2. Comment OrderService récupère les infos d'un user sans accéder à la BDD de UserService ?
3. Quand utiliser PostgreSQL vs Redis vs MongoDB ?
4. C'est quoi l'eventual consistency ?
5. Comment gérer une transaction sur 3 services différents ?

Si tu peux répondre → **✅ Fiche maîtrisée !**
