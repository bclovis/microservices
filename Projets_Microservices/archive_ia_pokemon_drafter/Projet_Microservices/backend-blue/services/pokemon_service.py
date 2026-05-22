"""
Pokemon service - Business logic for Pokemon operations
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional, List, Dict
import httpx
from repositories.pokemon_repository import PokemonRepository
from core.config import settings
from utils.helpers import normalize_type_name


class PokemonService:
    """Service for Pokemon operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.pokemon_repo = PokemonRepository(db)
    
    async def get_pokemon(self, pokemon_id: int) -> Dict:
        """Get Pokemon details (from cache or API)"""
        # Check cache first
        cached = self.pokemon_repo.get_by_id(pokemon_id)
        
        if cached and self.pokemon_repo.is_cache_valid(pokemon_id):
            return {
                "id": cached.id,
                "name": cached.name,
                "type_primary": cached.type_primary,
                "type_secondary": cached.type_secondary,
                "height": cached.height,
                "weight": cached.weight,
                "stats": cached.stats,
                "description": cached.description,
                "habitat": cached.habitat,
                "sprite_url": cached.sprite_url
            }
        
        # Fetch from PokeAPI
        async with httpx.AsyncClient() as client:
            try:
                # Get Pokemon data
                response = await client.get(f"{settings.pokeapi_base_url}/pokemon/{pokemon_id}", timeout=10.0)
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Pokemon not found"
                    )
                
                data = response.json()
                
                # Get species data for description
                species_response = await client.get(data["species"]["url"], timeout=10.0)
                species_data = species_response.json() if species_response.status_code == 200 else {}
                
                # Extract data
                type_primary = normalize_type_name(data["types"][0]["type"]["name"]) if data["types"] else "normal"
                type_secondary = normalize_type_name(data["types"][1]["type"]["name"]) if len(data["types"]) > 1 else None
                
                # Get French description if available
                description = None
                if "flavor_text_entries" in species_data:
                    fr_entries = [e for e in species_data["flavor_text_entries"] if e["language"]["name"] == "fr"]
                    if fr_entries:
                        description = fr_entries[0]["flavor_text"].replace("\n", " ")
                
                habitat = species_data.get("habitat", {}).get("name") if species_data else None
                
                # Cache the data
                self.pokemon_repo.cache_pokemon(
                    pokemon_id=data["id"],
                    name=data["name"],
                    type_primary=type_primary,
                    type_secondary=type_secondary,
                    height=data["height"],
                    weight=data["weight"],
                    stats={stat["stat"]["name"]: stat["base_stat"] for stat in data["stats"]},
                    description=description,
                    habitat=habitat,
                    sprite_url=data["sprites"].get("front_default")
                )
                
                return {
                    "id": data["id"],
                    "name": data["name"],
                    "type_primary": type_primary,
                    "type_secondary": type_secondary,
                    "height": data["height"],
                    "weight": data["weight"],
                    "stats": {stat["stat"]["name"]: stat["base_stat"] for stat in data["stats"]},
                    "description": description,
                    "habitat": habitat,
                    "sprite_url": data["sprites"].get("front_default")
                }
            
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Could not connect to PokeAPI"
                )
    
    def search_pokemon(self, name: Optional[str] = None,
                      type_primary: Optional[str] = None,
                      type_secondary: Optional[str] = None,
                      limit: int = 20, offset: int = 0) -> Dict:
        """Search Pokemon in cache"""
        pokemon_list = self.pokemon_repo.search(
            name=name,
            type_primary=normalize_type_name(type_primary) if type_primary else None,
            type_secondary=normalize_type_name(type_secondary) if type_secondary else None,
            limit=limit,
            offset=offset
        )
        
        return {
            "pokemon": [
                {
                    "id": p.id,
                    "name": p.name,
                    "type_primary": p.type_primary,
                    "type_secondary": p.type_secondary
                }
                for p in pokemon_list
            ],
            "total": len(pokemon_list),
            "limit": limit,
            "offset": offset
        }
