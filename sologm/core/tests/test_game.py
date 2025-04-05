"""Tests for the game management module."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sologm.core.game import GameManager
from sologm.database.session import DatabaseSession
from sologm.models.base import Base
from sologm.models.game import Game
from sologm.utils.errors import GameError


class TestGameManager:
    """Tests for the GameManager class."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Set up an in-memory SQLite database for testing."""
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")

        # Create all tables
        Base.metadata.create_all(self.engine)

        # Create a session factory
        self.session_factory = sessionmaker(bind=self.engine)

        # Create a session
        self.session = self.session_factory()

        # Create a database session instance
        self.db_session = DatabaseSession(engine=self.engine)
        DatabaseSession._instance = self.db_session

        # Create a game manager with the test session
        self.game_manager = GameManager(session=self.session)

        yield
        # Clean up
        self.session.close()
        Base.metadata.drop_all(self.engine)
        DatabaseSession._instance = None

    def test_create_game(self) -> None:
        """Test creating a new game."""
        game = self.game_manager.create_game(
            name="Test Game", description="A test game"
        )

        assert isinstance(game, Game)
        assert game.name == "Test Game"
        assert game.description == "A test game"
        assert game.created_at is not None
        assert game.modified_at is not None
        assert game.is_active is True

        # Verify game was saved to database
        db_game = self.session.query(Game).filter(Game.id == game.id).first()
        assert db_game is not None
        assert db_game.name == "Test Game"
        assert db_game.description == "A test game"
        assert db_game.is_active is True

    def test_create_game_with_duplicate_name(self) -> None:
        """Test creating games with the same name generates unique slugs."""
        game1 = self.game_manager.create_game(
            name="Test Game", description="First game"
        )
        game2 = self.game_manager.create_game(
            name="Test Game", description="Second game"
        )

        assert game1.id != game2.id
        assert game1.slug == "test-game"
        assert game2.slug != game1.slug  # Should have a unique slug

    def test_list_games_empty(self) -> None:
        """Test listing games when none exist."""
        games = self.game_manager.list_games()
        assert games == []

    def test_list_games(self) -> None:
        """Test listing multiple games."""
        # Create some games
        game1 = self.game_manager.create_game(name="Game 1", description="First game")
        game2 = self.game_manager.create_game(name="Game 2", description="Second game")

        games = self.game_manager.list_games()
        assert len(games) == 2
        assert games[0].id == game1.id  # Should be sorted by created_at
        assert games[1].id == game2.id

    def test_get_game(self) -> None:
        """Test getting a specific game."""
        created_game = self.game_manager.create_game(
            name="Test Game", description="A test game"
        )

        game = self.game_manager.get_game(created_game.id)
        assert game is not None
        assert game.id == created_game.id
        assert game.name == created_game.name
        assert game.description == created_game.description

    def test_get_game_nonexistent(self) -> None:
        """Test getting a nonexistent game."""
        game = self.game_manager.get_game("nonexistent-game")
        assert game is None

    def test_get_active_game_none(self) -> None:
        """Test getting active game when none is set."""
        # Deactivate all games first
        self.session.query(Game).update({Game.is_active: False})
        self.session.commit()

        game = self.game_manager.get_active_game()
        assert game is None

    def test_get_active_game(self) -> None:
        """Test getting the active game."""
        created_game = self.game_manager.create_game(
            name="Test Game", description="A test game"
        )

        game = self.game_manager.get_active_game()
        assert game is not None
        assert game.id == created_game.id

    def test_activate_game(self) -> None:
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

        # Verify the first game is no longer active
        self.session.refresh(game1)
        assert game1.is_active is False

    def test_activate_nonexistent_game(self) -> None:
        """Test activating a nonexistent game raises an error."""
        with pytest.raises(GameError) as exc:
            self.game_manager.activate_game("nonexistent-game")
        assert "Game not found" in str(exc.value)
