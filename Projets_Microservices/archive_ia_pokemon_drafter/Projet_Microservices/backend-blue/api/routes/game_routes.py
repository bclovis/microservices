"""
Game/Duel routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from schemas.game_schema import (
    DuelCreateRequest, DuelResponse, DuelDetailResponse,
    DuelAction, DuelHistoryResponse
)
from services.game_service import GameService
from core.security import verify_team_access
from api.dependencies import get_db

router = APIRouter(prefix="/duel", tags=["Duels"])


@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_duel(
    duel_data: DuelCreateRequest,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Create a new duel"""
    game_service = GameService(db)
    return await game_service.create_duel(
        player1_id=current_user["user_id"],
        opponent_id=duel_data.opponent_id,
        mode=duel_data.mode,
        team_id=duel_data.team_id
    )


@router.get("/{duel_id}", response_model=DuelResponse)
async def get_duel(
    duel_id: int,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Get duel details"""
    game_service = GameService(db)
    return game_service.get_duel(duel_id)


@router.post("/{duel_id}/forfeit")
async def forfeit_duel(
    duel_id: int,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Forfeit a duel"""
    game_service = GameService(db)
    return game_service.forfeit_duel(duel_id, current_user["user_id"])


@router.get("/history/me", response_model=List[DuelResponse])
async def get_my_history(
    limit: int = 50,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Get current user's duel history"""
    game_service = GameService(db)
    return game_service.get_user_history(current_user["user_id"], limit)
