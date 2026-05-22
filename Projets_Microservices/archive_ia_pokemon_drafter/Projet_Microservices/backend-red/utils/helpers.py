"""
Helper utility functions
"""
from typing import Optional, Tuple
from .constants import TYPE_EFFECTIVENESS


def calculate_type_advantage(
    pokemon_a_type_primary: str,
    pokemon_a_type_secondary: Optional[str],
    pokemon_b_type_primary: str,
    pokemon_b_type_secondary: Optional[str]
) -> Tuple[float, float]:
    """
    Calculate advantage between two pokemon using the formula from specifications:
    F(A) = 1*(W/Y)*(W/Z) + 1*(X/Y)*(X/Z)
    F(B) = 1*(Y/W)*(Y/X) + 1*(Z/W)*(Z/X)
    where A is type WX and B is type YZ
    
    Args:
        pokemon_a_type_primary: Primary type of Pokemon A (W)
        pokemon_a_type_secondary: Secondary type of Pokemon A (X)
        pokemon_b_type_primary: Primary type of Pokemon B (Y)
        pokemon_b_type_secondary: Secondary type of Pokemon B (Z)
    
    Returns:
        Tuple of (F(A), F(B)) representing the advantage factors
    """
    w = pokemon_a_type_primary.lower()
    x = pokemon_a_type_secondary.lower() if pokemon_a_type_secondary else w
    y = pokemon_b_type_primary.lower()
    z = pokemon_b_type_secondary.lower() if pokemon_b_type_secondary else y
    
    def get_multiplier(attacker: str, defender: str) -> float:
        """Get type effectiveness multiplier"""
        if attacker not in TYPE_EFFECTIVENESS:
            return 1.0
        return TYPE_EFFECTIVENESS[attacker].get(defender, 1.0)
    
    # F(A) = 1*(W/Y)*(W/Z) + 1*(X/Y)*(X/Z)
    f_a = (1 * get_multiplier(w, y) * get_multiplier(w, z) +
           1 * get_multiplier(x, y) * get_multiplier(x, z))
    
    # F(B) = 1*(Y/W)*(Y/X) + 1*(Z/W)*(Z/X)
    f_b = (1 * get_multiplier(y, w) * get_multiplier(y, x) +
           1 * get_multiplier(z, w) * get_multiplier(z, x))
    
    return f_a, f_b


def determine_turn_winner(advantage_a: float, advantage_b: float) -> str:
    """
    Determine the winner of a turn based on type advantages
    
    Args:
        advantage_a: Advantage factor for Pokemon A
        advantage_b: Advantage factor for Pokemon B
    
    Returns:
        "p1_wins", "p2_wins", or "draw"
    """
    if advantage_a > advantage_b:
        return "p1_wins"
    elif advantage_b > advantage_a:
        return "p2_wins"
    else:
        return "draw"


def normalize_type_name(type_name: str) -> str:
    """Normalize Pokemon type name for consistency"""
    type_mapping = {
        "fire": "feu",
        "water": "eau",
        "grass": "plante",
        "electric": "electrique",
        "ice": "glace",
        "fighting": "combat",
        "poison": "poison",
        "ground": "sol",
        "flying": "vol",
        "psychic": "psy",
        "bug": "insecte",
        "rock": "roche",
        "ghost": "spectre",
        "dragon": "dragon",
        "dark": "tenebres",
        "steel": "acier",
        "fairy": "fee",
        "normal": "normal"
    }
    
    normalized = type_name.lower().strip()
    return type_mapping.get(normalized, normalized)
