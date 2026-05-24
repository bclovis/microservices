# S5 — Kubernetes en microservices : Théorie + TP6 complet

> Cours de Lalanne Raphaël — Séance du 15 janvier  
> Source : `Kubernetes in micros.pdf`  
> Code : `TP6/`

---

## 1. Rappels concepts Kubernetes essentiels

### Pod
- Unité de base dans Kubernetes
- Contient un ou plusieurs containers Docker
- Éphémère : un pod peut être tué et recréé à tout moment
- A une IP interne (qui change à chaque recréation)

### Deployment
- Gère la création et le maintien d'un ensemble de pods **identiques** (replicas)
- Si un pod meurt → le Deployment en crée un nouveau automatiquement
- Permet le rolling update (mise à jour sans downtime)
- Définit : image Docker, nombre de replicas, ressources, labels

### Service
- **Adresse réseau stable** pour accéder à un ensemble de pods
- Les pods changent d'IP, le Service a une IP/DNS **fixe**
- Utilise les labels pour sélectionner les pods cibles

**Types de Service :**

| Type | Description | Quand utiliser |
|------|-------------|----------------|
| `ClusterIP` | Accessible **seulement depuis le cluster** (par défaut) | Communication inter-services |
| `NodePort` | Accessible depuis **l'extérieur** via `nodeIP:nodePort` | Tests/dev sur minikube |
| `LoadBalancer` | IP externe gérée par le cloud provider | Production cloud (AWS/GCP) |

### HPA — Horizontal Pod Autoscaler
- **Scale automatiquement** le nombre de pods en fonction de la charge CPU/mémoire
- Exige que les pods aient des `resources.requests` définis
- `minReplicas` ≤ replicas courants ≤ `maxReplicas`

### ConfigMap
- Stocker des données **non confidentielles** en dehors du code (ex: URLs, paramètres)
- Données sous forme de paires clé-valeur
- Injectables comme variables d'environnement ou volumes dans les pods

### Secret
- Comme ConfigMap mais pour les **données sensibles** (mots de passe, tokens, clés API)
- Encodé en base64 dans Kubernetes
- À ne jamais mettre dans le code source ou dans un Dockerfile

### Ingress
- Gère l'accès **HTTP/HTTPS depuis l'extérieur** vers les services du cluster
- Permet de router par chemin (`/users` → user-service, `/orders` → order-service)
- Nécessite un Ingress Controller (ex: nginx)

---

## 2. Lien avec les microservices

**Pourquoi Kubernetes est idéal pour les microservices ?**

| Problème microservices | Solution Kubernetes |
|------------------------|---------------------|
| Déployer plusieurs services | `kubectl apply -f k8s/` déploie tout |
| Services qui tombent | Deployment redémarre les pods automatiquement |
| Augmenter la capacité | HPA scale automatiquement |
| Communication inter-services | Service (ClusterIP) + noms DNS stables |
| Données de config sensibles | ConfigMaps + Secrets |
| Point d'entrée unique | Ingress controller |

**⚠️ Important du cours (slide 2) :**
> "POST /orders fait appel aux deux premières APIs. **Utilisez les noms de services plutôt que localhost:<port>.**"

→ Dans Kubernetes, `http://user-service:8000` (nom du Service K8s) au lieu de `http://localhost:8001`

---

## 3. Exercice 1 — Déploiement basique (TP6/ex1)

**Objectif :** Créer un cluster k8s-fastapi et y déployer :
- `user-service` : `GET /users/{user_id}` → user_id + name
- `product-service` : `GET /products/{product_id}` → product_id + name + price
- `order-service` : `POST /orders` → user + product + "Order Created"

### k8s/user-deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service       # Nom du Deployment
spec:
  replicas: 2              # 2 pods en permanence
  selector:
    matchLabels:
      app: user-service    # Cible les pods avec ce label
  template:
    metadata:
      labels:
        app: user-service  # Label mis sur les pods créés
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        imagePullPolicy: Never    # ← OBLIGATOIRE avec minikube local
        # "Never" = ne pas chercher l'image sur Docker Hub, utiliser l'image locale
        ports:
        - containerPort: 8000
```

### k8s/user-service.yaml (Service = ClusterIP par défaut)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service       # ← Ce nom devient le DNS interne du cluster
spec:
  selector:
    app: user-service      # Cible les pods avec le label app: user-service
  ports:
  - protocol: TCP
    port: 8000             # Port exposé par le Service
    targetPort: 8000       # Port du container
```

**Avec ce Service, `http://user-service:8000` fonctionne depuis n'importe quel pod du cluster.**

### Script de déploiement (ex1/deploy.sh)
```bash
#!/bin/bash

# 1. Pointer Docker vers le registry de minikube (obligatoire pour images locales)
eval $(minikube docker-env)

# 2. Builder les images dans le contexte Docker de minikube
cd user-service
docker build -t user-service:latest .
cd ../product-service
docker build -t product-service:latest .
cd ../order-service
docker build -t order-service:latest .
cd ..

# 3. Déployer les manifests Kubernetes
kubectl apply -f k8s/user-deployment.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/product-deployment.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/order-deployment.yaml
kubectl apply -f k8s/order-service.yaml

# 4. Vérifier le déploiement
sleep 10
kubectl get deployments
kubectl get services
kubectl get pods

echo "order-service accessible sur: http://$(minikube ip):30000"
```

---

## 4. Exercice 2 — Scaling (HPA + VPA) (TP6/ex2)

**Objectif :** Activer 2 types de scaling sur les déploiements + tester avec busybox

> "Activez 2 différents types de scaling sur vos déploiements (scaling = adaptation en fonction de la demande de ressource)."

### Deux types de scaling

| Type | Description | Objet K8s |
|------|-------------|-----------|
| **HPA** (Horizontal Pod Autoscaler) | Ajoute/retire des **pods** | `HorizontalPodAutoscaler` |
| **VPA** (Vertical Pod Autoscaler) | Augmente les **ressources** d'un pod (CPU/RAM) | `VerticalPodAutoscaler` |

### Déploiement avec resources obligatoires pour HPA

```yaml
# ex2/k8s/user-deployment.yaml (ajoute la section resources)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 2
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
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
      resources:
        requests:              # ← OBLIGATOIRE pour que HPA fonctionne
          cpu: 100m            # 100 millicores = 0.1 CPU
          memory: 128Mi        # 128 mégaoctets
        limits:                # Maximum autorisé
          cpu: 500m            # 500 millicores = 0.5 CPU
          memory: 256Mi
```

### HPA — Horizontal Pod Autoscaler
```yaml
# ex2/k8s/user-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service        # ← Cible ce Deployment
  minReplicas: 2              # Jamais moins de 2 pods
  maxReplicas: 10             # Jamais plus de 10 pods
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50   # Si CPU > 50% en moyenne → scale up
```

**Comment ça marche :**
- Si CPU moyen des pods > 50% → K8s ajoute des pods (jusqu'à maxReplicas)
- Si CPU moyen < 50% → K8s retire des pods (jusqu'à minReplicas)
- K8s vérifie toutes les 15-30 secondes

### Test de charge avec busybox (du cours, slide 3)
```bash
kubectl run -i --tty load-generator \
  --rm --image=curlimages/curl:latest \
  --restart=Never -- /bin/sh -c '
while sleep 0.01; do
  curl -s -X POST "http://order-service:8000/orders?user_id=1&product_id=1" \
    -H "Content-Type: application/json" \
    -d "{\"user\":\"Toto\",\"product\":\"Tata\"}" \
    -w "\nHTTP Status: %{http_code}\n"
done
'
```

**Notes :**
- `--rm` : supprime le pod après la fin
- `--restart=Never` : pod unique (pas géré par un Deployment)
- `curlimages/curl:latest` : image légère avec curl uniquement
- Le pod est **dans le cluster** → peut accéder à `http://order-service:8000` par DNS

### Depuis TP6/ex2 test-load.sh (code réel)
```bash
kubectl delete pod load-generator 2>/dev/null || true

kubectl run -i --tty load-generator \
  --rm --image=curlimages/curl:latest \
  --restart=Never -- /bin/sh -c '
while sleep 0.01; do
  curl -s -X POST "http://order-service:8000/orders?user_id=1&product_id=1" \
    -w "\nHTTP Status: %{http_code}\n"
done
'
```

### Vérifier le scaling en action
```bash
# Surveiller l'HPA en temps réel
kubectl get hpa --watch

# Voir les pods se multiplier
kubectl get pods --watch

# Stats détaillées
kubectl describe hpa user-service-hpa
```

---

## 5. Exercice 3 — Environnements : ConfigMaps + Secrets

**Objectif :** Sortir les données de configuration et sensibles du code

> "Bloquez derrière une clé d'API vos services, et sortez de votre code toutes les informations concernant un user et/ou un produit."

### ConfigMap — Données non confidentielles

```yaml
# k8s/app-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Clé-valeur simple
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  MAX_CONNECTIONS: "10"
  USER_SERVICE_URL: "http://user-service:8000"
  # Données structurées (JSON/YAML comme string)
  users: |
    [
      {"id": 1, "name": "Alice", "email": "alice@example.com"},
      {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ]
```

### Secret — Données confidentielles
```yaml
# k8s/app-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  # ← Valeurs encodées en base64
  # echo -n "secret-api-key-123" | base64
  API_KEY: c2VjcmV0LWFwaS1rZXktMTIz
  DB_PASSWORD: bXlzZWNyZXRwYXNzd29yZA==
  JWT_SECRET: c3VwZXJzZWNyZXRqd3RrZXk=
```

### Référencer ConfigMap + Secret dans un Deployment
```yaml
spec:
  containers:
  - name: order-service
    image: order-service:latest
    env:
    # Depuis ConfigMap
    - name: USER_SERVICE_URL
      valueFrom:
        configMapKeyRef:
          name: app-config           # Nom du ConfigMap
          key: USER_SERVICE_URL      # Clé dans le ConfigMap
    # Depuis Secret
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: app-secrets          # Nom du Secret
          key: API_KEY               # Clé dans le Secret
```

### Côté Python, lire les variables d'environnement
```python
import os

# Lire les variables d'env injectées par K8s (ConfigMap/Secret)
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
API_KEY = os.getenv("API_KEY", "default-key")
DB_PASSWORD = os.getenv("DB_PASSWORD")
```

---

## 6. Exercice 4 — Ingress Controller

**Objectif :** Services accessibles via un nom de domaine unique, routage par path

> "Installez un ingress controller avec la commande suivante :  
> `kubectl apply -f https://raw.githubusercontent.com/.../ingress-nginx/...deploy.yaml`
> 
> Puis appliquez une telle structure sur votre application, de sorte à ce que vos services soient appelés derrière un nom de domaine unique."

### Installer Ingress Controller nginx
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.14.1/deploy/static/provider/cloud/deploy.yaml
```

### Manifest Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx          # ← Utiliser le controller nginx
  rules:
  - host: myapp.local              # Nom de domaine unique
    http:
      paths:
      - path: /users               # /users → user-service
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 8000
      - path: /products            # /products → product-service
        pathType: Prefix
        backend:
          service:
            name: product-service
            port:
              number: 8000
      - path: /orders              # /orders → order-service
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 8000
```

### Accès via nom de domaine
```bash
# Avec minikube tunnel (expose l'IP externe)
minikube tunnel

# Ajouter dans /etc/hosts
echo "127.0.0.1 myapp.local" >> /etc/hosts

# Maintenant accessible !
curl http://myapp.local/users
curl http://myapp.local/products/1
curl -X POST http://myapp.local/orders
```

---

## 7. Commandes kubectl essentielles

```bash
# Voir l'état du cluster
kubectl get pods             # Liste des pods
kubectl get pods --watch     # En temps réel
kubectl get deployments      # Deployments
kubectl get services         # Services
kubectl get hpa              # Horizontal Pod Autoscalers
kubectl get configmaps       # ConfigMaps
kubectl get secrets          # Secrets

# Déployer
kubectl apply -f fichier.yaml           # Appliquer un manifest
kubectl apply -f k8s/                  # Appliquer tous les manifests d'un dossier

# Logs et debug
kubectl logs pod-name                  # Logs d'un pod
kubectl logs pod-name -f               # Logs en temps réel
kubectl describe pod pod-name          # Détails d'un pod
kubectl describe deployment deploy-name # Détails d'un deployment

# Nettoyage
kubectl delete -f k8s/                 # Supprimer tout ce qu'on a déployé
kubectl delete pod pod-name            # Supprimer un pod

# Minikube
eval $(minikube docker-env)            # Pointer Docker vers minikube
minikube ip                            # IP de minikube
minikube tunnel                        # Exposer les services externes
minikube start                         # Démarrer minikube
minikube stop                          # Arrêter minikube
```

---

## 8. Résumé des objets Kubernetes (pour l'oral)

| Objet | Type | Rôle |
|-------|------|------|
| `Deployment` | Contrôleur | Maintient N replicas de pods |
| `Service` | Réseau | Adresse stable pour un ensemble de pods |
| `HPA` | Autoscaling | Scale le nombre de pods selon métriques |
| `ConfigMap` | Config | Données non sensibles (URL, paramètres) |
| `Secret` | Config | Données sensibles (passwords, tokens) |
| `Ingress` | Réseau | Routage HTTP externe par path/domaine |
| `Pod` | Workload | Conteneur(s) en cours d'exécution |

---

## 9. Questions d'oral probables

**Q: Quelle est la différence entre un Deployment et un Service ?**  
R: Un Deployment gère la création et la maintenance de pods (combien, quelle image). Un Service donne une adresse réseau stable pour accéder à ces pods (les pods changent d'IP, le Service a une IP/DNS fixe).

**Q: Pourquoi utiliser `imagePullPolicy: Never` avec minikube ?**  
R: Par défaut, K8s essaie de télécharger l'image depuis Docker Hub. Avec minikube, les images sont buildées localement dans le contexte Docker de minikube (via `eval $(minikube docker-env)`). `imagePullPolicy: Never` indique à K8s d'utiliser l'image locale sans télécharger.

**Q: Comment fonctionne le HPA ?**  
R: HPA surveille les métriques (CPU/mémoire) des pods. Si la CPU moyenne dépasse `averageUtilization` → il augmente le nombre de pods (jusqu'à `maxReplicas`). Quand la charge baisse → il réduit les pods (jusqu'à `minReplicas`). Obligatoire : les pods doivent avoir des `resources.requests` définis.

**Q: Quelle est la différence entre ConfigMap et Secret ?**  
R: Même mécanisme, mais Secret est pour les données sensibles (stocké encodé en base64, accès restreint). ConfigMap est pour les données non sensibles (URL, paramètres de config). Les deux s'injectent comme variables d'environnement dans les pods.

**Q: Pourquoi utiliser des noms de services K8s plutôt que localhost dans le code ?**  
R: Dans K8s, plusieurs pods du même service tournent en parallèle. `localhost` ne fonctionnerait que pour le pod courant. Le nom du Service K8s (ex: `user-service`) est résolu par le DNS interne du cluster vers le bon pod (avec load balancing automatique entre les replicas).

**Q: Qu'est-ce qu'un Ingress et quand l'utiliser ?**  
R: Un Ingress est un proxy HTTP externe qui route les requêtes vers différents services selon le path ou le nom de domaine. Il faut d'abord installer un Ingress Controller (nginx). Utile pour avoir un seul point d'entrée extérieur avec un nom de domaine unique.
