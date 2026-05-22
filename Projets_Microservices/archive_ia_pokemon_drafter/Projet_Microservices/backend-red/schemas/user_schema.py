"""
Pydantic schemas for User DTOs
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    team: str  # RED or BLUE


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar: Optional[str] = None
    team: Optional[str] = None


class UserResponse(UserBase):
    id: int
    team: str
    avatar: str
    points: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    user_id: int
    username: str
    avatar: str
    points: int
    total_duels: int
    wins: int
    losses: int
    
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
