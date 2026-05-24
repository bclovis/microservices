# FICHE TP6 — Kubernetes : Deployment, Service, HPA, Scaling

> **Séance :** 15 janvier | **Niveau :** Avancé  
> **Objectif TP :** Déployer 3 microservices FastAPI sur un cluster Kubernetes (Minikube), configurer le scaling automatique (HPA), et comprendre la communication inter-services via les noms DNS Kubernetes

---

## 1. CONTEXTE DU TP — Ce qui était demandé

### Exercice 1 — Déploiement
Créer un cluster et déployer 3 services :
- `user-service` : `GET /users/{user_id}` → `{user_id, name}`
- `product-service` : `GET /products/{product_id}` → `{product_id, name, price}`
- `order-service` : `POST /orders` → appelle les deux autres services (via noms DNS K8s), retourne `{user, product, "Order Created"}`

### Exercice 2 — Scaling
- Activer 2 types de scaling : **HPA (Horizontal Pod Autoscaler)** + ressources (requests/limits)
- Lancer un générateur de charge (busybox/curl) sur order-service
- Vérifier l'autoscaling en direct

### Exercice 3 — Environnements
- **ConfigMaps** : pour les configs non-sensibles
- **Secrets** : pour les données sensibles (clés API, mots de passe)
- Sortir toutes les infos sensibles du code

### Exercice 4 — Ingress
- Installer un ingress controller (nginx)
- Configurer un nom de domaine unique pour accéder aux services

---

## 2. ARCHITECTURE K8s — Schéma

```
[Minikube Cluster]
│
├── Namespace: default
│
├── Deployment: user-service (2 replicas)
│   └── Pod user-service-xxx → Container user-service:latest → port 8000
│
├── Service: user-service (type: ClusterIP)
│   └── DNS interne: http://user-service:8000
│
├── Deployment: product-service (2 replicas)
│   └── Service: product-service → DNS: http://product-service:8000
│
├── Deployment: order-service (2 replicas)
│   └── Service: order-service (type: NodePort → accessible depuis l'extérieur)
│
└── HPA: (ex2)
    └── Scale up si CPU > 50%
```

**DNS K8s automatique :** Dans un cluster, chaque Service crée un nom DNS `<nom-service>:<port>`. Un pod peut appeler `http://user-service:8000/users/1` directement, sans connaître l'IP du pod.

---

## 3. LES MICROSERVICES — Code

### user-service/app.py
```python
from fastapi import FastAPI

app = FastAPI()

users = {
    1: {"user_id": 1, "name": "Betsaleel"},
    2: {"user_id": 2, "name": "Sara"},
    3: {"user_id": 3, "name": "Charlie"}
}

@app.get("/")
def root():
    return {"service": "user-service", "status": "running"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = users.get(user_id)
    if user:
        return user
    return {"error": "User not found"}
```

### order-service/app.py — Communication inter-services
```python
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

@app.post("/orders")
async def create_order(user_id: int, product_id: int):
    async with httpx.AsyncClient() as client:
        
        # ⚠️ Utiliser les noms de services K8s, PAS localhost:port !
        user_response = await client.get(f"http://user-service:8000/users/{user_id}")
        if user_response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        user = user_response.json()
        
        product_response = await client.get(f"http://product-service:8000/products/{product_id}")
        if product_response.status_code != 200:
            raise HTTPException(status_code=404, detail="Product not found")
        product = product_response.json()
    
    return {
        "user": user["name"],
        "product": product["name"],
        "price": product["price"],
        "message": "Order Created"
    }
```

### Dockerfile (identique pour tous les services)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 4. MANIFESTES KUBERNETES — Les 3 types

### 4.1 — Deployment
```yaml
# k8s/user-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service          # Nom du déploiement
spec:
  replicas: 2                 # 2 pods en permanence
  selector:
    matchLabels:
      app: user-service       # Sélectionne les pods avec ce label
  template:
    metadata:
      labels:
        app: user-service     # Label appliqué aux pods créés
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        imagePullPolicy: Never   # Utiliser l'image locale (Minikube), pas Docker Hub
        ports:
        - containerPort: 8000
        # Exercice 2 : ressources pour activer HPA
        resources:
          requests:
            cpu: 100m           # 100 millicores = 0.1 vCPU
            memory: 128Mi
          limits:
            cpu: 500m           # Max 0.5 vCPU
            memory: 256Mi
```

### 4.2 — Service (ClusterIP)
```yaml
# k8s/user-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service          # ← Ce nom devient le DNS interne !
spec:
  selector:
    app: user-service         # Redirige vers les pods avec ce label
  ports:
  - protocol: TCP
    port: 8000                # Port exposé par le service
    targetPort: 8000          # Port du container
  # type: ClusterIP (défaut) → accessible seulement à l'intérieur du cluster
```

### Service NodePort (pour accès externe)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  type: NodePort              # Accessible depuis l'extérieur du cluster
  selector:
    app: order-service
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
    nodePort: 30000           # Port sur l'IP de Minikube (30000-32767)
```

### 4.3 — HPA (Horizontal Pod Autoscaler)
```yaml
# k8s/user-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service        # Quel déploiement scaler ?
  minReplicas: 2              # Minimum 2 pods (même si pas de charge)
  maxReplicas: 10             # Maximum 10 pods
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50  # Scaler si CPU moyen > 50%
```

---

## 5. SCRIPT DE DÉPLOIEMENT

```bash
#!/bin/bash
# deploy.sh (Exercice 1)

# 1. Configurer Docker pour utiliser le registre interne de Minikube
eval $(minikube docker-env)
# ↑ Essentiel ! Sans ça, les images sont construites sur le Docker hôte,
#   pas dans Minikube → imagePullPolicy: Never ne trouve pas l'image

# 2. Construire les images Docker
cd user-service && docker build -t user-service:latest . && cd ..
cd product-service && docker build -t product-service:latest . && cd ..
cd order-service && docker build -t order-service:latest . && cd ..

# 3. Appliquer les manifestes K8s
kubectl apply -f k8s/user-deployment.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/product-deployment.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/order-deployment.yaml
kubectl apply -f k8s/order-service.yaml

# (Exercice 2 : HPA)
kubectl apply -f k8s/user-hpa.yaml
kubectl apply -f k8s/product-hpa.yaml
kubectl apply -f k8s/order-hpa.yaml

# 4. Vérifier le déploiement
kubectl get deployments
kubectl get services
kubectl get pods
kubectl get hpa
```

---

## 6. COMMANDES KUBECTL — Les essentielles

### Démarrage Minikube
```bash
minikube start                    # Démarrer le cluster
minikube status                   # Vérifier l'état
eval $(minikube docker-env)       # Connecter Docker à Minikube
minikube ip                       # Obtenir l'IP de Minikube
```

### Gestion des ressources
```bash
# Voir toutes les ressources
kubectl get all
kubectl get pods
kubectl get deployments
kubectl get services
kubectl get hpa

# Détails d'un pod
kubectl describe pod <pod-name>
kubectl describe deployment user-service

# Logs d'un pod
kubectl logs <pod-name>
kubectl logs -f <pod-name>          # Suivre en temps réel
kubectl logs deployment/user-service # Logs du déploiement
```

### Appliquer/Supprimer des manifestes
```bash
kubectl apply -f k8s/user-deployment.yaml    # Créer ou mettre à jour
kubectl delete -f k8s/user-deployment.yaml   # Supprimer
kubectl apply -f k8s/                        # Appliquer tout un dossier
```

### Debugging
```bash
# Entrer dans un pod
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec -it <pod-name> -- /bin/sh

# Port-forward pour tester localement
kubectl port-forward service/order-service 8080:8000
# → curl localhost:8080/orders

# Vérifier l'autoscaling
kubectl get hpa --watch               # Observer en temps réel
kubectl top pods                      # CPU/RAM des pods (nécessite metrics-server)
```

---

## 7. EXERCICE 2 — Test de Charge avec busybox

```bash
# Lancer un générateur de charge (curl en boucle)
kubectl run -i --tty load-generator \
  --rm --image=curlimages/curl:latest \
  --restart=Never -- /bin/sh -c '
while sleep 0.1; do
  curl -s -X POST http://order-service:8000/orders?user_id=1&product_id=1 \
    -w "\nHTTP Status: %{http_code}\n"
done
'

# Dans un autre terminal : observer l'autoscaling
kubectl get hpa --watch
# user-service-hpa   Deployment/user-service   cpu: 80%/50%   2         10        5          ...
# → K8s a créé 5 pods automatiquement !

kubectl get pods --watch
# user-service-xxx   Running
# user-service-yyy   Running
# user-service-zzz   ContainerCreating  ← nouvelles instances
```

---

## 8. EXERCICE 3 — ConfigMaps et Secrets

### ConfigMap (données non-sensibles)
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "production"
  MAX_CONNECTIONS: "100"
  SERVICE_NAME: "user-service"
```

### Secret (données sensibles)
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  # Valeurs encodées en base64 : echo -n "valeur" | base64
  API_KEY: c2VjcmV0LWFwaS1rZXktMTIz  # "secret-api-key-123" en base64
  DB_PASSWORD: cGFzc3dvcmQxMjM=        # "password123" en base64
```

### Utiliser dans le Deployment
```yaml
spec:
  containers:
  - name: user-service
    image: user-service:latest
    env:
    # Depuis ConfigMap
    - name: APP_ENV
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: APP_ENV
    # Depuis Secret
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: API_KEY
```

### Lire dans le code Python
```python
import os

API_KEY = os.getenv("API_KEY", "default-key")
APP_ENV = os.getenv("APP_ENV", "development")
```

---

## 9. EXERCICE 4 — Ingress Controller

```bash
# Installer l'ingress controller nginx
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.14.1/deploy/static/provider/cloud/deploy.yaml

# Vérifier l'installation
kubectl get pods -n ingress-nginx
```

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: microservices-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: microservices.local   # Nom de domaine unique
    http:
      paths:
      - path: /users
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 8000
      - path: /products
        pathType: Prefix
        backend:
          service:
            name: product-service
            port:
              number: 8000
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 8000
```

---

## 10. DIFFÉRENCES ClusterIP vs NodePort vs Ingress

| Type | Accessible depuis | Cas d'usage |
|------|------------------|-------------|
| `ClusterIP` (défaut) | Intérieur du cluster seulement | Communication inter-services |
| `NodePort` | IP Minikube + port 30000-32767 | Tests locaux |
| `LoadBalancer` | IP externe (cloud) | Production cloud |
| `Ingress` | Nom de domaine (via controller) | Production avec domaine |

---

## 11. QUESTIONS D'ORAL POSSIBLES SUR CE TP

**Q : Qu'est-ce qu'un Pod en Kubernetes ?**
> La plus petite unité déployable en K8s. Contient un ou plusieurs containers qui partagent le réseau et le stockage. Un Pod a une IP éphémère (change à chaque redémarrage). Le Service fournit une IP stable qui redirige vers les pods.

**Q : Pourquoi `imagePullPolicy: Never` ?**
> Par défaut K8s essaie de télécharger l'image depuis un registre (Docker Hub). Avec Minikube, les images sont construites localement avec `eval $(minikube docker-env)`. `Never` force K8s à utiliser l'image locale sans essayer de la télécharger.

**Q : Qu'est-ce que `eval $(minikube docker-env)` ?**
> Configure les variables d'environnement Docker (`DOCKER_HOST`, etc.) pour pointer vers le daemon Docker **à l'intérieur** de Minikube. Sans ça, les images sont construites sur le Docker du hôte, pas dans le cluster → K8s ne les trouve pas.

**Q : Comment fonctionne le DNS K8s ?**
> K8s crée automatiquement un enregistrement DNS pour chaque Service. Format : `<service-name>.<namespace>.svc.cluster.local`. Dans le même namespace, `http://user-service:8000` fonctionne directement. C'est pourquoi on utilise le nom du service et non l'IP (qui change).

**Q : Qu'est-ce que le HPA et comment déclenche-t-il le scaling ?**
> HorizontalPodAutoscaler surveille les métriques (CPU, RAM) des pods d'un Deployment. Si CPU moyen > seuil configuré (ex: 50%) → K8s crée de nouveaux pods (jusqu'à maxReplicas). Quand la charge baisse → K8s supprime les pods excédentaires (jusqu'à minReplicas).

**Q : Différence entre `requests` et `limits` pour les ressources ?**
> `requests` = ressources garanties (K8s schedule le pod sur un node qui a au moins ces ressources disponibles). `limits` = maximum autorisé (si le container dépasse → CPU throttling, ou si RAM → OOMKilled). Le HPA utilise `requests` comme référence pour calculer l'utilisation %.

**Q : Pourquoi les services communiquent via `http://user-service:8000` et non `http://localhost:8001` ?**
> En K8s, chaque pod a sa propre IP. `localhost` dans un pod ne pointe que sur ce pod. Le Service K8s crée un point d'entrée stable avec un DNS interne. `http://user-service:8000` est résolu par kube-dns vers les pods sains du service (avec load balancing automatique).
