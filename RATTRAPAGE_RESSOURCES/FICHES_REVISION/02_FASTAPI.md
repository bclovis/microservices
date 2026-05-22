# 📘 FICHE 2 : FASTAPI

> **Source** : Cours FastAPI.pdf + FastAPI manipulations avancées.pdf (05/11 & 12/11/2025)

---

## 🎯 QU'EST-CE QUE FASTAPI ?

**FastAPI** est un framework Python **moderne et rapide** pour créer des **API REST**.

### Caractéristiques principales
- ⚡ **Très rapide** (performances comparables à Node.js et Go)
- 🐍 **Python moderne** (type hints Python 3.7+)
- 📝 **Documentation automatique** (Swagger UI)
- ✅ **Validation automatique** des données (Pydantic)
- 🔒 **Support natif de l'asynchrone** (async/await)

### Installation
```bash
pip install fastapi uvicorn
```

---

## 🚀 CRÉATION D'UNE API SIMPLE

### Hello World

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

**Lancer le serveur :**
```bash
uvicorn main:app --reload --port 8000
```

**Tester :**
```bash
curl http://localhost:8000/
```

---

## 📡 MÉTHODES HTTP (VERBES)

### GET - Récupérer des données
```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": "John"}
```

**Usage :** Lire des données (ne modifie rien)

### POST - Créer une ressource
```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str

@app.post("/users")
def create_user(user: User):
    # Sauvegarder en BDD
    return {"message": "User created", "user": user}
```

**Usage :** Créer une nouvelle ressource

### PUT - Remplacer une ressource
```python
@app.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    # Remplacer complètement l'utilisateur
    return {"message": "User updated", "user_id": user_id}
```

**Usage :** Remplacer complètement une ressource

### PATCH - Modifier partiellement une ressource
```python
@app.patch("/users/{user_id}")
def partial_update(user_id: int, name: str = None, email: str = None):
    # Modifier seulement les champs fournis
    return {"message": "User partially updated"}
```

**Usage :** Modifier seulement certains champs

### DELETE - Supprimer une ressource
```python
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    # Supprimer de la BDD
    return {"message": "User deleted"}
```

**Usage :** Supprimer une ressource

---

## 🔍 PATH PARAMETERS vs QUERY PARAMETERS

### Path Parameters (dans l'URL)
```python
@app.get("/users/{user_id}/orders/{order_id}")
def get_order(user_id: int, order_id: int):
    return {"user_id": user_id, "order_id": order_id}
```

**URL :** `http://localhost:8000/users/42/orders/123`

**Usage :** Identifiants de ressources (obligatoires)

### Query Parameters (après le ?)
```python
@app.get("/users")
def list_users(skip: int = 0, limit: int = 10, active: bool = True):
    return {"skip": skip, "limit": limit, "active": active}
```

**URL :** `http://localhost:8000/users?skip=0&limit=10&active=true`

**Usage :** Filtres, pagination, options (optionnels)

---

## 📦 PYDANTIC MODELS (VALIDATION)

Pydantic valide **automatiquement** les données entrantes.

### Définition d'un modèle
```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class User(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr  # Validation email automatique
    age: int = Field(..., ge=0, le=150)  # 0 <= age <= 150
    is_active: bool = True
```

### Utilisation
```python
@app.post("/users")
def create_user(user: User):
    # FastAPI valide automatiquement les données
    # Si invalide → erreur 422 automatique
    return user
```

**Exemple de requête valide :**
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "age": 25
}
```

**Exemple de requête invalide :**
```json
{
  "name": "",  // ❌ min_length=1
  "email": "not-an-email",  // ❌ pas un email valide
  "age": -5  // ❌ age doit être >= 0
}
```
→ FastAPI retourne automatiquement une erreur 422 avec détails

---

## 🗄️ CONNEXION BASE DE DONNÉES

### Avec SQLAlchemy (exemple TP Wines)

```python
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuration BDD
DATABASE_URL = "sqlite:///./wines.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modèle SQLAlchemy
class Wine(Base):
    __tablename__ = "wines"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    alcohol = Column(Float)
    quality = Column(Integer)

# Créer les tables
Base.metadata.create_all(bind=engine)

# Dependency injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Route avec BDD
@app.get("/wines")
def list_wines(db: Session = Depends(get_db)):
    wines = db.query(Wine).all()
    return wines
```

---

## 🔒 SÉCURITÉ ET AUTHENTIFICATION

### API Key (simple)

```python
from fastapi import Header, HTTPException

API_KEY = "secret-api-key-123"

@app.get("/secure")
def secure_endpoint(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return {"message": "Access granted"}
```

**Usage :**
```bash
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/secure
```

### JWT (JSON Web Tokens) - Avancé

```python
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected")
def protected_route(user = Depends(verify_token)):
    return {"message": f"Hello {user['username']}"}
```

---

## ⚡ ASYNCHRONE (async/await)

FastAPI supporte nativement l'asynchrone pour de meilleures performances.

### Sans async (bloquant)
```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    # Bloque le thread pendant l'attente
    user = db.query(User).filter(User.id == user_id).first()
    return user
```

### Avec async (non-bloquant)
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # Ne bloque pas le thread
    user = await db.execute(select(User).where(User.id == user_id))
    return user
```

**Avantage :** Permet de traiter plusieurs requêtes en parallèle sans bloquer le serveur.

---

## 📚 DOCUMENTATION AUTOMATIQUE

FastAPI génère **automatiquement** une documentation interactive.

### Swagger UI
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

**Astuce :** Tu peux tester tes API directement dans `/docs` !

---

## 🛠️ MIDDLEWARE ET CORS

### CORS (Cross-Origin Resource Sharing)
Nécessaire pour que le frontend puisse appeler l'API.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Frontend Angular
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE...
    allow_headers=["*"],
)
```

### Middleware custom
```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## 🎤 QUESTIONS PROBABLES À L'ORAL

### Q1 : Qu'est-ce que FastAPI ?
**Réponse type :**
> "FastAPI est un framework Python moderne pour créer des API REST. Il est très rapide, génère automatiquement la documentation (Swagger), et valide automatiquement les données grâce à Pydantic. On l'a utilisé dans tous nos microservices du projet."

### Q2 : Quelle est la différence entre GET et POST ?
**Réponse type :**
> "GET sert à récupérer des données sans les modifier (ex: lire un utilisateur). POST sert à créer une nouvelle ressource (ex: créer un utilisateur). GET n'a pas de body, POST en a un. Dans notre projet, on utilise GET pour lire les Pokémon du Pokédex, et POST pour créer une équipe."

### Q3 : C'est quoi Pydantic ?
**Réponse type :**
> "Pydantic est une bibliothèque de validation de données. On définit des modèles avec des types (str, int, email...) et Pydantic valide automatiquement les données entrantes. Si les données sont invalides, FastAPI retourne automatiquement une erreur 422 avec les détails de l'erreur."

### Q4 : Pourquoi utiliser async/await ?
**Réponse type :**
> "async/await permet de gérer plusieurs requêtes en parallèle sans bloquer le serveur. Quand on attend une réponse de la base de données, le serveur peut traiter d'autres requêtes. Ça améliore les performances, surtout pour les opérations I/O comme les requêtes BDD ou les appels HTTP."

### Q5 : Comment sécuriser une API FastAPI ?
**Réponse type :**
> "Plusieurs méthodes : 1) API Key simple (X-API-Key dans le header), 2) JWT (JSON Web Tokens) pour authentifier les utilisateurs, 3) OAuth2 pour des cas plus complexes. Dans notre projet, on utilise JWT dans l'auth_service pour authentifier les joueurs."

---

## 💡 CONCEPTS CLÉS À RETENIR

1. **FastAPI** = framework Python pour API REST
2. **GET/POST/PUT/DELETE** = verbes HTTP pour CRUD
3. **Pydantic** = validation automatique des données
4. **Path parameters** = dans l'URL (obligatoires)
5. **Query parameters** = après le ? (optionnels)
6. **async/await** = non-bloquant, meilleures performances
7. **CORS** = nécessaire pour frontend → backend
8. **Documentation auto** = /docs (Swagger UI)

---

## ✅ AUTO-TEST

1. Écris un endpoint GET qui récupère un utilisateur par ID
2. Écris un endpoint POST qui crée un produit avec validation Pydantic
3. Quelle est la différence entre PUT et PATCH ?
4. Comment ajouter une API Key à une route FastAPI ?
5. Pourquoi utiliser async/await ?

Si tu peux répondre → **✅ Fiche maîtrisée !**
