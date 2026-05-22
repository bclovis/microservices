# 📘 FICHE 6 : KUBERNETES

> **Source** : Kubernetes in micros.pdf (15/01/2026)

---

## 🎯 QU'EST-CE QUE KUBERNETES (K8S) ?

**Kubernetes** est un **orchestrateur de conteneurs** qui automatise le déploiement, la mise à l'échelle, et la gestion des applications conteneurisées.

### Analogie
- **Docker** = conteneur (comme un appartement meublé portable)
- **Kubernetes** = gestionnaire d'immeuble (qui gère plein d'appartements)

---

## 🏗️ ARCHITECTURE KUBERNETES

```
┌─────────────────────────────────────────────┐
│           KUBERNETES CLUSTER                 │
│                                             │
│  ┌────────────┐  ┌────────────┐            │
│  │   Node 1   │  │   Node 2   │            │
│  │            │  │            │            │
│  │ ┌────────┐ │  │ ┌────────┐ │            │
│  │ │  Pod1  │ │  │ │  Pod2  │ │            │
│  │ │  🐳    │ │  │ │  🐳    │ │            │
│  │ └────────┘ │  │ └────────┘ │            │
│  └────────────┘  └────────────┘            │
│                                             │
│  Control Plane (Master)                     │
│  - API Server                               │
│  - Scheduler                                │
│  - Controller Manager                       │
└─────────────────────────────────────────────┘
```

---

## 📦 COMPOSANTS KUBERNETES

### 1. **Pod** 🥚
La plus petite unité déployable = **1 ou plusieurs conteneurs**.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: user-service-pod
spec:
  containers:
  - name: user-service
    image: user-service:latest
    ports:
    - containerPort: 8001
```

**Important :** On ne crée presque JAMAIS de Pods directement, on utilise des **Deployments**.

### 2. **Deployment** 🚀
Gère plusieurs réplicas d'un Pod.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3  # 3 instances du service
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

**Avantages :**
- Auto-healing : si un Pod crash, K8s en recrée un
- Scaling : changer `replicas: 3` → `replicas: 10`
- Rolling updates : déploiement sans downtime

### 3. **Service** 🌐
Expose les Pods avec un **DNS stable**.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP  # Interne au cluster
```

**Types de Service :**
- **ClusterIP** : Accessible seulement dans le cluster
- **NodePort** : Expose sur un port du node
- **LoadBalancer** : Crée un load balancer externe (AWS, GCP...)

### 4. **Namespace** 📁
Séparer les ressources (dev, staging, prod).

```bash
kubectl create namespace prod
kubectl create namespace dev
```

### 5. **ConfigMap** 🔧
Configuration externe (variables d'environnement).

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_URL: "postgresql://localhost:5432/mydb"
  LOG_LEVEL: "info"
```

### 6. **Secret** 🔐
Stocker des données sensibles (passwords, API keys).

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  password: cGFzc3dvcmQxMjM=  # base64 encodé
```

---

## 🚀 COMMANDES KUBECTL ESSENTIELLES

### Installation
```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Vérifier
kubectl version --client
```

### Minikube (cluster local)
```bash
# Installer
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Démarrer le cluster
minikube start

# Vérifier
kubectl cluster-info
```

### Déploiement
```bash
# Appliquer un fichier YAML
kubectl apply -f user-deployment.yaml

# Voir les deployments
kubectl get deployments

# Voir les pods
kubectl get pods

# Voir les services
kubectl get services

# Tout voir
kubectl get all
```

### Scaling
```bash
# Scaler à 5 replicas
kubectl scale deployment user-service --replicas=5

# Auto-scaling (HPA)
kubectl autoscale deployment user-service --cpu-percent=80 --min=2 --max=10
```

### Logs et Debug
```bash
# Logs d'un pod
kubectl logs user-service-abc123

# Logs en temps réel
kubectl logs -f user-service-abc123

# Décrire un pod (pour debug)
kubectl describe pod user-service-abc123

# Shell dans un pod
kubectl exec -it user-service-abc123 -- /bin/bash
```

### Suppression
```bash
# Supprimer un deployment
kubectl delete deployment user-service

# Supprimer à partir d'un fichier
kubectl delete -f user-deployment.yaml

# Tout supprimer
kubectl delete all --all
```

---

## 📦 EXEMPLE COMPLET : TP6

### Architecture

```
┌──────────────────────────────────────┐
│      KUBERNETES CLUSTER              │
│                                      │
│  ┌─────────────────────────────────┐│
│  │  Deployment: user-service       ││
│  │  Replicas: 2                    ││
│  │  ┌────────┐      ┌────────┐    ││
│  │  │ Pod 1  │      │ Pod 2  │    ││
│  │  └────────┘      └────────┘    ││
│  └─────────────────────────────────┘│
│              ▲                       │
│              │                       │
│  ┌─────────────────────────────────┐│
│  │  Service: user-service          ││
│  │  Type: ClusterIP                ││
│  │  Port: 8001                     ││
│  └─────────────────────────────────┘│
└──────────────────────────────────────┘
```

### 1. Dockerfile (user-service/Dockerfile)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2. Deployment (k8s/user-deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  labels:
    app: user-service
spec:
  replicas: 2  # 2 instances
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
        imagePullPolicy: Never  # Pour Minikube
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          value: "postgresql://localhost:5432/users"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
```

### 3. Service (k8s/user-service.yaml)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8001
  type: ClusterIP  # Accessible dans le cluster
```

### 4. Script de déploiement (deploy.sh)

```bash
#!/bin/bash

# Configurer Docker pour Minikube
eval $(minikube docker-env)

# Build les images dans Minikube
cd user-service
docker build -t user-service:latest .
cd ..

cd product-service
docker build -t product-service:latest .
cd ..

cd order-service
docker build -t order-service:latest .
cd ..

# Déployer sur K8s
kubectl apply -f k8s/user-deployment.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/product-deployment.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/order-deployment.yaml
kubectl apply -f k8s/order-service.yaml

# Attendre que les pods soient prêts
kubectl wait --for=condition=ready pod -l app=user-service --timeout=60s

# Vérifier
kubectl get all
```

---

## ⚡ SCALABILITÉ AVEC KUBERNETES

### Scaling manuel
```bash
# Scaler à 5 replicas
kubectl scale deployment user-service --replicas=5
```

### Horizontal Pod Autoscaler (HPA)
Auto-scaling basé sur le CPU ou la mémoire.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80  # Scaler si CPU > 80%
```

**Comportement :**
- Si CPU < 80% : maintenir 2 replicas
- Si CPU > 80% : créer plus de replicas (jusqu'à 10)
- Si CPU redescend : supprimer des replicas

---

## 🔄 ROLLING UPDATES

Déployer une nouvelle version **sans downtime**.

```bash
# Mettre à jour l'image
kubectl set image deployment/user-service user-service=user-service:v2

# K8s va :
# 1. Créer de nouveaux pods avec v2
# 2. Attendre qu'ils soient ready
# 3. Supprimer les anciens pods avec v1
```

**Rollback si problème :**
```bash
kubectl rollout undo deployment/user-service
```

---

## 🎤 QUESTIONS PROBABLES À L'ORAL

### Q1 : Qu'est-ce que Kubernetes ?
**Réponse type :**
> "Kubernetes est un orchestrateur de conteneurs qui automatise le déploiement, la mise à l'échelle, et la gestion des applications Docker. Il gère plusieurs machines (nodes), crée et surveille les conteneurs (pods), et assure la haute disponibilité. Dans notre TP6, on l'utilise pour déployer user-service, product-service, et order-service."

### Q2 : Quelle est la différence entre Docker et Kubernetes ?
**Réponse type :**
> "Docker permet de créer et exécuter des conteneurs. Kubernetes orchestre ces conteneurs : il gère plusieurs machines, assure que les conteneurs tournent toujours (auto-healing), permet de scaler facilement (replicas), et gère le réseau entre services. Docker = créer des conteneurs, Kubernetes = gérer plein de conteneurs en production."

### Q3 : C'est quoi un Pod, un Deployment, et un Service ?
**Réponse type :**
> "Un Pod est la plus petite unité K8s (1 ou plusieurs conteneurs). Un Deployment gère plusieurs réplicas d'un Pod avec auto-healing et scaling. Un Service expose les Pods avec un DNS stable pour que les autres services puissent les appeler. Par exemple, user-deployment crée 3 pods, et user-service permet d'y accéder via http://user-service:8001."

### Q4 : Comment scaler une application avec Kubernetes ?
**Réponse type :**
> "Deux méthodes : 1) Scaling manuel avec 'kubectl scale deployment user-service --replicas=5', 2) Auto-scaling avec HPA (Horizontal Pod Autoscaler) qui ajoute/supprime des pods selon le CPU ou la RAM. Par exemple, si CPU > 80%, K8s crée automatiquement plus de pods. Dans le TP6 ex2, on teste le scaling sous charge."

### Q5 : Qu'est-ce qu'un Rolling Update ?
**Réponse type :**
> "C'est un déploiement sans downtime. Kubernetes crée progressivement de nouveaux pods avec la nouvelle version, attend qu'ils soient prêts, puis supprime les anciens pods. Pendant le déploiement, l'app reste accessible. Si problème, on peut rollback avec 'kubectl rollout undo'."

---

## 💡 CONCEPTS CLÉS À RETENIR

1. **Kubernetes** = orchestrateur de conteneurs
2. **Pod** = plus petite unité (conteneurs)
3. **Deployment** = gestion de replicas + auto-healing
4. **Service** = DNS stable pour accéder aux Pods
5. **Scaling** = augmenter/diminuer les replicas
6. **HPA** = auto-scaling basé sur métriques
7. **Rolling Update** = déploiement sans downtime

---

## ✅ AUTO-TEST

1. Quelle est la différence entre Docker et Kubernetes ?
2. C'est quoi un Pod ? Un Deployment ? Un Service ?
3. Comment scaler de 2 à 10 replicas ?
4. Qu'est-ce que le HPA et comment ça fonctionne ?
5. Comment déployer une nouvelle version sans downtime ?

Si tu peux répondre → **✅ Fiche maîtrisée !**
