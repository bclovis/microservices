"""
Team management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from schemas.team_schema import TeamCreate, TeamUpdate, TeamResponse, TeamCompletionResponse
from services.team_service import TeamService
from core.security import verify_team_access
from api.dependencies import get_db

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/", response_model=List[TeamResponse])
async def get_my_teams(
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Get all teams for current user"""
    team_service = TeamService(db)
    return team_service.get_user_teams(current_user["user_id"])


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Get a specific team"""
    team_service = TeamService(db)
    return team_service.get_team(team_id, current_user["user_id"])


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    team_service = TeamService(db)
    return team_service.create_team(team_data, current_user["user_id"])


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Update an existing team"""
    team_service = TeamService(db)
    return team_service.update_team(team_id, team_data, current_user["user_id"])


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Delete a team"""
    team_service = TeamService(db)
    team_service.delete_team(team_id, current_user["user_id"])


@router.post("/{team_id}/complete", response_model=TeamCompletionResponse)
async def complete_team(
    team_id: int,
    num_recommendations: int = 1,
    current_user: dict = Depends(verify_team_access),
    db: Session = Depends(get_db)
):
    """Get recommendations to complete a team"""
    team_service = TeamService(db)
    return await team_service.complete_team(team_id, current_user["user_id"], num_recommendations)
