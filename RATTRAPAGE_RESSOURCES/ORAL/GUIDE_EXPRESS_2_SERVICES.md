# ⚡ GUIDE EXPRESS : MAÎTRISER 2 SERVICES EN 2 JOURS

> **Objectif** : Connaître parfaitement 2 services du projet pour l'oral

---

## 🎯 STRATÉGIE

### Jour 1 : Service 1 (8h)
- Matin : Lire tout le code et comprendre l'architecture
- Après-midi : Refaire le service from scratch
- Soir : Tester et préparer les réponses aux questions

### Jour 2 : Service 2 (8h)
- Même méthode que le Jour 1

---

## 🔥 OPTION A : AUTH_SERVICE + TEAM_SERVICE

### ⚙️ SERVICE 1 : AUTH_SERVICE (Le plus important)

#### Fichiers à maîtriser

```
auth_service/
├── main.py          ← Point d'entrée, routes
├── models.py        ← Modèle User en BDD
├── auth.py          ← Logique JWT
├── schemas.py       ← Validation Pydantic
└── database.py      ← Connexion PostgreSQL
```

#### Code essentiel à connaître PAR CŒUR

##### 1. Modèle User (models.py)

```python
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
```

**À retenir :**
- `username` et `email` sont uniques
- On stocke `hashed_password`, jamais le mot de passe en clair
- Héritage de `Base` pour SQLAlchemy

---

##### 2. Génération JWT (auth.py)

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hasher le mot de passe avec bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier que le mot de passe correspond au hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """Créer un JWT avec expiration 24h"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Décoder et vérifier un JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**À retenir :**
- `bcrypt` pour hasher (avec salt automatique)
- JWT contient `{"sub": user_id, "exp": timestamp}`
- `SECRET_KEY` doit être identique sur tous les services

---

##### 3. Routes principales (main.py)

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import schemas, models, auth
from database import get_db, engine

# Créer les tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")
security = HTTPBearer()

# ========== INSCRIPTION ==========
@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Vérifier si username existe déjà
    existing_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Créer le user
    hashed_pwd = auth.hash_password(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# ========== CONNEXION ==========
@app.post("/login")
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    # Récupérer le user
    user = db.query(models.User).filter(
        models.User.username == credentials.username
    ).first()
    
    if not user or not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Créer le JWT
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }

# ========== VÉRIFIER LE TOKEN ==========
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = auth.verify_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(payload.get("sub"))
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# ========== ROUTE PROTÉGÉE ==========
@app.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
```

**À retenir :**
- `register` : hasher le password, sauver en BDD
- `login` : vérifier password, créer JWT
- `get_current_user` : dependency pour protéger les routes
- `Depends(security)` : récupérer le token du header `Authorization: Bearer <token>`

---

#### Questions probables sur auth_service

**Q1 : Comment fonctionne l'authentification ?**
> "On utilise JWT (JSON Web Tokens). À la connexion, on vérifie le mot de passe hashé avec bcrypt. Si correct, on génère un JWT contenant l'ID utilisateur et une date d'expiration (24h). Le frontend stocke ce token et l'envoie dans le header Authorization pour chaque requête protégée. Les services vérifient le token avec la même clé secrète."

**Q2 : Pourquoi hasher les mots de passe ?**
> "On utilise bcrypt qui ajoute un 'salt' unique à chaque mot de passe avant de le hasher. Même si la BDD est compromise, l'attaquant ne peut pas récupérer les mots de passe en clair. Bcrypt est aussi lent volontairement pour ralentir les attaques par force brute."

**Q3 : Comment protéger une route ?**
> "On utilise une dependency `get_current_user` qui extrait le token du header Authorization, le vérifie, et récupère l'utilisateur en BDD. Si le token est invalide ou expiré, on retourne une erreur 401. Toutes les routes qui nécessitent l'authentification utilisent `Depends(get_current_user)`."

---

### ⚙️ SERVICE 2 : TEAM_SERVICE

#### Fichiers à maîtriser

```
team_service/
├── main.py          ← Routes CRUD teams
├── models.py        ← Team, TeamPokemon
├── recommender.py   ← AI Recommender
└── database.py      ← PostgreSQL
```

#### Code essentiel

##### 1. Modèles (models.py)

```python
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    user_id = Column(Integer, nullable=False)  # Référence à auth_service
    
    # Relation one-to-many
    pokemons = relationship("TeamPokemon", back_populates="team", cascade="all, delete-orphan")

class TeamPokemon(Base):
    __tablename__ = "team_pokemons"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    pokemon_id = Column(Integer, nullable=False)
    pokemon_name = Column(String, nullable=False)
    pokemon_types = Column(JSON, nullable=False)  # ["fire", "flying"]
    
    team = relationship("Team", back_populates="pokemons")
```

**À retenir :**
- Relation one-to-many : 1 team → plusieurs pokemons
- `cascade="all, delete-orphan"` : supprimer les pokémons si la team est supprimée
- `pokemon_types` en JSON pour stocker une liste

---

##### 2. Routes CRUD (main.py)

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

app = FastAPI(title="Team Service")

# ========== CRÉER UNE ÉQUIPE ==========
@app.post("/teams", response_model=schemas.TeamResponse)
def create_team(team: schemas.TeamCreate, user_id: int, db: Session = Depends(get_db)):
    # user_id vient du JWT vérifié par la gateway
    db_team = models.Team(
        name=team.name,
        description=team.description,
        user_id=user_id
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

# ========== LISTER MES ÉQUIPES ==========
@app.get("/teams", response_model=list[schemas.TeamResponse])
def list_teams(user_id: int, db: Session = Depends(get_db)):
    teams = db.query(models.Team).filter(models.Team.user_id == user_id).all()
    return teams

# ========== AJOUTER UN POKÉMON ==========
@app.post("/teams/{team_id}/pokemons")
def add_pokemon(
    team_id: int,
    pokemon: schemas.PokemonAdd,
    user_id: int,
    db: Session = Depends(get_db)
):
    # Vérifier que la team appartient à l'utilisateur
    team = db.query(models.Team).filter(
        models.Team.id == team_id,
        models.Team.user_id == user_id
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Vérifier max 6 pokémons
    if len(team.pokemons) >= 6:
        raise HTTPException(status_code=400, detail="Team already has 6 Pokémon")
    
    # Vérifier pas de doublons
    existing = [p.pokemon_id for p in team.pokemons]
    if pokemon.pokemon_id in existing:
        raise HTTPException(status_code=400, detail="Pokémon already in team")
    
    # Ajouter
    db_pokemon = models.TeamPokemon(
        team_id=team_id,
        pokemon_id=pokemon.pokemon_id,
        pokemon_name=pokemon.pokemon_name,
        pokemon_types=pokemon.pokemon_types
    )
    db.add(db_pokemon)
    db.commit()
    
    return {"message": "Pokémon added"}

# ========== SUPPRIMER UNE ÉQUIPE ==========
@app.delete("/teams/{team_id}")
def delete_team(team_id: int, user_id: int, db: Session = Depends(get_db)):
    team = db.query(models.Team).filter(
        models.Team.id == team_id,
        models.Team.user_id == user_id
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    db.delete(team)  # cascade supprimera aussi les pokémons
    db.commit()
    
    return {"message": "Team deleted"}
```

**À retenir :**
- Toujours vérifier `user_id` pour la sécurité
- Valider les règles métier (max 6, pas de doublons)
- `cascade` supprime automatiquement les pokémons

---

##### 3. AI Recommender (recommender.py)

```python
import requests
from typing import List

def recommend_pokemon(team_pokemons: List[dict]) -> List[dict]:
    """Suggérer des Pokémon pour compléter l'équipe"""
    
    # 1. Analyser les types actuels
    current_types = set()
    for p in team_pokemons:
        current_types.update(p["pokemon_types"])
    
    # 2. Types manquants
    all_types = ["fire", "water", "grass", "electric", "ground", 
                 "flying", "psychic", "bug", "rock", "ghost"]
    missing_types = list(set(all_types) - current_types)
    
    # 3. Récupérer des Pokémon via pokedex_service
    recommendations = []
    for missing_type in missing_types[:3]:  # Top 3
        try:
            response = requests.get(
                f"http://pokedex-service:8004/pokemon/type/{missing_type}",
                timeout=2
            )
            if response.status_code == 200:
                pokemons = response.json()
                if pokemons:
                    recommendations.append({
                        "id": pokemons[0]["id"],
                        "name": pokemons[0]["name"],
                        "types": pokemons[0]["types"],
                        "reason": f"Ajoute le type {missing_type}"
                    })
        except:
            continue
    
    return recommendations

# Route pour utiliser le recommender
@app.post("/teams/{team_id}/recommend")
def get_recommendations(team_id: int, user_id: int, db: Session = Depends(get_db)):
    team = db.query(models.Team).filter(
        models.Team.id == team_id,
        models.Team.user_id == user_id
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Convertir en dict pour le recommender
    team_data = [
        {
            "pokemon_id": p.pokemon_id,
            "pokemon_name": p.pokemon_name,
            "pokemon_types": p.pokemon_types
        }
        for p in team.pokemons
    ]
    
    recommendations = recommend_pokemon(team_data)
    return {"recommendations": recommendations}
```

**À retenir :**
- Appel REST synchrone à pokedex_service
- Analyse simple : types manquants
- Timeout pour éviter de bloquer si pokedex_service est down

---

#### Questions probables sur team_service

**Q1 : Comment fonctionne le recommender ?**
> "Il analyse les types actuels de l'équipe, identifie les types manquants parmi les 18 types Pokémon, et appelle pokedex_service pour récupérer des Pokémon de ces types. C'est une logique simplifiée qui pourrait être améliorée en prenant en compte les faiblesses de types et les synergies."

**Q2 : Comment empêcher un utilisateur de modifier l'équipe d'un autre ?**
> "On vérifie toujours le user_id extrait du JWT. Par exemple, dans `add_pokemon`, on fait un query avec `team_id` ET `user_id`. Si la team n'appartient pas à l'utilisateur, on retourne 404. C'est une sécurité au niveau application."

**Q3 : Pourquoi limiter à 6 Pokémon ?**
> "C'est une règle métier du jeu Pokémon. On valide côté backend avant d'ajouter un Pokémon. Si l'équipe a déjà 6 Pokémon, on retourne une erreur 400. On valide aussi côté frontend pour une meilleure UX, mais la vraie sécurité est côté backend."

---

## 🔥 PLAN D'ACTION RAPIDE

### Jour 6 (24 mai) : Auth Service

#### Matin (4h)
1. Lire tout le code (1h)
2. Dessiner l'architecture sur papier (30 min)
3. Refaire from scratch (2h)
4. Tester avec curl ou Postman (30 min)

```bash
# Test inscription
curl -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"pass123"}'

# Test connexion
curl -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pass123"}'

# Test route protégée
curl -X GET http://localhost:8001/me \
  -H "Authorization: Bearer <TOKEN>"
```

#### Après-midi (4h)
1. Comprendre JWT en profondeur (1h)
2. Expliquer à voix haute (1h)
3. Préparer réponses aux 10 questions probables (2h)

#### Soir (1h)
- Quiz personnel : 20 questions
- Refaire les schémas de mémoire

---

### Jour 7 (25 mai) : Team Service

#### Même planning qu'auth_service

**Tests à faire :**

```bash
# Créer une équipe (avec JWT)
curl -X POST http://localhost:8002/teams \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Team Thunder","description":"Équipe électrique"}'

# Ajouter un Pokémon
curl -X POST http://localhost:8002/teams/1/pokemons \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"pokemon_id":25,"pokemon_name":"Pikachu","pokemon_types":["electric"]}'

# Recommandations
curl -X POST http://localhost:8002/teams/1/recommend \
  -H "Authorization: Bearer <TOKEN>"
```

---

## ✅ CHECKLIST DE MAÎTRISE

### Auth Service
- [ ] Je connais le modèle User par cœur
- [ ] Je sais expliquer JWT (création, vérification)
- [ ] Je sais pourquoi on utilise bcrypt
- [ ] Je peux refaire les 3 routes principales
- [ ] Je peux répondre aux questions pièges

### Team Service
- [ ] Je connais les modèles Team et TeamPokemon
- [ ] Je comprends la relation one-to-many
- [ ] Je sais comment fonctionne le recommender
- [ ] Je peux expliquer les validations (max 6, pas de doublons)
- [ ] Je sais comment on appelle pokedex_service

---

## 🚀 SI TU AS MOINS DE TEMPS

### Version ultra-rapide (1 jour = 8h)

**Matin : Auth Service (4h)**
- Lire le code (1h)
- Comprendre JWT (1h)
- Tester (1h)
- Préparer réponses (1h)

**Après-midi : Team Service (4h)**
- Lire le code (1h)
- Comprendre le recommender (1h)
- Tester (1h)
- Préparer réponses (1h)

**Stratégie :**
- Accepte de ne pas TOUT savoir
- Concentre-toi sur les 80% essentiels
- Prépare des réponses types
- Sois honnête à l'oral

---

## 💪 TU PEUX LE FAIRE !

**2 services maîtrisés = 80% de chances de passer l'oral.**

Le prof ne veut pas un expert, il veut quelqu'un qui :
- A travaillé sur le projet
- Comprend ce qu'il a fait
- Peut expliquer ses choix

**Avec cette préparation, tu es largement au-dessus du minimum requis ! 🔥**
