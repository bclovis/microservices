import random
from typing import List
from uuid import UUID
import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.models.team import Team, TeamPokemon
from app.schemas.team import TeamCreate, TeamUpdate

class TeamService:
    async def list_teams(self, db: AsyncSession, user_id: UUID) -> List[Team]:
        result = await db.execute(
            select(Team).where(Team.user_id == user_id).options(selectinload(Team.pokemon))
        )
        return list(result.scalars().all())

    async def get_team(self, db: AsyncSession, team_id: UUID, user_id: UUID) -> Team:
        result = await db.execute(
            select(Team).where(Team.id == team_id, Team.user_id == user_id)
            .options(selectinload(Team.pokemon))
        )
        team = result.scalar_one_or_none()
        if not team:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")
        return team

    async def create_team(self, db: AsyncSession, user_id: UUID, payload: TeamCreate) -> Team:
        team = Team(user_id=user_id, name=payload.name)
        db.add(team)
        await db.flush()
        for p in payload.pokemon:
            db.add(TeamPokemon(team_id=team.id, **p.model_dump()))
        await db.commit()
        await db.refresh(team)
        return await self.get_team(db, team.id, user_id)

    async def update_team(self, db: AsyncSession, team_id: UUID, user_id: UUID, payload: TeamUpdate) -> Team:
        team = await self.get_team(db, team_id, user_id)
        if payload.name:
            team.name = payload.name
        if payload.pokemon is not None:
            for poke in team.pokemon:
                await db.delete(poke)
            await db.flush()
            for p in payload.pokemon:
                db.add(TeamPokemon(team_id=team.id, **p.model_dump()))
        await db.commit()
        return await self.get_team(db, team_id, user_id)

    async def delete_team(self, db: AsyncSession, team_id: UUID, user_id: UUID) -> None:
        team = await self.get_team(db, team_id, user_id)
        await db.delete(team)
        await db.commit()

    async def complete_team(self, db: AsyncSession, team_id: UUID, user_id: UUID) -> Team:
        team = await self.get_team(db, team_id, user_id)
        slots_needed = 6 - len(team.pokemon)
        if slots_needed <= 0:
            return team
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.POKEDEX_SERVICE_URL}/api/pokedex/random/{slots_needed * 3}")
            pool = resp.json()
        used_types = {p.type1 for p in team.pokemon} | {p.type2 for p in team.pokemon if p.type2}
        chosen = []
        used_slots = {p.slot for p in team.pokemon}
        for poke in pool:
            if len(chosen) >= slots_needed:
                break
            types = poke.get("types", [])
            t1 = types[0]["type"]["name"] if types else "normal"
            if t1 not in used_types:
                chosen.append(poke)
                used_types.add(t1)
        for poke in pool:
            if len(chosen) >= slots_needed:
                break
            if poke not in chosen:
                chosen.append(poke)
        next_slot = max(used_slots) + 1 if used_slots else 1
        for poke in chosen[:slots_needed]:
            types = poke.get("types", [])
            t1 = types[0]["type"]["name"] if types else "normal"
            t2 = types[1]["type"]["name"] if len(types) > 1 else None
            db.add(TeamPokemon(
                team_id=team.id, pokemon_id=poke["id"],
                pokemon_name=poke["name"], type1=t1, type2=t2, slot=next_slot,
            ))
            next_slot += 1
        await db.commit()
        return await self.get_team(db, team_id, user_id)

    async def export_team(self, db: AsyncSession, team_id: UUID, user_id: UUID) -> dict:
        team = await self.get_team(db, team_id, user_id)
        return {
            "team_id": str(team.id),
            "name": team.name,
            "pokemon": [
                {"slot": p.slot, "id": p.pokemon_id, "name": p.pokemon_name, "type1": p.type1, "type2": p.type2}
                for p in sorted(team.pokemon, key=lambda x: x.slot)
            ],
        }

team_service = TeamService()