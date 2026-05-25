# =============================================================================
# BATTLE SERVICE — routes/battle.py
# Contrôleur : toutes les routes HTTP de l'API Battle
# =============================================================================
# RÔLE DU FICHIER :
# Ce fichier définit tous les endpoints REST du Battle Service.
# C'est ici que les requêtes HTTP arrivent, sont validées par Pydantic, 
# traitées avec la BDD et les services, puis une réponse est renvoyée.
#
# ROUTES EXPOSÉES (préfixe /api/battle ajouté dans main.py) :
#   GET    /api/battle/battles/open          → lister les salles en attente
#   POST   /api/battle/battles/              → créer une bataille
#   POST   /api/battle/battles/{id}/join     → rejoindre une bataille
#   POST   /api/battle/battles/{id}/turn     → jouer un tour
#   POST   /api/battle/battles/{id}/end      → terminer la bataille
#   POST   /api/battle/battles/{id}/forfeit  → abandonner
#   GET    /api/battle/battles/{id}          → détails d'une bataille
#   GET    /api/battle/battles/history/{uid} → historique d'un joueur
# =============================================================================

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Dépendances et services
from app.core.database import get_db
from app.models.battle import Battle, BattleTurn
from app.schemas.battle import BattleCreate, BattleJoin, BattleOut, TurnPlay, TurnResult
from app.services.battle_engine import calc_advantage, resolve_turn
from app.services.kafka_service import publish_battle_event

# APIRouter : groupe des routes (équivalent d'un Blueprint Flask)
# prefix="/battles" : toutes les routes ici sont sous /battles/...
# tags=["battles"] : groupe dans la doc Swagger
router = APIRouter(prefix="/battles", tags=["battles"])


# =============================================================================
# GET /battles/open — Lister les salles en attente
# =============================================================================
@router.get("/open", response_model=List[BattleOut])
async def list_open_battles(db: AsyncSession = Depends(get_db)):
    # select(Battle).where(...) : génère un SELECT SQL avec clause WHERE
    # .where(Battle.status == "en_attente") : filtre sur le statut
    res = await db.execute(select(Battle).where(Battle.status == "en_attente"))
    # .scalars().all() : transforme le résultat SQLAlchemy en liste d'objets Battle
    return res.scalars().all()


# =============================================================================
# POST /battles/ — Créer une nouvelle bataille
# =============================================================================
# status_code=201 : HTTP Created (plus précis que 200 OK pour une création)
@router.post("/", response_model=BattleOut, status_code=status.HTTP_201_CREATED)
async def create_battle(payload: BattleCreate, db: AsyncSession = Depends(get_db)):
    # Pydantic a déjà validé que player_red_id est un UUID valide
    # Si player_blue_id est fourni → la bataille commence directement "en_cours"
    # Sinon → "en_attente" d'un 2ème joueur
    status_initial = "en_cours" if payload.player_blue_id else "en_attente"
    
    # Création de l'objet ORM (pas encore en BDD)
    battle = Battle(
        player_red_id=payload.player_red_id,
        player_blue_id=payload.player_blue_id,
        mode=payload.mode,
        status=status_initial,
    )
    db.add(battle)          # Ajoute l'objet à la session (file d'attente pour la BDD)
    await db.commit()       # Écrit en BDD (INSERT SQL)
    await db.refresh(battle)  # Recharge depuis la BDD pour récupérer id, created_at etc.
    return battle


# =============================================================================
# POST /battles/{battle_id}/join — Rejoindre une bataille existante
# =============================================================================
@router.post("/{battle_id}/join", response_model=BattleOut)
async def join_battle(battle_id: UUID, payload: BattleJoin, db: AsyncSession = Depends(get_db)):
    # db.get(Battle, battle_id) : SELECT * FROM battles WHERE id = battle_id
    # Plus efficace que select() pour récupérer par clé primaire
    battle = await db.get(Battle, battle_id)
    
    # VALIDATIONS MÉTIER — on vérifie avant de modifier la BDD
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status != "en_attente":
        raise HTTPException(status_code=400, detail="La salle n'est plus en attente")
    if battle.player_blue_id is not None:
        raise HTTPException(status_code=400, detail="La salle est déjà complète")
    # Empêcher un joueur de rejoindre sa propre salle
    if str(battle.player_red_id) == str(payload.player_blue_id):
        raise HTTPException(status_code=400, detail="Impossible de rejoindre sa propre salle")
    
    # Mise à jour de l'état
    battle.player_blue_id = payload.player_blue_id
    battle.status = "en_cours"  # La bataille peut commencer !
    await db.commit()
    await db.refresh(battle)
    return battle


# =============================================================================
# POST /battles/{battle_id}/turn — Jouer un tour (c'est le cœur du service !)
# =============================================================================
@router.post("/{battle_id}/turn", response_model=TurnResult)
async def play_turn(battle_id: UUID, payload: TurnPlay, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status == "termine":
        raise HTTPException(status_code=400, detail="La bataille est terminée")

    # === APPEL AU MOTEUR DE JEU ===
    # calc_advantage retourne F(A) et F(B) selon la formule typologique
    fa, fb = calc_advantage(payload.types_red, payload.types_blue)
    # resolve_turn retourne "A", "B" ou "draw"
    result = resolve_turn(payload.types_red, payload.types_blue)

    # On incrémente le compteur de tours DANS LA BDD
    turn_number = battle.current_turn + 1
    
    # Enregistrement du tour en BDD
    turn = BattleTurn(
        battle_id=battle_id,
        turn_number=turn_number,
        pokemon_red=payload.pokemon_red,
        pokemon_blue=payload.pokemon_blue,
        types_red=payload.types_red,    # Liste JSON stockée directement
        types_blue=payload.types_blue,
        score_red=str(fa),              # Converti en string pour éviter les pb de float
        score_blue=str(fb),
        result=result,
    )
    db.add(turn)
    battle.current_turn = turn_number  # Met à jour le compteur sur la bataille
    await db.commit()
    await db.refresh(turn)

    # === PUBLICATION KAFKA ===
    # ASYNCHRONE et NON-BLOQUANT : même si Kafka est down, le tour est joué
    # Le chat_service consomme cet event pour afficher le résultat en temps réel
    await publish_battle_event("turn_played", {
        "battle_id": str(battle_id),
        "turn_number": turn_number,
        "pokemon_red": payload.pokemon_red,
        "pokemon_blue": payload.pokemon_blue,
        "score_red": str(fa),
        "score_blue": str(fb),
        "result": result,
    })

    return turn  # Retourne le tour créé (converti en TurnResult par Pydantic)


# =============================================================================
# POST /battles/{battle_id}/end — Terminer une bataille et calculer le vainqueur
# =============================================================================
@router.post("/{battle_id}/end")
async def end_battle(battle_id: UUID, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status == "termine":
        raise HTTPException(status_code=400, detail="Déjà terminée")

    # On charge tous les tours de cette bataille
    res = await db.execute(select(BattleTurn).where(BattleTurn.battle_id == battle_id))
    turns = res.scalars().all()

    if not turns:
        raise HTTPException(status_code=400, detail="Aucun tour joué")

    # Comptage des victoires par équipe
    # sum() avec compréhension = Pythonic et efficace
    wins_red = sum(1 for t in turns if t.result == "A")   # "A" = rouge gagne
    wins_blue = sum(1 for t in turns if t.result == "B")  # "B" = bleu gagne

    # Détermination du vainqueur global
    if wins_red > wins_blue:
        battle.winner = "red"
    elif wins_blue > wins_red:
        battle.winner = "blue"
    else:
        battle.winner = "draw"

    battle.status = "termine"
    await db.commit()
    return {"winner": battle.winner, "wins_red": wins_red, "wins_blue": wins_blue}


# =============================================================================
# POST /battles/{battle_id}/forfeit — Abandonner une bataille
# =============================================================================
@router.post("/{battle_id}/forfeit")
async def forfeit(battle_id: UUID, player_id: UUID, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status == "termine":
        raise HTTPException(status_code=400, detail="Déjà terminée")

    # On identifie qui abandonne et on donne la victoire à l'autre
    if str(battle.player_red_id) == str(player_id):
        battle.winner = "blue"   # Rouge abandonne → bleu gagne
    elif str(battle.player_blue_id) == str(player_id):
        battle.winner = "red"    # Bleu abandonne → rouge gagne
    else:
        # Sécurité : on vérifie que le joueur est bien dans cette bataille
        raise HTTPException(status_code=403, detail="Joueur pas dans cette bataille")

    battle.status = "termine"
    await db.commit()
    return {"detail": "Abandon enregistré", "winner": battle.winner}


# =============================================================================
# GET /battles/{battle_id} — Détails d'une bataille
# =============================================================================
@router.get("/{battle_id}", response_model=BattleOut)
async def get_battle(battle_id: UUID, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    # La relation "turns" est chargée automatiquement (lazy="selectin" dans le modèle)
    return battle


# =============================================================================
# GET /battles/history/{user_id} — Historique d'un joueur
# =============================================================================
@router.get("/history/{user_id}", response_model=List[BattleOut])
async def battle_history(user_id: UUID, db: AsyncSession = Depends(get_db)):
    # Recherche les batailles où le joueur est rouge OU bleu
    # L'opérateur | en SQLAlchemy = OR dans le WHERE
    res = await db.execute(
        select(Battle).where(
            (Battle.player_red_id == user_id) | (Battle.player_blue_id == user_id)
        )
    )
    return res.scalars().all()
