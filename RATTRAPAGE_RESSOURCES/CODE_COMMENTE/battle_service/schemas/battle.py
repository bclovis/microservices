# =============================================================================
# BATTLE SERVICE — schemas/battle.py
# Schémas Pydantic : validation des données entrantes et sortantes de l'API
# =============================================================================
# RÔLE DU FICHIER :
# Les schémas Pydantic sont différents des modèles SQLAlchemy !
#   - Modèles SQLAlchemy (models/) = structure de la TABLE en base de données
#   - Schémas Pydantic (schemas/) = structure des DONNÉES dans les requêtes/réponses HTTP
# Pydantic valide automatiquement les types et lève une erreur 422 si les données sont invalides.
# =============================================================================

from __future__ import annotations  # Permet d'utiliser les annotations de type en forward reference
from enum import Enum                # Pour créer des types énumérés avec validation
from typing import List, Optional    # Types génériques Python
from uuid import UUID                # Pour les champs UUID
from pydantic import BaseModel       # Classe de base de tous les schémas
from datetime import datetime        # Pour les champs de date


# =============================================================================
# ÉNUMÉRATIONS — Valeurs autorisées
# =============================================================================
# str + Enum = l'enum sérialise en string (utile pour JSON)
class BattleMode(str, Enum):
    construit = "construit"   # Joueur amène son équipe pré-construite
    hasard = "hasard"         # Équipes générées aléatoirement
    pioche = "pioche"         # Draft : choix dans un pool partagé


class BattleStatus(str, Enum):
    en_attente = "en_attente"  # Salle créée, attente du 2ème joueur
    en_cours = "en_cours"      # Les deux joueurs sont là, la bataille tourne
    termine = "termine"        # Fin de la bataille, vainqueur déterminé


# =============================================================================
# SCHEMAS D'ENTRÉE (body des requêtes POST)
# =============================================================================

# Body du POST /api/battle/battles (créer une bataille)
class BattleCreate(BaseModel):
    player_red_id: UUID              # Obligatoire : qui crée la salle
    player_blue_id: Optional[UUID] = None  # Optionnel : si non fourni → status "en_attente"
    mode: str = "construit"          # Mode par défaut si non précisé


# Body du POST /api/battle/battles/{id}/join (rejoindre une bataille)
class BattleJoin(BaseModel):
    player_blue_id: UUID  # Le joueur bleu qui rejoint (obligatoire)


# Body du POST /api/battle/battles/{id}/turn (jouer un tour)
class TurnPlay(BaseModel):
    pokemon_red: str          # Nom du Pokémon rouge ex: "Dracaufeu"
    pokemon_blue: str         # Nom du Pokémon bleu ex: "Blastoise"
    types_red: List[str]      # Types du Pokémon rouge ex: ["Feu", "Vol"]
    types_blue: List[str]     # Types du Pokémon bleu ex: ["Eau"]


# =============================================================================
# SCHEMAS DE SORTIE (body des réponses)
# =============================================================================

# Résultat d'un tour (retourné par le POST /turn et dans BattleOut.turns)
class TurnResult(BaseModel):
    turn_number: int
    pokemon_red: str
    pokemon_blue: str
    score_red: Optional[str] = None   # F(A) calculé par battle_engine
    score_blue: Optional[str] = None  # F(B) calculé par battle_engine
    result: str                        # "A", "B", ou "draw"
    played_at: Optional[datetime] = None

    class Config:
        # from_attributes=True : permet de créer ce schéma depuis un objet SQLAlchemy
        # Sinon Pydantic refuse de lire un objet ORM (il attend un dict)
        from_attributes = True


# Représentation complète d'une bataille (retournée par la plupart des routes GET/POST)
class BattleOut(BaseModel):
    id: UUID
    player_red_id: UUID
    player_blue_id: Optional[UUID] = None
    mode: str
    status: str
    winner: Optional[str] = None   # None tant que la bataille n'est pas terminée
    current_turn: int = 0
    created_at: Optional[datetime] = None
    turns: List[TurnResult] = []   # Liste des tours joués (chargée via lazy="selectin")

    class Config:
        from_attributes = True  # Même raison que TurnResult


# =============================================================================
# POURQUOI SÉPARER SCHEMAS ET MODELS ?
# =============================================================================
# 1. SÉCURITÉ : on ne renvoie jamais accidentellement des champs sensibles
#    Ex: le mot de passe ne serait JAMAIS dans un schéma de sortie
# 2. FLEXIBILITÉ : l'API peut évoluer indépendamment de la BDD
# 3. VALIDATION : Pydantic valide les types AVANT qu'on touche à la BDD
#    → erreur 422 (Unprocessable Entity) au lieu d'une exception SQL
# 4. DOCUMENTATION : FastAPI génère la doc Swagger automatiquement depuis les schémas
