# FICHE TP2 — FastAPI Avancé : JWT Auth + CRUD Vins

> **Séance :** 12 novembre | **Niveau :** Intermédiaire  
> **Objectif TP :** Construire une API FastAPI complète avec authentification JWT, structure multi-fichiers, et opérations CRUD sur un dataset CSV

---

## 1. CONTEXTE DU TP — Ce qui était demandé

**Consigne exacte :**  
Écrire une API contenant chaque opération CRUD sur le dataset de vins.  
Utiliser le cours FastAPI Manipulations Avancées pour créer :

| Fichier | Rôle |
|---------|------|
| `main.py` | Point d'entrée, inclut les routeurs |
| `config.py` | Variables statiques JWT (clé secrète, durée de vie, algo) |
| `models.py` | Classes User, Token, WineData + fonctions utilisateurs |
| `auth.py` | Fonctions de gestion des tokens (créer, vérifier) |
| `dependencies.py` | Dépendance `get_current_user` pour protéger les routes |
| `auth_router.py` | Routes `/auth/token` (login) et `/auth/refresh` |
| `wine_router.py` | Routes CRUD `/wines/` (GET, POST, PUT, DELETE) |

**Règle de sécurité :**
- N'importe qui peut **lire** les vins (GET)
- Seul un utilisateur **authentifié** peut créer, modifier, supprimer (POST, PUT, DELETE)

---

## 2. ARCHITECTURE DU PROJET

```
wine_quality_api/
├── main.py              ← FastAPI app + include_router
├── config.py            ← Constantes JWT
├── models.py            ← Pydantic models + users en dur
├── auth.py              ← create_token, verify_token
├── dependencies.py      ← get_current_user (Depends)
├── routers/
│   ├── auth_router.py   ← POST /auth/token, POST /auth/refresh, GET /auth/me
│   └── wine_router.py   ← GET/POST/PUT/DELETE /wines/
└── data/
    └── WineQT.csv
```

---

## 3. main.py — Point d'entrée

```python
from fastapi import FastAPI
import uvicorn
from routers.auth_router import router as auth_router
from routers.wine_router import router as wine_router

app = FastAPI(title="Wine Quality API")

# Inclure les routeurs avec leur préfixe
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(wine_router, prefix="/wines", tags=["wines"])

@app.get("/")
async def root():
    return {"message": "Wine Quality API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Points clés `include_router` :**
- `prefix="/auth"` → toutes les routes du routeur sont préfixées par `/auth`
- `tags=["auth"]` → groupage dans `/docs`
- Séparer les routeurs = code maintenable, chaque fichier a une responsabilité

---

## 4. config.py — Variables JWT

```python
SECRET_KEY = "ma_cle_secrete_jwt_2024"  # Clé pour signer les tokens
ALGORITHM = "HS256"                      # Algorithme HMAC-SHA256
ACCESS_TOKEN_EXPIRE_MINUTES = 30         # Token d'accès valide 30 min
REFRESH_TOKEN_EXPIRE_DAYS = 7            # Refresh token valide 7 jours
```

**Pourquoi une clé secrète ?**
> Le token JWT est signé avec `SECRET_KEY`. Sans cette clé, personne ne peut forger un token valide. En production : utiliser une vraie clé aléatoire longue (`secrets.token_hex(32)`).

**⚠️ En production : ne jamais mettre la clé secrète en dur dans le code.** Utiliser les variables d'environnement (`.env` + `python-dotenv`).

---

## 5. models.py — Modèles Pydantic + Utilisateurs

```python
from pydantic import BaseModel
from typing import Optional
import bcrypt

# ===== MODÈLES UTILISATEUR =====
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserInDB(User):
    """User en base de données → ajoute le mot de passe hashé"""
    hashed_password: str

# ===== MODÈLES TOKEN =====
class Token(BaseModel):
    access_token: str
    token_type: str             # "bearer"
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None

# ===== MODÈLE VIN =====
class WineData(BaseModel):
    fixed_acidity: float
    volatile_acidity: float
    citric_acid: float
    residual_sugar: float
    chlorides: float
    free_sulfur_dioxide: float
    total_sulfur_dioxide: float
    density: float
    pH: float
    sulphates: float
    alcohol: float
    quality: int

class WineResponse(WineData):
    id: int  # L'id est ajouté à la réponse (index dans le CSV)

# ===== GESTION DES MOTS DE PASSE =====
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# ===== BASE DE DONNÉES SIMULÉE (dictionnaire en dur) =====
fake_users_db = {
    "betsaleel": {
        "username": "betsaleel",
        "full_name": "Betsaleel",
        "email": "betsaleel@cy-tech.fr",
        "hashed_password": "$2b$12$/5.5t4zsQagdXHi8egABJO...",  # hash de "password123"
        "disabled": False,
    },
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@cy-tech.fr",
        "hashed_password": "$2b$12$fyU5nA8...",
        "disabled": False,
    }
}

def get_user(username: str) -> Optional[UserInDB]:
    if username in fake_users_db:
        return UserInDB(**fake_users_db[username])
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
```

**Pourquoi `bcrypt` pour les mots de passe ?**
> bcrypt est un algorithme de hashage **lent exprès** (facteur de coût configurable). Il rend les attaques par force brute très coûteuses. Un hash bcrypt inclut automatiquement un **sel** (salt) aléatoire → deux hashes du même mot de passe seront différents.

---

## 6. auth.py — Création et Vérification de Tokens JWT

```python
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from models import TokenData

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    # Calculer la date d'expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Ajouter exp et type au payload
    to_encode.update({"exp": expire, "type": "access"})
    
    # Signer et encoder le token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> TokenData:
    try:
        # Décoder le token (vérifie la signature ET l'expiration)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        # Vérifier que le username existe et que le type est correct
        if username is None or payload.get("type") != token_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        return TokenData(username=username)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
```

### Anatomie d'un token JWT

```
HEADER.PAYLOAD.SIGNATURE

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
.eyJzdWIiOiJiZXRzYWxlZWwiLCJleHAiOjE3MDA1MDAwMDB9
.abc123xyz...

Décodé :
Header  : {"alg": "HS256", "typ": "JWT"}
Payload : {"sub": "betsaleel", "exp": 1700500000, "type": "access"}
Signature: HMACSHA256(header.payload, SECRET_KEY)
```

**`sub` = subject** → identifiant de l'utilisateur dans le token  
**`exp` = expiration** → timestamp Unix, vérifié automatiquement par `jwt.decode()`

---

## 7. dependencies.py — Injection de Dépendances

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from auth import verify_token
from models import User, get_user, TokenData

# Indique à FastAPI que les tokens arrivent via POST /auth/token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Extrait et vérifie automatiquement le Bearer token.
    FastAPI appelle oauth2_scheme → extrait le token du header Authorization.
    """
    token_data: TokenData = verify_token(token, token_type="access")
    
    if token_data.username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    user = get_user(username=token_data.username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return User(username=user.username, email=user.email, full_name=user.full_name, disabled=user.disabled)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Vérifie en plus que l'utilisateur n'est pas désactivé.
    Chaîne de dépendances : get_current_active_user → get_current_user → oauth2_scheme
    """
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
```

**Chaîne de dépendances (Depends) :**
```
Route protégée
    → Depends(get_current_active_user)
        → Depends(get_current_user)
            → Depends(oauth2_scheme)  ← extrait le token du header
```

---

## 8. auth_router.py — Routes d'Authentification

```python
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from models import Token, User, authenticate_user
from auth import create_access_token, create_refresh_token, verify_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from dependencies import get_current_active_user

router = APIRouter()

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login : POST /auth/token
    form_data = formulaire (username + password) — PAS du JSON !
    """
    user = authenticate_user(form_data.username, form_data.password)
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
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Form(...)):
    """
    Refresh : POST /auth/refresh
    Génère un nouveau access_token depuis le refresh_token
    """
    token_data = verify_token(refresh_token, token_type="refresh")
    if token_data.username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": token_data.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Retourne l'utilisateur connecté"""
    return current_user
```

**`OAuth2PasswordRequestForm`** → FastAPI lit automatiquement les champs `username` et `password` depuis le body de type `application/x-www-form-urlencoded` (formulaire, pas JSON).

---

## 9. wine_router.py — CRUD Complet

```python
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
import pandas as pd
from pathlib import Path
from models import WineData, WineResponse, User
from dependencies import get_current_active_user

router = APIRouter()
DATA_PATH = Path(__file__).parent.parent / "data" / "WineQT.csv"

def load_wines_df() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise HTTPException(status_code=500, detail="Dataset not found")
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.replace(' ', '_')
    if 'Id' in df.columns:
        df = df.drop('Id', axis=1)
    return df

def save_wines_df(df: pd.DataFrame):
    df_copy = df.copy()
    df_copy.columns = df_copy.columns.str.replace('_', ' ')
    df_copy.to_csv(DATA_PATH, index=False)

# GET /wines/ — lecture publique (pas de Depends auth)
@router.get("/", response_model=List[WineResponse])
async def get_all_wines(
    skip: int = Query(0, ge=0),           # Pagination : sauter N éléments
    limit: int = Query(100, ge=1, le=1000) # Pagination : max 1000 à la fois
):
    df = load_wines_df()
    wines_subset = df.iloc[skip:skip + limit]
    wines = []
    for idx, row in wines_subset.iterrows():
        wine_dict = row.to_dict()
        wine_dict['id'] = int(idx)
        wines.append(wine_dict)
    return wines

# GET /wines/{id} — lecture publique
@router.get("/{wine_id}", response_model=WineResponse)
async def get_wine(wine_id: int):
    df = load_wines_df()
    if wine_id < 0 or wine_id >= len(df):
        raise HTTPException(status_code=404, detail="Wine not found")
    wine_dict = df.iloc[wine_id].to_dict()
    wine_dict['id'] = wine_id
    return wine_dict

# POST /wines/ — PROTÉGÉ (auth obligatoire)
@router.post("/", response_model=WineResponse, status_code=201)
async def create_wine(wine: WineData, current_user: User = Depends(get_current_active_user)):
    df = load_wines_df()
    wine_dict = wine.model_dump()
    new_wine_df = pd.DataFrame([wine_dict])
    df = pd.concat([df, new_wine_df], ignore_index=True)
    save_wines_df(df)
    wine_id = len(df) - 1
    wine_dict['id'] = wine_id
    return wine_dict

# PUT /wines/{id} — PROTÉGÉ
@router.put("/{wine_id}", response_model=WineResponse)
async def update_wine(wine_id: int, wine: WineData, current_user: User = Depends(get_current_active_user)):
    df = load_wines_df()
    if wine_id < 0 or wine_id >= len(df):
        raise HTTPException(status_code=404, detail="Wine not found")
    wine_dict = wine.model_dump()
    for key, value in wine_dict.items():
        df.at[wine_id, key] = value
    save_wines_df(df)
    wine_dict['id'] = wine_id
    return wine_dict

# DELETE /wines/{id} — PROTÉGÉ
@router.delete("/{wine_id}", status_code=204)
async def delete_wine(wine_id: int, current_user: User = Depends(get_current_active_user)):
    df = load_wines_df()
    if wine_id < 0 or wine_id >= len(df):
        raise HTTPException(status_code=404, detail="Wine not found")
    df = df.drop(wine_id)
    df = df.reset_index(drop=True)  # Réindexer après suppression !
    save_wines_df(df)
    return None  # 204 No Content
```

---

## 10. COMMANDES CURL DE TEST

```bash
# 1) Démarrer l'API
uvicorn main:app --reload

# 2) Se connecter (formulaire, pas JSON)
curl -X POST "http://localhost:8000/auth/token" \
  -d "username=betsaleel&password=password123"
# Réponse : {"access_token": "eyJ...", "token_type": "bearer", "refresh_token": "eyJ..."}

# 3) Lire tous les vins (sans auth)
curl "http://localhost:8000/wines/?limit=5"

# 4) Lire un vin par id (sans auth)
curl "http://localhost:8000/wines/0"

# 5) Créer un vin (auth obligatoire)
curl -X POST "http://localhost:8000/wines/" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"fixed_acidity": 7.4, "volatile_acidity": 0.7, "citric_acid": 0.0, "residual_sugar": 1.9, "chlorides": 0.076, "free_sulfur_dioxide": 11.0, "total_sulfur_dioxide": 34.0, "density": 0.9978, "pH": 3.51, "sulphates": 0.56, "alcohol": 9.4, "quality": 5}'

# 6) Modifier un vin
curl -X PUT "http://localhost:8000/wines/0" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"quality": 7, ...}'

# 7) Supprimer un vin
curl -X DELETE "http://localhost:8000/wines/0" \
  -H "Authorization: Bearer eyJ..."

# 8) Refresh du token
curl -X POST "http://localhost:8000/auth/refresh" \
  -d "refresh_token=eyJ..."
```

---

## 11. QUESTIONS D'ORAL POSSIBLES SUR CE TP

**Q : Pourquoi le login utilise un formulaire et pas du JSON ?**
> La norme OAuth2 (que FastAPI implémente via `OAuth2PasswordRequestForm`) impose le format `application/x-www-form-urlencoded` pour l'échange des credentials. Cela permet la compatibilité avec tous les clients OAuth2. `curl -d "username=x&password=y"` envoie un formulaire.

**Q : Quelle est la différence entre `access_token` et `refresh_token` ?**
> `access_token` : durée courte (30 min), envoyé à chaque requête dans le header Authorization. `refresh_token` : durée longue (7 jours), utilisé **uniquement** pour obtenir un nouveau access_token quand l'ancien expire. On ne l'envoie pas à chaque requête.

**Q : Comment FastAPI sait que la route nécessite une authentification ?**
> Grâce à `Depends(get_current_active_user)` dans la signature de la fonction. FastAPI exécute automatiquement la dépendance avant d'appeler la fonction. Si la dépendance lève une exception, la route n'est pas exécutée.

**Q : Que fait `OAuth2PasswordBearer(tokenUrl="/auth/token")` ?**
> Définit un schéma de sécurité : le client doit envoyer le token dans le header `Authorization: Bearer <token>`. Le paramètre `tokenUrl` est juste pour la documentation (`/docs`) — FastAPI y affiche un bouton "Authorize".

**Q : Pourquoi `reset_index(drop=True)` après `df.drop()` ?**
> Après suppression d'une ligne, l'index a un trou (ex: 0, 1, 3, 4 après suppression de la ligne 2). `reset_index(drop=True)` réindexe proprement : 0, 1, 2, 3. Sans ça, les ids des vins seraient décalés.

**Q : Pourquoi le DELETE renvoie un status 204 et pas 200 ?**
> 204 = "No Content" → la suppression a réussi, mais il n'y a rien à retourner. C'est la convention REST : 201 = Created, 204 = No Content (après DELETE ou PUT sans retour).
