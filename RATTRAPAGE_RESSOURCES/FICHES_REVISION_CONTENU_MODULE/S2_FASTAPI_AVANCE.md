# S2 — FastAPI Avancé : OAuth2, JWT, APIRouter, Background Tasks

> Cours de Lalanne Raphaël — Séance du 12 novembre  
> Source : `FastAPI - Manipulations avancées.pdf`

---

## 1. Authentification avec JWT — Vue d'ensemble

### Flux d'authentification complet

```
1. Client envoie POST /auth/token { username, password }
2. Serveur vérifie les credentials
3. Serveur génère un JWT (access token)
4. Client stocke le token
5. Client envoie le token dans chaque requête : Authorization: Bearer <token>
6. Serveur vérifie le token sur chaque route protégée
```

### JWT (JSON Web Token)
Un JWT est composé de 3 parties séparées par des `.` :
```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJib2IifQ.hiMVLmssoTsy1MqbmIoviDeFPvo-nCd92d4UFiP2
─────────────────── ─────────────────── ────────────────────────────────────────────
     HEADER                PAYLOAD                       SIGNATURE
(algo + type)          (données)               (signé avec SECRET_KEY)
```

Le **payload** peut contenir n'importe quelles données, mais typiquement :
- `sub` : sujet (username/user_id)
- `exp` : date d'expiration (timestamp)
- `type` : "access" ou "refresh"

---

## 2. Configuration — Classes et constantes

```python
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional

# Endpoint où récupérer le token (pour Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Clé secrète (en PRODUCTION, mettre dans une variable d'env !)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Modèles Pydantic pour les tokens
class Token(BaseModel):
    access_token: str
    token_type: str         # toujours "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# Modèles utilisateur
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str    # ← jamais exposé dans les réponses
```

---

## 3. Création et vérification du token JWT

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Contexte pour hasher les mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})       # Ajouter l'expiration
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

---

## 4. Récupérer l'utilisateur courant (dépendance)

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

---

## 5. Route de login + routes protégées

```python
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm = formulaire standard avec username + password
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Route protégée : nécessite un token valide
@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Autre route protégée
@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]
```

---

## 6. Exemple complet TP2 — Wine Quality API avec JWT

### Structure du projet TP2
```
wine_quality_api/
├── main.py              # FastAPI app + include_router
├── auth.py              # create_access_token, verify_token
├── models.py            # User, UserInDB, Token, WineData
├── config.py            # SECRET_KEY, ALGORITHM, expirations
├── dependencies.py      # get_current_active_user
└── routers/
    ├── auth_router.py   # POST /auth/token, POST /auth/refresh, GET /auth/me
    └── wine_router.py   # CRUD complet sur les vins
```

### main.py
```python
from fastapi import FastAPI
from routers.auth_router import router as auth_router
from routers.wine_router import router as wine_router

app = FastAPI(title="Wine Quality API")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(wine_router, prefix="/wines", tags=["wines"])

@app.get("/")
async def root():
    return {"message": "Wine Quality API"}
```

### auth.py — gestion des tokens
```python
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or payload.get("type") != token_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return TokenData(username=username)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
```

### models.py — User + mot de passe hashé bcrypt
```python
from pydantic import BaseModel
from typing import Optional
import bcrypt

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserInDB(User):
    hashed_password: str    # ← JAMAIS retourné dans les réponses

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
```

### auth_router.py — Routes d'authentification
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

router = APIRouter()

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
```

---

## 7. APIRouter — Décomposer une grosse application

**Problème** : Quand l'application grossit, mettre toutes les routes dans `main.py` devient ingérable.

**Solution** : `APIRouter` = mini-FastAPI dans un fichier séparé.

### app/routers/users.py
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "Foo"}, {"username": "Bar"}]

@router.get("/users/me", tags=["users"])
async def read_user_me():
    return {"username": "Current_User"}

@router.get("/users/{username}", tags=["users"])
async def read_user(username: str):
    return {"username": username}
```

### app/main.py — Inclure le router
```python
from fastapi import FastAPI, Depends
from routers import users, items

app = FastAPI()

# include_router avec toutes les options
app.include_router(
    users.router,
    prefix="/admin",            # Toutes les routes préfixées par /admin
    tags=["admin"],             # Tag Swagger
    dependencies=[Depends(verify_token)],  # Auth requise pour tout le router
    responses={418: {"description": "I'm a teapot"}},  # Réponses par défaut
)

app.include_router(items.router)  # Sans options supplémentaires
```

**Points clés :**
- `prefix` : préfixe appliqué à toutes les routes du router
- `tags` : groupe dans Swagger UI
- `dependencies` : dépendance appliquée à **toutes** les routes du router (idéal pour l'auth)

---

## 8. Background Tasks — Tâches en arrière-plan

**Définition** : Tâches qui s'exécutent **après** que la réponse a été envoyée au client. Le client n'attend pas leur fin.

**Cas d'usage :**
- Envoi d'emails (opération lente, client n'a pas besoin d'attendre)
- Traitement de fichiers volumineux
- Notifications
- Logging asynchrone

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_notification(email: str, message: str = ""):
    # Simule l'envoi d'un email en écrivant dans un fichier log
    with open("log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    # Ajoute la tâche en arrière-plan
    background_tasks.add_task(
        write_notification,     # ← la fonction à exécuter
        email,                  # ← arg positionnel
        message="Suis une notif"  # ← arg keyword
    )
    # La réponse est envoyée IMMÉDIATEMENT, sans attendre l'email
    return {"message": "Notification sent in the background"}
```

**Fonctionnement interne :**
1. FastAPI envoie la réponse `{"message": "..."}` au client
2. **Après** que la connexion est fermée, FastAPI exécute `write_notification`
3. Le client ne voit jamais les résultats de la tâche de fond

---

## 9. Dependencies (Depends) avancé

### Hiérarchie de dépendances

```python
# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Décoder le JWT et récupérer l'utilisateur
    ...
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)  # ← chainage de depends
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Dans les routes
@app.get("/profile")
async def get_profile(user: User = Depends(get_current_active_user)):
    return user
```

### Dépendance avec yield (clean up)
```python
def get_db():
    db = SessionLocal()
    try:
        yield db         # ← code avant yield = setup
    finally:
        db.close()       # ← code dans finally = teardown (même si erreur)
```

---

## 10. TP3 — Wine Quality CRUD avec SQLAlchemy

### Structure TP3 (plus avancée que TP2)
```
wine-quality-crud-api/src/
├── main.py
├── config.py
├── auth.py
├── dependencies.py
├── models/
│   ├── wine_models.py     # Schémas Pydantic
│   ├── user_models.py
│   └── token_models.py
├── database/
│   └── connection.py      # SQLAlchemy engine + session
├── routers/
│   ├── wine_router.py
│   └── auth_router.py
└── services/
    └── wine_service.py    # Logique métier séparée des routes
```

### database/connection.py — SQLAlchemy
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./wine_quality.db"  # En prod : PostgreSQL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### models/wine_models.py — Pydantic + séparation Create/Update
```python
from pydantic import BaseModel
from typing import Optional

class Wine(BaseModel):
    id: Optional[int] = None
    name: str
    type: str            # "red", "white", "rosé"
    acidity: float
    sweetness: float
    alcohol_content: float
    quality: int

class WineCreate(BaseModel):
    name: str
    type: str
    acidity: float
    sweetness: float
    alcohol_content: float
    # Pas de quality ni d'id ici → à calculer par le service

class WineUpdate(BaseModel):
    # Tous les champs optionnels pour les mises à jour partielles (PATCH)
    name: Optional[str] = None
    type: Optional[str] = None
    acidity: Optional[float] = None
    sweetness: Optional[float] = None
    alcohol_content: Optional[float] = None
    quality: Optional[int] = None
```

**Pattern Wine/WineCreate/WineUpdate** = pattern standard pour CRUD :
- `WineCreate` : données nécessaires pour créer (sans id, sans champs calculés)
- `Wine` : modèle complet avec id (réponse)
- `WineUpdate` : mise à jour partielle (tout optionnel)

### routers/wine_router.py
```python
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()
wine_service = WineService()

@router.post("/wines/", response_model=Wine)
async def create_wine(wine: WineCreate):
    try:
        return await wine_service.create_wine(wine)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wines/", response_model=List[Wine])
async def read_wines(skip: int = 0, limit: int = 10):
    return await wine_service.get_wines(skip=skip, limit=limit)

@router.get("/wines/{wine_id}", response_model=Wine)
async def read_wine(wine_id: int):
    wine = await wine_service.get_wine(wine_id)
    if wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return wine

@router.put("/wines/{wine_id}", response_model=Wine)
async def update_wine(wine_id: int, wine: WineUpdate):
    updated = await wine_service.update_wine(wine_id, wine)
    if updated is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return updated

@router.delete("/wines/{wine_id}", response_model=Wine)
async def delete_wine(wine_id: int):
    deleted = await wine_service.delete_wine(wine_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return deleted
```

---

## 11. Questions d'oral probables

**Q: Comment fonctionne l'authentification JWT dans FastAPI ?**  
R: Le client envoie ses credentials à `/token`. Le serveur vérifie, génère un JWT signé avec `SECRET_KEY`, et le retourne. Pour chaque requête protégée, le client envoie `Authorization: Bearer <token>`. FastAPI utilise `OAuth2PasswordBearer` pour extraire le token, `jwt.decode()` pour le vérifier, et `Depends(get_current_user)` pour injecter l'utilisateur.

**Q: Pourquoi utiliser APIRouter ?**  
R: Pour séparer les routes par domaine fonctionnel (users, orders, auth...) dans des fichiers dédiés. Chaque router peut avoir son propre préfixe, ses tags Swagger, et des dépendances communes (ex: auth requise pour tout le router).

**Q: Qu'est-ce qu'une Background Task et quand l'utiliser ?**  
R: Une tâche qui s'exécute après l'envoi de la réponse au client. Utile pour les opérations longues dont le client n'a pas besoin d'attendre le résultat : envoi d'email, traitement de fichier, notification...

**Q: Quelle est la différence entre `User` et `UserInDB` ?**  
R: `UserInDB` hérite de `User` et ajoute `hashed_password`. Les routes utilisent `response_model=User` pour ne jamais exposer le hash du mot de passe dans les réponses.

**Q: Comment sécuriser toutes les routes d'un router sans répéter `Depends()` sur chaque route ?**  
R: Passer `dependencies=[Depends(get_current_user)]` dans `app.include_router(router, dependencies=[...])`.
