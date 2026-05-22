"""
Game service - Business logic for duels/games
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from repositories.game_repository import GameRepository
from repositories.user_repository import UserRepository
from repositories.team_repository import TeamRepository
from repositories.pokemon_repository import PokemonRepository
from services.pokemon_service import PokemonService
from utils.helpers import calculate_type_advantage, determine_turn_winner
from utils.constants import *
from core.kafka import send_duel_event
import random


class GameService:
    """Service for game/duel operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.game_repo = GameRepository(db)
        self.user_repo = UserRepository(db)
        self.team_repo = TeamRepository(db)
        self.pokemon_repo = PokemonRepository(db)
        self.pokemon_service = PokemonService(db)
    
    async def create_duel(self, player1_id: int, opponent_id: int, mode: str,
                         team_id: Optional[int] = None) -> Dict:
        """Create a new duel"""
        # Validate players exist
        player1 = self.user_repo.get_by_id(player1_id)
        player2 = self.user_repo.get_by_id(opponent_id)
        
        if not player1 or not player2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        # Validate players are from opposite teams
        if player1.team == player2.team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Players must be from opposite teams"
            )
        
        # Validate mode
        if mode not in [DUEL_MODE_RANDOM, DUEL_MODE_CONSTRUCTED, DUEL_MODE_DRAFT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid duel mode"
            )
        
        # For constructed mode, validate team
        player1_team_id = None
        if mode == DUEL_MODE_CONSTRUCTED:
            if not team_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Team ID required for constructed mode"
                )
            
            if not self.team_repo.is_owner(team_id, player1_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to use this team"
                )
            
            player1_team_id = team_id
        
        # Create duel
        duel = self.game_repo.create(
            player1_id=player1_id,
            player2_id=opponent_id,
            mode=mode,
            player1_team_id=player1_team_id
        )
        
        # Send Kafka event
        send_duel_event("duel_created", duel.id, {
            "player1_id": player1_id,
            "player2_id": opponent_id,
            "mode": mode
        })
        
        return {"duel_id": duel.id, "status": "created"}
    
    def get_duel(self, duel_id: int) -> Dict:
        """Get duel details"""
        duel = self.game_repo.get_by_id(duel_id)
        
        if not duel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Duel not found"
            )
        
        return duel
    
    def forfeit_duel(self, duel_id: int, user_id: int) -> Dict:
        """Forfeit a duel"""
        duel = self.game_repo.get_by_id(duel_id)
        
        if not duel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Duel not found"
            )
        
        # Verify user is in the duel
        if duel.player1_id != user_id and duel.player2_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Determine winner (opponent)
        winner_id = duel.player2_id if duel.player1_id == user_id else duel.player1_id
        
        # Update duel status
        self.game_repo.update_status(duel_id, DUEL_STATUS_FORFEITED, winner_id)
        
        # Update points
        self.user_repo.update_points(winner_id, POINTS_WIN)
        self.user_repo.update_points(user_id, POINTS_LOSS)
        
        # Send Kafka event
        send_duel_event("duel_forfeited", duel_id, {
            "forfeiter_id": user_id,
            "winner_id": winner_id
        })
        
        return {"status": "forfeited", "winner_id": winner_id}
    
    def get_user_history(self, user_id: int, limit: int = 50) -> List:
        """Get user's duel history"""
        return self.game_repo.get_user_duels(user_id, limit)
