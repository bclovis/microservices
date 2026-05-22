# Analyse du Projet Pokemon Drafter

## 1. Contexte et Objectifs

Le projet Pokemon Drafter est une application de duel en ligne basée sur un système de combat Pokemon utilisant les avantages de types. L'objectif est de créer une plateforme compétitive où deux équipes (Rouge et Bleue) s'affrontent en utilisant des stratégies basées sur la composition d'équipes.

## 2. Choix Architecturaux

### 2.1 Architecture Microservices

**Choix**: Adoption d'une architecture microservices complète

**Justification**:
- **Isolation**: Les équipes Rouge et Bleue ont des backends complètement séparés, garantissant l'intégrité des données
- **Scalabilité**: Chaque service peut être mis à l'échelle indépendamment selon la charge
- **Maintenabilité**: Code modulaire et responsabilités clairement définies
- **Résilience**: La défaillance d'un service n'affecte pas les autres
- **Développement parallèle**: Équipe peut travailler sur différents services simultanément

**Alternative considérée**: Monolithe
- Rejetée car ne permettrait pas l'isolation requise entre équipes Rouge et Bleue
- Moins flexible pour le scaling

### 2.2 Séparation Frontend Rouge/Bleu

**Choix**: Deux applications Angular distinctes

**Justification**:
- **Isolation de l'interface**: Chaque équipe a une expérience visuelle distincte
- **Sécurité**: Impossible de voir les données de l'équipe adverse
- **Personnalisation**: Thèmes et fonctionnalités spécifiques par équipe
- **Déploiement indépendant**: Possibilité de déployer des mises à jour par équipe

### 2.3 Communication Inter-Backend

**Choix**: Kafka + Service de chiffrement

**Justification**:
- **Asynchrone**: Les backends ne se bloquent pas mutuellement
- **Sécurité**: Toutes les communications sont chiffrées
- **Scalabilité**: Kafka gère facilement de nombreux messages
- **Audit**: Toutes les communications sont traçables
- **Temps réel**: Support natif du streaming pour le chat et les duels

**Alternative considérée**: API REST directe
- Rejetée car créerait un couplage fort entre backends
- Moins adaptée au temps réel

### 2.4 Base de Données

**Choix**: PostgreSQL unique avec PersistentVolume

**Justification**:
- **Transactions ACID**: Garantit l'intégrité des duels
- **Relations complexes**: Users, Teams, Duels, Tours
- **Performance**: Indexes optimisés pour les requêtes fréquentes
- **Persistence**: Volume Kubernetes garantit la durabilité
- **Maturité**: Base de données éprouvée et fiable

**Alternative considérée**: Une DB par backend
- Rejetée car complexifierait les duels inter-équipes
- Problèmes de cohérence des données

### 2.5 Cache avec Redis

**Choix**: Redis pour cacher les appels PokeAPI

**Justification**:
- **Performance**: Évite les appels répétés à l'API externe
- **Coût**: Réduit la latence et la charge réseau
- **Disponibilité**: Continue à fonctionner même si PokeAPI est down
- **Simple**: Structure clé-valeur parfaite pour ce cas

## 3. Stack Technique

### 3.1 Backend: FastAPI (Python)

**Justification**:
- **Performance**: Async/await natif, très rapide
- **Développement rapide**: Syntaxe Python claire et concise
- **Documentation auto**: OpenAPI/Swagger intégré
- **Validation**: Pydantic pour validation automatique
- **Type hints**: Code plus sûr et maintenable

**Alternative**: Spring Boot (Java)
- Rejetée car plus verbeux et complexe
- FastAPI mieux adapté pour un développement rapide

### 3.2 Frontend: Angular

**Justification**:
- **Framework complet**: Routing, forms, HTTP intégrés
- **TypeScript**: Type safety et meilleure maintenabilité
- **Testing**: Jasmine/Karma intégrés (requis par le cahier des charges)
- **Performance**: AOT compilation, lazy loading
- **Communauté**: Large écosystème et support

### 3.3 API Gateway: Nginx

**Justification**:
- **Performance**: Extrêmement rapide et léger
- **Fiabilité**: Produit mature et stable
- **Configuration**: Simple pour le reverse proxy
- **Load balancing**: Natif et efficace

### 3.4 Conteneurisation: Docker + Kubernetes

**Justification**:
- **Portabilité**: Fonctionne partout
- **Isolation**: Chaque service dans son conteneur
- **Orchestration**: Kubernetes gère le déploiement automatiquement
- **Scaling**: Réplication facile des services
- **Exigence**: Requis par le cahier des charges

## 4. Algorithme de Calcul d'Avantage

**Formule implémentée**:
```
F(A) = 1*(W/Y)*(W/Z) + 1*(X/Y)*(X/Z)
F(B) = 1*(Y/W)*(Y/X) + 1*(Z/W)*(Z/X)
```

**Choix d'implémentation**:
- Table de correspondance pour les multiplicateurs de types
- Fonction pure sans effets de bord
- Gestion des Pokemon mono-type (type secondaire = type primaire)
- Valeurs par défaut à 1.0 pour types non trouvés

## 5. Engine de Recommandation

**Algorithme**:
1. Analyse de la couverture de types actuelle
2. Identification des faiblesses de l'équipe
3. Scoring des Pokemon candidats:
   - +10 points par faiblesse couverte
   - +5 points par nouveau type offensif
   - -5 points par redondance de type
4. Retour des meilleurs candidats

**Justification**:
- Approche heuristique simple mais efficace
- Équilibre entre couverture et diversité
- Calculable rapidement (important pour UX)

## 6. Sécurité

### 6.1 Authentification

**Choix**: JWT avec Identity Provider (Keycloak prévu)

**Justification**:
- **Stateless**: Pas de session côté serveur
- **Standard**: JWT largement adopté
- **Flexible**: Peut contenir claims personnalisés (team_color, etc.)

### 6.2 Chiffrement Inter-Backend

**Choix**: Service dédié avec Fernet (cryptography)

**Justification**:
- **Isolation**: Logique de chiffrement centralisée
- **Sécurité**: Algorithme symétrique éprouvé
- **Performance**: Plus rapide que asymétrique pour ce cas

## 7. Gestion des Données

### 7.1 Conventions de Nommage

**Choix**: snake_case pour toutes les variables

**Justification**:
- **Cohérence**: Python et PostgreSQL utilisent snake_case
- **Lisibilité**: Plus facile à lire que camelCase
- **Convention**: Standard Python (PEP 8)

### 7.2 Persistence

**Choix**: PersistentVolume Kubernetes

**Justification**:
- **Durabilité**: Données survivent aux redémarrages
- **Exigence**: Requis par le cahier des charges
- **Simplicité**: Configuration Kubernetes standard

## 8. Tests

**Stratégie**:
- **Frontend**: Tests unitaires Jasmine pour tous les composants
- **Backend**: Tests pytest (à implémenter)
- **Intégration**: Tests end-to-end avec déploiement complet

**Justification**:
- **Qualité**: Détecte les bugs tôt
- **Refactoring**: Permet de modifier le code en confiance
- **Documentation**: Les tests servent de documentation

## 9. Choix Non Retenus

### 9.1 GraphQL
- Rejeté car REST suffit pour ce cas
- Ajouterait de la complexité inutile

### 9.2 MongoDB
- Rejeté car relations complexes nécessitent SQL
- PostgreSQL plus adapté

### 9.3 WebSockets directs
- Rejeté au profit de Kafka
- Kafka offre plus de fonctionnalités (replay, persistence, etc.)

## 10. Points d'Amélioration Futurs

1. **Monitoring**: Ajouter Prometheus + Grafana
2. **Tracing**: Jaeger pour distributed tracing
3. **CI/CD**: Pipeline GitHub Actions
4. **Cache distribué**: Passage à Redis Cluster
5. **API Rate Limiting**: Protection contre abus
6. **Backup automatique**: Cron job pour pg_dump

## 11. Conclusion

L'architecture choisie privilégie:
- **Maintenabilité**: Code clair et modulaire
- **Scalabilité**: Services indépendants
- **Sécurité**: Isolation et chiffrement
- **Performance**: Cache et async

Cette approche permet une application robuste et évolutive tout en respectant toutes les contraintes du cahier des charges.
