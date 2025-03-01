"""
Unit tests for dice rolling service.
"""
import pytest
import re
from unittest.mock import patch

from ..dice_service import roll_dice, DiceRollError


class TestDiceService:
    
    def test_valid_simple_roll(self):
        """Test a simple valid dice roll without modifiers."""
        with patch('random.randint', return_value=4):
            result = roll_dice("3d6")
            
            assert result["rolls"] == [4, 4, 4]
            assert result["total"] == 12
            assert result["dice_str"] == "3d6"
    
    def test_valid_roll_with_positive_modifier(self):
        """Test a valid dice roll with a positive modifier."""
        with patch('random.randint', return_value=3):
            result = roll_dice("2d8+5")
            
            assert result["rolls"] == [3, 3]
            assert result["total"] == 11  # 3 + 3 + 5
            assert result["dice_str"] == "2d8+5"
    
    def test_valid_roll_with_negative_modifier(self):
        """Test a valid dice roll with a negative modifier."""
        with patch('random.randint', return_value=6):
            result = roll_dice("4d6-10")
            
            assert result["rolls"] == [6, 6, 6, 6]
            assert result["total"] == 14  # 24 - 10
            assert result["dice_str"] == "4d6-10"
    
    def test_invalid_dice_format(self):
        """Test handling of invalid dice format."""
        invalid_formats = [
            "d20",        # Missing number of dice
            "20",         # Missing 'd' and dice type
            "3+5",        # Missing dice type
            "3d",         # Missing dice type
            "xd20",       # Non-numeric dice count
            "3dx",        # Non-numeric dice type
            "3d6+x",      # Non-numeric modifier
            "3d6+",       # Missing modifier value
            "hello",      # Completely invalid
            "",           # Empty string
        ]
        
        for dice_str in invalid_formats:
            with pytest.raises(DiceRollError) as excinfo:
                roll_dice(dice_str)
            assert "Invalid dice format" in str(excinfo.value)
    
    def test_partial_match_rejection(self):
        """Test that partial regex matches are properly rejected."""
        # These strings have valid prefixes but invalid suffixes
        partial_matches = [
            "3d6+x",      # Non-numeric modifier
            "3d6+",       # Missing modifier value
            "2d10extra",  # Extra text after valid dice
        ]
        
        # Verify the regex behavior directly
        from sologm.rpg_helper.services.dice_service import DICE_PATTERN
        for test_str in partial_matches:
            match = DICE_PATTERN.match(test_str)
            if match:
                # If there's a match, ensure it doesn't match the entire string
                assert match.group(0) != test_str, f"Regex shouldn't fully match {test_str}"
        
        # Verify the function behavior
        for dice_str in partial_matches:
            with pytest.raises(DiceRollError) as excinfo:
                roll_dice(dice_str)
            assert "Invalid dice format" in str(excinfo.value)
    
    def test_too_many_dice(self):
        """Test handling of too many dice."""
        with pytest.raises(DiceRollError) as excinfo:
            roll_dice("31d6")
        assert "Too many dice" in str(excinfo.value)
    
    def test_dice_type_too_large(self):
        """Test handling of dice type that is too large."""
        with pytest.raises(DiceRollError) as excinfo:
            roll_dice("3d101")
        assert "too large dice" in str(excinfo.value)
    
    def test_random_values_used(self):
        """Test that random values are properly used in calculations."""
        # Mock random.randint to return a sequence of values
        with patch('random.randint', side_effect=[2, 4, 6]):
            result = roll_dice("3d6")
            
            assert result["rolls"] == [2, 4, 6]
            assert result["total"] == 12
    
    def test_dice_pattern_regex(self):
        """Test the dice pattern regex directly."""
        from sologm.rpg_helper.services.dice_service import DICE_PATTERN
        
        # Valid patterns
        assert DICE_PATTERN.match("1d6")
        assert DICE_PATTERN.match("20d10")
        assert DICE_PATTERN.match("3d8+5")
        assert DICE_PATTERN.match("2d4-3")
        
        # Invalid patterns
        assert not DICE_PATTERN.match("d20")
        assert not DICE_PATTERN.match("3+5")
        assert not DICE_PATTERN.match("3d")
        assert not DICE_PATTERN.match("hello")
    
    def test_edge_case_single_die(self):
        """Test rolling a single die."""
        with patch('random.randint', return_value=20):
            result = roll_dice("1d20")
            
            assert result["rolls"] == [20]
            assert result["total"] == 20
    
    def test_edge_case_d1(self):
        """Test rolling a d1 (which always returns 1)."""
        result = roll_dice("5d1")
        
        assert result["rolls"] == [1, 1, 1, 1, 1]
        assert result["total"] == 5 