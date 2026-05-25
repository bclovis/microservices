# =============================================================================
# BATTLE SERVICE — models/battle.py
# Modèles SQLAlchemy : définition des tables PostgreSQL
# =============================================================================

import uuid  # Pour générer des UUIDs uniques comme clés primaires

# Column : définit une colonne SQL
# DateTime, Enum, Integer, JSON, String, func : types de colonnes SQL
# ForeignKey : clé étrangère (lien entre deux tables)
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String, func

# UUID : type PostgreSQL natif pour les identifiants universels
# Avantage vs Integer : pas de collision si on fusionne des BDD, URL non-devinables
from sqlalchemy.dialects.postgresql import UUID

# relationship : définit les liens ORM entre modèles (JOIN automatique)
from sqlalchemy.orm import relationship

from app.core.database import Base  # La classe de base commune à tous les modèles


# =============================================================================
# TABLE "battles" — Une partie entre deux joueurs
# =============================================================================
class Battle(Base):
    __tablename__ = "battles"  # Nom de la table dans PostgreSQL

    # Clé primaire : UUID v4 (aléatoire, non-séquentiel)
    # as_uuid=True : SQLAlchemy gère la conversion Python UUID ↔ PostgreSQL UUID
    # default=uuid.uuid4 : un nouvel UUID est généré automatiquement à la création
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Joueur rouge (créateur de la salle) — obligatoire
    player_red_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Joueur bleu (rejoint la salle) — nullable car pas encore connu à la création
    # Un battle peut être créé sans adversaire → status "en_attente"
    player_blue_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Mode de jeu : Enum SQL garantit qu'on ne peut stocker que ces 3 valeurs
    # - construit : chaque joueur amène son équipe
    # - hasard : équipes tirées au sort
    # - pioche : les joueurs choisissent parmi un pool commun
    mode = Column(
        Enum("construit", "hasard", "pioche", name="battle_mode"),
        nullable=False,
        default="construit",
    )
    
    # Statut de la bataille : machine à états
    # en_attente → en_cours → termine
    status = Column(
        Enum("en_attente", "en_cours", "termine", name="battle_status"),
        nullable=False,
        default="en_attente",  # Une bataille commence en attente du 2ème joueur
    )
    
    # Vainqueur : NULL tant que la bataille n'est pas terminée
    # Valeurs possibles : 'red', 'blue', 'draw'
    winner = Column(String(10), nullable=True)
    
    # Numéro du tour en cours (incrémenté à chaque tour joué)
    current_turn = Column(Integer, default=0)
    
    # Timestamps automatiques
    # server_default=func.now() : PostgreSQL génère la date côté serveur (pas Python)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # onupdate=func.now() : mis à jour automatiquement à chaque modification
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relation ORM : charge automatiquement les tours associés à cette bataille
    # back_populates : lien bidirectionnel (BattleTurn.battle → this Battle)
    # order_by : les tours sont toujours triés par numéro croissant
    # lazy="selectin" : SQLAlchemy charge les tours avec une requête SELECT IN (efficace)
    turns = relationship(
        "BattleTurn",
        back_populates="battle",
        order_by="BattleTurn.turn_number",
        lazy="selectin"  # Pas de N+1 queries : 1 requête pour battles + 1 pour tous les turns
    )


# =============================================================================
# TABLE "battle_turns" — Un tour d'une bataille
# =============================================================================
class BattleTurn(Base):
    __tablename__ = "battle_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Clé étrangère vers la table "battles"
    # Si la bataille est supprimée, les tours sont automatiquement supprimés (CASCADE implicite)
    # index=True : accélérer les requêtes "WHERE battle_id = ?"
    battle_id = Column(UUID(as_uuid=True), ForeignKey("battles.id"), nullable=False, index=True)
    
    # Numéro du tour dans la séquence (1, 2, 3...)
    turn_number = Column(Integer, nullable=False)
    
    # Noms des Pokémon joués dans ce tour
    pokemon_red = Column(String(100), nullable=False)
    pokemon_blue = Column(String(100), nullable=False)
    
    # Types des Pokémon stockés en JSON
    # Ex: ["Feu", "Vol"] pour un Pokémon avec deux types
    # JSON en PostgreSQL = flexible, pas besoin d'une table intermédiaire pour les types
    types_red = Column(JSON, nullable=False)
    types_blue = Column(JSON, nullable=False)
    
    # Scores calculés par la formule F(A) et F(B) (arrondis à 4 décimales)
    # Stockés en String pour éviter les problèmes de précision float
    score_red = Column(String(20), nullable=True)
    score_blue = Column(String(20), nullable=True)
    
    # Résultat du tour : 'A' (rouge gagne), 'B' (bleu gagne), 'draw'
    result = Column(String(10), nullable=False)
    
    # Quand ce tour a été joué
    played_at = Column(DateTime(timezone=True), server_default=func.now())

    # Lien retour vers la bataille parente
    battle = relationship("Battle", back_populates="turns")

# =============================================================================
# POURQUOI UUID ET PAS INTEGER AUTO-INCREMENT ?
# =============================================================================
# 1. Sécurité : on ne peut pas deviner l'ID d'une bataille (1, 2, 3... c'est trop facile)
# 2. Distribution : si on scinde en plusieurs BDD plus tard, pas de collision d'IDs
# 3. Génération côté app : l'ID est connu AVANT l'insertion en BDD
