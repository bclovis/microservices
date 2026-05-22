# 🎯 CONSEILS STRATÉGIQUES - COMMENT PRIORISER

> **Ta question :** "Des fois je me demande si on se concentre sur les bonnes choses"
> 
> **Réponse courte :** OUI, tu te concentres sur les bonnes choses ! Mais voici comment optimiser encore plus.

---

## ⚡ RÈGLE D'OR : 70% PROJET + 30% COURS

### Pourquoi ?
Le prof va **principalement tester TON CODE** pour vérifier que tu n'as pas juste copié l'IA.

**Répartition du temps :**
- **70%** → battle_service + chat_service (TES parties)
- **20%** → Kafka + Saga (lié à ton projet)
- **10%** → Reste du cours (survol rapide)

---

## 🔥 CE QUI EST **CRITIQUE** (À MAÎTRISER À 100%)

### 1. **calc_advantage() dans battle_service**
**Temps à y passer :** 3-4h total (J5-J6)

**Pourquoi critique ?**
- C'est TON code principal
- Le prof va FORCÉMENT te demander de l'expliquer
- Probabilité 90% qu'il te demande de le modifier en direct

**Ce que tu dois savoir :**
- ✅ Expliquer CHAQUE ligne sans hésiter
- ✅ Recoder from scratch en 15 min
- ✅ Modifier (ajouter un print, gérer 3 types, etc.)
- ✅ Expliquer la formule F(A) avec un exemple concret

**Comment réviser :**
- Relis le code 10 fois
- Explique à voix haute
- Enregistre-toi → réécoute
- Pratique les modifications (voir JOUR 6-7 du plan)

---

### 2. **Kafka consumer avec retry dans chat_service**
**Temps à y passer :** 2-3h total (J6-J7)

**Pourquoi critique ?**
- C'est TON code
- Montre que tu comprends l'asynchrone
- Retry logic = concept avancé

**Ce que tu dois savoir :**
- ✅ Expliquer le loop infini avec try/except
- ✅ Expliquer le backoff exponentiel (2s → 4s → 8s...)
- ✅ Pourquoi on fait un retry au lieu de crasher
- ✅ broadcast_all() vs broadcast()

**Comment réviser :**
- Dessine le flow sur papier
- Explique pourquoi chaque ligne existe
- Pratique : ajoute un print() dans le loop

---

### 3. **Kafka + Saga (FICHE 4)**
**Temps à y passer :** 2h lecture + 1h révision

**Pourquoi critique ?**
- Tu l'as utilisé dans ton projet
- Concept clé des microservices
- Le prof va forcément poser une question dessus

**Ce que tu dois savoir :**
- ✅ Pourquoi Kafka au lieu de REST ?
- ✅ Producer vs Consumer
- ✅ Saga choreography dans ton projet
- ✅ Exemple concret : "Turn played" → Kafka → chat_service

**Comment réviser :**
- Lis FICHE 4 (2h)
- Dessine le flow Kafka de ton projet
- Réponds à la question : "Pourquoi vous avez utilisé Kafka ?"

---

## 📚 CE QUI EST **IMPORTANT** (À COMPRENDRE, PAS À APPRENDRE PAR CŒUR)

### 4. **Microservices basics (FICHE 1)**
**Temps : 1h**
- ✅ Monolithe vs microservices (3 différences)
- ✅ Database per service
- ✅ Docker = quoi ?

**Comment réviser :**
- Lis rapidement (skim)
- Retiens les concepts clés
- Prépare 3 phrases types pour l'oral

---

### 5. **FastAPI (FICHE 2)**
**Temps : 1h**
- ✅ GET/POST/PUT/DELETE
- ✅ Pydantic = validation
- ✅ async/await

**Comment réviser :**
- Lis les exemples de code
- Retiens juste le vocabulaire
- Pas besoin d'apprendre par cœur

---

### 6. **API Gateway + Kubernetes (FICHE 5-6)**
**Temps : 1h total**
- ✅ Rôle du gateway (routage, cache)
- ✅ Kubernetes = orchestration
- ✅ HPA = auto-scaling

**Comment réviser :**
- Survol rapide (skim)
- Retiens les concepts
- Si le prof demande → explique en 2-3 phrases simples

---

## ❌ CE QUI EST **SECONDAIRE** (SKIM SEULEMENT)

### 7. **BDD (FICHE 3)**
**Temps : 30 min max**
- Tu as utilisé PostgreSQL
- Tu sais que chaque service a sa BDD
- C'est suffisant

**Comment réviser :**
- Lis les titres seulement
- Si question à l'oral → "On utilise PostgreSQL avec SQLAlchemy"

---

### 8. **Détails techniques avancés**
**Temps : SKIP**
- Configuration détaillée Docker Compose
- Syntaxe précise YAML Kubernetes
- Détails de l'infrastructure

**Pourquoi skip ?**
- Le prof ne va PAS te demander de réciter du YAML
- Il veut juste savoir si tu COMPRENDS les concepts
- Si question → explique l'idée générale

---

## 🎓 COMMENT LIRE EFFICACEMENT

### **Méthode 1 : SKIM (lecture rapide) - 15 min**
**Quand l'utiliser :** Contenu secondaire (FICHE 5, 6, BDD...)

**Comment faire :**
1. Lis les titres et sous-titres
2. Lis la première phrase de chaque paragraphe
3. Regarde les exemples de code (mais ne les mémorise pas)
4. Retiens 2-3 concepts clés maximum

**Exemple :** FICHE 6 Kubernetes
- Titre : "Kubernetes = orchestration de containers"
- Sous-titre : "HPA = auto-scaling"
- Retenu : "Kubernetes gère le déploiement et scale automatiquement"
- **Temps : 15 min au lieu de 1h → GAIN 45 min !**

---

### **Méthode 2 : DEEP (lecture approfondie) - 1-2h**
**Quand l'utiliser :** Contenu critique (calc_advantage, Kafka consumer, FICHE 4...)

**Comment faire :**
1. Lis lentement ligne par ligne
2. Explique à voix haute ce que tu lis
3. Recopie les schémas sur papier
4. Fais les exercices / auto-tests
5. Enregistre-toi en train d'expliquer

**Exemple :** battle_engine.py
- Lis calc_advantage() ligne par ligne
- Explique chaque variable (`w` = type attaquant, `y` = type défenseur, `val` = multiplicateur cumulé, `fa`/`fb` = score final)
- Dessine le flow
- Pratique : modifie le code
- **Temps : 2h → NÉCESSAIRE pour être solide**

---

## 📊 RÉPARTITION OPTIMALE DU TEMPS (8 JOURS)

```
┌─────────────────────────────────────────┐
│  PROJET (70% = 28h / 40h total)        │
├─────────────────────────────────────────┤
│  - battle_service : 10h                 │
│  - chat_service : 8h                    │
│  - Kafka/Saga : 5h                      │
│  - Simulations orales : 5h              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  COURS (30% = 12h / 40h total)         │
├─────────────────────────────────────────┤
│  - FICHE 1 (Microservices) : 2h        │
│  - FICHE 2 (FastAPI) : 2h              │
│  - FICHE 4 (Kafka + Saga) : 3h         │
│  - FICHE 3,5,6 (SKIM) : 2h             │
│  - Quiz + révisions : 3h                │
└─────────────────────────────────────────┘
```

---

## ⚠️ LES 5 PIÈGES À ÉVITER

### 1. ❌ Passer trop de temps sur les détails
**Mauvais :** Apprendre par cœur la syntaxe YAML Kubernetes
**Bon :** Comprendre que Kubernetes orchestre les containers

### 2. ❌ Lire toutes les fiches en profondeur
**Mauvais :** 2h sur FICHE 6 (Kubernetes)
**Bon :** 15 min SKIM + retenir 3 concepts

### 3. ❌ Négliger le code en direct
**Mauvais :** Juste lire le code
**Bon :** Pratiquer en modifiant et recodant

### 4. ❌ Réviser sans tester
**Mauvais :** Relire 10 fois sans vérifier
**Bon :** Auto-tests + explications à voix haute

### 5. ❌ Stresser sur "tout savoir"
**Mauvais :** "Je dois TOUT maîtriser"
**Bon :** "Je maîtrise L'ESSENTIEL et je comprends le reste"

---

## ✅ CHECKLIST "JE SUIS PRÊT"

### **PROJET (CRITIQUE)**
- [ ] Je peux expliquer calc_advantage() ligne par ligne
- [ ] Je peux recoder calc_advantage() en 15 min
- [ ] Je peux modifier calc_advantage() (ajouter print, 3 types...)
- [ ] Je peux expliquer le consumer Kafka avec retry
- [ ] Je peux dessiner le flow battle_service → Kafka → chat_service
- [ ] Je peux répondre : "Pourquoi Kafka ?"

### **COURS (IMPORTANT)**
- [ ] Je peux citer 3 différences monolithe vs microservices
- [ ] Je peux expliquer "database per service"
- [ ] Je peux dire ce qu'est Kafka (producer/consumer)
- [ ] Je peux expliquer le Saga pattern dans mon projet
- [ ] Je connais les 4 verbes HTTP (GET/POST/PUT/DELETE)
- [ ] Je sais ce qu'est Pydantic

### **ORAL (SIMULATION)**
- [ ] J'ai fait 2 simulations chronométrées 15+15 min
- [ ] Je peux présenter sans bloquer plus de 5 secondes
- [ ] Je peux répondre à "As-tu utilisé l'IA ?" honnêtement

**Si 15/18 ✅ → TU ES PRÊT ! 🔥**

---

## 💪 PLAN D'ACTION IMMÉDIAT

### **AUJOURD'HUI (J1 - 21 mai)**
1. ✅ Finis FICHE 2 FastAPI (SKIM rapide - 45 min)
2. ✅ Commence FICHE 3 BDD (SKIM - 30 min)
3. ✅ Quiz J1-J2 (1h)

### **DEMAIN (J2 - 22 mai)**
1. ✅ FICHE 4 Kafka + Saga (DEEP - 2h) ← **PRIORITÉ ABSOLUE**
2. ✅ Révision J1-J2 (30 min)
3. ✅ TP4 tester Kafka (1h)

### **J3-J4 (23-24 mai)**
1. ✅ FICHE 5-6 (SKIM - 1h total)
2. ✅ Quiz complet (1h)
3. ✅ Révision globale cours (1h)

### **J5-J7 (25-27 mai) ← CRUCIAL**
1. ✅ battle_service DEEP (6h)
2. ✅ chat_service DEEP (4h)
3. ✅ Code en direct practice (4h)

### **J8 (28 mai)**
1. ✅ Simulations orales x2 (4h)
2. ✅ Corrections (2h)

### **J9 (29 mai)**
1. ✅ Révision ciblée matin (3h)
2. ✅ REPOS après-midi
3. 🔥 **ORAL 21H**

---

## 🎯 RÉSUMÉ EN 3 PHRASES

1. **70% PROJET (battle + chat + Kafka) = PRIORITÉ ABSOLUE**
2. **30% COURS = SKIM les fiches secondaires, DEEP seulement FICHE 4**
3. **PRATIQUE > LECTURE = Code en direct + Simulations orales**

---

## 💬 POUR L'ORAL - PHRASES TYPES

### Si tu ne sais pas tout
> "Je ne connais pas tous les détails de [concept], mais dans notre projet on a utilisé [techno] et je peux vous montrer comment ça fonctionne dans notre code."

### Si le prof creuse un détail
> "C'est une bonne question. Dans notre implémentation, on a fait [choix]. Je peux vous montrer le code si vous voulez."

### Si tu as utilisé l'IA
> "Oui j'ai utilisé GitHub Copilot comme assistant, mais je comprends le code. Par exemple, la fonction calc_advantage() calcule les avantages de types Pokémon avec cette formule [explique]. Je peux la modifier si vous voulez."

---

**TU TE CONCENTRES SUR LES BONNES CHOSES ! Continue comme ça ! 🔥**

**Si doute → PRIORITÉ = calc_advantage() + Kafka consumer + FICHE 4**

**Le reste = SKIM ou SKIP si manque de temps !**

**TU VAS RÉUSSIR ! 💪**
