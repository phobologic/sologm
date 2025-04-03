"""Tests for the game management module."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from sologm.core.game import Game, GameManager
from sologm.storage.file_manager import FileManager
from sologm.utils.errors import GameError


class TestGameManager:
    """Tests for the GameManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.file_manager = FileManager(self.base_dir)
        self.game_manager = GameManager(self.file_manager)

    def teardown_method(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_create_game(self):
        """Test creating a new game."""
        game = self.game_manager.create_game(
            name="Test Game", description="A test game"
        )

        assert isinstance(game, Game)
        assert game.name == "Test Game"
        assert game.description == "A test game"
        assert isinstance(game.created_at, datetime)
        assert isinstance(game.modified_at, datetime)
        assert game.scenes == []

        # Verify file was created
        game_path = self.file_manager.get_game_path(game.id)
        assert game_path.exists()

        # Verify game data was saved correctly
        with open(game_path, "r") as f:
            data = yaml.safe_load(f)
            assert data["name"] == "Test Game"
            assert data["description"] == "A test game"
            assert data["scenes"] == []

        # Verify game was set as active
        assert self.file_manager.get_active_game_id() == game.id

    def test_create_game_with_duplicate_name(self):
        """Test creating games with the same name generates unique IDs."""
        game1 = self.game_manager.create_game(
            name="Test Game", description="First game"
        )
        game2 = self.game_manager.create_game(
            name="Test Game", description="Second game"
        )

        assert game1.id != game2.id
        assert game1.id.startswith("test-game")
        assert game2.id.startswith("test-game")

    def test_list_games_empty(self):
        """Test listing games when none exist."""
        games = self.game_manager.list_games()
        assert games == []

    def test_list_games(self):
        """Test listing multiple games."""
        # Create some games
        game1 = self.game_manager.create_game(name="Game 1", description="First game")
        game2 = self.game_manager.create_game(name="Game 2", description="Second game")

        games = self.game_manager.list_games()
        assert len(games) == 2
        assert games[0].id == game1.id  # Should be sorted by created_at
        assert games[1].id == game2.id

    def test_get_game(self):
        """Test getting a specific game."""
        created_game = self.game_manager.create_game(
            name="Test Game", description="A test game"
        )

        game = self.game_manager.get_game(created_game.id)
        assert game is not None
        assert game.id == created_game.id
        assert game.name == created_game.name
        assert game.description == created_game.description

    def test_get_game_nonexistent(self):
        """Test getting a nonexistent game."""
        game = self.game_manager.get_game("nonexistent-game")
        assert game is None

    def test_get_active_game_none(self):
        """Test getting active game when none is set."""
        game = self.game_manager.get_active_game()
        assert game is None

    def test_get_active_game(self):
        """Test getting the active game."""
        created_game = self.game_manager.create_game(
            name="Test Game", description="A test game"
        )

        game = self.game_manager.get_active_game()
        assert game is not None
        assert game.id == created_game.id

    def test_activate_game(self):
        """Test activating a game."""
        game1 = self.game_manager.create_game(name="Game 1", description="First game")
        game2 = self.game_manager.create_game(name="Game 2", description="Second game")

        # Activate the second game
        activated_game = self.game_manager.activate_game(game2.id)
        assert activated_game.id == game2.id

        # Verify it's now the active game
        active_game = self.game_manager.get_active_game()
        assert active_game is not None
        assert active_game.id == game2.id

    def test_activate_nonexistent_game(self):
        """Test activating a nonexistent game raises an error."""
        with pytest.raises(GameError) as exc:
            self.game_manager.activate_game("nonexistent-game")
        assert "Game not found" in str(exc.value)

    def test_current_interpretation_tracking(self):
        """Test tracking current interpretation in game data."""
        # Create a game
        game = self.game_manager.create_game(
            name="Test Game", description="A test game"
        )

        # Get the game path
        game_path = self.file_manager.get_game_path(game.id)

        # Read initial game data
        game_data = self.file_manager.read_yaml(game_path)
        assert "current_interpretation" not in game_data

        # Update game data with current interpretation
        game_data["current_interpretation"] = {
            "id": "test-interp-1",
            "context": "Test context",
            "results": "Test results",
            "retry_count": 0,
        }
        self.file_manager.write_yaml(game_path, game_data)

        # Read updated game data
        updated_data = self.file_manager.read_yaml(game_path)
        assert "current_interpretation" in updated_data
        assert updated_data["current_interpretation"]["id"] == "test-interp-1"
        assert updated_data["current_interpretation"]["retry_count"] == 0
