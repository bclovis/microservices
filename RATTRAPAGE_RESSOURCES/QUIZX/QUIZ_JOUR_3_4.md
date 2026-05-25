# 📝 QUIZ JOURS 3-4 : CONCEPTS AVANCÉS

> **Objectif** : Valider les patterns microservices et Kubernetes

---

## 🎯 PARTIE 1 : API GATEWAY

### Q1. À quoi sert une API Gateway ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Une API Gateway est un point d'entrée unique pour toutes les requêtes vers les microservices. Elle gère :
- Routage vers les bons services
- Sécurité (API Key, JWT)
- Cache
- Agrégation de données
- Rate limiting
- Load balancing
</details>

---

### Q2. Dans le TP5, pourquoi le frontend n'appelle pas directement user-service:8001 ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Parce qu'on utilise une API Gateway (port 8000) qui centralise :
- La sécurité (vérification de l'API Key)
- Le cache (Redis)
- L'agrégation de données (profile = user + orders)
- Le CORS pour autoriser les requêtes frontend

Le frontend ne connaît que la gateway, pas les services internes.
</details>

---

### Q3. Quel est le principal risque de l'API Gateway ?
**a)** Coût élevé  
**b)** Single Point of Failure  
**c)** Lenteur  
**d)** Complexité  

<details>
<summary>Voir la réponse</summary>
✅ **Réponse : b)**  
Single Point of Failure : si la gateway tombe, tous les services deviennent inaccessibles même s'ils fonctionnent. Solution : déployer plusieurs instances avec load balancer.
</details>

---

### Q4. Comment implémenter un cache simple dans la gateway ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379)

@app.get("/users")
async def get_users():
    # Vérifier le cache
    cached = redis_client.get("users")
    if cached:
        return json.loads(cached)
    
    # Appeler le service
    response = requests.get("http://user-service:8001/users")
    data = response.json()
    
    # Mettre en cache 60s
    redis_client.setex("users", 60, json.dumps(data))
    return data
```
</details>

---

## 🎯 PARTIE 2 : KAFKA ET SAGA

### Q5. Qu'est-ce qu'un Topic Kafka ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Un Topic est une catégorie de messages dans Kafka. Exemple : "order.created", "payment.succeeded". Les producers publient des messages dans un topic, et les consumers les lisent depuis ce topic.
</details>

---

### Q6. Quelle est la différence entre Producer et Consumer ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
- **Producer** : Service qui publie des événements dans Kafka (ex: OrderService publie "order.created")
- **Consumer** : Service qui lit et traite les événements (ex: InventoryService lit "order.created" et réserve le stock)
</details>

---

### Q7. Qu'est-ce qu'une Saga Chorégraphie ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
C'est un pattern pour gérer des transactions distribuées. Chaque service écoute des événements, exécute sa logique, et publie de nouveaux événements. Pas de coordinateur central, chaque service réagit aux événements de manière décentralisée.

Exemple TP4 : order.created → inventory.reserved → payment.succeeded/failed
</details>

---

### Q8. Dans le TP4, que se passe-t-il si PaymentService échoue (30% des cas) ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
1. PaymentService publie "payment.failed" avec les détails (order_id, product_id, quantity)
2. InventoryService écoute "payment.failed"
3. InventoryService libère le stock réservé (compensation)
4. La commande reste en status "failed"

C'est la phase de compensation de la saga.
</details>

---

### Q9. Pourquoi Kafka est plus résilient que REST ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Parce que les messages sont persistés dans Kafka. Si un service consommateur est down, les messages restent en attente. Quand le service redémarre, il peut traiter les messages en retard. Avec REST, si le service est down au moment de l'appel, la requête échoue.
</details>

---

### Q10. Complétez le code : Publier un événement Kafka

```python
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Publier "order.created"
producer.send('___________', {
    "order_id": 123,
    "product_id": "prod-1",
    "quantity": 5
})
```

<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
```python
producer.send('order.created', {
    "order_id": 123,
    "product_id": "prod-1",
    "quantity": 5
})
```
</details>

---

## 🎯 PARTIE 3 : KUBERNETES

### Q11. Quelle est la différence entre Docker et Kubernetes ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
- **Docker** : Crée et exécute des conteneurs (emballage de l'application)
- **Kubernetes** : Orchestre les conteneurs (gestion de plusieurs conteneurs sur plusieurs machines : déploiement, scaling, monitoring, auto-healing)

Docker = créer des conteneurs, Kubernetes = gérer des conteneurs en production
</details>

---

### Q12. Associez les composants K8s à leur rôle

| Composant | Rôle |
|-----------|------|
| Pod | ? |
| Deployment | ? |
| Service | ? |

<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
- **Pod** : Plus petite unité K8s (1 ou plusieurs conteneurs)
- **Deployment** : Gère plusieurs replicas d'un Pod avec auto-healing et scaling
- **Service** : Expose les Pods avec un DNS stable
</details>

---

### Q13. Comment scaler user-service de 2 à 10 replicas ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
```bash
kubectl scale deployment user-service --replicas=10
```

Ou modifier le YAML :
```yaml
spec:
  replicas: 10  # Avant : 2
```
Puis `kubectl apply -f user-deployment.yaml`
</details>

---

### Q14. Qu'est-ce que le HPA (Horizontal Pod Autoscaler) ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Le HPA permet l'auto-scaling automatique basé sur des métriques (CPU, RAM). Exemple : si CPU > 80%, K8s crée automatiquement plus de pods (jusqu'à un maximum défini). Si CPU redescend, il supprime des pods.

```bash
kubectl autoscale deployment user-service --cpu-percent=80 --min=2 --max=10
```
</details>

---

### Q15. Qu'est-ce qu'un Rolling Update ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Un déploiement sans downtime. K8s :
1. Crée de nouveaux pods avec la nouvelle version
2. Attend qu'ils soient ready
3. Supprime progressivement les anciens pods

Pendant ce temps, l'application reste accessible. Si problème, on peut rollback.
</details>

---

### Q16. Dans le TP6, pourquoi utilise-t-on `eval $(minikube docker-env)` ?
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
Pour configurer Docker afin qu'il utilise le Docker daemon de Minikube. Ainsi, les images buildées avec `docker build` sont directement disponibles dans Minikube, sans besoin de les pousser sur Docker Hub.
</details>

---

### Q17. Complétez le Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: ___  # 3 instances
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: ___________
    spec:
      containers:
      - name: user-service
        image: _______________
        ports:
        - containerPort: 8001
```

<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3  # 3 instances
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        ports:
        - containerPort: 8001
```
</details>

---

## 🎯 PARTIE 4 : ARCHITECTURE GLOBALE

### Q18. Dessinez l'architecture complète d'un système microservices
<details>
<summary>Voir la réponse</summary>
✅ **Réponse attendue :**

```
Frontend (Angular/React)
       │
       ▼
  API Gateway
  - Sécurité
  - Cache
  - Routage
       │
       ├───────────────┬───────────────┐
       ▼               ▼               ▼
  UserService    OrderService   ProductService
       │               │               │
       ▼               ▼               ▼
   DB Users        DB Orders      DB Products
       │               │               │
       └───────────────┴───────────────┘
                       │
                   KAFKA BUS
              (événements asynchrones)
```
</details>

---

### Q19. Expliquez le flux complet d'une création de commande (TP4)
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**

1. **Client** envoie POST /orders (product_id, quantity)
2. **OrderService** crée la commande en BDD (status: pending) et publie "order.created"
3. **InventoryService** reçoit "order.created", vérifie le stock, réserve si OK, publie "inventory.reserved"
4. **PaymentService** reçoit "inventory.reserved", traite le paiement (70% succès)
5. Si succès : publie "payment.succeeded" → Commande validée
6. Si échec : publie "payment.failed" → InventoryService libère le stock
7. **NotificationsService** affiche tous les événements dans les logs
</details>

---

### Q20. Citez 5 avantages de Kubernetes pour les microservices
<details>
<summary>Voir la réponse</summary>
✅ **Réponse :**
1. Auto-healing (si un pod crash, K8s en recrée un automatiquement)
2. Scaling facile (manuel ou automatique avec HPA)
3. Rolling updates (déploiement sans downtime)
4. Service discovery (DNS automatique entre services)
5. Load balancing (distribue le trafic entre replicas)
6. Gestion centralisée (kubectl pour tout gérer)
</details>

---

## 📊 SCORE

Compte tes bonnes réponses :

- **18-20** : ✅ Excellent ! Tu maîtrises les concepts avancés
- **15-17** : 👍 Très bien, quelques révisions mineures
- **12-14** : ⚠️ Moyen, relis les fiches 3-4-5-6
- **< 12** : ❌ Insuffisant, recommence les fiches

---

## 🎯 POINTS À REVOIR SI < 18

Si tu as raté des questions sur :
- **API Gateway** → Relis **FICHE 5**
- **Kafka/Saga** → Relis **FICHE 4** et refais le TP4
- **Kubernetes** → Relis **FICHE 6** et refais le TP6
- **Architecture** → Dessine des schémas à la main

**Objectif : 18/20 minimum avant de passer au projet ! 🔥**
