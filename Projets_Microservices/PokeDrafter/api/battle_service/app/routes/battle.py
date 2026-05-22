# TODO: factoriser les vérifs d'erreur, c'est moche là

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.battle import Battle, BattleTurn
from app.schemas.battle import BattleCreate, BattleJoin, BattleOut, TurnPlay, TurnResult
from app.services.battle_engine import calc_advantage, resolve_turn
from app.services.kafka_service import publish_battle_event

router = APIRouter(prefix="/battles", tags=["battles"])


@router.post("/", response_model=BattleOut, status_code=status.HTTP_201_CREATED)
async def create_battle(payload: BattleCreate, db: AsyncSession = Depends(get_db)):
    # Si l'adversaire n'est pas encore connu, la salle est en attente
    status_initial = "en_cours" if payload.player_blue_id else "en_attente"
    battle = Battle(
        player_red_id=payload.player_red_id,
        player_blue_id=payload.player_blue_id,
        mode=payload.mode,
        status=status_initial,
    )
    db.add(battle)
    await db.commit()
    await db.refresh(battle)
    return battle


@router.post("/{battle_id}/join", response_model=BattleOut)
async def join_battle(battle_id: UUID, payload: BattleJoin, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status != "en_attente":
        raise HTTPException(status_code=400, detail="La salle n'est plus en attente")
    if battle.player_blue_id is not None:
        raise HTTPException(status_code=400, detail="La salle est déjà complète")
    if str(battle.player_red_id) == str(payload.player_blue_id):
        raise HTTPException(status_code=400, detail="Impossible de rejoindre sa propre salle")
    battle.player_blue_id = payload.player_blue_id
    battle.status = "en_cours"
    await db.commit()
    await db.refresh(battle)
    return battle


@router.post("/{battle_id}/turn", response_model=TurnResult)
async def play_turn(battle_id: UUID, payload: TurnPlay, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status == "termine":
        raise HTTPException(status_code=400, detail="La bataille est terminée")

    fa, fb = calc_advantage(payload.types_red, payload.types_blue)
    result = resolve_turn(payload.types_red, payload.types_blue)

    turn_number = battle.current_turn + 1
    turn = BattleTurn(
        battle_id=battle_id,
        turn_number=turn_number,
        pokemon_red=payload.pokemon_red,
        pokemon_blue=payload.pokemon_blue,
        types_red=payload.types_red,
        types_blue=payload.types_blue,
        score_red=str(fa),
        score_blue=str(fb),
        result=result,
    )
    db.add(turn)
    battle.current_turn = turn_number
    await db.commit()
    await db.refresh(turn)

    await publish_battle_event("turn_played", {
        "battle_id": str(battle_id),
        "turn_number": turn_number,
        "pokemon_red": payload.pokemon_red,
        "pokemon_blue": payload.pokemon_blue,
        "score_red": str(fa),
        "score_blue": str(fb),
        "result": result,
    })

    return turn


@router.post("/{battle_id}/end")
async def end_battle(battle_id: UUID, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status == "termine":
        raise HTTPException(status_code=400, detail="Déjà terminée")

    # compte les tours gagnés
    res = await db.execute(select(BattleTurn).where(BattleTurn.battle_id == battle_id))
    turns = res.scalars().all()

    if not turns:
        raise HTTPException(status_code=400, detail="Aucun tour joué")

    wins_red = sum(1 for t in turns if t.result == "A")
    wins_blue = sum(1 for t in turns if t.result == "B")

    if wins_red > wins_blue:
        battle.winner = "red"
    elif wins_blue > wins_red:
        battle.winner = "blue"
    else:
        battle.winner = "draw"

    battle.status = "termine"
    await db.commit()
    return {"winner": battle.winner, "wins_red": wins_red, "wins_blue": wins_blue}


@router.post("/{battle_id}/forfeit")
async def forfeit(battle_id: UUID, player_id: UUID, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    if battle.status == "termine":
        raise HTTPException(status_code=400, detail="Déjà terminée")

    if str(battle.player_red_id) == str(player_id):
        battle.winner = "blue"
    elif str(battle.player_blue_id) == str(player_id):
        battle.winner = "red"
    else:
        raise HTTPException(status_code=403, detail="Joueur pas dans cette bataille")

    battle.status = "termine"
    await db.commit()
    return {"detail": "Abandon enregistré", "winner": battle.winner}


@router.get("/{battle_id}", response_model=BattleOut)
async def get_battle(battle_id: UUID, db: AsyncSession = Depends(get_db)):
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Bataille introuvable")
    return battle


@router.get("/history/{user_id}", response_model=List[BattleOut])
async def battle_history(user_id: UUID, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Battle).where(
            (Battle.player_red_id == user_id) | (Battle.player_blue_id == user_id)
        )
    )
    return res.scalars().all()
