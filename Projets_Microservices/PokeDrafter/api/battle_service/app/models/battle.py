import uuid
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Battle(Base):
    __tablename__ = "battles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_red_id = Column(UUID(as_uuid=True), nullable=False)
    player_blue_id = Column(UUID(as_uuid=True), nullable=True)  # nullable : rejoint via /join
    mode = Column(
        Enum("construit", "hasard", "pioche", name="battle_mode"),
        nullable=False,
        default="construit",
    )
    status = Column(
        Enum("en_attente", "en_cours", "termine", name="battle_status"),
        nullable=False,
        default="en_attente",
    )
    winner = Column(String(10), nullable=True)  # 'red', 'blue', 'draw'
    current_turn = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    turns = relationship("BattleTurn", back_populates="battle", order_by="BattleTurn.turn_number", lazy="selectin")


class BattleTurn(Base):
    __tablename__ = "battle_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    battle_id = Column(UUID(as_uuid=True), ForeignKey("battles.id"), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)
    pokemon_red = Column(String(100), nullable=False)
    pokemon_blue = Column(String(100), nullable=False)
    types_red = Column(JSON, nullable=False)  # ex: ["Feu", "Vol"]
    types_blue = Column(JSON, nullable=False)
    score_red = Column(String(20), nullable=True)   # fa arrondi
    score_blue = Column(String(20), nullable=True)
    result = Column(String(10), nullable=False)  # 'A', 'B', 'draw'
    played_at = Column(DateTime(timezone=True), server_default=func.now())

    battle = relationship("Battle", back_populates="turns")
