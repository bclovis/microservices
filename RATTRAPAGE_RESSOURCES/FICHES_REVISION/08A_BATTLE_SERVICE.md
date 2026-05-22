# 🥊 FICHE 08A : battle_service — Moteur F(A) + Routes + Kafka Producer

> Basée sur le rapport (page 3-4) + ton vrai code.
> **Ce que tu dois dire = ce qui est dans le rapport, pas autre chose.**

---

## 🎯 PRÉSENTATION (à dire en 30 secondes)

> *"Le battle_service contient le moteur qui calcule la puissance d'un Pokémon A contre un Pokémon B. On regarde les types de A et B, on applique les multiplicateurs officiels Pokémon, et on obtient un score F(A) et F(B). Le tour est sauvegardé en BDD, puis un événement est envoyé dans Kafka pour notifier le chat."*

---

## 1. Le moteur F(A) — `calc_advantage()`

**Fichier :** `api/battle_service/app/services/battle_engine.py`

### Le code réel soumis

```python
# F(A) = somme sur chaque type de A du produit des multis contre chaque type de B
# Conformément à la formule : F(A) = 1*(W/Y)*(W/Z) + 1*(X/Y)*(X/Z)
def calc_advantage(types_a, types_b):
    if not types_a or not types_b:
        return 0.0, 0.0

    fa = 0.0
    for w in types_a:      # Pour chaque type de A
        val = 1.0
        for y in types_b:  # Contre chaque type de B
            val *= get_multiplier(w, y)
        fa += val

    fb = 0.0
    for y in types_b:      # Pour chaque type de B
        val = 1.0
        for w in types_a:  # Contre chaque type de A
            val *= get_multiplier(y, w)
        fb += val

    return round(fa, 4), round(fb, 4)
```

### Ce que ça fait étape par étape

**Exemple : Dracaufeu [Feu, Vol] vs Bulbizarre [Plante, Poison]**

```
Calcul de F(A) — score de Dracaufeu contre Bulbizarre :
  w=Feu  : val = get_multiplier(Feu, Plante) × get_multiplier(Feu, Poison)
           val = 2.0 × 1.0 = 2.0  →  fa += 2.0
  w=Vol  : val = get_multiplier(Vol, Plante) × get_multiplier(Vol, Poison)
           val = 2.0 × 1.0 = 2.0  →  fa += 2.0
  → fa = 4.0

Calcul de F(B) — score de Bulbizarre contre Dracaufeu :
  y=Plante : val = get_multiplier(Plante, Feu) × get_multiplier(Plante, Vol)
             val = 0.5 × 0.5 = 0.25  →  fb += 0.25
  y=Poison : val = get_multiplier(Poison, Feu) × get_multiplier(Poison, Vol)
             val = 1.0 × 1.0 = 1.0   →  fb += 1.0
  → fb = 1.25

→ fa(4.0) > fb(1.25) → A (Rouge) gagne ce tour
```

### Lire le commentaire de la formule

Le commentaire dit : `F(A) = 1*(W/Y)*(W/Z) + 1*(X/Y)*(X/Z)`
- W, X = types du Pokémon A
- Y, Z = types du Pokémon B
- `(W/Y)` = `get_multiplier(W, Y)` (notation maison = efficacité du type W contre Y)

### ⚠️ Point important sur les monotypes

> "Dans cette version du code, si un Pokémon est monotype (`["Feu"]`), la boucle ne fait qu'une itération : F(A) a un seul terme. La formule s'applique aux types disponibles sans ajustement particulier."

Si on te pose une question là-dessus, tu dis : *"On a implémenté la formule telle quelle, en itérant sur les types disponibles du Pokémon."*

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
