# 📋 FICHE 12 — ÉCARTS SUJET vs RENDU + JUSTIFICATIONS

> Source : slides du sujet (Lalanne Raphaël, ICC)
> À connaître pour l'oral : **nommer soi-même les manquements avant que le prof les pointe**

---

## 🔴 MANQUEMENT CRITIQUE — Architecture rouge/bleue séparée

**Ce que le sujet demandait (diapo 12) :**
> *"Vous devrez avoir un front et un back différent pour chaque couleur d'équipe, qui seront utilisés par leurs utilisateurs respectifs après authentification."*

**Ce qui a été livré :**
1 seul frontend Angular, 1 seul backend par domaine (auth, battle, team...). La couleur rouge/bleu est un champ en base de données, pas deux backends séparés.

**Justification :**
Le groupe a interprété "rouge/bleu" comme des rôles utilisateur gérés par l'authentification, et non comme deux déploiements physiquement distincts. Quand on a réalisé l'écart avec le sujet, le projet était trop avancé pour repartir sur une architecture miroir complète.

---

## 🔴 Chiffrement entre backends

**Sujet :** *"La data envoyée d'un backend à un autre doit être chiffrée par une clé privée"*

**Livré :** Aucun chiffrement. Messages Kafka et appels REST circulent en clair.

**Justification :** La priorité a été de faire fonctionner les communications d'abord. Intégrer un chiffrement asymétrique sur les messages Kafka aurait nécessité une gestion de clés partagée entre services — complexité non planifiée dans le temps imparti.

---

## 🔴 Système de points (+10 victoire / -10 défaite / plancher à 0)

**Sujet :** *"Un joueur victorieux voit son Score augmenter de 10 points, le perdant diminuer de 10 points. Le total ne peut être inférieur à 0."*

**Livré :** Le champ `winner` est sauvegardé en BDD (`battle_service`) mais aucune mise à jour des points utilisateur n'est faite dans `auth_service`. Les points n'existent pas dans le modèle utilisateur.

**Justification :** Mettre à jour les points impliquait un appel inter-service de `battle_service` → `auth_service`, créant du couplage fort. L'alternative propre aurait été un event Kafka `battle_ended` consommé par `auth_service` — mais l'event `battle_ended` n'a pas été implémenté (voir fiche 10, section A7).

---

## 🔴 Mode Construit : l'adversaire devrait choisir son équipe aussi

**Sujet :** *"Les joueurs jouent **chacun** avec une équipe de leur choix"*

**Livré :** Seul le joueur local utilise son équipe construite. L'adversaire reçoit toujours 6 Pokémon aléatoires :
```typescript
// initConstructed() — battle-arena.component.ts
const blue = await firstValueFrom(this.pokedexService.getRandomPokemon(6));
```

**Justification :** Pour que les deux joueurs choisissent leur équipe, il faudrait que la sélection soit synchronisée côté serveur avant le début de la partie. Le matchmaking étant basique (polling), cette synchronisation n'a pas été implémentée.

---

## 🔴 Mode Pioche : le joueur Bleu peut choisir 2 Pokémon en même temps (1er tour)

**Sujet :** *"Le premier choix est toujours donné au joueur Rouge, mais le joueur Bleu peut choisir ses 2 premiers Pokémon en même temps."*

**Livré :** Tours strictement alternés 1-1 sans règle du double pick pour Bleu.

**Justification :** Règle spécifique non implémentée. Le draft étant local (non synchronisé entre joueurs), cette règle n'aurait de toute façon eu d'effet que visuellement.

---

## 🔴 Timer 90s → perte de partie (pas juste jouer automatiquement)

**Sujet :** *"Un joueur qui n'a pas joué à l'issue du chronomètre **perd la partie**."*

**Livré :** `onTimeout()` joue un tour automatiquement avec le Pokémon actif. Le joueur ne perd pas.

**Justification :** "Perdre au timeout" implique que le serveur sache qui n'a pas joué dans les 90s — impossible sans auth sur `/turn` et sans mécanisme de timeout côté backend.

---

## 🔴 Pokémon KO : doit être caché (pas juste grisé)

**Sujet :** *"Le bouton d'un Pokémon KO **ne doit pas s'afficher**."*

**Livré :** Pokémon KO visibles mais avec `opacity-40` et `pointer-events-none`. Ils sont inactifs mais toujours dans le DOM.

---

## 🔴 Sous-menu utilisateur (pseudo, couleur, avatar, historique, déco)

**Sujet :** Menu sans changer de page avec : Changer pseudo / Changer couleur / Changer avatar / Historique des parties / Déconnexion

**Livré :** Non implémenté ou très partiel. Pas de page/menu de profil identifié dans les routes Angular.

---

## 🔴 Chat : filtre par couleur d'équipe

**Sujet :** *"Un joueur peut activer l'option de ne lire et de n'avoir ses messages vus que par les membres de sa couleur"*

**Livré :** Chat global. Aucun filtrage rouge/bleu.

**Justification :** Le `chat_service` écoute les topics Kafka (`battle-events` + `chat-messages`) et broadcast via WebSocket à tous. Ajouter un filtre couleur aurait nécessité de stocker la couleur du joueur dans `chat_service` et de filtrer les connexions WebSocket par couleur.

---

## 🔴 Pseudo cliquable dans le chat (popup avec Pseudo, Avatar, Points)

**Sujet :** Popup sur clic d'un pseudo dans le chat.

**Livré :** Non implémenté.

---

## 🔴 CGU + Contacts

**Sujet :** Pages statiques demandées.

**Livré :** Non implémentées.

---

## 🔴 Console de logs admin

**Sujet :** *"Les logs de tous vos services sont accessibles par un admin sur la page principale."*

**Livré :** Pas d'utilisateur admin, pas de console de logs.

**Justification :** Nécessiterait un agrégateur de logs (ELK, Loki...) ou une route dédiée récupérant les logs de chaque service — infrastructure non planifiée.

---

## 🔴 Pop-up forfait si quitter la page duel

**Sujet :** *"Si un joueur tente de quitter la page de duel pendant une partie, une pop-up doit lui demander de déclarer forfait avant."*

**Livré :** Navigation libre hors de la page duel, sans confirmation.

---

## 🔴 Tests front (composants Angular)

**Sujet :** *"Les composants du front doivent être couverts par des tests techniques."*

**Livré :** Zéro test dans tout le projet (ni front ni back).

**Justification :** Les tests ont été systématiquement reportés à "une fois les features terminées" — les features ne l'ont jamais été complètement.

---

## 🔴 Persistance des données Kubernetes (PersistentVolume)

**Sujet :** *"Vos bases de données doivent perdurer après l'arrêt et le redémarrage de votre déploiement."*

**Livré :** Probablement pas de `PersistentVolumeClaim` dans les manifests K8s → données perdues à chaque `kubectl delete pod`.

**Justification :** Oubli au niveau de l'infrastructure K8s — les PVC ont été omis des manifests.

---

## 🔴 Jeu d'utilisateurs préexistants + credentials dans le README

**Sujet :** Comptes de test fournis avec identifiants dans le README.

**Livré :** Non présent.

---

## ⚠️ PROBLÈMES DE GROUPE

**Ce que le sujet valorisait :**
> *"Pas de gros push unique de code, les contributions de chaque élève peuvent entrer en compte dans la notation."*

**Ce qui s'est passé :**
- Utilisation importante de l'IA → historique Git peu représentatif du travail individuel réel
- Architecture rouge/bleu mal comprise en début de projet → décision structurante prise trop tard
- Coordination insuffisante sur les features transversales (points, logs, tests)
- Rendu en retard → 0/20 automatique, rattrapé par l'oral

**Ce que tu dis à l'oral :**
> *"La répartition était claire : j'avais battle_service, chat_service, Kafka, Docker, Kubernetes. Le problème principal de groupe a été la mauvaise compréhension de l'architecture rouge/bleu dès le départ — on a modélisé ça comme un rôle utilisateur au lieu de deux backends séparés. Quand on a réalisé l'écart avec le sujet, le projet était trop avancé pour repartir de zéro sur ce point."*

---

## RÉCAP RAPIDE — CE QUI FONCTIONNE vs CE QUI MANQUE

| Ce qui fonctionne | Ce qui manque |
|-------------------|---------------|
| Docker + K8s (namespace, ClusterIP, NodePort) | Architecture rouge/bleu séparée |
| Auth JWT (login, register, token) | Chiffrement inter-services |
| Battle (créer, rejoindre, jouer un tour, forfait) | Système de points utilisateur |
| Chat WebSocket temps réel | Filtre chat par couleur |
| Kafka (turn_played events) | Event `battle_ended` |
| Pokedex + cache Redis | Tests (front et back) |
| CRUD équipes | Persistance K8s (PVC) |
| 3 modes de jeu (UI) | Mode Construit vraiment multijoueur |
| Scoreboard + fin de partie | Console logs admin |
