# S4 — Microservices Redesign

> Cours de Lalanne Raphaël — Séance du 3 décembre  
> Source : `Microservices redesign (1).pdf`  
> Contexte : TP en groupe de 3 à rendre par mail

---

## 1. Objectif du TP

Ce TP est un exercice de **conception**. Il s'agit de prendre un système monolithique existant d'une entreprise réelle et de le décomposer en microservices.

**Exercices couverts :**

| Exercice | Entreprise | Système |
|----------|-----------|---------|
| Ex 1 | **Etsy** | Monolithe PHP d'une marketplace |
| Ex 2 | **Netflix** | Monolithe de location de DVD → streaming |
| Ex 3 | **Shopify** | Monolithe Ruby on Rails d'e-commerce |

---

## 2. Exercice 1 — Le monolithe d'Etsy

### Contexte du cours
> "Etsy est une application initialement développée comme un monolithe PHP, qui est devenu trop lourdement couplé pour soutenir l'afflux de nouveaux clients."

**Le système monolithique d'Etsy gérait :**
- Profils utilisateurs
- Liste des produits
- Recherche
- Recommandations
- Finalisation de commande
- Paiements
- Gestion des stocks

### Tâches demandées
1. Identifier **5 parties** pouvant devenir des microservices indépendants
2. Pour chaque service : sa responsabilité principale + BDD propriétaire ou partagée ?
3. Dessiner le diagramme d'architecture microservice
4. Workflow pour l'achat d'un produit

### Exemple de décomposition (réponse type)

| Microservice | Responsabilité | BDD | Justification |
|-------------|---------------|-----|---------------|
| `user-service` | Comptes utilisateurs, profils | Propriétaire | Données utilisateurs = domaine isolé |
| `product-service` | Catalogue produits, prix | Propriétaire | Données produits évoluent indépendamment |
| `search-service` | Indexation + recherche full-text | Propriétaire (Elasticsearch) | Technologie spécialisée (moteur de recherche) |
| `order-service` | Commandes, panier | Propriétaire | Logique métier complexe + transactionnelle |
| `payment-service` | Paiements, remboursements | Propriétaire | Critique + réglementations PCI-DSS |
| `inventory-service` | Stocks | Propriétaire | Synchro temps-réel nécessaire |
| `recommendation-service` | Suggestions personnalisées | Partagée (read) | Lit depuis product + user sans modifier |

### Workflow "acheter un produit" (Chorégraphie Saga)
```
Client POST /orders/
    ↓
order-service crée commande "pending"
    ↓ publie "order.created"
inventory-service vérifie + réserve stock
    ↓ publie "inventory.reserved"
payment-service débite le paiement
    ↓ publie "payment.succeeded"
order-service met commande "confirmed"
    ↓ publie "order.confirmed"
notification-service envoie email confirmation
```

---

## 3. Exercice 2 — Le menhir de Netflix

### Contexte du cours
> "À l'origine, Netflix utilisait un système monolithique de location de DVD. Avec le streaming, son modèle a évolué vers une architecture de microservices hautement distribuée, où chaque composant évolue indépendamment."

**Le système monolithique de Netflix gérait :**
- Gestion des comptes utilisateurs
- Catalogue de films
- Système de lecture
- Recommandations
- Facturation
- Gestion des appareils
- Analyse et indicateurs

### Tâches demandées
1. Identifier **4 parties** qui devraient scaler indépendamment
2. Pour chaque service : Synchrone ou Asynchrone ? Pourquoi ?
3. Un scénario en cas d'échec d'un service
4. Workflow : utilisateur cherche un film sans idée précise

### Exemple de décomposition avec justification

| Service | Scale ? | Synchro/Asynchro | Raison |
|---------|---------|-----------------|--------|
| `streaming-service` | ✅ OUI (très fort) | Synchrone | Lecture directe = latence critique |
| `recommendation-service` | ✅ OUI (fort) | Asynchrone | Calculs lourds, pas temps-réel |
| `catalog-service` | ✅ OUI (moyen) | Synchrone | Recherches fréquentes |
| `billing-service` | Non | Asynchrone | Traitement périodique |

**Scénario d'échec : recommendation-service est down**  
→ `recommendation-service` est asynchrone → l'app continue à fonctionner  
→ Afficher "Top films populaires" à la place des recommandations personnalisées  
→ Circuit breaker : après X échecs, renvoyer directement les données de fallback

---

## 4. Exercice 3 — Le caillou de Shopify

### Contexte du cours
> "Au début, Shopify était une application monolithique basée sur Ruby on Rails. Avec l'augmentation du nombre de marchands, Shopify a progressivement externalisé certains services liés au paiement, à la facturation, à la détection des fraudes et à la recherche."

**Le système monolithique de Shopify gérait :**
- Rendu de la boutique en ligne
- Panier
- Paiement
- Passerelle de paiements (Paypal, Visa, etc.)
- Administration marchande
- Gestion des stocks
- Discount engine
- Recherche

### Tâches demandées
1. Identifier les **3 services les plus sensibles à la latence** (à isoler en premier)
2. Dessiner l'architecture microservice complète de Shopify
3. Workflow complet pour l'achat d'un produit

### Les 3 services les plus sensibles à la latence

1. **`payment-service`** — Critique : si le paiement est lent, l'utilisateur abandonne
2. **`cart-service`** — Critique : ajouter au panier doit être instantané  
3. **`search-service`** — Critique : la recherche de produits doit être rapide

**Pourquoi isoler ces services en premier ?**
- Si le moteur de recherche est lent, les marchands perdent des ventes
- Si le paiement échoue, perte directe de revenus
- Ces services ont des besoins de scaling différents des autres

---

## 5. Principes de découpage en microservices

Du cours et des exercices, voici les principes clés :

### Principe 1 : Single Responsibility
Chaque service a une seule responsabilité métier claire.  
*Mauvais* : `user-order-payment-service`  
*Bon* : `user-service`, `order-service`, `payment-service`

### Principe 2 : Bases de données séparées
Chaque service a sa propre BDD. Pas de FK cross-service.  
*Sauf* : Les services de "read" peuvent partager des données via events Kafka.

### Principe 3 : Services indépendamment déployables
On doit pouvoir déployer `payment-service` sans toucher `order-service`.

### Principe 4 : Découpler avec les events
Les services communiquent par événements Kafka (asynchrone) plutôt que par appels HTTP directs (synchrone) autant que possible.

### Principe 5 : Granularité appropriée
Ni trop petit (micro-micro-services ingérables) ni trop grand (monolithe déguisé).  
Critère : un service = un domaine métier = une équipe.

---

## 6. Questions d'oral probables

**Q: Comment décider si deux fonctionnalités doivent être dans le même service ou dans deux services différents ?**  
R: Si les fonctionnalités changent toujours ensemble et pour la même raison → même service. Si elles ont des besoins de scaling différents, des cycles de déploiement différents, ou des équipes différentes → services séparés.

**Q: Pourquoi Netflix a choisi une architecture microservices ?**  
R: Pour scaler indépendamment chaque partie. En période de soirée, le streaming-service a besoin de 100x plus de ressources que le billing-service. Avec des microservices, on peut scaler chaque partie indépendamment.

**Q: Qu'est-ce qu'un service "sensible à la latence" ?**  
R: Un service dont la lenteur impacte directement l'expérience utilisateur et les revenus. Exemples : paiement, recherche, lecture streaming. Ces services doivent être isolés et scalés en priorité.
