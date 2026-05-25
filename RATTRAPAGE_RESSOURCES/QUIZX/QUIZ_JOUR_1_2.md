# 📝 QUIZ JOURS 1-2 : FONDAMENTAUX

> **Objectif** : Valider la compréhension des concepts de base

---

## 🎯 PARTIE 1 : MICROSERVICES VS MONOLITHE

### Q1. Qu'est-ce qu'un monolithe ?
**a)** Une application où tout le code est dans un seul projet  
**b)** Une application distribuée sur plusieurs serveurs  
**c)** Une base de données unique  
**d)** Un service qui gère plusieurs fonctionnalités  

<details>
<summary>Voir la réponse</summary>
✅ **Réponse : a)**  
Un monolithe est une application où tout le code est dans un seul projet, avec une seule base de données.
</details>

---

### Q2. Citez 3 avantages des microservices
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
1. Scalabilité ciblée (on scale seulement ce qui est nécessaire)
2. Résilience (un service peut tomber sans affecter les autres)
3. Déploiements indépendants et plus rapides
4. Équipes autonomes
5. Choix technologiques différents par service
</details>

---

### Q3. Pourquoi chaque microservice a SA propre base de données ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
C'est le principe "database per service" qui permet :
- Découplage total entre services
- Scalabilité indépendante des BDD
- Choix du type de BDD adapté à chaque service
- Isolation des pannes (si une BDD tombe, les autres continuent)
</details>

---

### Q4. Quel est le principal inconvénient des microservices ?
**a)** Coût élevé  
**b)** Complexité accrue  
**c)** Performance faible  
**d)** Impossible à tester  

<details>
<summary>Voir la réponse</summary>
✅ **Réponse : b)**  
La complexité accrue est le principal inconvénient : plus de services à gérer, communication réseau, transactions distribuées, monitoring plus difficile.
</details>

---

## 🎯 PARTIE 2 : API REST ET HTTP

### Q5. Associez chaque verbe HTTP à son usage

| Verbe | Usage |
|-------|-------|
| GET | ? |
| POST | ? |
| PUT | ? |
| DELETE | ? |

<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
- **GET** : Récupérer des données (lecture)
- **POST** : Créer une nouvelle ressource
- **PUT** : Remplacer complètement une ressource
- **DELETE** : Supprimer une ressource
</details>

---

### Q6. Quelle est la différence entre Path Parameters et Query Parameters ?

**Exemple :** `GET /users/42/orders?limit=10&sort=desc`

<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
- **Path Parameters** : `/users/42/orders` → `42` est un path parameter (obligatoire, identifie la ressource)
- **Query Parameters** : `?limit=10&sort=desc` → optionnels, utilisés pour filtrer/paginer
</details>

---

### Q7. Qu'est-ce que Pydantic fait automatiquement dans FastAPI ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Pydantic valide automatiquement les données entrantes selon les types définis. Si les données sont invalides, FastAPI retourne automatiquement une erreur 422 avec les détails de l'erreur.
</details>

---

## 🎯 PARTIE 3 : DOCKER

### Q8. Qu'est-ce que Docker ?
**a)** Un système d'exploitation  
**b)** Une plateforme de conteneurisation  
**c)** Un langage de programmation  
**d)** Une base de données  

<details>
<summary>Voir la réponse</summary>
✅ **Réponse : b)**  
Docker est une plateforme qui permet de packager une application avec toutes ses dépendances dans un conteneur isolé.
</details>

---

### Q9. Quelle est la différence entre un conteneur et une image Docker ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
- **Image** : Template immuable (comme une recette de cuisine)
- **Conteneur** : Instance en cours d'exécution d'une image (comme le plat cuisiné)

Analogie : Image = classe, Conteneur = instance de la classe
</details>

---

### Q10. À quoi sert docker-compose.yml ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
docker-compose.yml permet de définir et lancer plusieurs conteneurs en même temps avec leurs configurations (ports, volumes, réseaux, variables d'environnement). Une seule commande `docker compose up` lance tous les services.
</details>

---

## 🎯 PARTIE 4 : COMMUNICATION ENTRE SERVICES

### Q11. Quelle est la différence entre communication synchrone et asynchrone ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**

**Synchrone (REST/HTTP) :**
- Le service appelant attend la réponse
- Couplage temporel (le service doit être disponible)
- Plus simple à implémenter

**Asynchrone (Kafka) :**
- Le service publie un événement et continue
- Pas de couplage temporel (le consommateur peut être down)
- Plus résilient mais plus complexe
</details>

---

### Q12. Dans le TP4, comment OrderService informe InventoryService qu'une commande a été créée ?
**a)** Appel REST direct  
**b)** Événement Kafka "order.created"  
**c)** Accès direct à la BDD  
**d)** Email  

<details>
<summary>Voir la réponse</summary>
✅ **Réponse : b)**  
OrderService publie un événement Kafka "order.created" que InventoryService écoute. C'est de la communication asynchrone.
</details>

---

## 🎯 PARTIE 5 : BASES DE DONNÉES

### Q13. Quel type de BDD utilisez-vous pour quoi ?

Associez :
1. PostgreSQL
2. Redis
3. MongoDB

Avec :
- A. Cache rapide en mémoire
- B. Données relationnelles structurées
- C. Documents flexibles, logs

<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
1. PostgreSQL → B (données relationnelles structurées)
2. Redis → A (cache rapide en mémoire)
3. MongoDB → C (documents flexibles, logs)
</details>

---

### Q14. Pourquoi OrderService ne doit PAS accéder directement à la BDD de UserService ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Parce que ça crée un couplage fort, viole l'encapsulation, et rend les services non-indépendants. On doit passer par l'API REST de UserService ou utiliser des événements Kafka.
</details>

---

### Q15. C'est quoi l'eventual consistency ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
C'est quand les données ne sont pas immédiatement cohérentes entre tous les services, mais le deviennent après un court délai. Par exemple avec Kafka : il faut quelques millisecondes pour qu'un événement soit reçu par tous les consommateurs.
</details>

---

## 🎯 PARTIE 6 : QUESTIONS OUVERTES

### Q16. Dessinez l'architecture du TP4 Kafka
<details>
<summary>Voir la réponse</summary>
✅ **Réponse attendue :**

```
OrderService (crée commande)
     │
     ├─[order.created]──▶ InventoryService (réserve stock)
     │                          │
     │             [inventory.reserved]
     │                          ▼
     │                   PaymentService (70% succès)
     │                          │
     │         ┌────────────────┴────────────────┐
     │         │                                 │
     │  [payment.succeeded]          [payment.failed]
     │         │                                 │
     │         ▼                                 ▼
     │    ✅ Validé              ❌ Libérer stock (compensation)
     │
     └─────────▶ NotificationsService (logs)
```
</details>

---

### Q17. Expliquez la saga du TP4 en 5 étapes
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
1. OrderService crée une commande et publie "order.created"
2. InventoryService réserve le stock et publie "inventory.reserved"
3. PaymentService traite le paiement (70% succès)
4. Si succès : publie "payment.succeeded" → commande validée
5. Si échec : publie "payment.failed" → InventoryService libère le stock (compensation)
</details>

---

## 📊 SCORE

Compte tes bonnes réponses :

- **15-17** : ✅ Excellent ! Passe au Quiz suivant
- **12-14** : 👍 Bien, révise les points faibles
- **9-11** : ⚠️ Moyen, relis les fiches
- **< 9** : ❌ Insuffisant, recommence les fiches

---

## 🎯 POINTS À REVOIR SI < 15

Si tu as raté des questions sur :
- **Microservices** → Relis **FICHE 1**
- **API REST/FastAPI** → Relis **FICHE 2**
- **Docker** → Cherche des tutoriels Docker
- **Kafka** → Relis **FICHE 4**
- **BDD** → Relis **FICHE 3**

**Objectif : 15/17 minimum avant de passer aux jours 3-4 ! 🔥**
