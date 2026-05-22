"""
Pydantic schemas for Duel/Game DTOs
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class DuelCreateRequest(BaseModel):
    opponent_id: int
    mode: str  # random, constructed, draft
    team_id: Optional[int] = None  # Required for constructed mode


class DuelResponse(BaseModel):
    id: int
    player1_id: int
    player2_id: int
    mode: str
    status: str
    winner_id: Optional[int] = None
    current_turn: int
    turn_deadline: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DuelAction(BaseModel):
    pokemon_id: Optional[int] = None  # None means "stay"
    action_type: str  # "switch" or "stay"


class DuelTurnResult(BaseModel):
    turn_number: int
    player1_pokemon_id: int
    player2_pokemon_id: int
    player1_action: str
    player2_action: str
    advantage_p1: float
    advantage_p2: float
    result: str  # p1_wins, p2_wins, draw
    knocked_out_pokemon: List[int]


class DuelDetailResponse(DuelResponse):
    player1_team: List[int]
    player2_team: List[int]
    player1_active_pokemon: Optional[int] = None
    player2_active_pokemon: Optional[int] = None
    player1_knocked_out: List[int]
    player2_knocked_out: List[int]
    turns: List[DuelTurnResult]


class DuelHistoryResponse(BaseModel):
    duels: List[DuelResponse]
    total: int


class DraftPickRequest(BaseModel):
    duel_id: int
    pokemon_id: int
    pick_order: int


class DuelChatMessageRequest(BaseModel):
    message: str


class DuelChatMessageResponse(BaseModel):
    id: int
    duel_id: int
    username: str
    message: str
    is_bot: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
