"""
Pydantic schemas for Team DTOs
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


class TeamBase(BaseModel):
    name: str
    pokemon_ids: List[int]
    
    @field_validator('pokemon_ids')
    @classmethod
    def validate_team_size(cls, v):
        if len(v) > 6:
            raise ValueError('Team cannot have more than 6 Pokemon')
        if len(v) == 0:
            raise ValueError('Team must have at least 1 Pokemon')
        return v


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    pokemon_ids: Optional[List[int]] = None
    
    @field_validator('pokemon_ids')
    @classmethod
    def validate_team_size(cls, v):
        if v is not None:
            if len(v) > 6:
                raise ValueError('Team cannot have more than 6 Pokemon')
            if len(v) == 0:
                raise ValueError('Team must have at least 1 Pokemon')
        return v


class TeamResponse(TeamBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TeamCompletionRequest(BaseModel):
    team_id: int
    num_recommendations: int = 1


class TeamCompletionResponse(BaseModel):
    team_id: int
    current_pokemon: List[int]
    recommended_pokemon: List[int]
    reasoning: Optional[str] = None
