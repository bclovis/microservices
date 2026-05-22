"""
Team service - Business logic for team management
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
import httpx
from repositories.team_repository import TeamRepository
from repositories.pokemon_repository import PokemonRepository
from schemas.team_schema import TeamCreate, TeamUpdate
from core.config import settings
from models.database import Team


class TeamService:
    """Service for team operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.team_repo = TeamRepository(db)
        self.pokemon_repo = PokemonRepository(db)
    
    def get_user_teams(self, user_id: int) -> List[Team]:
        """Get all teams for a user"""
        return self.team_repo.get_by_user_id(user_id)
    
    def get_team(self, team_id: int, user_id: int) -> Team:
        """Get a specific team"""
        team = self.team_repo.get_by_id(team_id)
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        if team.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this team"
            )
        
        return team
    
    def create_team(self, team_data: TeamCreate, user_id: int) -> Team:
        """Create a new team"""
        # Validate team size
        if len(team_data.pokemon_ids) > 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team cannot have more than 6 Pokemon"
            )
        
        # Create team
        return self.team_repo.create(
            name=team_data.name,
            user_id=user_id,
            pokemon_ids=team_data.pokemon_ids
        )
    
    def update_team(self, team_id: int, team_data: TeamUpdate, user_id: int) -> Team:
        """Update an existing team"""
        # Verify ownership
        if not self.team_repo.is_owner(team_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this team"
            )
        
        # Update team
        updated = self.team_repo.update(
            team_id=team_id,
            name=team_data.name,
            pokemon_ids=team_data.pokemon_ids
        )
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        return updated
    
    def delete_team(self, team_id: int, user_id: int) -> bool:
        """Delete a team"""
        # Verify ownership
        if not self.team_repo.is_owner(team_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this team"
            )
        
        return self.team_repo.delete(team_id)
    
    async def complete_team(self, team_id: int, user_id: int, num_recommendations: int = 1) -> dict:
        """Get recommendations to complete a team"""
        team = self.get_team(team_id, user_id)
        
        # Call recommendation service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.recommendation_service_url}/recommend",
                    json={
                        "pokemon_ids": team.pokemon_ids,
                        "num_recommendations": num_recommendations
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Recommendation service unavailable"
                    )
                
                return response.json()
            
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Could not connect to recommendation service"
                )
