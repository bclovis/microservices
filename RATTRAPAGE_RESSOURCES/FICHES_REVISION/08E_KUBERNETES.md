# ☸️ FICHE 08E : Kubernetes — Déploiement production

> Basée sur le rapport (page 5) + tes vrais fichiers `infra/k8s/`.
> **Ce que tu dois dire = ce qui est dans le rapport, pas autre chose.**

---

## 🎯 PRÉSENTATION (à dire en 30 secondes)

> *"Docker Compose, c'est pour le développement local. Kubernetes, c'est pour la production — il gère automatiquement la scalabilité, le redémarrage si un service plante, et l'exposition sur un cluster. On a décrit l'infrastructure avec 6 fichiers YAML : namespace, PostgreSQL, Redis, Kafka, les 5 microservices, et la gateway en NodePort."*

---

## 1. Docker Compose vs Kubernetes

| | Docker Compose | Kubernetes |
|---|---|---|
| **Usage** | Développement local | Production / Cloud |
| **Scalabilité** | Manuel (`--scale`) | Automatique (`replicas: 3`) |
| **Redémarrage auto** | Non | Oui (`restartPolicy`) |
| **Load balancing** | Non | Oui (intégré) |
| **Exposition réseau** | `ports: "80:80"` | Service NodePort / LoadBalancer |
| **Persistance** | Volumes Docker | PersistentVolumeClaim (PVC) |
| **1 commande** | `docker compose up` | `kubectl apply -f k8s/` |

---

## 2. Les 6 fichiers YAML — Vue d'ensemble

**Dossier :** `infra/k8s/`

```
k8s/
├── namespace.yaml   → Isole le projet des autres déploiements
├── postgres.yaml    → Déploiement PostgreSQL + PVC 1Gi
├── redis.yaml       → Déploiement Redis + PVC 512Mi
├── kafka.yaml       → Zookeeper + Kafka Broker
├── services.yaml    → Les 5 microservices (5 Deployments + 5 Services)
└── gateway.yaml     → Nginx NodePort :30080
```

---

## 3. `namespace.yaml` — Isolation

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pokedrafter
```

**Pourquoi un namespace ?**
> "Un namespace isole le projet PokeDrafter des autres déploiements sur le cluster. Si d'autres projets tournent sur le même cluster, ils ne se mélangent pas. C'est comme un dossier de travail dédié."

**Usage pratique :**
```bash
kubectl apply -f k8s/ -n pokedrafter
kubectl get pods -n pokedrafter
```

---

## 4. `postgres.yaml` — Persistance des données

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi           # ← 1 gigaoctet pour PostgreSQL
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          env:
            - name: POSTGRES_USER
              value: "postgres"
          volumeMounts:
            - mountPath: /var/lib/postgresql/data
              name: postgres-storage
      volumes:
        - name: postgres-storage
          persistentVolumeClaim:
            claimName: postgres-pvc   # ← Utilise le PVC 1Gi
```

**Ce qu'il faut savoir :**
- **PVC (PersistentVolumeClaim)** = demande de stockage persistant au cluster
- `storage: 1Gi` = 1 gigaoctet alloué pour les données PostgreSQL
- Sans PVC, les données disparaissent si le pod redémarre

---

## 5. `redis.yaml` — Cache plus léger

```yaml
kind: PersistentVolumeClaim
spec:
  resources:
    requests:
      storage: 512Mi   # ← 512 Mo (moitié de PostgreSQL, cache plus léger)
```

**Pourquoi 512Mi et non 1Gi ?**
> "Redis stocke uniquement un cache de données Pokémon (noms, types, stats). C'est beaucoup plus léger que les données applicatives de PostgreSQL — utilisateurs, batailles, équipes."

---

## 6. `services.yaml` — Les 5 microservices

**Pattern répété 5 fois (auth, team, battle, pokedex, chat) :**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: battle-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: battle-service
  template:
    metadata:
      labels:
        app: battle-service
    spec:
      containers:
        - name: battle-service
          image: pokedrafter/battle-service:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              value: "postgresql+asyncpg://postgres:postgres@postgres:5432/battle_db"
            - name: KAFKA_BOOTSTRAP_SERVERS
              value: "kafka:29092"
---
apiVersion: v1
kind: Service
metadata:
  name: battle-service
spec:
  selector:
    app: battle-service     # ← Trouve les pods avec ce label
  ports:
    - port: 8003            # Port exposé dans le cluster
      targetPort: 8000      # Port dans le conteneur
  type: ClusterIP           # Accessible seulement en interne
```

**ClusterIP = réseau interne uniquement :**
> "Les services backend ne sont pas accessibles depuis l'extérieur du cluster. Seul Nginx (gateway) est exposé en NodePort."

---

## 7. `gateway.yaml` — NodePort :30080

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gateway
spec:
  selector:
    app: gateway
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080      # ← Port accessible depuis DEHORS le cluster
  type: NodePort
```

**Ce qu'il faut dire :**
> "Le service gateway est en NodePort 30080. C'est le seul point d'entrée externe. Pour accéder à l'application sur le cluster : `http://<IP_DU_NODE>:30080`."

**Différence ClusterIP vs NodePort :**
| Type | Accessible depuis | Usage |
|------|------------------|-------|
| `ClusterIP` | Seulement dans le cluster | Services internes (battle, auth...) |
| `NodePort` | Depuis l'extérieur sur un port fixe | Gateway Nginx uniquement |
| `LoadBalancer` | Via IP publique (cloud) | Non utilisé ici |

---

## 8. Les concepts Kubernetes à maîtriser

### Pod
- L'unité de base : 1 ou plusieurs conteneurs qui tournent ensemble
- Éphémère : si un pod plante, Kubernetes en crée un nouveau

### Deployment
- Gère les pods : "Je veux toujours 1 replica de battle-service"
- Si le pod plante → Kubernetes en recrée un automatiquement

### Service
- Point d'accès réseau stable pour un groupe de pods
- Les pods ont des IP qui changent → le Service a une IP stable

### PVC (PersistentVolumeClaim)
- Demande de stockage persistant
- Les données survivent si le pod redémarre

### Namespace
- Espace de travail isolé dans le cluster

---

## 9. Commandes utiles (à connaître pour l'oral)

```bash
# Déployer tout
kubectl apply -f infra/k8s/ -n pokedrafter

# Voir les pods
kubectl get pods -n pokedrafter

# Logs d'un service
kubectl logs -f deployment/battle-service -n pokedrafter

# Supprimer tout
kubectl delete -f infra/k8s/ -n pokedrafter
```

---

## 🔥 QUESTIONS PROBABLES SUR Kubernetes

| Question | Réponse courte |
|----------|---------------|
| "Pourquoi Kubernetes et pas Docker Compose ?" | Production : scalabilité auto, redémarrage auto, load balancing |
| "C'est quoi un Deployment ?" | Décrit combien de réplicas d'un service on veut, Kubernetes maintient ça |
| "C'est quoi un Service Kubernetes ?" | Point d'accès réseau stable pour atteindre les pods |
| "C'est quoi un PVC ?" | Demande de stockage persistant — les données survivent au redémarrage du pod |
| "Pourquoi 1Gi pour postgres et 512Mi pour redis ?" | Postgres stocke toutes les données appli, Redis c'est juste un cache Pokémon |
| "Comment accède-t-on à l'app ?" | Via NodePort :30080 sur l'IP du nœud |
| "Pourquoi un namespace ?" | Isoler le projet des autres déploiements sur le même cluster |
| "C'est quoi ClusterIP ?" | Services accessibles SEULEMENT en interne, pas depuis l'extérieur |
| "Que se passe-t-il si un pod plante ?" | Kubernetes en recrée un automatiquement (c'est le rôle du Deployment) |
