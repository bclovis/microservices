# Guide de Développement - Pokemon Drafter

## Prérequis

- Docker >= 20.10
- Kubernetes (minikube recommandé) >= 1.25
- kubectl >= 1.25
- Node.js >= 18 (pour développement frontend)
- Python >= 3.11 (pour développement backend)

## Installation Environnement de Développement

### 1. Développement Local avec Docker Compose

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose down
```

Accès aux services:
- Frontend Red: http://localhost:4201
- Frontend Blue: http://localhost:4202
- Backend Red: http://localhost:8001
- Backend Blue: http://localhost:8002
- Recommendation: http://localhost:8004
- Encryption: http://localhost:8003
- API Gateway: http://localhost:8080

### 2. Développement Backend

```bash
cd backend-red

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt

# Lancer serveur de dev
uvicorn main:app --reload --port 8001

# Lancer tests
pytest
```

### 3. Développement Frontend

```bash
cd frontend-red

# Installer dépendances
npm install

# Lancer serveur de dev
ng serve --port 4201

# Lancer tests
npm test

# Build production
ng build --configuration production
```

## Structure des Projets

### Backend (FastAPI)

```
backend-red/
├── main.py              # Application principale
├── requirements.txt     # Dépendances Python
├── Dockerfile          # Image Docker
├── models/             # Modèles Pydantic (à créer)
├── routes/             # Routes API (à créer)
├── services/           # Logique métier (à créer)
└── tests/              # Tests pytest (à créer)
```

### Frontend (Angular)

```
frontend-red/
├── src/
│   ├── app/
│   │   ├── components/      # Composants UI
│   │   ├── services/        # Services HTTP
│   │   ├── models/          # Interfaces TypeScript
│   │   └── guards/          # Route guards
│   ├── assets/             # Images, styles
│   └── environments/       # Config environnement
├── package.json
├── Dockerfile
└── nginx.conf
```

## Workflow de Développement

### 1. Créer une branche

```bash
git checkout -b feature/nom-fonctionnalite
```

### 2. Développer

- Écrire le code
- Ajouter des tests
- Vérifier le style (linting)

### 3. Tester

```bash
# Backend
cd backend-red
pytest

# Frontend
cd frontend-red
npm test
```

### 4. Commit

```bash
git add .
git commit -m "feat: description de la fonctionnalité"
```

Convention de commit:
- `feat:` nouvelle fonctionnalité
- `fix:` correction de bug
- `docs:` documentation
- `test:` ajout de tests
- `refactor:` refactorisation

### 5. Push et Pull Request

```bash
git push origin feature/nom-fonctionnalite
```

Créer une PR sur GitHub avec:
- Description claire
- Screenshots si UI
- Tests passants

## Ajout de Nouvelles Fonctionnalités

### Ajouter un Endpoint Backend

1. Créer la route dans `routes/`
2. Implémenter la logique dans `services/`
3. Ajouter le modèle dans `models/`
4. Écrire les tests dans `tests/`
5. Documenter dans docstring

Exemple:
```python
@app.get("/pokemon/{pokemon_id}")
async def get_pokemon(pokemon_id: int):
    """
    Get Pokemon details
    
    Args:
        pokemon_id: Pokemon ID from PokeAPI
        
    Returns:
        Pokemon object with types, stats, etc.
    """
    # Implementation
```

### Ajouter un Composant Frontend

1. Générer le composant:
```bash
ng generate component components/nom-composant
```

2. Créer le test:
```typescript
describe('NomComposant', () => {
  it('should create', () => {
    // Test code
  });
});
```

3. Ajouter au routing si nécessaire

### Ajouter une Table Database

1. Modifier `database/schema.sql`
2. Ajouter les indexes nécessaires
3. Créer migration si DB existe déjà
4. Mettre à jour les modèles backend

## Debugging

### Backend

```bash
# Logs détaillés
uvicorn main:app --reload --log-level debug

# Debugger Python
import pdb; pdb.set_trace()
```

### Frontend

```bash
# Mode debug Angular
ng serve --configuration development

# Chrome DevTools
# F12 > Sources > Set breakpoints
```

### Kubernetes

```bash
# Voir les pods
kubectl get pods -n pokemon-drafter

# Logs d'un pod
kubectl logs <pod-name> -n pokemon-drafter

# Shell dans un pod
kubectl exec -it <pod-name> -n pokemon-drafter -- /bin/sh

# Décrire un pod
kubectl describe pod <pod-name> -n pokemon-drafter
```

## Variables d'Environnement

### Backend

Créer `.env` dans backend-red/:
```
DATABASE_URL=postgresql://pokemon_user:pokemon_pass123@localhost:5432/pokemon_db
REDIS_URL=redis://localhost:6379
KAFKA_BROKER=localhost:9092
POKEAPI_BASE_URL=https://pokeapi.co/api/v2
ENCRYPTION_SERVICE_URL=http://localhost:8003
```

### Frontend

Créer `src/environments/environment.development.ts`:
```typescript
export const environment = {
  production: false,
  api_url: 'http://localhost:8001',
  ws_url: 'ws://localhost:9092'
};
```

## Bonnes Pratiques

### Code

1. **Snake_case**: Toutes les variables en snake_case
2. **Type hints**: Toujours typer (Python et TypeScript)
3. **Docstrings**: Documenter toutes les fonctions
4. **DRY**: Ne pas se répéter
5. **KISS**: Keep It Simple

### Git

1. **Commits fréquents**: Petits commits réguliers
2. **Messages clairs**: Décrire le "pourquoi"
3. **Branches**: Une par fonctionnalité
4. **Revue**: Toujours faire relire le code

### Tests

1. **Coverage**: Viser 80%+ de couverture
2. **Isolation**: Tests indépendants
3. **Nommage**: `test_should_do_something_when_condition`
4. **Assertions**: Une assertion principale par test

## Troubleshooting

### "Cannot connect to database"

```bash
# Vérifier que PostgreSQL est lancé
docker-compose ps

# Vérifier les logs
docker-compose logs database

# Recréer le conteneur
docker-compose down database
docker-compose up -d database
```

### "Redis connection failed"

```bash
# Redémarrer Redis
docker-compose restart cache-service
```

### "Kafka timeout"

```bash
# Kafka prend du temps à démarrer
# Attendre 30-60 secondes

# Vérifier les logs
docker-compose logs kafka
```

### "Angular build fails"

```bash
# Nettoyer et réinstaller
rm -rf node_modules package-lock.json
npm install

# Nettoyer le cache Angular
rm -rf .angular
```

## Performance

### Backend

1. **Indexes DB**: Créer pour les colonnes souvent requêtées
2. **Cache Redis**: Utiliser pour les données fréquentes
3. **Async/await**: Toujours en async pour I/O
4. **Batch queries**: Grouper les requêtes DB

### Frontend

1. **Lazy loading**: Charger modules à la demande
2. **OnPush strategy**: Pour les composants statiques
3. **TrackBy**: Dans les *ngFor
4. **Unsubscribe**: Toujours se désabonner des Observables

## Ressources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Angular Docs](https://angular.io/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [PokeAPI](https://pokeapi.co/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
