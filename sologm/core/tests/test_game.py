"""Tests for the game management module."""

import pytest
from sqlalchemy.exc import IntegrityError

# Import factory and models needed for test setup
from sologm.core.factory import create_all_managers
from sologm.database.session import SessionContext
from sologm.models.game import Game
from sologm.utils.errors import GameError


class TestGameManager:
    """Tests for the GameManager class."""

    def test_create_game(self, session_context: SessionContext) -> None:
        """Test creating a new game."""
        with session_context as session:
            managers = create_all_managers(session)
            game = managers.game.create_game(
                name="Test Game", description="A test game"
            )

            assert isinstance(game, Game)
            assert game.name == "Test Game"
        assert game.description == "A test game"
        assert game.created_at is not None
        assert game.modified_at is not None
        assert game.is_active is True

        # Verify game was saved to database
        db_game = session.get(Game, game.id)
        assert db_game is not None
        assert db_game.name == "Test Game"
        assert db_game.description == "A test game"
        assert db_game.is_active is True

    def test_create_game_inactive(self, session_context: SessionContext) -> None:
        """Test creating a new inactive game."""
        with session_context as session:
            managers = create_all_managers(session)
            game = managers.game.create_game(
                name="Inactive Game",
                description="An inactive test game",
                is_active=False,
            )

            assert game.is_active is False

            # Verify game was saved to database with correct active status
            db_game = session.get(Game, game.id)
            assert db_game.is_active is False

    def test_create_game_with_different_names(
        self, session_context: SessionContext
    ) -> None:
        """Test creating games with different names generates different slugs."""
        with session_context as session:
            managers = create_all_managers(session)
            game1 = managers.game.create_game(
                name="Test Game", description="First game"
            )
            game2 = managers.game.create_game(
                name="Test Game 2", description="Second game"
            )

            assert game1.id != game2.id
            assert game1.slug == "test-game"
            assert game2.slug == "test-game-2"  # Different slug for different name

    def test_list_games_empty(self, session_context: SessionContext) -> None:
        """Test listing games when none exist."""
        with session_context as session:
            managers = create_all_managers(session)
            games = managers.game.list_games()
            assert games == []

    def test_list_games(self, session_context: SessionContext) -> None:
        """Test listing multiple games."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create some games
            game1 = managers.game.create_game(name="Game 1", description="First game")
            game2 = managers.game.create_game(name="Game 2", description="Second game")

            games = managers.game.list_games()
            assert len(games) == 2
            assert games[0].id == game1.id  # Should be sorted by created_at
            assert games[1].id == game2.id

    def test_get_game(self, session_context: SessionContext) -> None:
        """Test getting a game by ID."""
        with session_context as session:
            managers = create_all_managers(session)
            created_game = managers.game.create_game(
                name="Test Game", description="A test game"
            )

            game = managers.game.get_game(created_game.id)
            assert game is not None
            assert game.id == created_game.id
            assert game.name == created_game.name
            assert game.description == created_game.description

    def test_get_game_by_id(self, session_context: SessionContext) -> None:
        """Test getting a specific game by ID."""
        with session_context as session:
            managers = create_all_managers(session)
            created_game = managers.game.create_game(
                name="Test Game", description="A test game"
            )

            game = managers.game.get_game_by_id(created_game.id)
            assert game is not None
            assert game.id == created_game.id
            assert game.name == created_game.name
            assert game.description == created_game.description

    def test_get_game_by_id_nonexistent(self, session_context: SessionContext) -> None:
        """Test getting a nonexistent game by ID."""
        with session_context as session:
            managers = create_all_managers(session)
            game = managers.game.get_game_by_id("nonexistent-game")
            assert game is None

    def test_get_game_by_slug(self, session_context: SessionContext) -> None:
        """Test getting a specific game by slug."""
        with session_context as session:
            managers = create_all_managers(session)
            created_game = managers.game.create_game(
                name="Test Game", description="A test game"
            )

            game = managers.game.get_game_by_slug("test-game")
            assert game is not None
            assert game.id == created_game.id
            assert game.name == created_game.name
            assert game.description == created_game.description

    def test_get_game_by_slug_nonexistent(
        self, session_context: SessionContext
    ) -> None:
        """Test getting a nonexistent game by slug."""
        with session_context as session:
            managers = create_all_managers(session)
            game = managers.game.get_game_by_slug("nonexistent-game")
            assert game is None

    def test_create_game_with_duplicate_name_fails(
        self, session_context: SessionContext
    ) -> None:
        """Test creating a game with a duplicate name raises an error."""
        with session_context as session:
            managers = create_all_managers(session)
            managers.game.create_game(name="Duplicate Name", description="First game")

            with pytest.raises(GameError) as exc:
                managers.game.create_game(
                    name="Duplicate Name", description="Second game"
                )

            assert "already exists" in str(exc.value).lower()

    def test_get_active_game_none(self, session_context: SessionContext) -> None:
        """Test getting active game when none is set."""
        with session_context as session:
            managers = create_all_managers(session)
            # Deactivate all games first
            session.query(Game).update({Game.is_active: False})
            # No commit needed, context manager handles it

            game = managers.game.get_active_game()
            assert game is None

    def test_get_active_game(self, session_context: SessionContext) -> None:
        """Test getting the active game."""
        with session_context as session:
            managers = create_all_managers(session)
            created_game = managers.game.create_game(
                name="Test Game", description="A test game"
            )

            game = managers.game.get_active_game()
            assert game is not None
            assert game.id == created_game.id

    def test_activate_game(self, session_context: SessionContext) -> None:
        """Test activating a game."""
        with session_context as session:
            managers = create_all_managers(session)
            game1 = managers.game.create_game(name="Game 1", description="First game")
            game2 = managers.game.create_game(name="Game 2", description="Second game")

            # Activate the second game
            activated_game = managers.game.activate_game(game2.id)
            assert activated_game.id == game2.id

            # Verify it's now the active game
            active_game = managers.game.get_active_game()
            assert active_game is not None
            assert active_game.id == game2.id

            # Verify the first game is no longer active
            session.refresh(game1)
            assert game1.is_active is False

    def test_activate_game_always_deactivates_others(
        self, session_context: SessionContext
    ) -> None:
        """Test that activating any game always deactivates all other games."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create multiple games
            games = [
                managers.game.create_game(name=f"Game {i}", description=f"Game {i}")
                for i in range(1, 4)
            ]

            # Manually set all games to active (this shouldn't happen in practice)
            # Note: The create_game logic already deactivates others, so this
            # simulates a potentially inconsistent state before activation.
            for game in games:
                game.is_active = True
            session.flush()  # Flush the manual changes

            # Now activate one specific game
            activated_game = managers.game.activate_game(games[1].id)
            assert activated_game.id == games[1].id
            assert activated_game.is_active is True

            # Verify all other games are inactive
            for i, game in enumerate(games):
                session.refresh(game)
                if i == 1:  # This is our activated game
                    assert game.is_active is True
                else:
                    assert game.is_active is False

    def test_activate_nonexistent_game(self, session_context: SessionContext) -> None:
        """Test activating a nonexistent game raises an error."""
        with session_context as session:
            managers = create_all_managers(session)
            with pytest.raises(GameError) as exc:
                managers.game.activate_game("nonexistent-game")
            assert "Game not found" in str(exc.value)

    def test_deactivate_game(self, session_context: SessionContext) -> None:
        """Test deactivating a game."""
        with session_context as session:
            managers = create_all_managers(session)
            game = managers.game.create_game(
                name="Test Game", description="A test game"
            )
            assert game.is_active is True

            # Deactivate the game
            deactivated_game = managers.game.deactivate_game(game.id)
            assert deactivated_game.id == game.id
            assert deactivated_game.is_active is False

            # Verify it's no longer the active game
            session.refresh(game)
            assert game.is_active is False

            # Verify there's no active game
            active_game = managers.game.get_active_game()
            assert active_game is None

    def test_deactivate_nonexistent_game(self, session_context: SessionContext) -> None:
        """Test deactivating a nonexistent game raises an error."""
        with session_context as session:
            managers = create_all_managers(session)
            with pytest.raises(GameError) as exc:
                managers.game.deactivate_game("nonexistent-game")
            assert "Game not found" in str(exc.value)

    def test_update_game(self, session_context: SessionContext) -> None:
        """Test updating a game's name and description."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create a game first
            game = managers.game.create_game(
                name="Original Name", description="Original description"
            )

            # Update the game
            updated_game = managers.game.update_game(
                game_id=game.id, name="Updated Name", description="Updated description"
            )

            # Verify the update
            assert updated_game.id == game.id
            assert updated_game.name == "Updated Name"
            assert updated_game.description == "Updated description"
            assert updated_game.slug == "updated-name"

            # Get the game again to verify persistence
            retrieved_game = managers.game.get_game_by_id(game.id)
            assert retrieved_game.name == "Updated Name"
            assert retrieved_game.description == "Updated description"

    def test_update_game_partial(self, session_context: SessionContext) -> None:
        """Test updating only some fields of a game."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create a game first
            game = managers.game.create_game(
                name="Original Name", description="Original description"
            )

            # Update only the name
            updated_game = managers.game.update_game(
                game_id=game.id, name="Updated Name"
            )
            assert updated_game.name == "Updated Name"
            assert updated_game.description == "Original description"

            # Update only the description
            updated_game = managers.game.update_game(
                game_id=game.id, description="Updated description"
            )
            assert updated_game.name == "Updated Name"  # Still has the updated name
            assert updated_game.description == "Updated description"

    def test_update_game_with_duplicate_name_fails(
        self, session_context: SessionContext
    ) -> None:
        """Test updating a game with a duplicate name raises an error."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create two games
            game1 = managers.game.create_game(
                name="First Game", description="First description"
            )
            game2 = managers.game.create_game(
                name="Second Game", description="Second description"
            )

            # Try to update the second game with the first game's name
            with pytest.raises(GameError) as exc:
                managers.game.update_game(game_id=game2.id, name="First Game")

            assert "already exists" in str(exc.value).lower()

    def test_delete_game(self, session_context: SessionContext) -> None:
        """Test deleting a game."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create a game first
            game = managers.game.create_game(
                name="Test Game", description="A test game"
            )

            # Delete the game
            result = managers.game.delete_game(game.id)
            assert result is True

            # Verify the game is gone
            db_game = session.get(Game, game.id)
            assert db_game is None

    def test_delete_nonexistent_game(self, session_context: SessionContext) -> None:
        """Test deleting a nonexistent game."""
        with session_context as session:
            managers = create_all_managers(session)
            result = managers.game.delete_game("nonexistent-game")
            assert result is False

    def test_act_manager_property(self, session_context: SessionContext):
        """Test the act_manager property."""
        with session_context as session:
            managers = create_all_managers(session)
            # Access the act_manager property
            act_manager = managers.game.act_manager

            # Verify it's the correct type
            from sologm.core.act import ActManager

            assert isinstance(act_manager, ActManager)

            # Verify it has a reference back to the game_manager
            assert act_manager.game_manager is managers.game

            # Verify it shares the same session
            assert act_manager._session is managers.game._session

    def test_game_model_validation(self, session_context: SessionContext):
        """Test Game model validation."""
        with session_context as session:
            # Test empty name validation
            with pytest.raises(ValueError) as exc:
                Game.create(name="", description="Test")

            # Accept either error message since both validations are valid
            error_msg = str(exc.value).lower()
            assert (
                "name cannot be empty" in error_msg
                or "slug cannot be empty" in error_msg
            )

            # Test slug generation
            game = Game.create(name="Test Game", description="Test")
            assert game.slug == "test-game"

            # Test name uniqueness
            session.add(game)
            session.flush()  # Flush to check constraint before commit

            with pytest.raises(IntegrityError) as exc:
                game2 = Game.create(name="Test Game", description="Another test")
                session.add(game2)
                session.flush()  # Trigger the unique constraint check
                # *** ADD ROLLBACK HERE ***
                session.rollback()  # Clean up session state after expected error
            assert "unique constraint" in str(exc.value).lower()
