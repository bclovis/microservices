# EXPLICATIONS DÉTAILLÉES - TP5 API Gateway

## 📚 CONCEPTS CLÉS

### 1. Microservices
**C'est quoi ?**
Au lieu d'avoir une grosse application monolithique, on découpe en petits services indépendants.

**Pourquoi ?**
- Chaque service peut évoluer séparément
- Si un service tombe, les autres continuent
- Équipes différentes peuvent travailler sur des services différents

**Dans notre projet :**
- `users` → gère uniquement les utilisateurs
- `orders` → gère uniquement les commandes
- `gateway` → orchestre le tout

---

### 2. API Gateway
**C'est quoi ?**
Un point d'entrée unique qui fait office de "portier" pour tous les microservices.

**Analogie :** C'est comme la réception d'un hôtel
- Le client parle à la réception (gateway)
- La réception redirige vers le bon service (chambre, restaurant, spa...)
- La réception gère la sécurité (clé d'accès)

**Avantages :**
✅ Le client n'a qu'une seule URL à connaître
✅ Centralise la sécurité (pas besoin de dupliquer sur chaque service)
✅ Peut combiner des données de plusieurs services
✅ Cache, rate limiting, monitoring au même endroit

**Schéma :**
```
Client 
  ↓
Gateway (port 8000)
  ↓
  ├→ Users Service (port 8001)
  ├→ Orders Service (port 8002)
  └→ Données locales (items)
```

---

### 3. Middleware
**C'est quoi ?**
Une fonction qui s'exécute AVANT chaque requête.

**Analogie :** C'est comme un contrôle de sécurité à l'aéroport
- Tout le monde passe par là AVANT d'accéder à l'avion
- Si problème détecté → refusé
- Si tout OK → peut continuer

**Dans notre projet :**
1. **Middleware d'authentification** : Vérifie la clé API
2. **Middleware de rate limiting** : Limite le spam

**Ordre d'exécution :**
```
Requête client
  ↓
Middleware Rate Limiting (vérifie pas trop de requêtes)
  ↓
Middleware API Key (vérifie la clé)
  ↓
Route demandée (ex: /users)
  ↓
Réponse
```

---

### 4. Authentification par API Key
**C'est quoi ?**
Une clé secrète que le client doit fournir pour accéder à l'API.

**Comment ça marche ?**
1. Le serveur définit une clé : `secret-api-key-123`
2. Le client envoie cette clé dans les headers HTTP : `X-API-Key: secret-api-key-123`
3. Le middleware compare : clé reçue == clé attendue ?
4. Si oui → OK, si non → erreur 401 Unauthorized

**Pourquoi X-API-Key ?**
C'est une convention. Le `X-` indique un header personnalisé.

**Code simplifié :**
```python
api_key = request.headers.get("X-API-Key")
if api_key != "secret-api-key-123":
    return "401 Unauthorized"
```

---

### 5. Cache
**C'est quoi ?**
Stocker temporairement en mémoire les résultats d'une requête coûteuse.

**Analogie :** C'est comme un pense-bête
- Tu cherches un numéro de téléphone dans l'annuaire (lent)
- Tu le notes sur un post-it (cache)
- Les prochaines fois, tu regardes le post-it (rapide)
- Après 10 minutes, tu jettes le post-it (expiration)

**Bénéfices :**
⚡ Réponse ultra-rapide (pas d'appel réseau)
📉 Réduit la charge sur les microservices
💰 Économise des ressources

**Structure du cache :**
```python
cache = {
    "users": {
        "data": [...],
        "expires_at": datetime(2025, 12, 3, 15, 30)
    }
}
```

**Workflow :**
```
1. Client demande /users
2. Gateway vérifie le cache
   → Trouvé et valide ? Retourne direct
   → Pas trouvé ou expiré ? Appelle le microservice
3. Stocke le résultat en cache avec timestamp
4. Retourne au client
```

---

### 6. Rate Limiting
**C'est quoi ?**
Limiter le nombre de requêtes qu'un client peut faire dans un temps donné.

**Analogie :** C'est comme un vigile à l'entrée d'un magasin
- "Vous êtes déjà entré il y a 5 secondes, attendez 15 secondes"
- Empêche les abus et les surcharges

**Pourquoi c'est important ?**
🛡️ Protection contre les attaques DDoS
💸 Évite qu'un client consomme toutes les ressources
⚖️ Équité : tout le monde a accès

**Notre implémentation :**
- **Limite** : 1 requête toutes les 20 secondes
- **Identification** : Par adresse IP du client
- **Réponse** : HTTP 429 "Too Many Requests"

**Algorithme simplifié :**
```python
rate_limit_store = {}  # IP → timestamp dernière requête

if IP in rate_limit_store:
    temps_ecoulé = maintenant - derniere_requete
    if temps_ecoulé < 20 secondes:
        return "429 Too Many Requests"

rate_limit_store[IP] = maintenant
# Continuer...
```

---

### 7. Agrégation de données
**C'est quoi ?**
Combiner des données de plusieurs sources en une seule réponse.

**Pourquoi ?**
Le client fait 1 requête au lieu de 2+ → plus simple et plus rapide

**Exemple 1 : /poubelle**
```python
# Sans agrégation (2 requêtes client)
users = client.get("/users")
items = client.get("/items")

# Avec agrégation (1 requête client)
poubelle = client.get("/poubelle")  # Contient users + items
```

**Exemple 2 : /profile/Alice**
```python
# La gateway fait 2 appels internes
users_data = microservice_users.get("/users")
orders_data = microservice_orders.get("/orders/Alice")

# Combine et retourne
return {
    "user": {...},
    "orders": [...]
}
```

---

## 🔧 ARCHITECTURE TECHNIQUE

### Flux d'une requête complète

```
1. Client envoie : GET /users avec header X-API-Key: secret-api-key-123

2. Middleware Rate Limiting
   → Vérifie : dernière requête de cette IP > 20 sec ?
   → Si non → 429 Too Many Requests (STOP)
   → Si oui → Continue

3. Middleware API Key
   → Vérifie : X-API-Key == secret-api-key-123 ?
   → Si non → 401 Unauthorized (STOP)
   → Si oui → Continue

4. Route /users
   → Vérifie le cache
   → Si trouvé et valide → Retourne depuis cache
   → Si non → Appel HTTP à http://localhost:8001/users

5. Stocke en cache avec expiration 10 min

6. Retourne la réponse au client
```

---

## 📊 PORTS ET SERVICES

| Service | Port | Rôle |
|---------|------|------|
| Users | 8001 | Gère les utilisateurs |
| Orders | 8002 | Gère les commandes |
| Gateway | 8000 | Point d'entrée unique |

**Important :** 
- Les microservices (8001, 8002) ne sont PAS accessibles directement par le client
- Le client parle UNIQUEMENT à la gateway (8000)
- C'est la gateway qui fait les appels internes aux microservices

---

## 🎯 ENDPOINTS DE LA GATEWAY

### 1. GET /users
**Quoi :** Liste tous les utilisateurs
**Source :** Microservice users (port 8001)
**Cache :** Oui (10 min)
**Exemple :**
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
```

### 2. GET /orders/{user}
**Quoi :** Commandes d'un utilisateur spécifique
**Source :** Microservice orders (port 8002)
**Cache :** Oui (10 min, par utilisateur)
**Exemple :**
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/orders/Alice
```

### 3. GET /items
**Quoi :** Liste des items
**Source :** Stocké localement dans la gateway
**Cache :** Non (déjà en mémoire)
**Exemple :**
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/items
```

### 4. GET /poubelle
**Quoi :** Agrégation users + items
**Source :** Microservice users + stockage local
**Cache :** Non (agrégation dynamique)
**Exemple :**
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/poubelle
```

### 5. GET /profile/{user}
**Quoi :** Profil complet (user + ses commandes)
**Source :** Microservice users + microservice orders
**Cache :** Non (agrégation dynamique)
**Exemple :**
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/profile/Alice
```

---

## 🚀 ORDRE DE LANCEMENT

**IMPORTANT :** Lancer dans cet ordre !

1. **Users service** (terminal 1)
```bash
uvicorn users.main:app --port 8001
```

2. **Orders service** (terminal 2)
```bash
uvicorn orders.main:app --port 8002
```

3. **Gateway** (terminal 3)
```bash
uvicorn gateway.main:app --port 8000
```

**Pourquoi cet ordre ?**
La gateway fait des appels aux services users et orders. Si ces services ne sont pas démarrés, la gateway ne pourra pas les contacter.

---

## 🧪 TESTER LE PROJET

### Option 1 : Script Python automatisé
```bash
python test_gateway.py
```
Ce script teste toutes les fonctionnalités automatiquement.

### Option 2 : Commandes curl manuelles
Voir le fichier `CURL_COMMANDS.md`

### Option 3 : Navigateur (Swagger UI)
Ouvre http://localhost:8000/docs dans ton navigateur.
Tu auras une interface interactive pour tester l'API.

⚠️ N'oublie pas d'ajouter le header `X-API-Key` dans l'interface !

---

## ❓ QUESTIONS FRÉQUENTES

### Pourquoi httpx et pas requests ?
`httpx` supporte l'asynchrone (`async/await`), ce qui permet de faire plusieurs requêtes en parallèle sans bloquer. `requests` est synchrone.

### C'est quoi async/await ?
Permet d'exécuter du code sans bloquer pendant les opérations lentes (réseau, I/O).
```python
# Synchrone (bloquant)
response = requests.get(url)  # Attend la réponse

# Asynchrone (non-bloquant)
response = await client.get(url)  # Peut faire autre chose pendant l'attente
```

### Pourquoi pas de vraie BDD ?
L'exercice se concentre sur l'architecture de l'API Gateway, pas sur la persistance des données. Les données en dur simplifient le TP.

### Le cache est-il persistant ?
Non, il est en mémoire. Si tu redémarres la gateway, le cache est vidé.

### Peut-on avoir plusieurs clés API ?
Oui, dans une vraie application, on aurait une base de clés avec différents niveaux d'accès. Ici, on simplifie avec une seule clé.

### Le rate limiting est-il réinitialisé au redémarrage ?
Oui, car il est stocké en mémoire. Dans une vraie appli, on utiliserait Redis.

---

## 🎓 COMPÉTENCES ACQUISES

✅ Architecture microservices
✅ API Gateway pattern
✅ Middlewares FastAPI
✅ Authentification par API Key
✅ Système de cache avec expiration
✅ Rate limiting
✅ Agrégation de données
✅ Requêtes HTTP asynchrones (httpx)
✅ Gestion des erreurs HTTP (401, 429)

---

## 📖 POUR ALLER PLUS LOIN

**Améliorations possibles :**
- Utiliser Redis pour le cache et le rate limiting (persistant)
- Ajouter un système de logs centralisé
- Implémenter circuit breaker (si un service est down)
- Ajouter CORS pour les appels depuis le navigateur
- Monitoring avec Prometheus/Grafana
- Load balancing avec plusieurs instances
- OAuth2 au lieu d'API Key simple
- Dockeriser les services
- Tests unitaires et d'intégration

**Ressources :**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Microservices Patterns](https://microservices.io/patterns/index.html)
- [API Gateway Pattern](https://microservices.io/patterns/apigateway.html)
