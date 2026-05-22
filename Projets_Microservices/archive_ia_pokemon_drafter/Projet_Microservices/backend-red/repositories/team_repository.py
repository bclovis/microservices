"""
Team repository - Database access layer for teams
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from models.database import Team


class TeamRepository:
    """Repository for Team database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by ID"""
        return self.db.query(Team).filter(Team.id == team_id).first()
    
    def get_by_user_id(self, user_id: int) -> List[Team]:
        """Get all teams for a user"""
        return self.db.query(Team).filter(Team.user_id == user_id).all()
    
    def create(self, name: str, user_id: int, pokemon_ids: List[int]) -> Team:
        """Create a new team"""
        team = Team(
            name=name,
            user_id=user_id,
            pokemon_ids=pokemon_ids
        )
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team
    
    def update(self, team_id: int, name: Optional[str] = None, 
               pokemon_ids: Optional[List[int]] = None) -> Optional[Team]:
        """Update team"""
        team = self.get_by_id(team_id)
        if not team:
            return None
        
        if name is not None:
            team.name = name
        if pokemon_ids is not None:
            team.pokemon_ids = pokemon_ids
        
        self.db.commit()
        self.db.refresh(team)
        return team
    
    def delete(self, team_id: int) -> bool:
        """Delete a team"""
        team = self.get_by_id(team_id)
        if not team:
            return False
        
        self.db.delete(team)
        self.db.commit()
        return True
    
    def is_owner(self, team_id: int, user_id: int) -> bool:
        """Check if user owns the team"""
        team = self.get_by_id(team_id)
        return team is not None and team.user_id == user_id
