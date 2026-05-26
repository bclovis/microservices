# 📋 ÉCARTS SUJET vs RENDU — ANALYSE HONNÊTE + JUSTIFICATIONS

> Fiche critique pour l'oral. À lire avant de dormir le 28 mai.

---
"Ce qui manque, c'est conscient de ma part. Quand j'ai vu qu'on ne pourrait pas tout faire, j'ai choisi de livrer quelque chose de compréhensible et défendable plutôt que d'implémenter les 2 backends en rush sans les comprendre."
---

## 👥 RÉPARTITION RÉELLE DE L'ÉQUIPE (cohérent avec les commits GitHub)

| Membre | GitHub | Parties |
|--------|--------|---------|
| **Toi** | BETOUZ92 / bclovis | battle_service, chat_service, K8s manifests |
| **Abdellatif** | abdemeh | Frontend Angular, corrections finales battle (matchmaking) |
| **Alaa** | BOUGHAMMOURAAlaa | auth_service, team_service, pokedex_service, Alembic migrations |

> **À dire à l'oral si on te demande qui a fait quoi :** "On était 3. J'ai pris en charge battle_service, chat_service et l'infra K8s. Alaa a fait auth et team service. Abdellatif s'occupait du frontend."

---

## 📅 TIMELINE DE TES COMMITS — pour raconter le développement

| Date | Commit | Ce que ça prouve |
|------|--------|-----------------|
| 21 avr | `debut battle service, config de base + moteur de types` | Tu as commencé par le moteur F(A) |
| 21 avr | `fix cas liste vide dans calc_advantage` | Premier bug trouvé dans le moteur |
| 22 avr | `modeles db et schemas pydantic pour les batailles` | Modélisation BDD avant les routes |
| 22 avr | `routes battles + main, endpoints create/turn/forfeit/history` | Architecture REST complète |
| 22 avr | `erreur si on essaie de terminer une bataille sans tours` | Validation métier explicite |
| 23 avr | `kafka producer + requirements + dockerfile` | Kafka intégré battle_service |
| 23 avr | `chat service, config et schema message` | Démarrage chat_service |
| 23 avr | `websocket chat + gestion des connexions par team` | WebSocket + rooms par équipe |
| 23 avr | `main chat + bot kafka + dockerfile` | Consumer Kafka + bot messages |
| 23 avr | `fix broadcast sur team inexistante` | Bug edge case broadcast |
| 27 avr | `fix bug battle + clean chat service` | Stabilisation avant fin |
| 30 avr | `feat(battle): join endpoint, player_blue_id optionnel` | Join ajouté tardivement |
| 30 avr | `feat: ajout ws battle pour pvp` | Tentative WS dans battle (non finalisée) |
| 30 avr | `k8s manifests` | K8s ajouté tout à la fin |

> **Leçon à tirer :** Tu as développé battle_service ET chat_service en **9 jours** (21-30 avril). C'est serré. Ça explique les concessions.

> **Sur le commit "feat: ajout ws battle pour pvp" :** Si le prof voit ce commit, explique : "J'avais commencé un WebSocket dans battle_service pour le PvP temps réel, mais j'ai réalisé que la synchronisation des états en WebSocket doublonnait la logique REST déjà en place. J'ai décidé de garder le REST pour le tour et de laisser le chat_service gérer le temps réel via Kafka."

---

## 🟢 CE QUI EST FAIT ET DEMANDÉ — à valoriser

| Sujet (extrait exact) | Ce qui est livré |
|----------------------|-----------------|
| "Gère le déroulement d'un duel" | ✅ battle_service complet : create/join/turn/end/forfeit, moteur F(A) |
| "Afficher une fenêtre de chat. Un bot doit afficher les actions à l'issue du tour" | ✅ chat_service WebSocket + bot Kafka |
| "Message broker (Kafka)" | ✅ Kafka producer (battle) + consumer (chat) |
| "Chaque brique applicative sera conteneurisée sous Docker" | ✅ 10 Dockerfiles + docker-compose.yml |
| "Déployé sous Kubernetes dans un namespace unique" | ✅ infra/k8s/ : namespace, deployments, services, PVC |
| "Vos bases de données doivent perdurer après redémarrage" | ✅ PVC pour PostgreSQL et Redis dans K8s |
| "L'API est gratuite, votre programme sera plus performant si vous cachez la data" | ✅ Redis cache TTL dans pokedex_service |
| "Gère les recommandations" | ✅ team_service recommendation engine |
| "Afficher un bouton pour déclarer forfait" | ✅ POST /battles/{id}/forfeit |
| "Un joueur peut consulter l'historique de ses parties" | ✅ GET /battles/history/{uid} |
| "Reverse Proxy / API Gateway" | ✅ Nginx avec routing /api/* et upgrade WebSocket |
| "Création de compte + Authentification" | ✅ auth_service JWT |
| "CRUD sur les équipes d'un joueur" | ✅ team_service |
| "Dex — recherche Pokémon" | ✅ pokedex_service avec filtres |

---

## 🔴 CE QUI MANQUE — avec justification pour chaque

---

### ❌ 1. Deux backends rouge/bleu séparés
**Sujet :** *"Vous devrez avoir un front et un back différent pour chaque couleur d'équipe, qui seront utilisés par leurs utilisateurs respectifs après authentification. Les deux backends ne communiquent pas entre eux directement."*

**Ce qui est livré :** 1 seul backend, la couleur est un attribut utilisateur en BDD.

**Justification :**
> "On a interprété 'rouge/bleu' comme des rôles utilisateur, pas comme deux déploiements distincts. Cette décision d'architecture a été prise dès le début. Quand on a compris l'écart avec le sujet, le projet était trop avancé pour refactoriser en deux backends miroirs — surtout avec les difficultés qu'on avait déjà sur le battle_service et le chat_service."

---

### ❌ 2. Chiffrement inter-backends (clé privée)
**Sujet :** *"la data envoyée d'un backend à un autre doit être chiffrée par une clé privée"*

**Ce qui est livré :** Messages Kafka et appels REST en clair.

**Justification :**
> "Le chiffrement asymétrique sur Kafka implique une gestion de clés partagées entre services — il faut distribuer les clés publiques à chaque consumer, gérer la rotation. On a priorisé faire fonctionner la communication d'abord. En production, on ajouterait TLS sur le broker Kafka et HTTPS entre services."

---

### ❌ 3. Système de points (+10 victoire / -10 défaite / plancher 0)
**Sujet :** *"Un joueur victorieux voit son Score augmenter de 10 points, le perdant diminuer de 10 points. Le total ne peut être inférieur à 0."*

**Ce qui est livré :** Le `winner` est sauvegardé dans `battle_db`, mais aucune mise à jour des points dans `auth_service`.

**Justification :**
> "Le résultat de la bataille est persisté. Mettre à jour les points impliquait un appel inter-service de battle_service → auth_service, ce qui créait du couplage fort. L'architecture propre aurait été un event Kafka `battle_ended` consommé par auth_service — mais vu le temps passé à faire marcher le battle_service (le turn notamment) et le chat_service, on a dû faire des concessions. C'est une amélioration identifiée."

---

### ❌ 4. Chronomètre 90s relié au back (forfait automatique)
**Sujet :** *"Afficher un chronomètre de 90 secondes. Un joueur qui n'a pas joué à l'issue du chronomètre perd la partie."*

**Ce qui est livré :** Le composant `battle-timer` existe dans le front mais n'est pas relié à un forfait automatique côté serveur.

**Justification :**
> "Le timer front est implémenté. L'auto-forfait côté serveur nécessite un mécanisme de timeout asynchrone — une tâche en background qui vérifie si un joueur n'a pas joué depuis 90s. Avec un broker Kafka et un service déjà complexe, ajouter cette logique de timeout sans la tester correctement risquait de casser le turn existant. On a priorisé la robustesse du tour manuel."

---

### ❌ 5. Mode Construit : l'adversaire choisit aussi son équipe
**Sujet :** *"Les joueurs jouent chacun avec une équipe de leur choix"*

**Ce qui est livré :** Le joueur rouge utilise son équipe construite, le joueur bleu reçoit 6 Pokémon aléatoires.

**Justification :**
> "Pour synchroniser la sélection d'équipe des deux joueurs avant le début de la partie, il faudrait un WebSocket de lobby — le serveur attend que les deux joueurs aient confirmé leur équipe avant de démarrer. Notre matchmaking par polling ne permet pas au serveur d'initier cette synchronisation. C'est une limite de l'architecture de matchmaking."

---

### ❌ 6. Mode Pioche : double pick Bleu au 1er tour
**Sujet :** *"Le premier choix est toujours donné au joueur Rouge, mais le joueur Bleu peut choisir ses 2 premiers Pokémon en même temps."*

**Ce qui est livré :** Tours strictement alternés 1-1.

**Justification :**
> "La règle du double pick Bleu est une règle métier spécifique au mode Pioche. Le moteur de tour actuel est symétrique. Implémenter cette règle aurait nécessité d'ajouter un état 'phase de pioche' séparé de la phase de combat dans battle_service. Avec les difficultés déjà rencontrées sur le tour de combat, on a d'abord fait fonctionner le cas général."

---

### ❌ 7. Dissimuler les Pokémon non joués en mode Hasard
**Sujet :** *"vous devrez dissimuler l'icône des Pokémon qui n'ont pas encore été mis en jeu"*

**Ce qui est livré :** Tous les Pokémon visibles dès le début.

**Justification :**
> "C'est une feature purement front. Abdellatif gérait le front — la répartition des tâches faisait que je me concentrais sur les services backend et l'infra. Cette feature n'a pas été implémentée dans le temps imparti."

---

### ❌ 8. Tests frontend
**Sujet :** *"Les composants du front doivent être couverts par des tests techniques."*

**Ce qui est livré :** Aucun fichier `.spec.ts`.

**Justification :**
> "Les tests frontend n'ont pas été écrits. En tant que responsable backend et infra, j'ai concentré les efforts sur les tests manuels via Swagger et sur la stabilité des services. Les tests Angular auraient nécessité du temps dédié côté front."

---

### ❌ 9. Console de logs admin
**Sujet :** *"Les logs de tous vos services sont accessibles par un admin sur la page principale."*

**Justification :**
> "Une console de logs centralisée nécessite un stack de log management (ELK, Loki/Grafana). On a les logs dans chaque container Docker via `docker logs`. L'exposition dans le front n'a pas été implémentée."

---

### ❌ 10. Pop-up forfait si quitter la page de duel
**Justification :**
> "Feature purement front, dans la partie d'Abdellatif."

---

### ❌ 11. Pseudo cliquable (fenêtre Pseudo/Avatar/Points)
**Justification :**
> "Feature purement front, non prioritaire par rapport au fonctionnement du duel."

---

## 🎯 MON AVIS HONNÊTE — à quel point j'ai respecté le sujet ?

### Ce qui est solide (à valoriser) :
- Le **cœur métier** est là : moteur F(A), Kafka, WebSocket, persistance, infra Docker/K8s
- L'architecture microservices est **propre et cohérente** : separation of concerns, un service = une BDD
- Le sujet dit littéralement : *"Une application maintenable mais partiellement fonctionnelle sera plus valorisée qu'une application non maintenable mais entièrement fonctionnelle."* → tu es dans cette case

### Ce qui est vraiment problématique :
- La **séparation rouge/bleu** était une contrainte technique centrale — c'est le gap le plus visible
- Le **chiffrement** était explicitement demandé
- Ces deux points sont architecturaux, pas des features oubliées

### Verdict réaliste :
> Le cœur du projet fonctionne et est bien architecturé. Les deux contraintes techniques majeures (2 backends, chiffrement) manquent. Le front est incomplet sur certaines features du duel. C'est un rendu **partiel mais solide sur la partie backend/infra**. La note ne sera pas excellente, mais tu peux défendre ce que tu as fait avec des arguments cohérents.

---

## 🗣️ FORMULATION GÉNÉRALE à l'oral si le prof insiste

> "On a eu plusieurs challenges sur ce projet. D'abord faire fonctionner le battle_service — le endpoint `/turn` notamment, qui devait calculer F(A), persister le tour et publier sur Kafka de façon atomique. Ensuite, chat_service ne démarrait pas à cause du timing avec Kafka, ce qui a pris du temps à diagnostiquer et résoudre avec le retry backoff. On se voyait peu en physique, avec des contraintes de langue et un mois d'avril très chargé en projets parallèles. J'ai pris des décisions de priorisation : avoir quelque chose qui marche et que je comprends sur mes parties plutôt que de tout implémenter à moitié. Abdellatif s'occupait du front conformément à notre répartition. J'ai récupéré l'infra un peu tardivement dans le projet, mais j'ai réussi à livrer Docker Compose + Nginx + les manifests Kubernetes fonctionnels."

---

## 📌 COMMANDES DEMO pour l'oral (Swagger)

```bash
# Lancer le projet
cd ~/Desktop/Architecture\ Microservices/Projets_Microservices/PokeDrafter_GitHub_Latest/infra/docker
docker compose up --build

# URLs Swagger à montrer
http://localhost:8003/docs   # battle_service
http://localhost:8005/docs   # chat_service
http://localhost:8004/docs   # pokedex_service
http://localhost/docs        # via Nginx gateway
```

**Ordre de démo dans Swagger battle_service :**
1. `POST /api/battle/battles/` — créer une salle (mode: "random")
2. `POST /api/battle/battles/{id}/join` — rejoindre
3. `POST /api/battle/battles/{id}/turn` — jouer (types_red: ["fire"], types_blue: ["water"])
4. Montrer le résultat : fa, fb, result "B" (eau bat feu)
5. `GET /api/battle/battles/history/{uid}` — historique
