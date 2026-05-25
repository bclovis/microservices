# =============================================================================
# CHAT SERVICE — models/message.py
# Modèle SQLAlchemy : table "messages" en base de données
# =============================================================================
# RÔLE DU FICHIER :
# Définit la structure de la table qui persiste tous les messages du chat.
# Permet de retrouver l'historique des conversations même après un redémarrage.
# =============================================================================

import uuid
from sqlalchemy import Column, DateTime, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"  # Nom de la table dans PostgreSQL (base chat_db)

    # Clé primaire UUID : identifiant unique pour chaque message
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Room (salon) où le message a été envoyé
    # nullable=True car les messages globaux (broadcasts bot) n'ont pas de room
    # index=True : requêtes rapides "WHERE room = 'red'" pour l'historique d'une room
    room = Column(String(100), nullable=True, index=True)

    # Nom de l'auteur (username du joueur ou "bot" pour les messages système)
    author = Column(String(100), nullable=False)

    # Contenu du message (limité à 1000 caractères)
    content = Column(String(1000), nullable=False)

    # is_bot : True si message système (résultat de tour, notification)
    # False si message d'un joueur humain
    # Le frontend peut utiliser ce flag pour styliser différemment les messages
    is_bot = Column(Boolean, default=False)

    # Équipe de l'auteur : "red" ou "blue" (ou None pour les messages de battle room)
    team = Column(String(50), nullable=True)

    # Timestamp d'envoi : généré automatiquement par PostgreSQL
    # index=True : requêtes rapides "ORDER BY sent_at" pour l'historique chronologique
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
