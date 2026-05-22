"""
SQLAlchemy models for Pokemon Drafter
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    team = Column(String(10), nullable=False)  # RED or BLUE
    avatar = Column(String(255), default="default_avatar.png")
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teams = relationship("Team", back_populates="user", cascade="all, delete-orphan")
    duels_as_player1 = relationship("Duel", foreign_keys="Duel.player1_id", back_populates="player1")
    duels_as_player2 = relationship("Duel", foreign_keys="Duel.player2_id", back_populates="player2")


class Team(Base):
    """Pokemon team model"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pokemon_ids = Column(JSON, nullable=False)  # List of Pokemon IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="teams")


class Duel(Base):
    """Duel/Game model"""
    __tablename__ = "duels"
    
    id = Column(Integer, primary_key=True, index=True)
    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mode = Column(String(20), nullable=False)  # random, constructed, draft
    status = Column(String(20), default="pending")  # pending, active, completed, forfeited
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    player1_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    player2_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    current_turn = Column(Integer, default=0)
    turn_deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    player1 = relationship("User", foreign_keys=[player1_id], back_populates="duels_as_player1")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="duels_as_player2")
    turns = relationship("DuelTurn", back_populates="duel", cascade="all, delete-orphan")
    chat_messages = relationship("DuelChatMessage", back_populates="duel", cascade="all, delete-orphan")


class DuelTurn(Base):
    """Duel turn history"""
    __tablename__ = "duel_turns"
    
    id = Column(Integer, primary_key=True, index=True)
    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    player1_pokemon_id = Column(Integer, nullable=False)
    player2_pokemon_id = Column(Integer, nullable=False)
    player1_action = Column(String(20), nullable=False)  # switch, stay
    player2_action = Column(String(20), nullable=False)
    advantage_p1 = Column(JSON, nullable=True)  # Advantage calculation
    advantage_p2 = Column(JSON, nullable=True)
    result = Column(String(50), nullable=False)  # p1_wins, p2_wins, draw
    knocked_out_pokemon = Column(JSON, nullable=True)  # List of KO'd Pokemon IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    duel = relationship("Duel", back_populates="turns")


class DuelChatMessage(Base):
    """Chat messages in a duel"""
    __tablename__ = "duel_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for bot messages
    username = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    is_bot = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    duel = relationship("Duel", back_populates="chat_messages")


class PokemonCache(Base):
    """Cache for Pokemon data from PokeAPI"""
    __tablename__ = "pokemon_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    type_primary = Column(String(50), nullable=False)
    type_secondary = Column(String(50), nullable=True)
    height = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    stats = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    habitat = Column(String(100), nullable=True)
    sprite_url = Column(String(255), nullable=True)
    cached_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
