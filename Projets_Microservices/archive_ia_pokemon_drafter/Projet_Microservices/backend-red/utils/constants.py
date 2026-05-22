"""
Constants used throughout the application
"""

# Pokemon type effectiveness table (from project specifications)
# dino was here
TYPE_EFFECTIVENESS = {
    "normal": {"roche": 0.5, "spectre": 0, "acier": 0.5},
    "feu": {"feu": 0.5, "eau": 0.5, "plante": 2, "glace": 2, "insecte": 2, "roche": 0.5, "dragon": 0.5, "acier": 2},
    "eau": {"feu": 2, "eau": 0.5, "plante": 0.5, "sol": 2, "roche": 2, "dragon": 0.5},
    "plante": {"feu": 0.5, "eau": 2, "plante": 0.5, "poison": 0.5, "sol": 2, "vol": 0.5, "insecte": 0.5, "roche": 2, "dragon": 0.5, "acier": 0.5},
    "electrique": {"eau": 2, "electrique": 0.5, "plante": 0.5, "sol": 0, "vol": 2, "dragon": 0.5},
    "glace": {"feu": 0.5, "eau": 0.5, "plante": 2, "glace": 0.5, "sol": 2, "vol": 2, "dragon": 2, "acier": 0.5},
    "combat": {"normal": 2, "glace": 2, "poison": 0.5, "vol": 0.5, "psy": 0.5, "insecte": 0.5, "roche": 2, "spectre": 0, "tenebres": 2, "acier": 2, "fee": 0.5},
    "poison": {"plante": 2, "poison": 0.5, "sol": 0.5, "roche": 0.5, "spectre": 0.5, "acier": 0, "fee": 2},
    "sol": {"feu": 2, "electrique": 2, "plante": 0.5, "poison": 2, "vol": 0, "insecte": 0.5, "roche": 2, "acier": 2},
    "vol": {"electrique": 0.5, "plante": 2, "combat": 2, "insecte": 2, "roche": 0.5, "acier": 0.5},
    "psy": {"combat": 2, "poison": 2, "psy": 0.5, "tenebres": 0, "acier": 0.5},
    "insecte": {"feu": 0.5, "plante": 2, "combat": 0.5, "poison": 0.5, "vol": 0.5, "psy": 2, "spectre": 0.5, "tenebres": 2, "acier": 0.5, "fee": 0.5},
    "roche": {"feu": 2, "glace": 2, "combat": 0.5, "sol": 0.5, "vol": 2, "insecte": 2, "acier": 0.5},
    "spectre": {"normal": 0, "psy": 2, "spectre": 2, "tenebres": 0.5},
    "dragon": {"dragon": 2, "acier": 0.5, "fee": 0},
    "tenebres": {"combat": 0.5, "psy": 2, "spectre": 2, "tenebres": 0.5, "fee": 0.5},
    "acier": {"feu": 0.5, "eau": 0.5, "electrique": 0.5, "glace": 2, "roche": 2, "acier": 0.5, "fee": 2},
    "fee": {"feu": 0.5, "combat": 2, "poison": 0.5, "dragon": 2, "tenebres": 2, "acier": 0.5}
}

# Duel modes
DUEL_MODE_RANDOM = "random"
DUEL_MODE_CONSTRUCTED = "constructed"
DUEL_MODE_DRAFT = "draft"

# Duel statuses
DUEL_STATUS_PENDING = "pending"
DUEL_STATUS_ACTIVE = "active"
DUEL_STATUS_COMPLETED = "completed"
DUEL_STATUS_FORFEITED = "forfeited"

# Action types
ACTION_SWITCH = "switch"
ACTION_STAY = "stay"

# Turn results
RESULT_P1_WINS = "p1_wins"
RESULT_P2_WINS = "p2_wins"
RESULT_DRAW = "draw"

# Teams
TEAM_RED = "RED"
TEAM_BLUE = "BLUE"

# Points
POINTS_WIN = 10
POINTS_LOSS = -10
POINTS_MIN = 0

# Team constraints
MAX_TEAM_SIZE = 6
MIN_TEAM_SIZE = 1

# Turn timeout
TURN_TIMEOUT_SECONDS = 90
