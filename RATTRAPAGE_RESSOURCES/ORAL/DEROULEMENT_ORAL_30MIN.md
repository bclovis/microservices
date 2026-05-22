# 📋 DÉROULEMENT DE L'ORAL - 30 MINUTES

## ⏱️ PARTIE 1 : THÉORIE (15 min)

### Minutes 0-2 : Installation
- Tu rentres, tu t'assois
- Prof : "Bonjour, vous êtes prêt ? On commence"
- Pas de présentation longue, direct au sujet

---

### Minutes 2-7 : Questions théoriques rapides
Prof va poser **4-5 questions basiques** pour tester si t'as les bases :

**Questions probables :**
- "C'est quoi la différence entre monolithe et microservices ?"
- "Pourquoi vous avez choisi Kafka ?"
- "Expliquez-moi le pattern SAGA en 2 phrases"
- "C'est quoi un API Gateway ?"
- "Comment on scale avec Kubernetes ?"

**⚠️ PIÈGE** : Si tu bloques sur une question basique → il insiste → tu perds du temps

---

### Minutes 7-12 : Question de fond
Il va choisir **UN sujet** et creuser :
- Soit communication asynchrone (Kafka)
- Soit gestion des données (database-per-service)
- Soit orchestration (Kubernetes)

**Exemple de question :**
> "Vous utilisez Kafka dans votre projet. Que se passe-t-il si le chat_service est down quand battle_service envoie un event ?"

**Réponse attendue :**
- L'event reste dans Kafka (persistance)
- Quand chat_service redémarre, il consomme les events en attente
- C'est pour ça qu'on utilise Kafka et pas REST

---

### Minutes 12-15 : Cas pratique théorique
**Exemple :**
> "Si je vous demande d'ajouter un service de notifications email, vous le feriez comment ?"

**Ce qu'il teste :** Si t'as compris l'architecture, pas si tu sais coder

**Bonne réponse :**
1. Nouveau microservice `notification_service`
2. S'abonne au topic Kafka `battle-events`
3. Envoie un email quand bataille terminée
4. Base de données séparée pour l'historique des notifications

---

## 🖥️ PARTIE 2 : PROJET (15 min)

### Minutes 15-17 : Présentation rapide
- "Présentez-moi votre architecture en 2 minutes"
- Tu montres le schéma (si t'en as un) ou tu expliques oralement
- Les 5 services + leurs rôles

**Ce que tu dis :**
> "J'ai 5 microservices : auth pour l'authentification JWT, pokedex pour les données Pokémon, team pour la gestion des équipes, battle pour les combats avec calcul d'avantages de types, et chat pour les notifications temps réel via WebSocket. Ils communiquent de façon asynchrone via Kafka."

---

### Minutes 17-25 : Code Deep Dive
Le prof va choisir **UN fichier** et te demander de l'expliquer ligne par ligne.

#### 🎯 Scénario 1 : battle_service/routes/battle.py (LE PLUS PROBABLE)

**Questions attendues :**
- "Expliquez-moi la route `play_turn()`"
- "Pourquoi vous publiez l'event APRÈS avoir enregistré en BDD ?"
- "Que se passe-t-il si Kafka est down ici ?"

**Ce que tu dois expliquer :**
```python
@router.post("/{battle_id}/turn", response_model=TurnResult)
async def play_turn(battle_id: UUID, payload: TurnPlay, db: AsyncSession = Depends(get_db)):
    # 1. Calcul des avantages de types
    fa, fb = calc_advantage(payload.types_red, payload.types_blue)
    
    # 2. Détermination du gagnant
    result = resolve_turn(payload.types_red, payload.types_blue)
    
    # 3. Sauvegarde en BDD
    turn = BattleTurn(...)
    db.add(turn)
    await db.commit()
    
    # 4. Publication asynchrone dans Kafka
    await publish_battle_event("turn_played", {...})
    
    # 5. Retour immédiat au client
    return turn
```

**Points à mentionner :**
- ✅ Persistance d'abord (BDD), notification après
- ✅ Si Kafka fail, le tour est quand même enregistré
- ✅ publish_battle_event est async mais on attend pas la réponse du chat_service
- ⚠️ Redondance : `calc_advantage()` appelé 2 fois (dans resolve_turn aussi)

---

#### 🎯 Scénario 2 : chat_service/main.py

**Questions attendues :**
- "Expliquez-moi ce consumer Kafka"
- "C'est quoi ce `retry_delay` ?"
- "Pourquoi un `while True` ?"

**Ce que tu dois expliquer :**
```python
async def kafka_consumer_loop():
    retry_delay = 2
    while True:
        try:
            consumer = AIOKafkaConsumer(...)
            await consumer.start()
            retry_delay = 2  # Reset après succès
            
            async for msg in consumer:
                # Traitement du message
                ...
        except Exception as e:
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)  # Exponential backoff
```

**Points à mentionner :**
- ✅ `while True` : service qui tourne en continu
- ✅ Retry exponentiel : 2s → 4s → 8s → 16s → 30s max
- ✅ Reset après succès : ne pénalise pas les erreurs temporaires
- ✅ Résilience : si Kafka crash, le service réessaye automatiquement

---

#### 🎯 Scénario 3 : auth_service (moins probable)

**Questions attendues :**
- "Comment vous gérez les JWT ?"
- "Où est stocké le secret ?"
- "Combien de temps est valide un token ?"

---

### Minutes 25-28 : Questions de modification

**Exemples de questions :**
- "Si je vous demande d'ajouter un timeout sur Kafka, où vous le mettez ?"
  → Dans la config du producer : `request_timeout_ms=10000`

- "Comment vous feriez pour logger tous les events ?"
  → Middleware dans battle_service avant publish + logging dans chat_service après consommation

- "Si le battle dure trop longtemps, comment vous gérez ?"
  → Ajouter un champ `max_turns` dans la table battles + vérification avant chaque tour

---

### Minutes 28-30 : Conclusion
- "Vous avez des questions ?"
- Ou "Ok merci, vous pouvez sortir"

---

## 🎯 CE QUI FAIT VRAIMENT LA DIFFÉRENCE

### ✅ À FAIRE
- Répondre **vite** aux questions basiques (gagne du temps pour le code)
- Dire **"je sais pas"** plutôt que d'inventer (le prof préfère l'honnêteté)
- Montrer la **logique** : "Ici j'ai fait ça PARCE QUE..."
- Avoir **UN truc que tu maîtrises à fond** (genre l'avantage de types)

### ❌ À ÉVITER
- Inventer des réponses
- Parler trop vite ou trop lentement
- Dire "j'ai oublié" pour tout
- Critiquer ton propre code négativement

---

## 🔥 QUESTIONS PIÈGES CLASSIQUES

### 1. "Pourquoi pas un monolithe ?"
**Réponse attendue :**
- Scalabilité indépendante (scale battle_service sans scaler auth)
- Déploiement séparé (mise à jour chat sans redémarrer tout)
- Technologies différentes possibles (Python + Node.js + Go)
- Isolation des pannes (si chat crash, auth continue)

### 2. "C'est quoi la différence entre GET et POST ?"
**⚠️ Si tu hésites = mauvais signe**
- GET : récupération de données (idempotent)
- POST : création de ressources (non idempotent)
- PUT : mise à jour complète
- DELETE : suppression

### 3. "Kafka vs REST, pourquoi ?"
**Réponse :**
- **Asynchrone** : battle_service ne bloque pas en attendant chat_service
- **Découplage** : services ne se connaissent pas directement
- **Retry automatique** : si chat_service down, les events sont conservés
- **Performance** : pas de timeout HTTP à gérer

### 4. "Vous avez testé votre code ?"
**⚠️ Sois honnête :**
- "Pas de tests unitaires automatisés"
- "J'ai testé manuellement avec Postman/curl"
- "J'ai vérifié les logs Docker"
- *(Si tu mens, il peut demander de les montrer)*

### 5. "C'est quoi database-per-service ?"
**Réponse :**
- Chaque microservice a **sa propre BDD**
- battle_service → `battle_db`
- auth_service → `auth_db`
- **Avantage** : isolation, pas de dépendance
- **Inconvénient** : pas de JOIN entre services

---

## 📊 RÉPARTITION DU TEMPS

| Phase | Temps | Contenu |
|-------|-------|---------|
| Questions théoriques rapides | 5 min | 4-5 questions de base |
| Question de fond | 5 min | 1 sujet creusé (Kafka, BDD, K8s) |
| Cas pratique | 3 min | "Ajoutez un service X" |
| Présentation archi | 2 min | Les 5 services + schéma |
| Explication code | 8 min | 1 fichier détaillé |
| Questions modification | 3 min | "Et si..." |
| Conclusion | 4 min | Questions/sortie |

---

## 🎯 PRÉDICTIONS RÉALISTES

### Si tu finis le plan à 75% :
**Note attendue : 10-12/20** ✅ (PASSAGE)
- Tu réponds aux questions basiques
- Tu expliques battle.py ou chat main.py correctement
- Tu montres que tu comprends la logique

### Si tu bachottes juste la veille :
**Note attendue : 6-8/20** ❌ (RATÉ)
- Tu hésites sur les bases
- Tu ne sais pas expliquer ton code
- Le prof sent que tu as juste lu sans comprendre

### Si tu maîtrises tes 3 piliers + théorie :
**Note attendue : 12-14/20** 🎉 (BIEN)
- Tu réponds avec assurance
- Tu proposes des améliorations
- Tu montres une vraie compréhension

---

## 🎓 TON OBJECTIF : PASSAGE (10/20)

**Ce qu'il faut ABSOLUMENT maîtriser :**
1. **battle_service** : play_turn() ligne par ligne
2. **chat_service** : kafka_consumer_loop() + retry logic
3. **Kafka** : pourquoi asynchrone, que se passe-t-il si service down
4. **Monolithe vs Microservices** : 3 avantages, 3 inconvénients
5. **Types Pokémon** : avantage Feu vs Plante = 2x (ton truc unique)

**Si tu maîtrises ces 5 points = 10/20 GARANTI** ✅

---

## 💪 DERNIERS CONSEILS

1. **La veille de l'oral** : Relis juste battle.py et chat main.py, ne découvre rien de nouveau
2. **Le matin même** : Relis la fiche 01 (Introduction Microservices)
3. **Dans la salle** : Respire, parle lentement, c'est OK de réfléchir 5 secondes avant de répondre
4. **Si tu bloques** : "Je ne suis pas sûr mais je dirais que..." (mieux que le silence)

**BON COURAGE ! 🚀**
