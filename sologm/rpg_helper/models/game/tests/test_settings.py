"""
Tests for game settings.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from sqlalchemy import Column, String, Text

from sologm.rpg_helper.models.game.settings import GameSetting
from sologm.rpg_helper.models.base import BaseModel
from sologm.rpg_helper.models.game.errors import SettingTypeChangeError


class TestGameSetting:
    """Tests for the GameSetting class."""
    
    def test_inheritance(self):
        """Test that GameSetting inherits from BaseModel."""
        assert issubclass(GameSetting, BaseModel)
    
    def test_columns(self):
        """Test that GameSetting has the expected columns."""
        # Get the table columns
        columns = GameSetting.__table__.columns
        
        # Check that the columns exist
        assert 'game_id' in columns
        assert 'name' in columns
        assert 'value_str' in columns
        assert 'value_type' in columns
        
        # Check column types and constraints
        assert isinstance(columns['name'].type, String)
        assert isinstance(columns['value_str'].type, Text)
        assert isinstance(columns['value_type'].type, String)
        assert isinstance(columns['game_id'].type, String)
        
        # Check column constraints
        assert not columns['name'].nullable
        assert not columns['game_id'].nullable
        assert not columns['value_type'].nullable
        assert not columns['value_str'].nullable
        
        # Check string lengths where applicable
        assert columns['name'].type.length == 100
        assert columns['value_type'].type.length == 10
        assert columns['game_id'].type.length == 36
    
    def test_relationships(self):
        """Test that GameSetting has the expected relationships."""
        assert hasattr(GameSetting, 'game')
    
    def test_table_constraints(self):
        """Test that GameSetting has the expected table constraints."""
        # Find the unique constraint
        unique_constraint = next(
            (c for c in GameSetting.__table__.constraints 
             if c.name == 'uix_game_setting'),
            None
        )
        
        # Verify it exists and has the correct columns
        assert unique_constraint is not None, "Unique constraint not found"
        constraint_columns = {c.name for c in unique_constraint.columns}
        assert constraint_columns == {'game_id', 'name'}, "Unexpected constraint columns"
    
    def test_init(self):
        """Test initialization with required parameters."""
        game_id = "test-game-id"
        name = "test-setting"
        
        # Test initialization with value parameter
        setting = GameSetting(
            game_id=game_id,
            name=name,
            value="test-value"
        )
        assert setting.game_id == game_id
        assert setting.name == name
        assert setting.value_str == "test-value"
        assert setting.value_type == "str"
        assert setting.value == "test-value"
        
        # Test initialization with value_str and value_type
        setting = GameSetting(
            game_id=game_id,
            name=name,
            value_str="42",
            value_type="int"
        )
        assert setting.game_id == game_id
        assert setting.name == name
        assert setting.value_str == "42"
        assert setting.value_type == "int"
        assert setting.value == 42
        
        # Test initialization fails without required parameters
        with pytest.raises(ValueError) as exc_info:
            GameSetting(game_id=game_id, name=name)
        assert "Must provide either value parameter" in str(exc_info.value)
        
        # Test initialization fails with None value
        with pytest.raises(ValueError) as exc_info:
            GameSetting(game_id=game_id, name=name, value=None)
        assert "Must provide either value parameter" in str(exc_info.value)
        
        # Test initialization fails with partial value_str/value_type
        with pytest.raises(ValueError) as exc_info:
            GameSetting(game_id=game_id, name=name, value_str="42")
        assert "Must provide either value parameter" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            GameSetting(game_id=game_id, name=name, value_type="int")
        assert "Must provide either value parameter" in str(exc_info.value)
    
    def test_value_getter_string(self):
        """Test getting value when type is string."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value_str="test-value",
            value_type="str"
        )
        assert setting.value == "test-value"
    
    def test_value_getter_int(self):
        """Test getting value when type is integer."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value_str="123",
            value_type="int"
        )
        assert setting.value == 123
        assert isinstance(setting.value, int)
    
    def test_value_getter_bool(self):
        """Test getting value when type is boolean."""
        # Test True
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value_str="true",
            value_type="bool"
        )
        assert setting.value is True
        
        # Test False
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value_str="false",
            value_type="bool"
        )
        assert setting.value is False
    
    def test_value_setter_string(self):
        """Test setting value to a string."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value="initial-string"  # Initialize with a string since we'll set string value
        )
        setting.value = "test-value"
        assert setting.value_str == "test-value"
        assert setting.value_type == "str"
        assert setting.value == "test-value"  # Verify round-trip conversion
    
    def test_value_setter_int(self):
        """Test setting value to an integer."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value=0  # Initialize with an integer since we'll set integer value
        )
        setting.value = 123
        assert setting.value_str == "123"
        assert setting.value_type == "int"
        assert setting.value == 123  # Verify round-trip conversion
    
    def test_value_setter_bool(self):
        """Test setting value to a boolean."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value=False  # Initialize with a boolean since we'll set boolean values
        )
        
        # Test True
        setting.value = True
        assert setting.value_str == "true"
        assert setting.value_type == "bool"
        assert setting.value is True
        
        # Test False
        setting.value = False
        assert setting.value_str == "false"
        assert setting.value_type == "bool"
        assert setting.value is False
    
    def test_repr(self):
        """Test the __repr__ method."""
        game_id = "test-game-id"
        name = "test-setting"
        
        setting = GameSetting(
            game_id=game_id,
            name=name,
            value_str="test-value",
            value_type="str"
        )
        repr_str = repr(setting)
        assert game_id in repr_str
        assert name in repr_str
        assert "test-value" in repr_str
    
    def test_to_dict(self):
        """Test the to_dict method with different value types."""
        game_id = "test-game-id"
        name = "test-setting"
        
        # Test string value (including empty string)
        setting = GameSetting(
            game_id=game_id,
            name=name,
            value_str="",
            value_type="str"
        )
        setting.created_at = datetime(2023, 1, 1, 12, 0, 0)
        setting.updated_at = datetime(2023, 1, 2, 12, 0, 0)
        
        result = setting.to_dict()
        assert result["id"] == setting.id
        assert result["game_id"] == game_id
        assert result["name"] == name
        assert result["value_str"] == ""
        assert result["value_type"] == "str"
        assert result["value"] == ""
        assert result["created_at"] == "2023-01-01T12:00:00"
        assert result["updated_at"] == "2023-01-02T12:00:00"
    
    def test_value_setter_rejects_none(self):
        """Test that setting value to None raises an error."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value="initial"  # Initialize with any valid value
        )
        
        with pytest.raises(ValueError) as exc_info:
            setting.value = None
        assert "Setting value cannot be None" in str(exc_info.value)
    
    def test_value_setter_empty_string(self):
        """Test setting value to an empty string."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value="initial"  # Initialize with non-empty string since we'll set string value
        )
        setting.value = ""
        assert setting.value_str == ""
        assert setting.value_type == "str"
        assert setting.value == ""  # Verify round-trip conversion
    
    def test_init_with_empty_string(self):
        """Test initialization with an empty string value."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value_str="",
            value_type="str"
        )
        assert setting.value_str == ""
        assert setting.value_type == "str"
        assert setting.value == ""
    
    def test_value_setter_prevents_type_change(self):
        """Test that value setter prevents type changes."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value="test-value"  # Initialize with string
        )
        
        # Attempt to change from string to int
        with pytest.raises(SettingTypeChangeError) as exc_info:
            setting.value = 42
        
        error = exc_info.value
        assert error.setting_name == setting.name
        assert error.current_type == "str"
        assert error.new_type == "int"
        assert error.game_id == setting.game_id
        assert "Use reset_value()" in str(error)
        
        # Verify value was not changed
        assert setting.value_type == "str"
        assert setting.value_str == "test-value"
    
    def test_reset_value_allows_type_change(self):
        """Test that reset_value allows type changes."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value="123"  # Initialize with string
        )
        
        # Change from string to int
        setting.reset_value(42)
        
        assert setting.value_type == "int"
        assert setting.value_str == "42"
        assert setting.value == 42
    
    def test_reset_value_with_bool(self):
        """Test reset_value with boolean values."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value="test"  # Initialize with string
        )
        
        # Change from string to bool
        setting.reset_value(True)
        
        assert setting.value_type == "bool"
        assert setting.value_str == "true"
        assert setting.value is True
    
    def test_reset_value_rejects_none(self):
        """Test that reset_value rejects None values."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value=""  # Initialize with empty string
        )
        
        with pytest.raises(ValueError) as exc_info:
            setting.reset_value(None)
        assert "Setting value cannot be None" in str(exc_info.value)
    
    def test_value_setter_same_type_allowed(self):
        """Test that value setter allows changes within the same type."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value=123  # Initialize with int since we'll set integer value
        )
        
        # Change to different int
        setting.value = 456
        
        assert setting.value_type == "int"
        assert setting.value_str == "456"
        assert setting.value == 456
    
    def test_value_getter_unknown_type(self):
        """Test getting value when type is unknown."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value_str="test",
            value_type="unknown"  # Use unknown type
        )
        assert setting.value == "test"  # Should return raw string
    
    def test_value_getter_conversion_error(self):
        """Test getting value when conversion fails."""
        setting = GameSetting(
            game_id="test-game-id",
            name="test-setting",
            value_str="not-an-int",
            value_type="int"  # This will cause conversion error
        )
        assert setting.value == "not-an-int"  # Should return raw string on error 