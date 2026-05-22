# Wine Quality API

API REST avec FastAPI pour gérer un dataset de vins avec authentification JWT.

## Fichiers

- `main.py` : point d'entrée de l'application
- `config.py` : configuration JWT
- `models.py` : modèles utilisateurs et vins
- `auth.py` : gestion des tokens
- `dependencies.py` : dépendances FastAPI
- `routers/auth_router.py` : endpoints d'authentification
- `routers/wine_router.py` : endpoints CRUD vins

## Installation

```bash
pip install -r requirements.txt
```

## Démarrage

```bash
python main.py
```

## Utilisateurs

- betsaleel : 123
- clovis : password123
- admin : admin

## Tests

```bash
# Login
curl -X POST "http://127.0.0.1:8000/auth/token" -d "username=peio&password=123"

# Voir les vins
curl "http://127.0.0.1:8000/wines/"

# Créer un vin (avec token)
curl -X POST "http://127.0.0.1:8000/wines/" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"fixed_acidity":7.0,"volatile_acidity":0.27,"citric_acid":0.36,"residual_sugar":20.7,"chlorides":0.045,"free_sulfur_dioxide":45.0,"total_sulfur_dioxide":170.0,"density":1.001,"pH":3.0,"sulphates":0.45,"alcohol":8.8,"quality":6}'
```
