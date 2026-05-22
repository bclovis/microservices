"""
Pokemon cache repository - Database access for cached Pokemon data
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from models.database import PokemonCache


class PokemonRepository:
    """Repository for Pokemon cache operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, pokemon_id: int) -> Optional[PokemonCache]:
        """Get cached Pokemon by ID"""
        return self.db.query(PokemonCache).filter(PokemonCache.id == pokemon_id).first()
    
    def get_by_name(self, name: str) -> Optional[PokemonCache]:
        """Get cached Pokemon by name"""
        return self.db.query(PokemonCache).filter(PokemonCache.name == name.lower()).first()
    
    def cache_pokemon(self, pokemon_id: int, name: str, type_primary: str,
                      type_secondary: Optional[str], height: int, weight: int,
                      stats: dict, description: Optional[str] = None,
                      habitat: Optional[str] = None, sprite_url: Optional[str] = None) -> PokemonCache:
        """Cache Pokemon data"""
        # Check if already exists
        existing = self.get_by_id(pokemon_id)
        
        if existing:
            # Update existing cache
            existing.name = name.lower()
            existing.type_primary = type_primary
            existing.type_secondary = type_secondary
            existing.height = height
            existing.weight = weight
            existing.stats = stats
            existing.description = description
            existing.habitat = habitat
            existing.sprite_url = sprite_url
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new cache entry
            pokemon = PokemonCache(
                id=pokemon_id,
                name=name.lower(),
                type_primary=type_primary,
                type_secondary=type_secondary,
                height=height,
                weight=weight,
                stats=stats,
                description=description,
                habitat=habitat,
                sprite_url=sprite_url
            )
            self.db.add(pokemon)
            self.db.commit()
            self.db.refresh(pokemon)
            return pokemon
    
    def search(self, name: Optional[str] = None,
               type_primary: Optional[str] = None,
               type_secondary: Optional[str] = None,
               limit: int = 20, offset: int = 0) -> List[PokemonCache]:
        """Search cached Pokemon"""
        query = self.db.query(PokemonCache)
        
        if name:
            query = query.filter(PokemonCache.name.ilike(f"%{name.lower()}%"))
        if type_primary:
            query = query.filter(PokemonCache.type_primary == type_primary.lower())
        if type_secondary:
            query = query.filter(PokemonCache.type_secondary == type_secondary.lower())
        
        return query.offset(offset).limit(limit).all()
    
    def is_cache_valid(self, pokemon_id: int, max_age_hours: int = 24) -> bool:
        """Check if cached Pokemon is still valid"""
        pokemon = self.get_by_id(pokemon_id)
        if not pokemon:
            return False
        
        cache_age = datetime.utcnow() - pokemon.cached_at
        return cache_age < timedelta(hours=max_age_hours)
