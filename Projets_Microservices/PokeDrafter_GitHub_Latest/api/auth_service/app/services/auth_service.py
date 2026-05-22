from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UpdateProfileRequest

class AuthService:
    async def register(self, db: AsyncSession, payload: RegisterRequest) -> User:
        existing = await db.execute(
            select(User).where((User.email == payload.email) | (User.username == payload.username))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "Email or username already taken")

        user = User(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            color=payload.color,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def login(self, db: AsyncSession, payload: LoginRequest) -> TokenResponse:
        result = await db.execute(
            select(User).where(
                (User.email == payload.username_or_email) | (User.username == payload.username_or_email)
            )
        )
        user: Optional[User] = result.scalar_one_or_none()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def get_user(self, db: AsyncSession, user_id: UUID) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return user

    async def update_profile(self, db: AsyncSession, user: User, payload: UpdateProfileRequest) -> User:
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        await db.commit()
        await db.refresh(user)
        return user

auth_service = AuthService()