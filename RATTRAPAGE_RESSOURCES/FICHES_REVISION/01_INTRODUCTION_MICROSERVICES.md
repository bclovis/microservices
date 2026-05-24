# 📘 FICHE 1 : INTRODUCTION AUX MICROSERVICES

> **Source** : Introduction aux microservices.pdf (05/11/2025)

---

## 🎯 QU'EST-CE QU'UN MICROSERVICE ?

### Définition officielle — Martin Fowler
> *"Le style architectural des microservices est une approche permettant de développer une application unique sous la forme d'une suite logicielle intégrant plusieurs services. Ces services sont construits autour des capacités de l'entreprise et peuvent être déployés de façon indépendante."*
> — **Martin Fowler**

### Définition simple
Un microservice est **un service indépendant** qui :
- Fait **UNE seule chose** (principe de responsabilité unique)
- Peut être **déployé seul** sans affecter les autres services
- Communique avec les autres services via **API** (souvent REST/HTTP)
- Possède **sa propre base de données** (database per service)

### Analogie
Imagine un restaurant :
- **Monolithe** = un seul employé fait TOUT (cuisine, service, caisse, ménage)
- **Microservices** = chaque employé a son rôle (cuisinier, serveur, caissier, etc.)

---

## 🏛️ MONOLITHE vs MICROSERVICES

### Architecture Monolithique

```
┌──────────────────────────────────┐
│     APPLICATION MONOLITHIQUE     │
│                                  │
│  ┌────────┐  ┌────────┐         │
│  │  Auth  │  │ Orders │         │
│  └────────┘  └────────┘         │
│  ┌────────┐  ┌────────┐         │
│  │ Users  │  │Products│         │
│  └────────┘  └────────┘         │
│                                  │
│    UNE SEULE BASE DE DONNÉES    │
└──────────────────────────────────┘
```

**Caractéristiques :**
- Tout le code dans un seul projet
- Une seule base de données centralisée
- Déploiement = tout ou rien
- Si un module crash → toute l'application crash

**Avantages :**
✅ Simple à développer au début
✅ Facile à tester localement
✅ Déploiement simple (un seul binaire)

**Inconvénients :**
❌ Difficile à scaler (tout doit scaler en même temps)
❌ Couplage fort entre modules
❌ Déploiement risqué (tout change en même temps)
❌ Une erreur peut tout faire tomber

---

### Architecture Microservices

```
┌────────────┐   ┌────────────┐   ┌────────────┐
│  Service   │   │  Service   │   │  Service   │
│   Users    │──▶│   Orders   │──▶│  Products  │
│            │   │            │   │            │
│  DB Users  │   │  DB Orders │   │ DB Products│
└────────────┘   └────────────┘   └────────────┘
```

**Caractéristiques :**
- Chaque service est **indépendant**
- Chaque service a **sa propre base de données**
- Communication via **API REST** ou **messages** (Kafka)
- Déploiement **indépendant** de chaque service

**Avantages :**
✅ Scalabilité ciblée (on scale seulement ce qui est nécessaire)
✅ Résilience (un service peut tomber sans affecter les autres)
✅ Technologies différentes par service (polyglotte)
✅ Équipes indépendantes (chaque équipe gère son service)
✅ Déploiements plus rapides et moins risqués

**Inconvénients :**
❌ Complexité accrue (plus de services à gérer)
❌ Communication réseau (latence, pannes)
❌ Transactions distribuées complexes
❌ Monitoring et debugging plus difficiles

---

## 📊 QUAND UTILISER MICROSERVICES ?

### ✅ Utiliser Microservices SI :
- Application **grande et complexe**
- **Plusieurs équipes** travaillent dessus
- Besoin de **scaler différemment** certaines parties
- Besoin de **technologies différentes** pour chaque module
- Déploiements **fréquents** et **indépendants**

### ❌ Rester Monolithe SI :
- Petit projet / MVP / prototype
- Équipe réduite (< 5 personnes)
- Pas besoin de scalabilité différenciée
- Simplicity > Scalability

---

## 🔑 PRINCIPES FONDAMENTAUX

### 1. **Single Responsibility Principle**
Chaque service fait **UNE seule chose bien**.

❌ **Mauvais** : Service "BusinessLogic" qui gère users + orders + products
✅ **Bon** : 3 services séparés (UserService, OrderService, ProductService)

### 2. **Database per Service**
Chaque service a **sa propre base de données**.

❌ **Mauvais** : Tous les services accèdent à la même BDD
✅ **Bon** : Chaque service a sa BDD (isolation des données)

**Pourquoi ?**
- Évite le couplage
- Permet de choisir le bon type de BDD par service (PostgreSQL, MongoDB, Redis...)
- Isolation des pannes

### 3. **Communication via API**
Les services ne partagent PAS de code, ils communiquent via **API REST** ou **messages**.

❌ **Mauvais** : Import direct de classes entre services
✅ **Bon** : Appel HTTP REST ou messages Kafka

### 4. **Déploiement Indépendant**
On peut déployer un service **sans impacter les autres**.

❌ **Mauvais** : Déployer UserService oblige à redéployer OrderService
✅ **Bon** : Déployer UserService n'affecte que UserService

### 5. **Tolérance aux pannes**
Si un service tombe, les autres **continuent de fonctionner**.

❌ **Mauvais** : ProductService down → toute l'app est down
✅ **Bon** : ProductService down → OrderService retourne un message d'erreur mais reste up

---

## 🌐 COMMUNICATION ENTRE SERVICES

### 1. Synchrone (REST/HTTP)

```python
# OrderService appelle UserService
import requests

user = requests.get(f"http://user-service:8001/users/{user_id}")
```

**Avantages :**
✅ Simple à comprendre et implémenter
✅ Réponse immédiate

**Inconvénients :**
❌ Couplage temporel (le service doit être disponible)
❌ Latence accumulée (appels en cascade)

### 2. Asynchrone (Messages/Kafka)

```python
# OrderService publie un événement
kafka_producer.send("order.created", {"order_id": 123})

# InventoryService écoute l'événement
@kafka_consumer("order.created")
def handle_order(event):
    reserve_stock(event["order_id"])
```

**Avantages :**
✅ Découplage total (le service n'a pas besoin d'être disponible)
✅ Meilleure scalabilité
✅ Résilience (retry automatique)

**Inconvénients :**
❌ Plus complexe à implémenter
❌ Pas de réponse immédiate
❌ Eventual consistency

---

## 📦 DÉPLOIEMENT

### Conteneurisation (Docker)
Chaque service est **empaqueté dans un container Docker**.

```dockerfile
FROM python:3.11
COPY . /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

**Avantages :**
- Même environnement partout (dev, test, prod)
- Isolation des dépendances
- Déploiement rapide

### Orchestration (Kubernetes)
**Kubernetes** gère le déploiement, scaling, et monitoring des containers.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3  # 3 instances du service
```

---

## 🎤 QUESTIONS PROBABLES À L'ORAL

### Q1 : Quelle est la différence entre monolithe et microservices ?
**Réponse type :**
> "Un monolithe est une application où tout le code est dans un seul projet avec une seule base de données. Les microservices découpent l'application en services indépendants, chacun avec sa propre base de données et déployable séparément. L'avantage principal est la scalabilité ciblée et la résilience."

### Q2 : Quels sont les avantages des microservices ?
**Réponse type :**
> "Les principaux avantages sont : 1) Scalabilité ciblée (on scale seulement ce qui est nécessaire), 2) Résilience (un service peut tomber sans affecter les autres), 3) Déploiements indépendants et plus rapides, 4) Équipes autonomes qui peuvent travailler en parallèle."

### Q3 : Quels sont les inconvénients des microservices ?
**Réponse type :**
> "Les inconvénients sont : 1) Complexité accrue (plus de services à gérer), 2) Communication réseau avec latence, 3) Transactions distribuées complexes, 4) Monitoring et debugging plus difficiles. C'est pourquoi on ne recommande pas les microservices pour les petits projets."

### Q4 : Pourquoi chaque service a sa propre base de données ?
**Réponse type :**
> "C'est le principe 'database per service'. Ça permet : 1) D'éviter le couplage entre services, 2) De choisir le meilleur type de BDD pour chaque service (PostgreSQL, Redis, MongoDB...), 3) D'isoler les pannes (si une BDD tombe, les autres continuent). C'est un principe fondamental des microservices."

### Q5 : Comment les microservices communiquent entre eux ?
**Réponse type :**
> "Deux méthodes principales : 1) **Synchrone** via API REST/HTTP (simple mais crée du couplage), 2) **Asynchrone** via messages (Kafka) pour découpler totalement les services. Dans notre projet, on utilise les deux : REST pour les requêtes directes, et Kafka pour les événements comme la création de commandes."

---

## 💡 CONCEPTS CLÉS À RETENIR

1. **Microservice** = service indépendant avec une seule responsabilité
2. **Database per service** = isolation des données
3. **Communication** = REST (sync) ou Kafka (async)
4. **Conteneurisation** = Docker pour packager
5. **Orchestration** = Kubernetes pour gérer le déploiement
6. **Scalabilité** = on scale seulement ce qui est nécessaire
7. **Résilience** = un service peut tomber sans affecter les autres

---

Image = Template figé (recette)
Container = Instance qui tourne (plat cuisiné)
Dockerfile = Instructions pour créer l'image
Volume = Dossier persistant (données qui survivent)
Docker Compose = Lancer plusieurs services ensemble

## ✅ AUTO-TEST

Réponds à ces questions **sans regarder** :

1. Cite 3 différences entre monolithe et microservices
2. Pourquoi chaque service a sa propre BDD ?
3. Quelle est la différence entre communication synchrone et asynchrone ?
4. Dans quel cas utiliser microservices ? Dans quel cas rester monolithe ?
5. Qu'est-ce que Docker ? Qu'est-ce que Kubernetes ?

Si tu peux répondre à ces 5 questions → **✅ Fiche maîtrisée !**
