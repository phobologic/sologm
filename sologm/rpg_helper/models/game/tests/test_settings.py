"""
Tests for game settings.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from sqlalchemy import Column, String, Text

from sologm.rpg_helper.models.game.settings import GameSetting
from sologm.rpg_helper.models.base import BaseModel


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
        
        # Check defaults
        assert columns['value_str'].default.arg == ""
        assert columns['value_type'].default.arg == "str"
        
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
        """Test initialization with game_id and name."""
        game_id = "test-game-id"
        name = "test-setting"
        
        setting = GameSetting(game_id=game_id, name=name)
        
        assert setting.game_id == game_id
        assert setting.name == name
        assert setting.value_str == ""  # Should default to empty string
        assert setting.value_type == "str"  # Default type should be string
    
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
        setting = GameSetting(game_id="test-game-id", name="test-setting")
        setting.value = "test-value"
        assert setting.value_str == "test-value"
        assert setting.value_type == "str"
        assert setting.value == "test-value"  # Verify round-trip conversion
    
    def test_value_setter_int(self):
        """Test setting value to an integer."""
        setting = GameSetting(game_id="test-game-id", name="test-setting")
        setting.value = 123
        assert setting.value_str == "123"
        assert setting.value_type == "int"
        assert setting.value == 123  # Verify round-trip conversion
    
    def test_value_setter_bool(self):
        """Test setting value to a boolean."""
        setting = GameSetting(game_id="test-game-id", name="test-setting")
        
        # Test True
        setting.value = True
        assert setting.value_str == "true"
        assert setting.value_type == "bool"
        assert setting.value is True  # Verify round-trip conversion
        
        # Test False
        setting.value = False
        assert setting.value_str == "false"
        assert setting.value_type == "bool"
        assert setting.value is False  # Verify round-trip conversion
    
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
        setting = GameSetting(game_id="test-game-id", name="test-setting")
        
        with pytest.raises(ValueError) as exc_info:
            setting.value = None
        assert "Setting value cannot be None" in str(exc_info.value)
    
    def test_value_setter_empty_string(self):
        """Test setting value to an empty string."""
        setting = GameSetting(game_id="test-game-id", name="test-setting")
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