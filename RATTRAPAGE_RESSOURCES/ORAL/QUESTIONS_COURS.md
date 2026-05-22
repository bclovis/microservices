# 🎤 QUESTIONS PROBABLES ORAL - PARTIE COURS (15 minutes)

> **Format** : 15 premières minutes sur les concepts du cours et applications pratiques

---

## 🔥 QUESTIONS ULTRA-PROBABLES (Prépare-les à 100%)

### Q1. Expliquez-moi la différence entre une architecture monolithique et une architecture microservices

**Réponse type :**
> "Une architecture monolithique regroupe tout le code dans un seul projet avec une seule base de données. Tous les modules sont couplés et déployés ensemble. En microservices, on découpe l'application en services indépendants, chacun avec sa propre base de données et son propre déploiement. L'avantage principal est la scalabilité ciblée et la résilience : si un service tombe, les autres continuent. L'inconvénient est la complexité accrue."

**Points bonus à mentionner :**
- Database per service
- Exemple concret de votre projet
- Quand utiliser l'un ou l'autre

---

### Q2. Pourquoi chaque microservice a sa propre base de données ?

**Réponse type :**
> "C'est le principe 'database per service'. Ça permet un découplage total : chaque service est responsable de ses données. On peut choisir le type de BDD adapté à chaque service : PostgreSQL pour les données relationnelles, Redis pour le cache, MongoDB pour les logs. Ça permet aussi de scaler indépendamment et d'isoler les pannes : si une BDD tombe, les autres services continuent de fonctionner."

**Anticiper la question suivante :**
> "Mais comment un service récupère des données d'un autre service ? On utilise soit des appels API REST pour les besoins synchrones, soit des événements Kafka pour les besoins asynchrones. On ne doit JAMAIS accéder directement à la BDD d'un autre service."

---

### Q3. Expliquez les différents verbes HTTP (GET, POST, PUT, DELETE)

**Réponse type :**
> "GET sert à récupérer des données sans les modifier. POST crée une nouvelle ressource. PUT remplace complètement une ressource existante. DELETE supprime une ressource. Il y a aussi PATCH pour modifier partiellement. Par exemple dans notre projet : GET /pokemon/{id} pour lire un Pokémon, POST /teams pour créer une équipe, PUT /teams/{id} pour modifier une équipe, DELETE /teams/{id} pour la supprimer."

---

### Q4. Qu'est-ce qu'une API Gateway et pourquoi l'utiliser ?

**Réponse type :**
> "Une API Gateway est un point d'entrée unique pour toutes les requêtes vers les microservices. Elle gère le routage vers les bons services, la sécurité (vérification des API Keys ou JWT), le cache pour améliorer les performances, l'agrégation de données de plusieurs services, et le rate limiting. Dans notre projet, on utilise Nginx comme gateway : le frontend Angular appelle uniquement la gateway qui redirige vers les 5 microservices."

**Anticiper :**
> "Le principal risque est le Single Point of Failure : si la gateway tombe, tout devient inaccessible. On mitigue ça en déployant plusieurs instances avec un load balancer."

---

### Q5. C'est quoi Kafka et pourquoi l'utiliser plutôt que REST ?

**Réponse type :**
> "Kafka est une plateforme de streaming d'événements pour la communication asynchrone entre microservices. Les services publient des événements dans des topics, et d'autres services les consomment. C'est plus résilient que REST car les messages sont persistés : si un service est down, il peut traiter les messages en retard quand il redémarre. On l'utilise pour découpler complètement les services et améliorer la scalabilité."

**Exemple concret :**
> "Dans notre TP4, quand une commande est créée, OrderService publie 'order.created' dans Kafka. InventoryService le reçoit et réserve le stock sans que OrderService ait besoin d'attendre."

---

### Q6. Qu'est-ce qu'une Saga et pourquoi en a-t-on besoin ?

**Réponse type :**
> "Une Saga est un pattern pour gérer des transactions distribuées sur plusieurs microservices. Comme on ne peut pas utiliser les transactions SQL classiques (elles ne traversent pas les services), on utilise une série d'événements. Si une étape échoue, on publie des événements de compensation pour annuler les étapes précédentes. Dans notre TP4, si le paiement échoue, on publie 'payment.failed' et InventoryService libère le stock réservé."

**Types de Saga :**
> "Il y a deux types : chorégraphie (chaque service réagit aux événements de manière décentralisée) et orchestration (un orchestrateur central coordonne). On a utilisé la chorégraphie dans le TP4."

---

### Q7. Qu'est-ce que Kubernetes et pourquoi l'utiliser ?

**Réponse type :**
> "Kubernetes est un orchestrateur de conteneurs qui automatise le déploiement, le scaling, et la gestion des applications Docker. Il gère plusieurs machines (nodes), assure que les conteneurs tournent toujours (auto-healing), permet de scaler facilement avec des replicas, et gère le réseau entre services. Dans notre TP6, on déploie nos microservices sur Kubernetes pour bénéficier de l'auto-healing et du scaling automatique."

---

### Q8. Quelle est la différence entre un Pod, un Deployment, et un Service dans Kubernetes ?

**Réponse type :**
> "Un Pod est la plus petite unité Kubernetes, c'est un ou plusieurs conteneurs qui s'exécutent ensemble. Un Deployment gère plusieurs réplicas d'un Pod avec auto-healing : si un Pod crash, K8s en recrée un automatiquement. Un Service expose les Pods avec un DNS stable pour que les autres services puissent les appeler. Par exemple, user-deployment crée 3 pods, et user-service permet d'y accéder via http://user-service:8001."

---

## 🎯 QUESTIONS TECHNIQUES (Moyennement probables)

### Q9. Comment gérez-vous la sécurité dans vos microservices ?

**Réponse type :**
> "On utilise plusieurs niveaux : 1) API Keys pour les appels simples dans le TP5, 2) JWT (JSON Web Tokens) dans le projet PokeDrafter pour authentifier les utilisateurs. Le frontend envoie le JWT dans le header Authorization, et chaque service protégé le vérifie. On a aussi le CORS configuré dans la gateway pour autoriser les requêtes depuis le frontend."

---

### Q10. Comment scaler une application avec Kubernetes ?

**Réponse type :**
> "Deux méthodes : scaling manuel avec 'kubectl scale deployment user-service --replicas=5', ou auto-scaling avec HPA (Horizontal Pod Autoscaler) qui ajoute/supprime automatiquement des pods selon des métriques comme le CPU. Par exemple, on peut configurer : si CPU > 80%, créer plus de pods jusqu'à un maximum de 10. Dans le TP6 exercice 2, on teste le scaling sous charge."

---

### Q11. Qu'est-ce que Docker et à quoi ça sert ?

**Réponse type :**
> "Docker est une plateforme de conteneurisation qui permet d'empaqueter une application avec toutes ses dépendances dans un conteneur isolé. Ça garantit que l'application tourne de la même manière en dev, test, et prod. On définit l'environnement dans un Dockerfile, et on peut lancer plusieurs services avec docker-compose. Tous nos microservices sont conteneurisés avec Docker."

---

### Q12. Expliquez le concept de "database per service"

**Réponse type :**
> "Chaque microservice possède sa propre base de données pour assurer le découplage. Si un service veut des données d'un autre service, il doit passer par son API ou écouter ses événements Kafka. Ça permet de choisir le type de BDD adapté à chaque service et d'isoler les pannes. C'est un principe fondamental des microservices, même si ça rend les transactions plus complexes."

---

### Q13. Comment gérer les appels entre microservices ?

**Réponse type :**
> "Deux approches : synchrone avec REST/HTTP pour les besoins immédiats (ex: récupérer un utilisateur), et asynchrone avec Kafka pour les événements (ex: notifier qu'une commande a été créée). Le synchrone est simple mais crée du couplage. L'asynchrone est plus résilient mais plus complexe. On choisit selon le cas d'usage."

---

### Q14. Qu'est-ce que le CORS et pourquoi est-ce nécessaire ?

**Réponse type :**
> "CORS (Cross-Origin Resource Sharing) est un mécanisme de sécurité des navigateurs qui bloque les requêtes HTTP entre domaines différents par défaut. Notre frontend tourne sur localhost:4200 et le backend sur localhost:8000, donc on doit configurer CORS dans la gateway pour autoriser ces requêtes. On ajoute un middleware CORS qui liste les origines autorisées."

---

### Q15. Qu'est-ce que Pydantic et pourquoi l'utiliser avec FastAPI ?

**Réponse type :**
> "Pydantic est une bibliothèque de validation de données. On définit des modèles avec des types (str, int, email...) et Pydantic valide automatiquement les données entrantes. Si invalides, FastAPI retourne automatiquement une erreur 422 avec les détails. Ça évite d'écrire du code de validation manuellement et génère automatiquement la documentation OpenAPI."

---

## 🔧 QUESTIONS SUR LES CHOIX TECHNIQUES

### Q16. Pourquoi avoir choisi FastAPI plutôt que Flask ou Django ?

**Réponse type :**
> "FastAPI est moderne, très rapide (performances comparables à Node.js), supporte nativement l'asynchrone (async/await), génère automatiquement la documentation Swagger, et valide les données avec Pydantic. C'est parfait pour des microservices performants. Flask est plus simple mais moins complet, et Django est trop lourd pour des microservices."

---

### Q17. Quels sont les avantages et inconvénients des microservices ?

**Réponse type :**

**Avantages :**
- Scalabilité ciblée
- Résilience (isolation des pannes)
- Déploiements indépendants
- Équipes autonomes
- Choix technologiques différents

**Inconvénients :**
- Complexité accrue
- Communication réseau (latence)
- Transactions distribuées complexes
- Monitoring plus difficile
- Overhead opérationnel

> "C'est un trade-off : les microservices sont puissants pour les grandes apps avec plusieurs équipes, mais overkill pour les petits projets."

---

### Q18. Comment testez-vous vos microservices ?

**Réponse type :**
> "Plusieurs niveaux : tests unitaires pour la logique métier, tests d'intégration pour les API (appels REST), tests end-to-end pour les flux complets (ex: créer une commande du début à la fin), et tests de charge avec des outils comme JMeter pour vérifier la scalabilité. On utilise aussi la documentation Swagger de FastAPI pour tester manuellement les endpoints."

---

### Q19. Qu'est-ce qu'un Rolling Update et pourquoi est-ce important ?

**Réponse type :**
> "C'est un déploiement sans downtime dans Kubernetes. K8s crée progressivement de nouveaux pods avec la nouvelle version, attend qu'ils soient prêts, puis supprime les anciens pods. Pendant ce temps, l'application reste accessible. Si problème, on peut rollback facilement. C'est crucial en production pour ne pas avoir de coupure de service."

---

### Q20. Expliquez le concept de "eventual consistency"

**Réponse type :**
> "Dans les microservices, les données ne sont pas toujours immédiatement cohérentes entre tous les services, mais le deviennent après un court délai. Par exemple avec Kafka : quand un user est créé dans auth_service, il faut quelques millisecondes pour que team_service reçoive l'événement et mette à jour son cache local. Pendant ce délai, les données sont 'eventually consistent'. On accepte ce trade-off pour gagner en performance et résilience."

---

## 💡 QUESTIONS PIÈGES / AVANCÉES

### Q21. Si un service est en panne, comment les autres services réagissent ?

**Réponse type :**
> "Ça dépend du type de communication. Avec REST synchrone, on peut implémenter un Circuit Breaker qui détecte les échecs répétés et arrête temporairement les appels pour éviter de surcharger le service. Avec Kafka asynchrone, les messages restent en attente et seront traités quand le service redémarre. Dans tous les cas, les autres services continuent de fonctionner, c'est la résilience des microservices."

---

### Q22. Qu'est-ce qu'un Circuit Breaker ?

**Réponse type :**
> "C'est un pattern de résilience qui détecte quand un service est défaillant et arrête temporairement les appels vers ce service. Après un timeout, il réessaie. Ça évite de surcharger un service déjà en difficulté et améliore l'expérience utilisateur en échouant rapidement plutôt que d'attendre un timeout. C'est implémentable avec des bibliothèques comme Hystrix ou Resilience4j."

---

### Q23. Comment monitorer vos microservices en production ?

**Réponse type :**
> "On utilise plusieurs outils : logs centralisés (ELK stack ou Loki), métriques (Prometheus + Grafana pour suivre CPU, RAM, latence), et tracing distribué (Jaeger ou Zipkin pour suivre une requête à travers plusieurs services). Dans Kubernetes, on utilise kubectl logs pour les logs et kubectl top pour les métriques. Le monitoring est crucial car avec plusieurs services, le debugging est plus complexe."

---

### Q24. Qu'est-ce que le Service Discovery et pourquoi en a-t-on besoin ?

**Réponse type :**
> "C'est un mécanisme qui permet aux services de se trouver automatiquement sans configuration manuelle. Dans Kubernetes, c'est natif : chaque Service a un DNS (ex: user-service:8001) que les autres peuvent utiliser. Sans ça, on devrait hardcoder les IPs de chaque service, ce qui serait ingérable quand on scale et que les pods changent d'IP."

---

### Q25. Quelle est la différence entre scalabilité verticale et horizontale ?

**Réponse type :**
> "Scalabilité verticale = augmenter les ressources d'une machine (plus de CPU, RAM). Limitée et coûteuse. Scalabilité horizontale = ajouter plus de machines/pods. C'est l'approche des microservices et Kubernetes : au lieu d'un pod puissant, on a 10 pods moyens. C'est plus résilient (si un pod tombe, les autres continuent) et plus économique."

---

### Q26. Expliquez le pattern Outbox pour Kafka

**Réponse type :**
> "C'est un pattern pour garantir la cohérence entre la BDD et Kafka. Au lieu de publier directement dans Kafka, on écrit l'événement dans une table 'outbox' dans la même transaction que les données métier. Un processus séparé lit l'outbox et publie dans Kafka. Ça garantit qu'on ne perd jamais d'événements, même en cas de crash. On l'utilise dans le TP4 pour OrderService."

---

### Q27. Comment gérer les secrets (passwords, API keys) dans Kubernetes ?

**Réponse type :**
> "On utilise des Secrets Kubernetes qui stockent les données sensibles encodées en base64. Les pods peuvent monter ces secrets comme variables d'environnement ou fichiers. En production, on utiliserait des solutions comme HashiCorp Vault ou AWS Secrets Manager pour plus de sécurité. On ne doit JAMAIS hardcoder les secrets dans le code ou les YAML."

---

### Q28. Qu'est-ce qu'un Load Balancer et comment Kubernetes le gère ?

**Réponse type :**
> "Un Load Balancer distribue le trafic entre plusieurs instances d'un service. Dans Kubernetes, quand on crée un Service avec plusieurs pods, K8s fait automatiquement du load balancing round-robin : chaque requête est envoyée à un pod différent. On peut aussi utiliser un LoadBalancer externe (AWS ELB, GCP Load Balancer) pour exposer les services à l'extérieur du cluster."

---

### Q29. Comment gérer les mises à jour de schéma de base de données dans les microservices ?

**Réponse type :**
> "C'est complexe car chaque service a sa BDD. On utilise des migrations (Alembic pour Python, Flyway pour Java) qui versionnent les changements de schéma. On déploie d'abord les migrations, puis le nouveau code. Pour les changements breaking, on fait des déploiements en deux étapes : d'abord une version compatible avec l'ancien et le nouveau schéma, puis le changement de schéma, puis suppression de la compatibilité."

---

### Q30. Quelle est la différence entre stateless et stateful services ?

**Réponse type :**
> "Un service stateless ne stocke pas d'état entre les requêtes : chaque requête est indépendante. C'est idéal pour scaler (on peut ajouter des pods sans problème). Un service stateful garde un état local (ex: session utilisateur, cache local). C'est plus difficile à scaler car il faut synchroniser l'état. Nos microservices sont stateless, l'état est dans les BDD ou Redis."

---

## 🎯 STRATÉGIE DE RÉPONSE

### Si tu connais la réponse
1. Commence par une définition claire
2. Donne un exemple concret de votre projet
3. Mentionne les avantages/inconvénients si pertinent
4. Parle avec assurance et enthousiasme

### Si tu hésites
1. Commence par ce que tu sais : "Je ne suis pas certain de tous les détails, mais voici ce que je comprends..."
2. Construis logiquement à partir de concepts que tu maîtrises
3. Admets les limites de ta réponse si nécessaire

### Si tu ne sais pas
1. Ne mens jamais
2. Essaie de faire un lien avec un concept proche
3. "Je ne connais pas ce concept précis, mais je sais que [concept proche]..."

---

## 📝 MOTS-CLÉS À PLACER (Impressionne le prof)

- **Découplage** / **Loose coupling**
- **Scalabilité horizontale**
- **Résilience** / **Fault tolerance**
- **Event-driven architecture**
- **Eventual consistency**
- **Circuit breaker**
- **Auto-healing**
- **Service discovery**
- **Container orchestration**
- **Rolling update**
- **Database per service**
- **Saga chorégraphie**

---

**🔥 Prépare TOUTES les 10 premières questions à la perfection. Si tu les maîtrises, tu as déjà 80% de chances de bien réussir l'oral !**
