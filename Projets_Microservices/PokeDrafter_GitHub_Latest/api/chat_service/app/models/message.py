import uuid
from sqlalchemy import Column, DateTime, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room = Column(String(100), nullable=True, index=True)
    author = Column(String(100), nullable=False)
    content = Column(String(1000), nullable=False)
    is_bot = Column(Boolean, default=False)
    team = Column(String(50), nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
