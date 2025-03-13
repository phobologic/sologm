"""
Tests for game constants.
"""
import pytest

from sologm.rpg_helper.models.game.constants import (
    GameType, MythicChaosFactor, ChaosBoundaryError
)
from sologm.rpg_helper.models.game.errors import GameError


class TestGameType:
    """Tests for the GameType enum."""
    
    def test_values(self):
        """Test that GameType has the expected values."""
        assert GameType.STANDARD.value == "standard"
        assert GameType.MYTHIC.value == "mythic"
    
    def test_is_string_enum(self):
        """Test that GameType is a string enum."""
        assert isinstance(GameType.STANDARD.value, str)
        assert isinstance(GameType.MYTHIC.value, str)


class TestMythicChaosFactor:
    """Tests for the MythicChaosFactor enum."""
    
    def test_values(self):
        """Test that MythicChaosFactor has the expected values."""
        assert MythicChaosFactor.MIN == 1
        assert MythicChaosFactor.LOW == 3
        assert MythicChaosFactor.AVERAGE == 5
        assert MythicChaosFactor.HIGH == 7
        assert MythicChaosFactor.MAX == 9
    
    def test_is_int_enum(self):
        """Test that MythicChaosFactor is an int enum."""
        assert isinstance(MythicChaosFactor.MIN, int)
        assert isinstance(MythicChaosFactor.AVERAGE, int)
        assert isinstance(MythicChaosFactor.MAX, int)
    
    def test_ordering(self):
        """Test that MythicChaosFactor values are ordered correctly."""
        assert MythicChaosFactor.MIN < MythicChaosFactor.LOW
        assert MythicChaosFactor.LOW < MythicChaosFactor.AVERAGE
        assert MythicChaosFactor.AVERAGE < MythicChaosFactor.HIGH
        assert MythicChaosFactor.HIGH < MythicChaosFactor.MAX


class TestChaosBoundaryError:
    """Tests for the ChaosBoundaryError class."""
    
    def test_inheritance(self):
        """Test that ChaosBoundaryError inherits from GameError."""
        assert issubclass(ChaosBoundaryError, GameError)
    
    def test_init_below_min(self):
        """Test initialization with a value below minimum."""
        attempted = MythicChaosFactor.MIN - 1
        current = MythicChaosFactor.MIN
        
        error = ChaosBoundaryError(attempted=attempted, current=current)
        
        assert error.attempted == attempted
        assert error.current == current
        assert "Cannot decrease chaos factor below minimum" in str(error)
        assert str(MythicChaosFactor.MIN) in str(error)
        assert str(attempted) in str(error)
    
    def test_init_above_max(self):
        """Test initialization with a value above maximum."""
        attempted = MythicChaosFactor.MAX + 1
        current = MythicChaosFactor.MAX
        
        error = ChaosBoundaryError(attempted=attempted, current=current)
        
        assert error.attempted == attempted
        assert error.current == current
        assert "Cannot increase chaos factor above maximum" in str(error)
        assert str(MythicChaosFactor.MAX) in str(error)
        assert str(attempted) in str(error)
    
    def test_init_invalid(self):
        """Test initialization with an invalid value."""
        attempted = -100  # Some arbitrary invalid value
        
        error = ChaosBoundaryError(attempted=attempted)
        
        assert error.attempted == attempted
        assert error.current is None
        assert "Invalid chaos factor" in str(error)
        assert str(attempted) in str(error)
    
    def test_init_with_none(self):
        """Test initialization with None value."""
        error = ChaosBoundaryError(attempted=None)
        assert error.attempted is None
        assert error.current is None
        assert "cannot be None" in str(error)
    
    def test_init_with_boolean(self):
        """Test initialization with boolean values."""
        # Test with True
        error_true = ChaosBoundaryError(attempted=True)
        assert error_true.attempted is True
        assert error_true.current is None
        assert "boolean values are not allowed" in str(error_true)
        
        # Test with False
        error_false = ChaosBoundaryError(attempted=False)
        assert error_false.attempted is False
        assert error_false.current is None
        assert "boolean values are not allowed" in str(error_false) 