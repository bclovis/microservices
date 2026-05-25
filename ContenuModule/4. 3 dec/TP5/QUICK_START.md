# GUIDE DE DÉMARRAGE RAPIDE

## 🚀 Installation et lancement (3 minutes)

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancer les services (3 terminaux)

**Terminal 1 :**
```bash
uvicorn users.main:app --port 8001
```

**Terminal 2 :**
```bash
uvicorn orders.main:app --port 8002
```

**Terminal 3 :**
```bash
uvicorn gateway.main:app --port 8000
```

### 3. Tester
```bash
python test_gateway.py
```

---

## ⚡ Test rapide avec curl

```bash
# Test basique (devrait marcher)
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users

# Test sans clé (devrait échouer avec 401)
curl http://localhost:8000/users
```

---

## 📋 Checklist du TP

### Exigences de base
- [x] 3 microservices FastAPI (users, orders, gateway)
- [x] Chaque service sur un port différent (8001, 8002, 8000)
- [x] Données en dur (pas de BDD)

### Endpoints de la gateway
- [x] `GET /users` → liste des utilisateurs
- [x] `GET /orders/{user}` → commandes d'un utilisateur
- [x] `GET /items` → liste des items

### Middleware et sécurité
- [x] Middleware d'authentification par API Key
- [x] Clé API : `secret-api-key-123`
- [x] Blocage des requêtes sans clé (401)

### Agrégation
- [x] `GET /poubelle` → users + items
- [x] `GET /profile/{user}` → user + ses commandes

### Cache
- [x] Système de cache implémenté
- [x] Expiration après 10 minutes
- [x] Logs pour voir CACHE HIT/MISS

### Rate Limiting
- [x] Middleware de rate limiting
- [x] 1 requête toutes les 20 secondes max
- [x] Erreur 429 si dépassé

---

## 🧪 Tests à effectuer

### Test 1 : Authentification
```bash
# Doit réussir (200)
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/items

# Doit échouer (401)
curl http://localhost:8000/items
```

### Test 2 : Endpoints de base
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/orders/Alice
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/items
```

### Test 3 : Agrégation
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/poubelle
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/profile/Bob
```

### Test 4 : Cache
```bash
# Première requête (CACHE MISS - regarde les logs gateway)
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users

# Deuxième requête (CACHE HIT - regarde les logs gateway)
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
```

### Test 5 : Rate Limiting
```bash
# Première requête (OK)
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/items

# Deuxième requête immédiate (doit retourner 429)
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/items

# Attendre 21 secondes puis réessayer (OK)
sleep 21
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/items
```

---

## 🐛 Résolution de problèmes

### Erreur : "Address already in use"
Un service est déjà lancé sur ce port.
```bash
# Trouver et tuer le processus
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
lsof -ti:8002 | xargs kill -9
```

### Erreur : "Connection refused"
Les microservices ne sont pas lancés.
→ Vérifie que users et orders tournent avant de lancer gateway.

### Erreur : "Module not found"
Les dépendances ne sont pas installées.
```bash
pip install -r requirements.txt
```

### Les logs ne s'affichent pas
Ajoute `--log-level debug` :
```bash
uvicorn gateway.main:app --port 8000 --log-level debug
```

---

## 📊 Résultats attendus

### GET /users (première fois)
```
[Console gateway] [CACHE MISS] Pas de cache pour : users
[Console gateway] [CACHE SET] Mise en cache : users (expire dans 10 min)

{"users": [
  {"id": 1, "name": "Alice", "email": "alice@example.com"},
  {"id": 2, "name": "Bob", "email": "bob@example.com"},
  {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
]}
```

### GET /users (deuxième fois, < 10 min)
```
[Console gateway] [CACHE HIT] Récupération depuis le cache : users

{"users": [...]}  (même résultat mais instantané)
```

### GET /profile/Alice
```json
{
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  },
  "orders": [
    {"id": 101, "product": "Laptop", "price": 1200},
    {"id": 102, "product": "Mouse", "price": 25}
  ]
}
```

### Rate limiting dépassé (429)
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Please wait 15.3 seconds."
}
```

### API Key invalide (401)
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

---

## 📚 Fichiers de documentation

| Fichier | Description |
|---------|-------------|
| `README.md` | Instructions de base |
| `EXPLICATIONS.md` | Concepts détaillés (middleware, cache, etc.) |
| `ARCHITECTURE.md` | Schémas et flux de données |
| `CURL_COMMANDS.md` | Commandes de test |
| `QUICK_START.md` | Ce fichier (démarrage rapide) |

---

## 🎓 Points clés à retenir

1. **API Gateway** = Point d'entrée unique qui orchestre les microservices
2. **Middleware** = Code qui s'exécute avant chaque requête
3. **Cache** = Stockage temporaire pour accélérer les réponses
4. **Rate Limiting** = Protection contre le spam
5. **Agrégation** = Combiner plusieurs sources de données en une réponse

---

## ✅ Validation du TP

Ton TP est complet si tu peux :
- [x] Lancer les 3 services sans erreur
- [x] Faire une requête avec API Key qui fonctionne
- [x] Faire une requête sans API Key qui échoue (401)
- [x] Voir les logs de cache (MISS puis HIT)
- [x] Déclencher le rate limiting (429)
- [x] Recevoir des données agrégées depuis /poubelle et /profile

**Temps estimé :** 15-20 minutes de tests complets
