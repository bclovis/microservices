"""
Dependencies for API routes
"""
from sqlalchemy.orm import Session
from repositories.database import get_db

# Export common dependencies
__all__ = ["get_db"]
