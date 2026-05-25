# 📅 PLAN DE RÉVISION — VENDREDI 29 MAI 20H

> **Règle générale à partir du moment où tu as lu les fiches :**
> Zéro relecture passive. Tout se fait à voix haute, code ouvert devant toi.

---

## 🗓️ SAMEDI 23 MAI — PREMIÈRE JOURNÉE DE PRATIQUE

### 13h00 – 14h00 : battle_engine.py
Ouvre `api/battle_service/app/services/battle_engine.py`.
Lis `calc_advantage` et `resolve_turn`. **Ferme le fichier.**
Explique à voix haute : la double boucle, le produit des multiplicateurs, pourquoi `round(fa, 4)`, quand le résultat est `"A"` / `"B"` / `"draw"`.
Rouvre et vérifie. Recommence jusqu'à pouvoir l'expliquer sans regarder.

### 14h00 – 15h00 : routes/battle.py — play_turn
Ouvre `api/battle_service/app/routes/battle.py`.
Lis `play_turn` ligne par ligne. **Ferme le fichier.**
Explique à voix haute comme si le prof regardait avec toi. Ordre obligatoire : calcul → BDD commit → Kafka publish. Explique pourquoi cet ordre (BDD avant Kafka).
Cite spontanément : "et il manque l'auth sur cette route, ce qu'il aurait fallu c'est `get_current_user`".

### 15h00 – 15h30 : Pause

### 15h30 – 16h30 : chat_service/main.py — kafka_consumer_loop
Ouvre `api/chat_service/app/main.py`.
Lis `kafka_consumer_loop` et le `lifespan`. **Ferme le fichier.**
Explique à voix haute les 4 points obligatoires :
1. Pourquoi `while True`
2. Retry exponentiel 2→30s + reset après succès
3. 2 topics dans 1 consumer (routage via `msg.topic`)
4. `create_task` pas `await` (sinon serveur HTTP ne démarre jamais)

### 16h30 – 17h30 : docker-compose.yml
Ouvre `infra/docker/docker-compose.yml`.
Pour chaque service, dis à voix haute ce qu'il fait et pourquoi il est là.
Points obligatoires : 1 postgres 4 BDD (compromis dev), `kafka:29092` vs `9092`, `depends_on` sans healthcheck (limitation connue), `restart: always`.

### 17h30 – 18h00 : Pause

### 18h00 – 19h00 : K8s manifests
Ouvre `infra/k8s/services.yaml` et `infra/k8s/gateway.yaml`.
Explique à voix haute : namespace `pokedrafter`, pourquoi ClusterIP par défaut (services internes), pourquoi NodePort 30080 seulement sur gateway, pourquoi `replicas: 1` et ce que ça impliquerait en prod.

### 19h00 – 20h00 : Théorie à voix haute — SANS NOTES
5 questions dans l'ordre, tu réponds à voix haute sans regarder :
1. Monolithe vs microservices — 3 avantages, 1 inconvénient
2. Kafka vs REST — quand choisir l'un ou l'autre
3. Database-per-service — avantage + inconvénient concret
4. API Gateway — rôle de Nginx dans PokeDrafter
5. "chat_service est down, que se passe-t-il ?" — réponse avec Kafka

### 20h00 – 21h00 : Simulation orale complète — AUCUNE NOTE
Tu joues le prof et l'étudiant à voix haute.
- **15 min théorie** : pose-toi 3 questions au hasard et réponds
- **15 min projet** : ouvre battle.py et explique `play_turn` comme si le prof regardait avec toi, puis passe à `kafka_consumer_loop`

---

## 🗓️ DIMANCHE 24 – MERCREDI 27 MAI

### Chaque jour : 1h maximum, pas plus

| Jour | Focus |
|------|-------|
| Dimanche 24 | Relis fiche 10 (justifications). Explique 5 choix à voix haute sans notes. |
| Lundi 25 | Simulation Q&R théorie : prends QUESTIONS_COURS.md, réponds sans regarder les réponses |
| Mardi 26 | Relis fiche F (faiblesses du code). Entraîne-toi à dire "on n'avait pas d'auth parce que..." |
| Mercredi 27 | Simulation orale 30 min complète, chronomètre en main |

---

## 🗓️ JEUDI 28 MAI — VEILLE

**Pas de nouveau contenu. Pas de lecture longue.**

- Relis `battle.py` → `play_turn` à voix haute (15 min)
- Relis `chat_service/main.py` → `kafka_consumer_loop` à voix haute (15 min)
- Relis ATTITUDE_ET_POSTURE_ORAL.md (10 min)
- Stop. Repos.

---

## 🗓️ VENDREDI 29 MAI — JOUR J

**Matin :** Relis la fiche 01 (Introduction Microservices). Rien d'autre.

**Après-midi :** Ne touche plus aux fiches. Mange, repose-toi.

**À 20h dans la salle :**
- Parle lentement
- Prends 3-5 secondes avant de répondre — c'est normal
- Si tu bloques : "Je ne suis pas sûr mais je dirais que..."
- Si le prof pointe une erreur : "Vous avez raison, ce qu'il aurait fallu faire c'est..."

---

## ✅ INDICATEUR : TU ES PRÊT QUAND...

- [ ] Tu peux expliquer `play_turn` à voix haute sans ouvrir le fichier
- [ ] Tu peux expliquer `kafka_consumer_loop` à voix haute sans ouvrir le fichier
- [ ] Tu peux citer 3 erreurs du projet avant qu'on te les pointe
- [ ] Tu peux répondre à "Kafka vs REST pourquoi ?" en moins de 30 secondes
- [ ] Tu as fait au moins 1 simulation orale complète de 30 min
