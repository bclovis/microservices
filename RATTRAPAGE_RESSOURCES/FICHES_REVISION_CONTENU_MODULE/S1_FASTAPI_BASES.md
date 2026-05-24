# S1 — FastAPI : Bases complètes

> Cours de Lucas Pauzies — Séance du 05 novembre  
> Source : `Cours7-FastAPI (1).pdf`

---

## 1. Installation et démarrage

### Installation
```bash
pip install "fastapi[all]"
# "fastapi[all]" installe aussi uvicorn, pydantic, etc.
# PAS juste "pip install fastapi" — le [all] est important !
```

### Hello World minimal
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### Lancer le serveur
```bash
uvicorn main:app --reload
# main = nom du fichier Python (main.py)
# app = nom de l'instance FastAPI
# --reload = redémarre automatiquement quand le code change (DEV uniquement)
```

Le serveur tourne sur : `http://127.0.0.1:8000`

### Documentation automatique (TRÈS IMPORTANT)
FastAPI génère automatiquement une doc interactive :
- **Swagger UI** : `http://127.0.0.1:8000/docs`
- **ReDoc** : `http://127.0.0.1:8000/redoc`

---

## 2. Path Parameters (paramètres de chemin)

Les paramètres dans l'URL entre `{}` sont des path parameters.

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# Exemple d'appel : GET /items/42
# FastAPI convertit automatiquement "42" (string) en int
```

### Avec validation de type
FastAPI valide le type automatiquement. Si on envoie `/items/foo` avec `item_id: int`, FastAPI retourne une erreur 422 automatiquement.

### Ordre des routes (PIÈGE CLASSIQUE)
```python
@app.get("/users/me")      # ← doit être AVANT /users/{user_id}
async def read_user_me():
    return {"user_id": "the current user"}

@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}
```
⚠️ Si `/users/{user_id}` est avant `/users/me`, alors "me" sera interprété comme un `user_id`.

---

## 3. Query Parameters (paramètres de requête)

Les paramètres **non présents dans le path** sont automatiquement des query params.

```python
from fastapi import FastAPI

app = FastAPI()

fake_items_db = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"}
]

@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]

# Appel : GET /items/?skip=1&limit=2
# Retourne [{"item_name": "Bar"}, {"item_name": "Baz"}]
```

### Query params optionnels
```python
from typing import Optional

@app.get("/items/{item_id}")
async def read_item(item_id: str, q: Optional[str] = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

---

## 4. Body Parameters (paramètres dans le corps)

Pour les requêtes POST/PUT, les données sont envoyées dans le corps (body) de la requête.

```python
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item

# Corps JSON envoyé :
# {
#   "name": "Laptop",
#   "price": 999.99
# }
```

FastAPI utilise **Pydantic** pour :
- Valider les données automatiquement
- Convertir les types
- Générer la documentation

### Multiple body params
```python
class Item(BaseModel):
    name: str
    price: float

class User(BaseModel):
    username: str

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, user: User):
    return {"item_id": item_id, "item": item, "user": user}

# Corps JSON :
# {
#   "item": {"name": "Laptop", "price": 999.99},
#   "user": {"username": "john"}
# }
```

---

## 5. Field() — Validation avancée avec Pydantic

`Field()` permet d'ajouter des contraintes de validation sur les champs.

```python
from pydantic import BaseModel, Field
from typing import Optional

class Item(BaseModel):
    name: str
    description: Optional[str] = Field(None, max_length=300)
    price: float = Field(..., gt=0, description="Prix en euros, doit être > 0")
    tax: Optional[float] = Field(None, ge=0)

# gt = greater than (strictement supérieur)
# ge = greater or equal (supérieur ou égal)
# lt = less than (strictement inférieur)
# le = less or equal (inférieur ou égal)
# max_length = longueur maximale (pour les strings)
# min_length = longueur minimale (pour les strings)
```

---

## 6. Nested Body (modèles imbriqués)

```python
from pydantic import BaseModel
from typing import Set, List

class Image(BaseModel):
    url: str
    name: str

class Item(BaseModel):
    name: str
    tags: Set[str] = set()    # ensemble de tags (pas de doublons)
    images: List[Image] = []  # liste d'objets Image imbriqués

@app.post("/items/")
async def create_item(item: Item):
    return item
```

---

## 7. Headers

Les headers sont récupérés avec `Header(...)`. FastAPI convertit automatiquement les underscores en tirets.

```python
from typing import List, Optional
from fastapi import FastAPI, Header

app = FastAPI()

@app.get("/items/")
async def read_items(x_token: Optional[List[str]] = Header(None)):
    return {"X-Token values": x_token}

# ⚠️ x_token (underscore) dans le code correspond à X-Token (tiret) dans le header
# C'est automatique dans FastAPI (case sensitive !)
```

---

## 8. Response Model — Filtrer la réponse

`response_model` permet de définir quel modèle Pydantic sera utilisé pour **sérialiser et filtrer** la réponse. Les champs supplémentaires sont exclus automatiquement.

```python
from pydantic import BaseModel
from typing import Optional

class UserIn(BaseModel):
    username: str
    password: str        # ← contient le mot de passe
    email: str

class UserOut(BaseModel):
    username: str
    email: str           # ← PAS de password

@app.post("/users/", response_model=UserOut)  # ← filtre avec UserOut
async def create_user(user: UserIn):
    return user          # FastAPI retire automatiquement le password !
```

**Pourquoi c'est crucial ?** → Ne jamais retourner le mot de passe dans la réponse.

---

## 9. Status Codes HTTP

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/items/", status_code=201)   # 201 = Created
async def create_item(name: str):
    return {"name": name}

# Codes courants :
# 200 = OK (par défaut)
# 201 = Created (pour les POST qui créent une ressource)
# 204 = No Content (pour les DELETE)
# 400 = Bad Request
# 401 = Unauthorized (non authentifié)
# 403 = Forbidden (authentifié mais pas autorisé)
# 404 = Not Found
# 422 = Unprocessable Entity (erreur de validation Pydantic)
# 429 = Too Many Requests (rate limiting)
# 500 = Internal Server Error
```

---

## 10. HTTP Exceptions

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}
```

`detail` peut être une string, un dict, une liste... FastAPI le sérialise en JSON automatiquement.

---

## 11. Middlewares

Un middleware s'exécute **avant et après chaque requête**. Il peut :
- Inspecter la requête (auth, logging...)
- Modifier la réponse
- Bloquer la requête (retourner une erreur)

```python
import time
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)   # ← exécute la route
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

**Schéma d'exécution :**
```
Requête → middleware 1 (avant) → middleware 2 (avant) → route → middleware 2 (après) → middleware 1 (après) → Réponse
```

---

## 12. CORS — Cross-Origin Resource Sharing

**Problème :** Si un frontend sur `localhost:4200` (Angular) appelle un backend sur `localhost:8000` (FastAPI), le navigateur bloque la requête par politique CORS.

**Solution :** Configurer le middleware CORS sur le backend.

**Mécanisme :**
1. Le navigateur envoie une requête OPTIONS (preflight)
2. Le backend répond avec les origines autorisées
3. Le navigateur envoie la vraie requête

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:4200",    # Angular en dev
    "http://localhost:3000",    # React en dev
    "https://monsite.com",      # Production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Origines autorisées
    allow_credentials=True,      # Cookies autorisés
    allow_methods=["*"],         # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],         # Tous les headers autorisés
)
```

Pour **tout autoriser** (dev seulement, DANGEREUX en prod) :
```python
allow_origins=["*"]
```

---

## 13. Architecture recommandée FastAPI

### Structure standard d'un projet FastAPI

```
project/
├── app/
│   ├── __init__.py          # ← rend le dossier un package Python
│   ├── main.py              # ← point d'entrée, instance FastAPI
│   ├── dependencies.py      # ← dépendances partagées (get_db, get_current_user)
│   ├── routers/             # ← un fichier par domaine fonctionnel
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── items.py
│   ├── models/              # ← schémas Pydantic
│   └── database/            # ← connexion BDD
├── requirements.txt
└── README.md
```

### Structure avancée (vue en cours)
```
app/
├── api/           # routes
├── authorization/ # logique d'auth
├── datasource/    # accès aux données
├── domain/        # logique métier
├── setup/         # configuration
├── static/        # fichiers statiques
├── tests/         # tests
├── main.py
└── requirements.txt
documentation/
    developer_guide.md
pipeline/
```

---

## 14. Depends — Injection de dépendances

`Depends` est le mécanisme central de FastAPI pour **réutiliser du code** (auth, DB session...).

```python
from fastapi import Depends, FastAPI

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db    # ← yield = le code après s'exécute après la requête (cleanup)
    finally:
        db.close()

@app.get("/items/")
async def read_items(db = Depends(get_db)):
    # db est injecté automatiquement par FastAPI
    return db.query(Item).all()
```

---

## 15. Async vs Sync dans FastAPI

```python
# Async — pour les opérations I/O (BDD, HTTP calls, fichiers)
@app.get("/items/")
async def read_items():
    await some_async_db_call()
    return items

# Sync — pour les calculs CPU
@app.get("/compute/")
def compute():
    result = heavy_computation()
    return result
```

FastAPI gère les deux, mais `async` est recommandé pour les microservices car il permet de gérer beaucoup de requêtes simultanées sans bloquer.

---

## 16. Résumé des patterns clés

| Pattern | Code | Quand l'utiliser |
|---------|------|-----------------|
| Path param | `item_id: int` dans le path | ID de ressource dans l'URL |
| Query param | `skip: int = 0` sans path | Filtres, pagination |
| Body | `item: Item` avec BaseModel | Créer/modifier une ressource |
| Header | `x_token = Header(None)` | Auth, tokens |
| Response model | `response_model=UserOut` | Filtrer les champs retournés |
| Status code | `status_code=201` | Indiquer le résultat HTTP |
| Exception | `raise HTTPException(404)` | Erreurs métier |
| Middleware | `@app.middleware("http")` | Auth globale, logging, rate limit |
| CORS | `CORSMiddleware` | Frontend sur domaine différent |
| Depends | `Depends(get_db)` | Injection de dépendances |

---

## 17. Questions d'oral probables

**Q: Pourquoi utiliser FastAPI plutôt que Flask ?**  
R: FastAPI est asynchrone, valide automatiquement les types avec Pydantic, génère la documentation Swagger automatiquement, et est plus performant (comparable à NodeJS/Go).

**Q: Comment FastAPI génère-t-il la documentation automatiquement ?**  
R: Grâce aux type hints Python et aux schémas Pydantic. FastAPI inspecte les signatures de fonctions pour construire le schéma OpenAPI, qui alimente Swagger UI.

**Q: Qu'est-ce qu'un middleware dans FastAPI ?**  
R: Une fonction qui s'exécute pour chaque requête, avant et après le traitement par la route. Sert à l'auth, logging, rate limiting, CORS...

**Q: Quelle est la différence entre `response_model` et le type de retour ?**  
R: `response_model` filtre et sérialise la réponse selon un schéma Pydantic, permettant d'exclure des champs sensibles (comme un mot de passe) même si l'objet interne les contient.
