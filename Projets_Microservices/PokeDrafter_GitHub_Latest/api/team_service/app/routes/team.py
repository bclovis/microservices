from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user_id, get_db
from app.schemas.team import TeamCreate, TeamOut, TeamUpdate
from app.services.team_service import team_service

router = APIRouter(prefix="/api/teams", tags=["teams"])

@router.get("", response_model=list[TeamOut])
async def list_teams(db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return await team_service.list_teams(db, user_id)

@router.post("", response_model=TeamOut, status_code=201)
async def create_team(payload: TeamCreate, db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return await team_service.create_team(db, user_id, payload)

@router.get("/{team_id}", response_model=TeamOut)
async def get_team(team_id: UUID, db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return await team_service.get_team(db, team_id, user_id)

@router.put("/{team_id}", response_model=TeamOut)
async def update_team(team_id: UUID, payload: TeamUpdate, db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return await team_service.update_team(db, team_id, user_id, payload)

@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: UUID, db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    await team_service.delete_team(db, team_id, user_id)

@router.post("/{team_id}/complete", response_model=TeamOut)
async def complete_team(team_id: UUID, db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return await team_service.complete_team(db, team_id, user_id)

@router.get("/{team_id}/export")
async def export_team(team_id: UUID, db: AsyncSession = Depends(get_db), user_id: UUID = Depends(get_current_user_id)):
    return await team_service.export_team(db, team_id, user_id)