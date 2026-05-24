# FICHE TP1 — Pandas + Première API FastAPI (Wine Quality Prediction)

> **Séance :** 05 novembre | **Niveau :** Introduction  
> **Objectif TP :** Explorer un dataset avec Pandas, puis créer une API FastAPI qui sert un modèle ML prédictif de qualité de vin

---

## 1. CONTEXTE DU TP — Ce qui était demandé

### Partie A — Exploration Pandas (Video Game Market)
Le dataset : `vgsales.xlsx` (ventes de jeux vidéo mondiales)

Tâches demandées :
- Charger le dataset
- Stats sur les ventes mondiales (min/max/médiane/moyenne) par éditeur et par console
- Combien de jeux possède chaque éditeur ?
- Groupage : ventes mondiales totales par genre (top 5)
- Moyenne des ventes globales pour la PS4
- L'éditeur avec les meilleures ventes globales en 2010 ? De tout temps ?
- Les jeux les plus vendus par zone géographique
- Comparer les ventes de 1985 à aujourd'hui par périodes de 5 ans
- Supprimer les jeux sans ventes globales

### Partie B — API FastAPI (Wine Quality Prediction)
Créer une API FastAPI avec un modèle ML (Random Forest / Gradient Boosting) entraîné sur le dataset WineQT.csv :

| Route | Description |
|-------|-------------|
| `POST /api/predict` | Prédire la qualité d'un vin (note /10) depuis les caractéristiques |
| `GET /api/predict` | Générer les caractéristiques du "vin parfait" |
| `GET /api/model` | Retourner le modèle sérialisé (fichier .pkl) |
| `GET /api/model/description` | Infos sur le modèle : paramètres, métriques de performance |
| `PUT /api/model` | Ajouter un vin au dataset d'entraînement |
| `POST /api/model/retrain` | Réentraîner le modèle (en tenant compte des données ajoutées) |

---

## 2. CONCEPTS PANDAS — Méthodes clés à connaître

### Charger un dataset
```python
import pandas as pd

# Depuis Excel
df = pd.read_excel("vgsales.xlsx")

# Depuis CSV
df = pd.read_csv("WineQT.csv")

# Voir les premières lignes
df.head()
df.shape  # (nb_lignes, nb_colonnes)
df.info()  # types des colonnes
df.describe()  # statistiques de base
```

### Statistiques groupées — .groupby()
```python
# Stats par éditeur
publisher_stats = df.groupby("Publisher")["Global_Sales"].agg(['min', 'max', 'median', 'mean'])

# Ventes totales par genre → top 5
genre_sales = df.groupby("Genre")["Global_Sales"].sum().sort_values(ascending=False).head(5)

# Meilleur éditeur en 2010
best_2010 = df[df["Year"] == 2010].groupby("Publisher")["Global_Sales"].sum().idxmax()

# Ventes par zone géographique (top jeux)
zones = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
for zone in zones:
    print(f"\nTop jeux {zone} :")
    print(df.nlargest(5, zone)[["Name", "Publisher", zone]])
```

### Filtrage et nettoyage
```python
# Supprimer les jeux sans ventes globales
df = df[df["Global_Sales"] > 0]
print(f"Jeux restants : {len(df)}")

# Ventes PS4
ps4_mean = df[df["Platform"] == "PS4"]["Global_Sales"].mean()
```

### Regrouper par périodes de 5 ans
```python
# Créer des bins de 5 ans
df["Period"] = pd.cut(df["Year"], bins=range(1985, 2025, 5), labels=[f"{y}-{y+4}" for y in range(1985, 2020, 5)])
period_sales = df.groupby("Period")["Global_Sales"].sum().sort_values(ascending=False)
print("5 années les plus rentables :")
print(period_sales.head(5))
```

### Méthode IQR — Détection d'outliers
```python
Q1 = df["Global_Sales"].quantile(0.25)
Q3 = df["Global_Sales"].quantile(0.75)
IQR = Q3 - Q1

# Un outlier est > Q3 + 1.5*IQR ou < Q1 - 1.5*IQR
upper_bound = Q3 + 1.5 * IQR
lower_bound = Q1 - 1.5 * IQR

outliers_high = df[df["Global_Sales"] > upper_bound]
outliers_low = df[df["Global_Sales"] < lower_bound]

print(f"Total outliers : {len(outliers_high) + len(outliers_low)}")
print(f"Au dessus : {len(outliers_high)}, En dessous : {len(outliers_low)}")
print("Top 5 outliers :")
print(outliers_high.nlargest(5, "Global_Sales")[["Name", "Publisher", "Global_Sales"]])
```

---

## 3. API FASTAPI — Structure du projet

```
wine_quality_prediction/
├── main.py          ← API FastAPI
├── model.py         ← Entraînement, sauvegarde, chargement
├── data/
│   └── WineQT.csv   ← Dataset de base
└── models_storage/
    └── wine_model.pkl  ← Modèle persisté
```

---

## 4. LE MODÈLE ML — Concepts clés

### Colonnes du dataset WineQT.csv (caractéristiques d'un vin)
```
fixed_acidity, volatile_acidity, citric_acid, residual_sugar, 
chlorides, free_sulfur_dioxide, total_sulfur_dioxide, density, 
pH, sulphates, alcohol → quality (target : 3 à 8)
```

### Entraîner et sauvegarder le modèle
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

MODEL_PATH = "models_storage/wine_model.pkl"

def train_model():
    df = pd.read_csv("data/WineQT.csv")
    
    # Séparer features / target
    X = df.drop("quality", axis=1)
    y = df["quality"]
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Entraîner
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Évaluer
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Sauvegarder sur le disque (persistance !)
    os.makedirs("models_storage", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    
    return model, accuracy

def load_model():
    """Charger le modèle depuis le disque — pas de réentraînement au démarrage"""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    else:
        model, _ = train_model()
        return model
```

### Pourquoi `joblib.dump` ? — Point important à l'oral
> Le modèle ne doit **pas** être réentraîné à chaque démarrage. On le **persiste sur le disque** avec `joblib.dump()`, et on le charge avec `joblib.load()`. Cela évite de perdre des secondes précieuses à chaque redémarrage.

---

## 5. L'API FASTAPI — Code complet

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
import joblib
import os

app = FastAPI(title="Wine Quality Prediction API")

MODEL_PATH = "models_storage/wine_model.pkl"
DATA_PATH = "data/WineQT.csv"

# Charger le modèle au démarrage (pas réentraîner !)
model = load_model()

# ===== MODÈLE DE DONNÉES =====
class WineFeatures(BaseModel):
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

class WineWithQuality(WineFeatures):
    quality: int  # Pour ajouter un vin au dataset

# ===== ROUTES =====

@app.post("/api/predict")
def predict_quality(wine: WineFeatures):
    """Prédit la qualité du vin (note entre 3 et 8)"""
    features = [[
        wine.fixed_acidity, wine.volatile_acidity, wine.citric_acid,
        wine.residual_sugar, wine.chlorides, wine.free_sulfur_dioxide,
        wine.total_sulfur_dioxide, wine.density, wine.pH,
        wine.sulphates, wine.alcohol
    ]]
    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    
    return {
        "predicted_quality": int(prediction),
        "confidence": float(max(probabilities)),
        "scale": "3-8"
    }

@app.get("/api/predict")
def perfect_wine():
    """Génère les caractéristiques du 'vin parfait' (qualité maximale)"""
    df = pd.read_csv(DATA_PATH)
    
    # Vin parfait = vins de qualité maximale, moyenne de leurs caractéristiques
    best_wines = df[df["quality"] == df["quality"].max()]
    perfect = best_wines.mean().to_dict()
    
    features = {k: v for k, v in perfect.items() if k != "quality"}
    
    return {
        "perfect_wine_features": features,
        "predicted_quality": int(perfect.get("quality", 8)),
        "message": "Statistiquement parfait, probablement inexistant"
    }

@app.get("/api/model")
def get_model():
    """Retourne le modèle sérialisé (.pkl) en téléchargement"""
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=404, detail="Model not found")
    return FileResponse(MODEL_PATH, filename="wine_model.pkl")

@app.get("/api/model/description")
def model_description():
    """Informations sur le modèle : paramètres, métriques"""
    params = model.get_params()
    
    # Recalculer les métriques sur le test set
    df = pd.read_csv(DATA_PATH)
    X = df.drop("quality", axis=1)
    y = df["quality"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    from sklearn.metrics import accuracy_score, classification_report
    y_pred = model.predict(X_test)
    
    return {
        "model_type": "RandomForestClassifier",
        "parameters": params,
        "performance": {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "test_size": len(y_test),
            "train_size": len(y_train)
        },
        "feature_importance": dict(zip(X.columns, model.feature_importances_.tolist()))
    }

@app.put("/api/model")
def add_wine(wine: WineWithQuality):
    """Ajoute un vin au dataset (pour enrichissement futur)"""
    df = pd.read_csv(DATA_PATH)
    new_row = pd.DataFrame([wine.model_dump()])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)
    
    return {
        "message": "Wine added to dataset",
        "new_total": len(df),
        "note": "Use POST /api/model/retrain to apply changes"
    }

@app.post("/api/model/retrain")
def retrain():
    """Réentraîne le modèle avec les nouvelles données"""
    global model
    model, accuracy = train_model()  # Réentraîne et sauvegarde
    
    return {
        "message": "Model retrained successfully",
        "accuracy": accuracy,
        "model_saved": MODEL_PATH
    }
```

---

## 6. STRUCTURE MULTI-FICHIERS — Architecture propre

Le TP exigeait une structure propre. Structure idéale :

```python
# main.py — Point d'entrée, inclut les routeurs
from fastapi import FastAPI
from routers.predict_router import router as predict_router
from routers.model_router import router as model_router

app = FastAPI()
app.include_router(predict_router, prefix="/api/predict", tags=["Predictions"])
app.include_router(model_router, prefix="/api/model", tags=["Model"])
```

---

## 7. COMMANDES CLÉS À RETENIR

```bash
# Lancer l'API
uvicorn main:app --reload --port 8000

# Tester la prédiction
curl -X POST "http://localhost:8000/api/predict" \
  -H "Content-Type: application/json" \
  -d '{"fixed_acidity": 7.4, "volatile_acidity": 0.7, "citric_acid": 0.0,
       "residual_sugar": 1.9, "chlorides": 0.076, "free_sulfur_dioxide": 11.0,
       "total_sulfur_dioxide": 34.0, "density": 0.9978, "pH": 3.51,
       "sulphates": 0.56, "alcohol": 9.4}'

# Documentation auto-générée
http://localhost:8000/docs
```

---

## 8. QUESTIONS D'ORAL POSSIBLES SUR CE TP

**Q : Pourquoi le modèle ne doit-il pas être réentraîné à chaque démarrage ?**
> Car le réentraînement prend du temps (calcul intensif) et consomme des ressources. On entraîne une fois, on sauvegarde avec `joblib.dump()`, puis on charge avec `joblib.load()` à chaque démarrage. → C'est la **persistance du modèle**.

**Q : Différence entre `POST /api/predict` et `GET /api/predict` ?**
> `POST` = on envoie les caractéristiques d'un vin et on obtient sa note prédite. `GET` = on demande les caractéristiques du "vin parfait" (calculé depuis les vins de qualité max du dataset).

**Q : Qu'est-ce que `predict_proba` ?**
> `model.predict_proba(X)` retourne les probabilités pour chaque classe. Ex: `[0.1, 0.7, 0.2]` pour les qualités 5, 6, 7 → le modèle est à 70% sûr que la qualité est 6. `predict()` retourne juste la classe la plus probable.

**Q : Pourquoi `train_test_split` ?**
> Pour évaluer honnêtement les performances du modèle sur des données qu'il n'a jamais vues. Si on testait sur les données d'entraînement, l'accuracy serait artificiellement haute (overfitting).

**Q : Qu'est-ce que `feature_importances_` ?**
> Attribut du RandomForestClassifier qui dit quelles features ont le plus influencé les prédictions. Ex : `alcohol` souvent la plus importante pour la qualité du vin.
