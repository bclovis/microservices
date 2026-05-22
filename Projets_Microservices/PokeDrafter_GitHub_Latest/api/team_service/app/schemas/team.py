from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class TeamPokemonIn(BaseModel):
    pokemon_id: int
    pokemon_name: str
    type1: str
    type2: Optional[str] = None
    slot: int = Field(..., ge=1, le=6)

class TeamPokemonOut(TeamPokemonIn):
    id: UUID
    model_config = {"from_attributes": True}

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    pokemon: List[TeamPokemonIn] = Field(default_factory=list, max_length=6)

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    pokemon: Optional[List[TeamPokemonIn]] = None

class TeamOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    pokemon: List[TeamPokemonOut]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}