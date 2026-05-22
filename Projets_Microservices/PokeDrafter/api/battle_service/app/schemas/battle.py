from __future__ import annotations
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class BattleMode(str, Enum):
    construit = "construit"
    hasard = "hasard"
    pioche = "pioche"


class BattleStatus(str, Enum):
    en_attente = "en_attente"
    en_cours = "en_cours"
    termine = "termine"


class BattleCreate(BaseModel):
    player_red_id: UUID
    player_blue_id: Optional[UUID] = None  # optionnel : l'adversaire peut rejoindre plus tard via /join
    mode: BattleMode = BattleMode.construit


class BattleJoin(BaseModel):
    player_blue_id: UUID


class TurnPlay(BaseModel):
    pokemon_red: str
    pokemon_blue: str
    types_red: List[str]
    types_blue: List[str]


class TurnResult(BaseModel):
    turn_number: int
    pokemon_red: str
    pokemon_blue: str
    score_red: str
    score_blue: str
    result: str  # 'A'=rouge gagne, 'B'=bleu gagne, 'draw'
    played_at: datetime

    class Config:
        from_attributes = True


class BattleOut(BaseModel):
    id: UUID
    player_red_id: UUID
    player_blue_id: Optional[UUID]
    mode: BattleMode
    status: BattleStatus
    winner: Optional[str]
    current_turn: int
    created_at: datetime
    turns: List[TurnResult] = []

    class Config:
        from_attributes = True
