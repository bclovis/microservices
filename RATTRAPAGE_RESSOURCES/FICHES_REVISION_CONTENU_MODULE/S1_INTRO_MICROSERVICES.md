# S1 — Introduction aux Microservices

> Cours de Lalanne Raphaël — Séance du 05 novembre

---

## 1. Le problème du Monolithe

### Définition
Un monolithe = une seule application qui contient **tout** :  
interface utilisateur + logique métier + accès aux données.

### Problèmes identifiés dans le cours :

| Problème | Description |
|----------|-------------|
| **Stabilité** | Une erreur dans un module fait tomber **tout le système** |
| **Évolution** | Les technologies sont figées pour tout le projet |
| **Vitesse de développement** | Les équipes se bloquent mutuellement |
| **Déploiement** | Tout redéployer pour changer une petite chose |

---

## 2. La Solution : Microservices

### Définition officielle — Martin Fowler

> *"Le style architectural des microservices est une approche permettant de développer une application unique sous la forme d'une suite logicielle intégrant plusieurs services. Ces services sont construits autour des capacités de l'entreprise et peuvent être déployés de façon indépendante."*

### Caractéristiques clés :
- **Chaque service** = process indépendant
- Communication via API (HTTP/REST ou messages asynchrones)
- Chaque service peut avoir **sa propre base de données**
- Déployables et scalables **indépendamment**

---

## 3. Avantages

| Avantage | Explication |
|----------|-------------|
| **Stabilité** | La panne d'un service ne tue pas les autres |
| **Evolution** | Chaque service choisit son stack tech |
| **Scalabilité** | On peut scaler uniquement le service sous charge |
| **Développement** | Équipes indépendantes sur chaque service |
| **Déploiement continu** | Deploy d'un seul service sans toucher aux autres |

---

## 4. Inconvénients (CRITIQUES à connaître pour l'oral)

### 4.1 BDD cloisonnées — Problème de cohérence
Chaque service a sa propre BDD → **pas de foreign key cross-services**  
Mise à jour de données communes = complexe → nécessite des patterns (Saga, Outbox)

### 4.2 Débogage difficile
- Une requête traverse plusieurs services
- Besoin de tracing distribué (ex: Jaeger, Zipkin)
- Logs dispersés dans plusieurs pods/containers

### 4.3 Versioning complexe
- Si le contrat API change, tous les services qui consomment doivent s'adapter
- Besoin de versionner les APIs (`/v1/`, `/v2/`)

### 4.4 Latence réseau
- Les appels inter-services passent par le réseau
- Solution : **préférer les appels asynchrones** (Kafka) plutôt que synchrones (HTTP)
- Utiliser du **cache** pour réduire les allers-retours

### 4.5 Sécurité inter-services
- Besoin d'auth/chiffrage entre services
- JWT tokens ou mTLS pour sécuriser les communications

---

## 5. Architecture du Projet PokeDrafter (exemple concret)

```
FRONT (Angular)
      ↓
  GATEWAY (nginx:80)
      ↓
  ┌───────────────────────────────────────────┐
  │  auth_service:8001  ←──── JWT tokens      │
  │  team_service:8002  ←──── auth via JWT    │
  │  battle_service:8003 ──→  Kafka events    │
  │  pokedex_service:8004 ←── PokéAPI         │
  │  chat_service:8005  ←──── Kafka events    │
  └───────────────────────────────────────────┘
         ↕ kafka:29092 ↕
  ┌────────────────────┐
  │  PostgreSQL (DB)   │
  │  Kafka (Broker)    │
  └────────────────────┘
```

### Topics Kafka du projet :
- `battle-events` : événements de combat
- `chat-messages` : messages du chat

---

## 6. Questions d'oral probables

**Q: Pourquoi choisir des microservices plutôt qu'un monolithe ?**  
R: Indépendance de déploiement, scalabilité fine, isolation des pannes, liberté technologique par équipe.

**Q: Quels sont les inconvénients des microservices ?**  
R: Gestion distribuée des données (pas d'ACID global), débogage complexe, latence réseau, versioning des APIs.

**Q: Comment Martin Fowler définit-il les microservices ?**  
R: *"Suite logicielle de services construits autour des capacités de l'entreprise, déployables indépendamment"*

**Q: Comment sécuriser les communications entre microservices ?**  
R: JWT tokens (auth_service génère, les autres vérifient), mTLS, API Gateway avec API Key.
