# EXERCICES — FastAPI Bases (auto-évaluation oral)

> Fais chaque exercice sans regarder la fiche. Puis vérifie.

---

## Exercice 1 — Hello World (2 min)

**Écris de mémoire :**
1. La commande d'installation de FastAPI
2. Un fichier `main.py` avec une route `GET /` qui retourne `{"message": "Hello World"}`
3. La commande pour lancer le serveur avec rechargement auto

<details>
<summary>👁️ Correction</summary>

```bash
pip install "fastapi[all]"
```

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

```bash
uvicorn main:app --reload
```

**Pièges :** les crochets `[all]`, et `main:app` (nom du fichier : nom de l'instance).
</details>

---

## Exercice 2 — Path + Query params (3 min)

**Écris un endpoint qui :**
- `GET /products/{product_id}` → retourne `product_id` (int) + un query param optionnel `category` (str)
- Si `category` est fourni → retourner `{"product_id": ..., "category": ...}`
- Sinon → retourner juste `{"product_id": ...}`

<details>
<summary>👁️ Correction</summary>

```python
from typing import Optional
from fastapi import FastAPI

app = FastAPI()

@app.get("/products/{product_id}")
async def get_product(product_id: int, category: Optional[str] = None):
    if category:
        return {"product_id": product_id, "category": category}
    return {"product_id": product_id}
```

**Appels :**
- `GET /products/5` → `{"product_id": 5}`
- `GET /products/5?category=electronics` → `{"product_id": 5, "category": "electronics"}`
</details>

---

## Exercice 3 — Body + Pydantic (3 min)

**Crée un endpoint `POST /users/` qui :**
- Reçoit un body JSON avec : `username` (str, obligatoire), `email` (str, obligatoire), `age` (int, optionnel)
- Retourne les données reçues + `{"created": True}`

<details>
<summary>👁️ Correction</summary>

```python
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: str
    age: Optional[int] = None

@app.post("/users/")
async def create_user(user: UserCreate):
    return {**user.model_dump(), "created": True}
```

**Body JSON envoyé :**
```json
{"username": "alice", "email": "alice@example.com"}
```
</details>

---

## Exercice 4 — Exception HTTP (2 min)

**Écris un endpoint `GET /users/{user_id}` qui :**
- Cherche dans `users_db = {1: "Alice", 2: "Bob"}`
- Retourne `{"user_id": ..., "name": ...}` si trouvé
- Lève une erreur **404** avec le message `"User not found"` sinon

<details>
<summary>👁️ Correction</summary>

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()
users_db = {1: "Alice", 2: "Bob"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "name": users_db[user_id]}
```
</details>

---

## Exercice 5 — Middleware auth (3 min)

**Écris un middleware qui :**
- Vérifie la présence du header `X-API-Key`
- Si la clé est différente de `"mon-secret"` → retourner une réponse **401** avec `{"error": "Unauthorized"}`
- Sinon → laisser passer la requête normalement

<details>
<summary>👁️ Correction</summary>

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key != "mon-secret":
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return await call_next(request)
```

**Points clés :**
- `request.headers.get("X-API-Key")` pour lire un header
- `JSONResponse(status_code=401, content=...)` pour bloquer
- `await call_next(request)` pour laisser passer
</details>

---

## Exercice 6 — Questions théoriques (oral direct)

Réponds à voix haute sans regarder :

1. **Quelle est la différence entre un path param et un query param ?**
2. **Pourquoi utiliser `response_model` ?**
3. **Qu'est-ce que `Depends` et à quoi ça sert ?**
4. **Pourquoi `async def` plutôt que `def` dans FastAPI ?**
5. **C'est quoi CORS et pourquoi on en a besoin ?**

<details>
<summary>👁️ Réponses</summary>

1. Path param = dans l'URL (`/users/{id}`), obligatoire. Query param = après `?` (`/users?skip=0`), optionnel avec valeur par défaut.
2. Pour filtrer les champs retournés (ex: ne pas retourner le mot de passe), même si l'objet en mémoire le contient.
3. Injection de dépendances — FastAPI appelle automatiquement la fonction et injecte le résultat. Sert pour la session BDD, l'auth, etc.
4. `async def` + `await` permet de gérer beaucoup de requêtes simultanées sans bloquer (I/O non-bloquant). Indispensable pour les microservices.
5. CORS = politique du navigateur qui bloque les requêtes vers un domaine différent. On configure `CORSMiddleware` pour autoriser le frontend (ex: localhost:4200) à appeler le backend (localhost:8000).
</details>

---

## Score

| Exercice | Points |
|----------|--------|
| Ex 1 — Hello World | /3 |
| Ex 2 — Path + Query | /3 |
| Ex 3 — Body Pydantic | /3 |
| Ex 4 — Exception | /3 |
| Ex 5 — Middleware | /3 |
| Ex 6 — Théorie (5 questions) | /5 |
| **Total** | **/20** |

- **16-20** : Tu gères, révise juste les pièges
- **12-15** : Bien mais revoir middlewares et Pydantic
- **< 12** : Relis la fiche S1_FASTAPI_BASES.md en entier
