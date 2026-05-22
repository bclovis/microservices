# Guide de Contribution - Pokemon Drafter

Merci de votre intérêt pour contribuer à Pokemon Drafter ! 🎮

## 📋 Code of Conduct

- Respectez les autres contributeurs
- Soyez constructif dans vos commentaires
- Pas de langage inapproprié
- Concentrez-vous sur l'amélioration du projet

## 🚀 Comment Contribuer

### 1. Fork et Clone

```bash
# Fork le projet sur GitHub
# Puis clone votre fork
git clone https://github.com/VOTRE_USERNAME/Projet_Microservices.git
cd Projet_Microservices

# Ajouter le repo original comme remote
git remote add upstream https://github.com/bclovis/Projet_Microservices.git
```

### 2. Créer une Branche

```bash
# Synchroniser avec le repo principal
git fetch upstream
git checkout main
git merge upstream/main

# Créer une branche pour votre fonctionnalité
git checkout -b feature/ma-fonctionnalite
# ou
git checkout -b fix/correction-bug
```

### 3. Développer

#### Installation
```bash
# Backend
make install-backend

# Frontend
make install-frontend

# Environnement de dev
make dev-up
```

#### Convention de Code

**Python (Backend)**
- Style: PEP 8
- Variables: snake_case
- Fonctions: snake_case
- Classes: PascalCase
- Constantes: UPPER_SNAKE_CASE
- Type hints obligatoires
- Docstrings pour toutes les fonctions

Exemple:
```python
def calculate_advantage(
    pokemon_a_type_primary: str,
    pokemon_a_type_secondary: Optional[str]
) -> tuple[float, float]:
    """
    Calculate type advantage between two Pokemon.
    
    Args:
        pokemon_a_type_primary: Primary type of Pokemon A
        pokemon_a_type_secondary: Secondary type of Pokemon A
        
    Returns:
        Tuple of (advantage_a, advantage_b)
    """
    # Implementation
    pass
```

**TypeScript (Frontend)**
- Style: Angular Style Guide
- Variables: snake_case (requis par le projet)
- Fonctions: snake_case
- Classes: PascalCase
- Interfaces: PascalCase avec préfixe I
- Composants: kebab-case pour les sélecteurs

Exemple:
```typescript
interface IPokemon {
  pokemon_id: number;
  pokemon_name: string;
  type_primary: string;
}

class TeamService {
  get_user_teams(): Observable<Team[]> {
    // Implementation
  }
}
```

#### Tests

**Backend**
```bash
cd backend-red
pytest tests/
pytest --cov=. tests/  # Avec couverture
```

**Frontend**
```bash
cd frontend-red
npm test
npm test -- --code-coverage
```

Tous les tests doivent passer avant de soumettre une PR.

### 4. Commit

#### Format des Messages

```
<type>(<scope>): <description>

[corps optionnel]

[footer optionnel]
```

**Types:**
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage (pas de changement de code)
- `refactor`: Refactorisation
- `test`: Ajout de tests
- `chore`: Tâches de maintenance

**Exemples:**
```bash
git commit -m "feat(backend): add duel creation endpoint"
git commit -m "fix(frontend): correct team display bug"
git commit -m "docs: update architecture diagram"
git commit -m "test(backend): add tests for advantage calculation"
```

### 5. Push et Pull Request

```bash
# Push vers votre fork
git push origin feature/ma-fonctionnalite

# Créer une PR sur GitHub
```

#### Template Pull Request

```markdown
## Description
[Description claire de ce que fait la PR]

## Type de changement
- [ ] Bug fix
- [ ] Nouvelle fonctionnalité
- [ ] Breaking change
- [ ] Documentation

## Checklist
- [ ] Mon code suit le style du projet
- [ ] J'ai commenté les parties complexes
- [ ] J'ai mis à jour la documentation
- [ ] J'ai ajouté des tests
- [ ] Tous les tests passent
- [ ] Pas de conflits avec main

## Tests effectués
[Description des tests]

## Screenshots
[Si applicable]
```

## 🐛 Signaler un Bug

### Template Issue Bug

```markdown
**Description du bug**
[Description claire et concise]

**Étapes pour reproduire**
1. Aller sur '...'
2. Cliquer sur '...'
3. Voir l'erreur

**Comportement attendu**
[Ce qui devrait se passer]

**Comportement actuel**
[Ce qui se passe réellement]

**Screenshots**
[Si applicable]

**Environnement:**
- OS: [e.g. Ubuntu 22.04]
- Navigateur: [e.g. Chrome 120]
- Version: [e.g. 1.0.0]

**Logs/Erreurs**
[Copier les logs pertinents]

**Contexte additionnel**
[Informations supplémentaires]
```

## 💡 Proposer une Fonctionnalité

### Template Issue Feature

```markdown
**Problème à résoudre**
[Quel problème cette fonctionnalité résout-elle?]

**Solution proposée**
[Description de la fonctionnalité]

**Alternatives considérées**
[Autres approches possibles]

**Contexte additionnel**
[Mockups, exemples, etc.]
```

## 🏗️ Domaines de Contribution

### Backend
- [ ] Compléter endpoints duels
- [ ] Intégrer Kafka pour temps réel
- [ ] Améliorer système de recommandation
- [ ] Ajouter validation avancée
- [ ] Optimiser requêtes DB
- [ ] Augmenter couverture tests

### Frontend
- [ ] Créer page de duel complète
- [ ] Implémenter chat temps réel
- [ ] Améliorer UX/UI
- [ ] Ajouter animations
- [ ] Responsive design
- [ ] Composants réutilisables

### DevOps
- [ ] CI/CD pipeline
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Logging centralisé
- [ ] Backup automatique
- [ ] Documentation déploiement
- [ ] Scripts d'automatisation

### Documentation
- [ ] Guide utilisateur
- [ ] Tutoriels vidéo
- [ ] API documentation
- [ ] Diagrammes
- [ ] Exemples de code
- [ ] Troubleshooting guide

### Tests
- [ ] Tests unitaires backend
- [ ] Tests intégration
- [ ] Tests end-to-end
- [ ] Tests de charge
- [ ] Tests sécurité

## 🎯 Bonnes Pratiques

### Code Quality

1. **DRY (Don't Repeat Yourself)**
   - Extraire le code répété en fonctions
   - Utiliser l'héritage judicieusement

2. **KISS (Keep It Simple, Stupid)**
   - Solutions simples préférées
   - Code lisible > code "clever"

3. **YAGNI (You Ain't Gonna Need It)**
   - N'implémenter que ce qui est nécessaire
   - Pas de sur-engineering

4. **Single Responsibility**
   - Une fonction = une responsabilité
   - Classes cohésives

### Git

1. **Commits fréquents**
   - Petits commits atomiques
   - Facilite le review et le revert

2. **Messages descriptifs**
   - Expliquer le "pourquoi"
   - Référencer les issues

3. **Branches courtes**
   - Feature branches pas trop longues
   - Merge fréquemment

### Review

1. **Code Review**
   - Reviewer le code des autres
   - Être constructif
   - Apprendre des reviews

2. **Répondre aux commentaires**
   - Traiter tous les commentaires
   - Expliquer vos choix

## 📝 Checklist Avant PR

- [ ] Code compilé/build sans erreur
- [ ] Tests passent (make test)
- [ ] Linting OK
- [ ] Documentation mise à jour
- [ ] Pas de console.log/print debug
- [ ] Variables en snake_case
- [ ] Commentaires en français
- [ ] Pas de secrets committés
- [ ] Branch synchronisée avec main

## 🎓 Ressources

### Documentation Projet
- [README](README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Guide Dev](docs/GUIDE_DEVELOPPEMENT.md)
- [Quick Start](QUICKSTART.md)

### Technologies
- [FastAPI](https://fastapi.tiangolo.com/)
- [Angular](https://angular.io/docs)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Docker](https://docs.docker.com/)
- [Kubernetes](https://kubernetes.io/docs/)

### Outils
- [PEP 8](https://pep8.org/)
- [Angular Style Guide](https://angular.io/guide/styleguide)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 🏆 Contributors

Un grand merci à tous les contributeurs ! 🎉

<!-- ALL-CONTRIBUTORS-LIST:START -->
<!-- Sera rempli automatiquement -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## 📧 Questions?

- Ouvrir une [Issue](https://github.com/bclovis/Projet_Microservices/issues)
- Discussion sur [GitHub Discussions](https://github.com/bclovis/Projet_Microservices/discussions)
- Email: dev@pokemon-drafter.local

---

**Merci de contribuer à Pokemon Drafter !** 🚀

N'oubliez pas: même les petites contributions comptent. Documentation, tests, corrections de typos... tout est apprécié ! ❤️
