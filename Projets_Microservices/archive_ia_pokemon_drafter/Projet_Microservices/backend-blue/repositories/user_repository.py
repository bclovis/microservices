"""
User repository - Database access layer for users
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from models.database import User
from core.security import hash_password


class UserRepository:
    """Repository for User database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, username: str, email: str, password: str, team: str,
               first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Create a new user"""
        hashed_pwd = hash_password(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_pwd,
            team=team,
            first_name=first_name,
            last_name=last_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_points(self, user_id: int, points_delta: int) -> Optional[User]:
        """Update user points (ensure not below 0)"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        new_points = max(0, user.points + points_delta)
        user.points = new_points
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_all_by_team(self, team: str) -> List[User]:
        """Get all users from a specific team"""
        return self.db.query(User).filter(User.team == team).all()
    
    def delete(self, user_id: int) -> bool:
        """Delete a user"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
