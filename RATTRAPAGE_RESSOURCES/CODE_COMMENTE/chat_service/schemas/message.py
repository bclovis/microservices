# =============================================================================
# CHAT SERVICE — schemas/message.py
# Schémas Pydantic : validation des données du chat
# =============================================================================
# RÔLE DU FICHIER :
# Définit la structure des données attendues pour les messages de chat.
# Pydantic valide automatiquement les données reçues et lève une erreur 422
# si les contraintes ne sont pas respectées.
# =============================================================================

from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    # Literal["red", "blue"] = validation stricte : seules ces deux valeurs sont acceptées
    # Si le client envoie "green" → Pydantic lève une ValidationError → FastAPI renvoie 422
    team: Literal["red", "blue"]

    # Nom de l'auteur du message (username du joueur)
    author: str

    # Contenu du message
    content: str

    # Indique si le message vient d'un bot (résultat de tour, notification système)
    # default=False = par défaut les messages sont de vrais joueurs
    is_bot: bool = False
