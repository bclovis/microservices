"""
Game/Duel repository - Database access layer for duels
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from models.database import Duel, DuelTurn, DuelChatMessage
from utils.constants import DUEL_STATUS_PENDING, TURN_TIMEOUT_SECONDS


class GameRepository:
    """Repository for Duel/Game database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, duel_id: int) -> Optional[Duel]:
        """Get duel by ID"""
        return self.db.query(Duel).filter(Duel.id == duel_id).first()
    
    def create(self, player1_id: int, player2_id: int, mode: str,
               player1_team_id: Optional[int] = None,
               player2_team_id: Optional[int] = None) -> Duel:
        """Create a new duel"""
        duel = Duel(
            player1_id=player1_id,
            player2_id=player2_id,
            mode=mode,
            status=DUEL_STATUS_PENDING,
            player1_team_id=player1_team_id,
            player2_team_id=player2_team_id,
            turn_deadline=datetime.utcnow() + timedelta(seconds=TURN_TIMEOUT_SECONDS)
        )
        self.db.add(duel)
        self.db.commit()
        self.db.refresh(duel)
        return duel
    
    def update_status(self, duel_id: int, status: str, 
                      winner_id: Optional[int] = None) -> Optional[Duel]:
        """Update duel status"""
        duel = self.get_by_id(duel_id)
        if not duel:
            return None
        
        duel.status = status
        if winner_id is not None:
            duel.winner_id = winner_id
        
        if status == "completed" or status == "forfeited":
            duel.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(duel)
        return duel
    
    def add_turn(self, duel_id: int, turn_number: int, 
                 player1_pokemon_id: int, player2_pokemon_id: int,
                 player1_action: str, player2_action: str,
                 advantage_p1: dict, advantage_p2: dict,
                 result: str, knocked_out_pokemon: List[int]) -> DuelTurn:
        """Add a turn to duel history"""
        turn = DuelTurn(
            duel_id=duel_id,
            turn_number=turn_number,
            player1_pokemon_id=player1_pokemon_id,
            player2_pokemon_id=player2_pokemon_id,
            player1_action=player1_action,
            player2_action=player2_action,
            advantage_p1=advantage_p1,
            advantage_p2=advantage_p2,
            result=result,
            knocked_out_pokemon=knocked_out_pokemon
        )
        self.db.add(turn)
        
        # Update duel turn counter and deadline
        duel = self.get_by_id(duel_id)
        duel.current_turn = turn_number
        duel.turn_deadline = datetime.utcnow() + timedelta(seconds=TURN_TIMEOUT_SECONDS)
        
        self.db.commit()
        self.db.refresh(turn)
        return turn
    
    def get_turns(self, duel_id: int) -> List[DuelTurn]:
        """Get all turns for a duel"""
        return self.db.query(DuelTurn).filter(DuelTurn.duel_id == duel_id)\
            .order_by(DuelTurn.turn_number).all()
    
    def get_user_duels(self, user_id: int, limit: int = 50) -> List[Duel]:
        """Get all duels for a user"""
        return self.db.query(Duel)\
            .filter((Duel.player1_id == user_id) | (Duel.player2_id == user_id))\
            .order_by(Duel.created_at.desc())\
            .limit(limit)\
            .all()
    
    def add_chat_message(self, duel_id: int, user_id: Optional[int],
                         username: str, message: str, is_bot: bool = False) -> DuelChatMessage:
        """Add a chat message to a duel"""
        chat_msg = DuelChatMessage(
            duel_id=duel_id,
            user_id=user_id,
            username=username,
            message=message,
            is_bot=is_bot
        )
        self.db.add(chat_msg)
        self.db.commit()
        self.db.refresh(chat_msg)
        return chat_msg
    
    def get_chat_messages(self, duel_id: int, limit: int = 100) -> List[DuelChatMessage]:
        """Get chat messages for a duel"""
        return self.db.query(DuelChatMessage)\
            .filter(DuelChatMessage.duel_id == duel_id)\
            .order_by(DuelChatMessage.created_at.desc())\
            .limit(limit)\
            .all()
