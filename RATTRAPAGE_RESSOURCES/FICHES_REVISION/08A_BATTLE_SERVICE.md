# 🥊 FICHE 08A : battle_service — Moteur F(A) + Routes + Kafka Producer

> Basée sur le rapport (page 3-4) + ton vrai code.
> **Ce que tu dois dire = ce qui est dans le rapport, pas autre chose.**

---

## 🎯 PRÉSENTATION (à dire en 30 secondes)

> *"Le battle_service contient le moteur qui calcule la puissance d'un Pokémon A contre un Pokémon B. On regarde les types de A et B, on applique les multiplicateurs officiels Pokémon, et on obtient un score F(A) et F(B). Le tour est sauvegardé en BDD, puis un événement est envoyé dans Kafka pour notifier le chat."*

---

## 1. Le moteur F(A) — `calc_advantage()`

**Fichier :** `api/battle_service/app/services/battle_engine.py`

### Le code complet

```python
def calc_advantage(types_a, types_b):
    if not types_a or not types_b:
        return 0.0, 0.0

    # Si 1 seul type → on le compte 2 fois
    ta = types_a if len(types_a) == 2 else [types_a[0], types_a[0]]
    tb = types_b if len(types_b) == 2 else [types_b[0], types_b[0]]

    fa = 0.0
    for w in ta:           # Pour chaque type de A
        val = 1.0
        for y in tb:       # Contre chaque type de B
            val *= get_multiplier(w, y)
        fa += val

    fb = 0.0
    for y in tb:
        val = 1.0
        for w in ta:
            val *= get_multiplier(y, w)
        fb += val

    return round(fa, 4), round(fb, 4)
```

### Ce que ça fait étape par étape

**Étape 1 : Normalisation des types**
```
Pokémon A = ["Feu"]      → ta = ["Feu", "Feu"]   (dupliqué)
Pokémon B = ["Plante", "Sol"]  → tb = ["Plante", "Sol"]  (déjà 2 types)
```

**Étape 2 : Calcul de F(A) = score de A contre B**
```
Pour type "Feu" de A :
    val = get_multiplier("Feu", "Plante") × get_multiplier("Feu", "Sol")
    val = 2.0 × 2.0 = 4.0
    fa += 4.0

Pour type "Feu" de A (encore, car dupliqué) :
    val = 2.0 × 2.0 = 4.0
    fa += 4.0

→ fa = 8.0
```

**Étape 3 : Calcul de F(B) = score de B contre A**
```
Pour type "Plante" de B :
    val = get_multiplier("Plante", "Feu") × get_multiplier("Plante", "Feu")
    val = 0.5 × 0.5 = 0.25
    fb += 0.25

Pour type "Sol" de B :
    val = get_multiplier("Sol", "Feu") × get_multiplier("Sol", "Feu")
    val = 2.0 × 2.0 = 4.0
    fb += 4.0

→ fb = 4.25
```

**Résultat :** F(A) = 8.0 > F(B) = 4.25 → **A (Rouge) gagne ce tour**

---

### Pourquoi dupliquer le type si 1 seul ?

**Ce qu'il faut dire (du rapport) :**
> *"Pour éviter qu'un Pokémon avec un seul type soit désavantagé, on considère son type deux fois dans le calcul."*

**Exemple concret :**
- Sans duplication : Pokémon mono-type a 1 interaction, bi-type en a 4 → déséquilibre
- Avec duplication : les deux ont toujours 4 interactions → comparaison équitable

---

## 2. `resolve_turn()` — Qui gagne ?

```python
def resolve_turn(types_a, types_b):
    fa, fb = calc_advantage(types_a, types_b)
    if fa > fb:
        return "A"
    if fb > fa:
        return "B"
    return "draw"
```

Juste : compare F(A) et F(B), retourne `"A"`, `"B"` ou `"draw"`.

---

## 3. Les routes — `routes/battle.py`

### Route `/battles/` — Créer une salle

```python
@router.post("/")
async def create_battle(payload: BattleCreate, db: AsyncSession = Depends(get_db)):
    status_initial = "en_cours" if payload.player_blue_id else "en_attente"
    battle = Battle(
        player_red_id=payload.player_red_id,
        status=status_initial,
    )
    db.add(battle)
    await db.commit()
    return battle
```

**Logique des statuts :**
- `player_blue_id` fourni → `"en_cours"` (mode direct)
- Pas de `player_blue_id` → `"en_attente"` (mode lobby, quelqu'un rejoint après)

---

### Route `/{id}/join` — Rejoindre une salle

**Les 4 vérifications (à connaître) :**
```python
if not battle:                                    → 404 Bataille introuvable
if battle.status != "en_attente":                 → 400 Salle pas en attente
if battle.player_blue_id is not None:             → 400 Salle déjà complète
if str(battle.player_red_id) == str(player_id):  → 400 Pas contre soi-même
```

Après : `battle.status = "en_cours"` et commit.

---

### Route `/{id}/turn` — Jouer un tour ⭐ (LA PLUS IMPORTANTE)

**Les 5 étapes dans l'ordre :**

```
1. Vérifier  → bataille existe + pas terminée
2. Calculer  → fa, fb = calc_advantage()  +  result = resolve_turn()
3. Créer     → objet BattleTurn avec tous les scores
4. Sauvegarder → db.add(turn) + db.commit()   ← BDD EN PREMIER
5. Notifier  → publish_battle_event("turn_played", {...})  ← KAFKA APRÈS
6. Retourner → return turn
```

**La phrase clé du rapport :**
> *"Si Kafka ne fonctionne pas, le tour est quand même enregistré : le jeu continue normalement, même sans notification."*

---

## 4. Kafka Producer — `kafka_service.py`

```python
async def publish_battle_event(event_type: str, data: dict) -> None:
    try:
        producer = await get_producer()
        payload = {"type": event_type, **data}
        await producer.send_and_wait(settings.KAFKA_TOPIC_BATTLE, payload)
    except Exception as exc:
        _producer = None           # Reset → reconnexion au prochain appel
        logger.warning("Kafka unavailable, event dropped: %s", exc)
        # Pas de raise → le tour continue quand même
```

**Points importants :**
- `send_and_wait` → attend la confirmation Kafka (fiable)
- Exception attrapée silencieusement → **résilience délibérée** (comme dans le rapport)
- `_producer = None` → force reconnexion au prochain tour

---

## 🔥 QUESTIONS PROBABLES SUR battle_service

| Question | Réponse courte |
|----------|---------------|
| "Expliquez F(A) avec un exemple" | Feu vs Plante = get_multiplier("Feu","Plante") = 2.0 → A fort |
| "Pourquoi dupliquer le type ?" | Équité entre mono-type et bi-type |
| "Pourquoi BDD avant Kafka ?" | Le tour est critique, la notif non. Si Kafka down, jeu continue |
| "Que se passe-t-il si Kafka est down ?" | Exception attrapée, event droppé, tour quand même sauvegardé |
| "C'est quoi `resolve_turn()` ?" | Compare fa et fb, retourne A/B/draw |
| "Pourquoi `en_attente` comme statut ?" | Mode multijoueur lobby : joueur rouge crée, joueur bleu rejoint |
