"""Tests for the game management module."""

import pytest

from sologm.models.game import Game
from sologm.utils.errors import GameError


class TestGameManager:
    """Tests for the GameManager class."""

    def test_create_game(self, game_manager, db_session) -> None:
        """Test creating a new game."""
        game = game_manager.create_game(name="Test Game", description="A test game")

        assert isinstance(game, Game)
        assert game.name == "Test Game"
        assert game.description == "A test game"
        assert game.created_at is not None
        assert game.modified_at is not None
        assert game.is_active is True

        # Verify game was saved to database
        db_game = db_session.query(Game).filter(Game.id == game.id).first()
        assert db_game is not None
        assert db_game.name == "Test Game"
        assert db_game.description == "A test game"
        assert db_game.is_active is True

    def test_create_game_inactive(self, game_manager, db_session) -> None:
        """Test creating a new inactive game."""
        game = game_manager.create_game(
            name="Inactive Game", description="An inactive test game", is_active=False
        )

        assert game.is_active is False

        # Verify game was saved to database with correct active status
        db_game = db_session.query(Game).filter(Game.id == game.id).first()
        assert db_game.is_active is False

    def test_create_game_with_different_names(self, game_manager) -> None:
        """Test creating games with different names generates different slugs."""
        game1 = game_manager.create_game(name="Test Game", description="First game")
        game2 = game_manager.create_game(name="Test Game 2", description="Second game")

        assert game1.id != game2.id
        assert game1.slug == "test-game"
        assert game2.slug == "test-game-2"  # Different slug for different name

    def test_list_games_empty(self, game_manager) -> None:
        """Test listing games when none exist."""
        games = game_manager.list_games()
        assert games == []

    def test_list_games(self, game_manager) -> None:
        """Test listing multiple games."""
        # Create some games
        game1 = game_manager.create_game(name="Game 1", description="First game")
        game2 = game_manager.create_game(name="Game 2", description="Second game")

        games = game_manager.list_games()
        assert len(games) == 2
        assert games[0].id == game1.id  # Should be sorted by created_at
        assert games[1].id == game2.id

    def test_get_game_by_id(self, game_manager) -> None:
        """Test getting a specific game by ID."""
        created_game = game_manager.create_game(
            name="Test Game", description="A test game"
        )

        game = game_manager.get_game_by_id(created_game.id)
        assert game is not None
        assert game.id == created_game.id
        assert game.name == created_game.name
        assert game.description == created_game.description

    def test_get_game_by_id_nonexistent(self, game_manager) -> None:
        """Test getting a nonexistent game by ID."""
        game = game_manager.get_game_by_id("nonexistent-game")
        assert game is None

    def test_get_game_by_slug(self, game_manager) -> None:
        """Test getting a specific game by slug."""
        created_game = game_manager.create_game(
            name="Test Game", description="A test game"
        )

        game = game_manager.get_game_by_slug("test-game")
        assert game is not None
        assert game.id == created_game.id
        assert game.name == created_game.name
        assert game.description == created_game.description

    def test_get_game_by_slug_nonexistent(self, game_manager) -> None:
        """Test getting a nonexistent game by slug."""
        game = game_manager.get_game_by_slug("nonexistent-game")
        assert game is None

    def test_create_game_with_duplicate_name_fails(self, game_manager) -> None:
        """Test creating a game with a duplicate name raises an error."""
        game_manager.create_game(name="Duplicate Name", description="First game")

        with pytest.raises(GameError) as exc:
            game_manager.create_game(name="Duplicate Name", description="Second game")

        assert "already exists" in str(exc.value).lower()

    def test_get_active_game_none(self, game_manager, db_session) -> None:
        """Test getting active game when none is set."""
        # Deactivate all games first
        db_session.query(Game).update({Game.is_active: False})
        db_session.commit()

        game = game_manager.get_active_game()
        assert game is None

    def test_get_active_game(self, game_manager) -> None:
        """Test getting the active game."""
        created_game = game_manager.create_game(
            name="Test Game", description="A test game"
        )

        game = game_manager.get_active_game()
        assert game is not None
        assert game.id == created_game.id

    def test_activate_game(self, game_manager, db_session) -> None:
        """Test activating a game."""
        game1 = game_manager.create_game(name="Game 1", description="First game")
        game2 = game_manager.create_game(name="Game 2", description="Second game")

        # Activate the second game
        activated_game = game_manager.activate_game(game2.id)
        assert activated_game.id == game2.id

        # Verify it's now the active game
        active_game = game_manager.get_active_game()
        assert active_game is not None
        assert active_game.id == game2.id

        # Verify the first game is no longer active
        db_session.refresh(game1)
        assert game1.is_active is False

    def test_activate_game_always_deactivates_others(
        self, game_manager, db_session
    ) -> None:
        """Test that activating any game always deactivates all other games."""
        # Create multiple games
        games = [
            game_manager.create_game(name=f"Game {i}", description=f"Game {i}")
            for i in range(1, 4)
        ]

        # Manually set all games to active (this shouldn't happen in practice)
        for game in games:
            game.is_active = True
        db_session.commit()

        # Now activate one specific game
        activated_game = game_manager.activate_game(games[1].id)
        assert activated_game.id == games[1].id
        assert activated_game.is_active is True

        # Verify all other games are inactive
        for i, game in enumerate(games):
            db_session.refresh(game)
            if i == 1:  # This is our activated game
                assert game.is_active is True
            else:
                assert game.is_active is False

    def test_activate_nonexistent_game(self, game_manager) -> None:
        """Test activating a nonexistent game raises an error."""
        with pytest.raises(GameError) as exc:
            game_manager.activate_game("nonexistent-game")
        assert "Game not found" in str(exc.value)

    def test_deactivate_game(self, game_manager, db_session) -> None:
        """Test deactivating a game."""
        game = game_manager.create_game(name="Test Game", description="A test game")
        assert game.is_active is True

        # Deactivate the game
        deactivated_game = game_manager.deactivate_game(game.id)
        assert deactivated_game.id == game.id
        assert deactivated_game.is_active is False

        # Verify it's no longer the active game
        db_session.refresh(game)
        assert game.is_active is False

        # Verify there's no active game
        active_game = game_manager.get_active_game()
        assert active_game is None

    def test_deactivate_nonexistent_game(self, game_manager) -> None:
        """Test deactivating a nonexistent game raises an error."""
        with pytest.raises(GameError) as exc:
            game_manager.deactivate_game("nonexistent-game")
        assert "Game not found" in str(exc.value)

    def test_update_game(self, game_manager) -> None:
        """Test updating a game's name and description."""
        # Create a game first
        game = game_manager.create_game(
            name="Original Name", description="Original description"
        )

        # Update the game
        updated_game = game_manager.update_game(
            game_id=game.id, name="Updated Name", description="Updated description"
        )

        # Verify the update
        assert updated_game.id == game.id
        assert updated_game.name == "Updated Name"
        assert updated_game.description == "Updated description"
        assert updated_game.slug == "updated-name"

        # Get the game again to verify persistence
        retrieved_game = game_manager.get_game_by_id(game.id)
        assert retrieved_game.name == "Updated Name"
        assert retrieved_game.description == "Updated description"

    def test_update_game_partial(self, game_manager) -> None:
        """Test updating only some fields of a game."""
        # Create a game first
        game = game_manager.create_game(
            name="Original Name", description="Original description"
        )

        # Update only the name
        updated_game = game_manager.update_game(game_id=game.id, name="Updated Name")
        assert updated_game.name == "Updated Name"
        assert updated_game.description == "Original description"

        # Update only the description
        updated_game = game_manager.update_game(
            game_id=game.id, description="Updated description"
        )
        assert updated_game.name == "Updated Name"  # Still has the updated name
        assert updated_game.description == "Updated description"

    def test_update_game_with_duplicate_name_fails(self, game_manager) -> None:
        """Test updating a game with a duplicate name raises an error."""
        # Create two games
        game1 = game_manager.create_game(
            name="First Game", description="First description"
        )
        game2 = game_manager.create_game(
            name="Second Game", description="Second description"
        )

        # Try to update the second game with the first game's name
        with pytest.raises(GameError) as exc:
            game_manager.update_game(game_id=game2.id, name="First Game")

        assert "already exists" in str(exc.value).lower()

    def test_delete_game(self, game_manager, db_session) -> None:
        """Test deleting a game."""
        # Create a game first
        game = game_manager.create_game(name="Test Game", description="A test game")

        # Delete the game
        result = game_manager.delete_game(game.id)
        assert result is True

        # Verify the game is gone
        db_game = db_session.query(Game).filter(Game.id == game.id).first()
        assert db_game is None

    def test_delete_nonexistent_game(self, game_manager) -> None:
        """Test deleting a nonexistent game."""
        result = game_manager.delete_game("nonexistent-game")
        assert result is False

    def test_game_model_validation(self, db_session):
        """Test Game model validation."""
        # Test empty name validation
        with pytest.raises(ValueError) as exc:
            Game.create(name="", description="Test")

        # Accept either error message since both validations are valid
        error_msg = str(exc.value).lower()
        assert (
            "name cannot be empty" in error_msg or "slug cannot be empty" in error_msg
        )

        # Test slug generation
        game = Game.create(name="Test Game", description="Test")
        assert game.slug == "test-game"

        # Test name uniqueness
        db_session.add(game)
        db_session.commit()

        with pytest.raises(Exception) as exc:
            game2 = Game.create(name="Test Game", description="Another test")
            db_session.add(game2)
            db_session.commit()
        assert "unique constraint" in str(exc.value).lower()
