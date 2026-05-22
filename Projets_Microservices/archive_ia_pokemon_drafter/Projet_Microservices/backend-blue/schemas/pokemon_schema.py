"""
Pydantic schemas for Pokemon DTOs
"""
from pydantic import BaseModel
from typing import Optional, Dict


class PokemonBase(BaseModel):
    id: int
    name: str
    type_primary: str
    type_secondary: Optional[str] = None


class PokemonDetail(PokemonBase):
    height: int
    weight: int
    stats: Dict[str, int]
    description: Optional[str] = None
    habitat: Optional[str] = None
    sprite_url: Optional[str] = None


class PokemonSearchRequest(BaseModel):
    name: Optional[str] = None
    type_primary: Optional[str] = None
    type_secondary: Optional[str] = None
    limit: int = 20
    offset: int = 0


class PokemonSearchResponse(BaseModel):
    pokemon: list[PokemonBase]
    total: int
    limit: int
    offset: int
