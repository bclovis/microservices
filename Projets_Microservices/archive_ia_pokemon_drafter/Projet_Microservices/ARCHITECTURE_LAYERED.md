# Pokemon Drafter - Architecture Layered

## 🏗️ Architecture

Ce projet utilise une **architecture en couches (layered architecture)** pour les backends Blue et Red, suivant les principes SOLID et de séparation des responsabilités.

```
backend-{blue|red}/
├── main.py                 # Point d'entrée FastAPI
│
├── api/                    # Couche API (Routes)
│   ├── routes/
│   │   ├── auth_routes.py       # Routes d'authentification
│   │   ├── team_routes.py       # Routes de gestion d'équipes
│   │   ├── game_routes.py       # Routes de duels
│   │   └── pokemon_routes.py    # Routes Pokémon
│   └── dependencies.py          # Dépendances communes
│
├── core/                   # Configuration & Infrastructure
│   ├── config.py               # Variables d'environnement
│   ├── security.py             # JWT, hash, authentification
│   ├── kafka.py                # Producer/Consumer Kafka
│   └── logging.py              # Configuration logs
│
├── models/                 # ORM (SQLAlchemy)
│   └── database.py             # Modèles DB (User, Team, Duel, etc.)
│
├── schemas/                # DTOs (Pydantic)
│   ├── user_schema.py          # Schémas utilisateur
│   ├── team_schema.py          # Schémas équipe
│   ├── game_schema.py          # Schémas duel
│   └── pokemon_schema.py       # Schémas Pokémon
│
├── repositories/           # Accès données
│   ├── database.py             # Gestion session DB
│   ├── user_repository.py      # CRUD utilisateurs
│   ├── team_repository.py      # CRUD équipes
│   ├── game_repository.py      # CRUD duels
│   └── pokemon_repository.py   # Cache Pokémon
│
├── services/               # Logique métier
│   ├── auth_service.py         # Authentification
│   ├── team_service.py         # Gestion équipes
│   ├── game_service.py         # Logique duels
│   └── pokemon_service.py      # API Pokémon
│
├── consumers/              # Kafka listeners
│   └── game_events.py          # Événements de jeu
│
├── tests/                  # Tests
│   ├── unit/                   # Tests unitaires
│   └── integration/            # Tests d'intégration
│
└── utils/                  # Utilitaires
    ├── constants.py            # Constantes (types, statuts)
    └── helpers.py              # Fonctions utilitaires
```

## 🎯 Principes

### 1. **Séparation des responsabilités**
- **Routes** : Gèrent HTTP, validation des entrées
- **Services** : Contiennent la logique métier
- **Repositories** : Accès aux données uniquement
- **Models** : Structure des données DB
- **Schemas** : Validation et sérialisation

### 2. **Flux de données**
```
Request → Route → Service → Repository → Database
                    ↓
                 Kafka/API externe
```

### 3. **Avantages**
- ✅ **Maintenabilité** : Code organisé et facile à modifier
- ✅ **Testabilité** : Chaque couche testable indépendamment
- ✅ **Scalabilité** : Ajout de fonctionnalités sans tout casser
- ✅ **Collaboration** : Équipe peut travailler sur différentes couches

## 🚀 Utilisation

### Installation
```bash
cd backend-blue  # ou backend-red
pip install -r requirements.txt
```

### Lancement
```bash
python main.py
```

### Tests
```bash
pytest tests/
```

## 📝 Exemple d'ajout de fonctionnalité

Pour ajouter une nouvelle route `/teams/{id}/statistics`:

1. **Schema** (`schemas/team_schema.py`)
```python
class TeamStatistics(BaseModel):
    total_duels: int
    wins: int
    losses: int
```

2. **Repository** (`repositories/team_repository.py`)
```python
def get_team_statistics(self, team_id: int) -> dict:
    # Query database for team stats
    pass
```

3. **Service** (`services/team_service.py`)
```python
def get_team_stats(self, team_id: int, user_id: int) -> TeamStatistics:
    # Business logic
    stats = self.team_repo.get_team_statistics(team_id)
    return TeamStatistics(**stats)
```

4. **Route** (`api/routes/team_routes.py`)
```python
@router.get("/{team_id}/statistics", response_model=TeamStatistics)
async def get_team_statistics(team_id: int, ...):
    return team_service.get_team_stats(team_id, user_id)
```

## 🔑 Points clés du projet

### Calcul d'avantage de types
Implémenté dans `utils/helpers.py::calculate_type_advantage()`
```
F(A) = 1*(W/Y)*(W/Z) + 1*(X/Y)*(X/Z)
F(B) = 1*(Y/W)*(Y/X) + 1*(Z/W)*(Z/X)
```

### Communication Kafka
- **Duels** : Événements de création, tours, résultats
- **Chat** : Messages temps réel
- **Notifications** : Alertes utilisateurs

### Sécurité
- JWT pour authentification
- Bcrypt pour mots de passe
- Validation équipe (RED/BLUE)

## 🐛 Debug

Les logs sont formatés avec le tag `[BLUE]` ou `[RED]` pour faciliter le débogage.

```
2024-01-26 10:30:45 - uvicorn - INFO - [BLUE] - Application startup complete
```

## 🎨 Easter Eggs
Cherchez "dino" dans le code ! 🦕
