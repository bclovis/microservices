"""
Unit tests for type advantage calculation
"""
import pytest
from utils.helpers import calculate_type_advantage, determine_turn_winner


def test_calculate_advantage_fire_vs_water():
    """Test fire vs water type advantage"""
    f_fire, f_water = calculate_type_advantage("feu", None, "eau", None)
    assert f_water > f_fire  # Water should have advantage


def test_calculate_advantage_dracaufeu_vs_laggron():
    """Test example from project specifications: Dracaufeu (Fire/Flying) vs Laggron (Water/Ground)"""
    # Dracaufeu: Fire/Flying vs Laggron: Water/Ground
    f_a, f_b = calculate_type_advantage("feu", "vol", "eau", "sol")
    
    # Expected: F(Dracaufeu) = 1.5, F(Laggron) = 2
    assert f_a == 1.5
    assert f_b == 2.0
    
    # Laggron should win
    result = determine_turn_winner(f_a, f_b)
    assert result == "p2_wins"


def test_determine_winner_equal():
    """Test draw condition"""
    result = determine_turn_winner(2.0, 2.0)
    assert result == "draw"


def test_determine_winner_p1():
    """Test player 1 wins"""
    result = determine_turn_winner(3.0, 2.0)
    assert result == "p1_wins"


def test_determine_winner_p2():
    """Test player 2 wins"""
    result = determine_turn_winner(2.0, 3.0)
    assert result == "p2_wins"
