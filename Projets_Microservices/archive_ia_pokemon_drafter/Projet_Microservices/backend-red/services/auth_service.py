"""
Authentication service - Business logic for authentication
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from repositories.user_repository import UserRepository
from core.security import verify_password, create_access_token, hash_password
from schemas.user_schema import UserCreate, UserLogin
from typing import Dict


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def register(self, user_data: UserCreate) -> Dict:
        """Register a new user"""
        # Check if username already exists
        if self.user_repo.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if self.user_repo.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate team
        if user_data.team not in ["RED", "BLUE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team must be RED or BLUE"
            )
        
        # Create user
        user = self.user_repo.create(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            team=user_data.team,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        # Generate token
        token = create_access_token({
            "sub": str(user.id),
            "username": user.username,
            "team": user.team
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
    
    def login(self, login_data: UserLogin) -> Dict:
        """Authenticate user and return token"""
        # Get user by username
        user = self.user_repo.get_by_username(login_data.username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Generate token
        token = create_access_token({
            "sub": str(user.id),
            "username": user.username,
            "team": user.team
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
        
        # Update password
        user.hashed_password = hash_password(new_password)
        self.db.commit()
        
        return True
