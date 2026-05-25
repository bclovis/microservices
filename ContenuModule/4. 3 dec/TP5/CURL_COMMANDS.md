# Commandes CURL pour tester l'API Gateway

## 1. Test sans authentification (devrait échouer)
```bash
curl http://localhost:8000/users
# Résultat attendu : 401 Unauthorized
```

## 2. Test avec authentification (devrait réussir)
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
```

## 3. Liste des items
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/items
```

## 4. Commandes d'un utilisateur
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/orders/Alice
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/orders/Bob
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/orders/Charlie
```

## 5. Agrégation : /poubelle (users + items)
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/poubelle
```

## 6. Agrégation : /profile/{user}
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/profile/Alice
```

## 7. Test du cache
Exécuter 2 fois la même commande rapidement, regarder les logs de la gateway :
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
```
La deuxième devrait afficher [CACHE HIT] dans les logs.

## 8. Test du rate limiting
Exécuter cette commande 2 fois rapidement (< 20 secondes) :
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/items
```
La deuxième requête devrait retourner une erreur 429 "Too Many Requests".
