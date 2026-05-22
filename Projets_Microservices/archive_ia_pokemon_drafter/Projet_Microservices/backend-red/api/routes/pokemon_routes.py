"""
Pokemon routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from schemas.pokemon_schema import PokemonDetail, PokemonSearchResponse
from services.pokemon_service import PokemonService
from core.security import verify_team_access
from api.dependencies import get_db

router = APIRouter(prefix="/pokemon", tags=["Pokemon"])


@router.get("/{pokemon_id}", response_model=PokemonDetail)
async def get_pokemon(
    pokemon_id: int,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Get Pokemon details"""
    pokemon_service = PokemonService(db)
    return await pokemon_service.get_pokemon(pokemon_id)


@router.get("/", response_model=PokemonSearchResponse)
async def search_pokemon(
    name: Optional[str] = Query(None),
    type_primary: Optional[str] = Query(None),
    type_secondary: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Search Pokemon"""
    pokemon_service = PokemonService(db)
    return pokemon_service.search_pokemon(name, type_primary, type_secondary, limit, offset)
