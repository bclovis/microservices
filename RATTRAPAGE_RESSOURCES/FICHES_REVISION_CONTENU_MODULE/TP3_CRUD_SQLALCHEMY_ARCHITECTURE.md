# FICHE TP3 — Architecture Propre : CRUD avec SQLAlchemy + Service Layer

> **Séance :** 19 novembre | **Niveau :** Intermédiaire+  
> **Objectif TP :** Refactoriser l'API Wine Quality avec une vraie base de données (SQLite/SQLAlchemy), une architecture en couches (router → service → BDD), et des modèles Pydantic séparés (création / mise à jour / réponse)

---

## 1. CONTEXTE DU TP — Ce qui était demandé

Le TP3 est une **évolution du TP2** : même API vins, mais architecture beaucoup plus propre :
- **BDD réelle** (SQLite via SQLAlchemy) au lieu d'un simple CSV
- **Architecture en couches** : chaque couche a une responsabilité unique
- **Modèles Pydantic distincts** : `WineCreate` ≠ `WineUpdate` ≠ `Wine` (réponse)
- **Service layer** : la logique métier est isolée dans un service

---

## 2. ARCHITECTURE EN COUCHES

```
Requête HTTP
     ↓
[Router]      → reçoit la requête, valide les params, appelle le service
     ↓
[Service]     → logique métier, appelle la BDD
     ↓
[Database]    → SQLAlchemy, connexion, session
     ↓
[Modèles]     → Pydantic (validation) + SQLAlchemy ORM (table)
```

**Structure du projet :**
```
src/
├── main.py
├── config.py
├── auth.py
├── dependencies.py
├── routers/
│   ├── auth_router.py
│   └── wine_router.py
├── services/
│   ├── wine_service.py     ← Logique métier CRUD
│   └── auth_service.py
├── models/
│   ├── wine_models.py      ← Pydantic (Wine, WineCreate, WineUpdate)
│   ├── user_models.py
│   └── token_models.py
└── database/
    └── connection.py       ← SQLAlchemy engine + session
```

---

## 3. database/connection.py — Connexion SQLAlchemy

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de connexion SQLite (fichier local)
DATABASE_URL = "sqlite:///./wine_quality.db"

# Engine = objet qui gère la connexion à la BDD
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Nécessaire pour SQLite avec FastAPI (threads multiples)
)

# SessionLocal = factory pour créer des sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = classe de base pour tous les modèles SQLAlchemy ORM
Base = declarative_base()

def get_db():
    """
    Dépendance FastAPI : génère une session BDD pour une requête.
    Utilise 'yield' → garantit la fermeture même en cas d'erreur.
    """
    db = SessionLocal()
    try:
        yield db      # La session est passée à la route
    finally:
        db.close()    # Toujours fermée après la requête
```

**Points clés SQLAlchemy :**

| Concept | Rôle |
|---------|------|
| `create_engine(url)` | Crée la connexion à la BDD |
| `SessionLocal()` | Crée une session (transaction) |
| `declarative_base()` | Classe parente pour les modèles ORM |
| `yield db` | Pattern "générateur" pour injection de dépendances |
| `check_same_thread=False` | Permet l'utilisation depuis plusieurs threads (FastAPI async) |

---

## 4. Modèle ORM — Table SQL

```python
# Dans wine_models.py (partie ORM)
from sqlalchemy import Column, Integer, Float, String
from database.connection import Base

class WineORM(Base):
    """Modèle SQLAlchemy → représente la table 'wines' en BDD"""
    __tablename__ = "wines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)     # "red", "white", "rosé"
    acidity = Column(Float)
    sweetness = Column(Float)
    alcohol_content = Column(Float)
    quality = Column(Integer)
```

---

## 5. Modèles Pydantic — Trois niveaux

```python
from pydantic import BaseModel
from typing import Optional

class WineCreate(BaseModel):
    """Données reçues à la CRÉATION — pas d'id, pas de quality"""
    name: str
    type: str
    acidity: float
    sweetness: float
    alcohol_content: float
    # quality n'est pas requis à la création

class WineUpdate(BaseModel):
    """Données reçues à la MODIFICATION — tout est optionnel"""
    name: Optional[str] = None
    type: Optional[str] = None
    acidity: Optional[float] = None
    sweetness: Optional[float] = None
    alcohol_content: Optional[float] = None
    quality: Optional[int] = None

class Wine(BaseModel):
    """Réponse complète — inclut l'id et la quality"""
    id: Optional[int] = None
    name: str
    type: str
    acidity: float
    sweetness: float
    alcohol_content: float
    quality: int
    
    class Config:
        from_attributes = True  # Permet la conversion ORM → Pydantic (Pydantic v2)
        # Ancienne syntaxe Pydantic v1 : orm_mode = True
```

**Pourquoi trois modèles distincts ?**

| Modèle | Quand | Pourquoi |
|--------|-------|----------|
| `WineCreate` | POST /wines/ | L'id est généré par la BDD, pas fourni par l'utilisateur |
| `WineUpdate` | PUT /wines/{id} | On veut pouvoir modifier un seul champ sans toucher les autres |
| `Wine` | Réponse (response_model) | Contient tout, y compris l'id généré |

---

## 6. services/wine_service.py — Logique Métier

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from models.wine_models import WineORM, WineCreate, WineUpdate, Wine

class WineService:
    """
    Service layer : contient toute la logique métier.
    Les routers appellent ce service, pas la BDD directement.
    """
    
    async def create_wine(self, db: Session, wine: WineCreate) -> Wine:
        """Crée un nouveau vin en BDD"""
        db_wine = WineORM(
            name=wine.name,
            type=wine.type,
            acidity=wine.acidity,
            sweetness=wine.sweetness,
            alcohol_content=wine.alcohol_content,
            quality=0  # Qualité par défaut
        )
        db.add(db_wine)
        db.commit()           # Sauvegarde en BDD
        db.refresh(db_wine)   # Recharge pour obtenir l'id généré
        return db_wine
    
    async def get_wines(self, db: Session, skip: int = 0, limit: int = 10) -> List[Wine]:
        """Liste les vins avec pagination"""
        return db.query(WineORM).offset(skip).limit(limit).all()
    
    async def get_wine(self, db: Session, wine_id: int) -> Optional[Wine]:
        """Récupère un vin par son id"""
        return db.query(WineORM).filter(WineORM.id == wine_id).first()
    
    async def update_wine(self, db: Session, wine_id: int, wine: WineUpdate) -> Optional[Wine]:
        """Met à jour partiellement un vin (PATCH-like)"""
        db_wine = db.query(WineORM).filter(WineORM.id == wine_id).first()
        if db_wine is None:
            return None
        
        # Met à jour seulement les champs non-None
        update_data = wine.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_wine, key, value)
        
        db.commit()
        db.refresh(db_wine)
        return db_wine
    
    async def delete_wine(self, db: Session, wine_id: int) -> Optional[Wine]:
        """Supprime un vin"""
        db_wine = db.query(WineORM).filter(WineORM.id == wine_id).first()
        if db_wine is None:
            return None
        db.delete(db_wine)
        db.commit()
        return db_wine
```

**Méthodes SQLAlchemy importantes :**

| Méthode | Action |
|---------|--------|
| `db.add(obj)` | Ajoute en session (pas encore en BDD) |
| `db.commit()` | Valide la transaction (écrit en BDD) |
| `db.refresh(obj)` | Recharge l'objet depuis la BDD (pour avoir l'id généré) |
| `db.delete(obj)` | Marque pour suppression |
| `db.query(Model).filter(...).first()` | SELECT ... WHERE ... LIMIT 1 |
| `db.query(Model).offset(n).limit(k).all()` | Pagination |

---

## 7. routers/wine_router.py — Router avec Injection BDD

```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from models.wine_models import Wine, WineCreate, WineUpdate
from services.wine_service import WineService
from database.connection import get_db

router = APIRouter()
wine_service = WineService()

@router.post("/wines/", response_model=Wine, status_code=201)
async def create_wine(wine: WineCreate, db: Session = Depends(get_db)):
    """
    db est injecté automatiquement par Depends(get_db)
    Le router ne connaît pas SQLAlchemy, il délègue au service
    """
    try:
        return await wine_service.create_wine(db, wine)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wines/", response_model=List[Wine])
async def read_wines(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        return await wine_service.get_wines(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wines/{wine_id}", response_model=Wine)
async def read_wine(wine_id: int, db: Session = Depends(get_db)):
    wine = await wine_service.get_wine(db, wine_id)
    if wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return wine

@router.put("/wines/{wine_id}", response_model=Wine)
async def update_wine(wine_id: int, wine: WineUpdate, db: Session = Depends(get_db)):
    updated = await wine_service.update_wine(db, wine_id, wine)
    if updated is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return updated

@router.delete("/wines/{wine_id}")
async def delete_wine(wine_id: int, db: Session = Depends(get_db)):
    deleted = await wine_service.delete_wine(db, wine_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return {"detail": "Wine deleted"}
```

---

## 8. Initialisation de la BDD au démarrage

```python
# main.py
from fastapi import FastAPI
from database.connection import engine, Base
from models.wine_models import WineORM  # Important : importer pour que Base connaisse le modèle

# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wine Quality CRUD API")
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(wine_router, prefix="", tags=["Wines"])
```

**`Base.metadata.create_all(bind=engine)` :**  
→ Compare les modèles ORM avec les tables existantes et crée ce qui manque (ne supprime pas les données existantes).

---

## 9. COMPARAISON TP2 vs TP3

| Aspect | TP2 | TP3 |
|--------|-----|-----|
| Stockage | CSV (pandas) | SQLite (SQLAlchemy ORM) |
| Architecture | 2 couches (router + logique mélangée) | 3 couches (router → service → BDD) |
| Modèles Pydantic | Un seul `WineData` | Trois : `WineCreate`, `WineUpdate`, `Wine` |
| Persistance | Fichier CSV | Base de données relationnelle |
| Transactions | Pas de transactions | `commit()` / `rollback()` |
| Session BDD | Pas de session | `Depends(get_db)` → session injectée |

---

## 10. QUESTIONS D'ORAL POSSIBLES SUR CE TP

**Q : Pourquoi utiliser SQLAlchemy plutôt qu'un CSV ?**
> Une BDD relationnelle est **ACID** (Atomicité, Cohérence, Isolation, Durabilité). Un CSV n'a pas de transactions — si deux utilisateurs modifient en même temps, les données peuvent se corrompre. SQLAlchemy garantit la cohérence via des sessions et des commits.

**Q : Qu'est-ce que `yield db` dans `get_db()` ?**
> `yield` transforme la fonction en générateur. FastAPI exécute le code avant `yield` (ouvrir la session), injecte la session dans la route, exécute la route, puis continue après `yield` dans le bloc `finally` (fermer la session). Cela garantit que la session est **toujours fermée**, même si la route lève une exception.

**Q : Pourquoi `db.refresh(db_wine)` après `db.add()` + `db.commit()` ?**
> Après `commit()`, SQLAlchemy met à jour son cache interne mais l'objet Python `db_wine` n'a pas encore l'id généré par la BDD. `refresh()` recharge l'objet depuis la BDD pour qu'il ait les valeurs finales (notamment l'id auto-incrémenté).

**Q : Différence entre `WineCreate` et `WineUpdate` ?**
> `WineCreate` : tous les champs obligatoires (sauf id, généré par BDD). `WineUpdate` : tous les champs `Optional` → on peut modifier un seul champ sans envoyer tous les autres. `model_dump(exclude_unset=True)` ne retourne que les champs explicitement fournis.

**Q : Qu'est-ce que `from_attributes = True` dans la classe Config ?**
> Pydantic v2 : permet de créer un objet Pydantic depuis un objet ORM (SQLAlchemy). Sans ça, Pydantic ne sait pas lire les attributs d'un objet non-dictionnaire. Ancien nom : `orm_mode = True` (Pydantic v1).
