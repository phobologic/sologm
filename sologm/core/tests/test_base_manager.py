"""Tests for the BaseManager class."""

import pytest

from sologm.core.base_manager import BaseManager
from sologm.database.session import SessionContext
from sologm.models.game import Game
from sologm.utils.errors import SoloGMError


# Define a simple custom exception for testing error raising
class BaseManagerTestError(SoloGMError):
    """Custom exception for BaseManager tests."""

    pass


class TestBaseManagerIntegration:
    """Integration tests for BaseManager using real session and Game model."""

    # --- Tests for get_entity_by_identifier ---

    def test_get_entity_by_identifier_finds_by_id(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test finding an entity by ID."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            game = create_test_game(session, name="FindByID Game")
            # Pass session explicitly as it's required by the method signature
            found_entity = base_manager.get_entity_by_identifier(
                session,
                Game,
                game.id,
            )
            assert found_entity is not None
            assert found_entity.id == game.id
            assert found_entity.name == "FindByID Game"

    def test_get_entity_by_identifier_finds_by_slug(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test finding an entity by slug."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            game = create_test_game(session, name="FindBySlug Game")
            # Ensure slug is generated correctly by the model/factory
            assert game.slug == "findbyslug-game"
            # Pass session explicitly
            found_entity = base_manager.get_entity_by_identifier(
                session,
                Game,
                "findbyslug-game",
            )
            assert found_entity is not None
            assert found_entity.id == game.id
            assert found_entity.slug == "findbyslug-game"

    def test_get_entity_by_identifier_returns_none_for_nonexistent(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test returning None when identifier does not match ID or slug."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            # Pass session explicitly
            found_entity = base_manager.get_entity_by_identifier(
                session,
                Game,
                "nonexistent-identifier",
            )
            assert found_entity is None

    # --- Tests for get_entity_by_identifier_or_error ---

    def test_get_entity_by_identifier_or_error_finds_by_id(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test finding an entity by ID using the _or_error method."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            game = create_test_game(session, name="FindByIDOrError Game")
            # Pass session explicitly
            found_entity = base_manager.get_entity_by_identifier_or_error(
                session,
                Game,
                game.id,
                BaseManagerTestError,
            )
            assert found_entity is not None
            assert found_entity.id == game.id

    def test_get_entity_by_identifier_or_error_finds_by_slug(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test finding an entity by slug using the _or_error method."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            game = create_test_game(session, name="FindBySlugOrError Game")
            assert game.slug == "findbyslugorerror-game"
            # Pass session explicitly
            found_entity = base_manager.get_entity_by_identifier_or_error(
                session,
                Game,
                "findbyslugorerror-game",
                BaseManagerTestError,
            )
            assert found_entity is not None
            assert found_entity.slug == "findbyslugorerror-game"

    def test_get_entity_by_identifier_or_error_raises_error(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test raising the specified error when identifier is not found."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            identifier = "nonexistent-for-error"
            with pytest.raises(BaseManagerTestError) as exc_info:
                # Pass session explicitly
                base_manager.get_entity_by_identifier_or_error(
                    session,
                    Game,
                    identifier,
                    BaseManagerTestError,
                )
            # Check default error message
            assert f"Game not found with identifier '{identifier}'" in str(
                exc_info.value,
            )

    def test_get_entity_by_identifier_or_error_raises_custom_error(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test raising the specified error with a custom message."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            identifier = "nonexistent-for-custom-error"
            custom_message = "Custom not found message."
            with pytest.raises(BaseManagerTestError) as exc_info:
                # Pass session explicitly
                base_manager.get_entity_by_identifier_or_error(
                    session,
                    Game,
                    identifier,
                    BaseManagerTestError,
                    custom_message,
                )
            assert custom_message in str(exc_info.value)

    # --- Tests for get_entity_or_error ---

    def test_get_entity_or_error_finds_by_id(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test finding an entity by ID using get_entity_or_error."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            game = create_test_game(session, name="GetOrError Game")
            # Pass session explicitly
            found_entity = base_manager.get_entity_or_error(
                session,
                Game,
                game.id,
                BaseManagerTestError,
            )
            assert found_entity is not None
            assert found_entity.id == game.id

    def test_get_entity_or_error_raises_error(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test get_entity_or_error raises error for nonexistent ID."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            entity_id = "nonexistent-id-for-get-error"
            with pytest.raises(BaseManagerTestError) as exc_info:
                # Pass session explicitly
                base_manager.get_entity_or_error(
                    session,
                    Game,
                    entity_id,
                    BaseManagerTestError,
                )
            # Check default error message
            assert f"Game with ID {entity_id} not found" in str(exc_info.value)

    # --- Tests for list_entities ---

    def test_list_entities_no_filters(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test listing entities with no filters."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            game1 = create_test_game(session, name="List Game 1")
            game2 = create_test_game(session, name="List Game 2")
            # list_entities uses the manager's session via _execute_db_operation
            entities = base_manager.list_entities(Game)
            assert len(entities) >= 2  # Might be other games from previous tests
            # Now game1 and entities should be from the same session
            assert game1 in entities
            assert game2 in entities

    def test_list_entities_with_filter(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test listing entities with a filter."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            create_test_game(session, name="Filter Other Game")
            game_to_find = create_test_game(session, name="Filter Target Game")
            entities = base_manager.list_entities(
                Game,
                filters={"name": "Filter Target Game"},
            )
            assert len(entities) == 1
            assert entities[0].id == game_to_find.id

    def test_list_entities_with_ordering_asc(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test listing entities with ascending order."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            game_b = create_test_game(session, name="Order B Game")
            game_a = create_test_game(session, name="Order A Game")
            entities = base_manager.list_entities(
                Game,
                order_by="name",
                order_direction="asc",
            )
            # Find the indices of our specific games in the potentially larger list
            ids = [g.id for g in entities]
            try:
                index_a = ids.index(game_a.id)
                index_b = ids.index(game_b.id)
                assert index_a < index_b
            except ValueError:
                pytest.fail("Created games not found in the listed entities")

    def test_list_entities_with_ordering_desc(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test listing entities with descending order."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            game_a = create_test_game(session, name="Order A Game Desc")
            game_b = create_test_game(session, name="Order B Game Desc")
            entities = base_manager.list_entities(
                Game,
                order_by="name",
                order_direction="desc",
            )
            ids = [g.id for g in entities]
            try:
                index_a = ids.index(game_a.id)
                index_b = ids.index(game_b.id)
                assert index_b < index_a  # B should come before A in descending
            except ValueError:
                pytest.fail("Created games not found in the listed entities")

    def test_list_entities_with_limit(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test listing entities with a limit."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            # Create more games than the limit
            create_test_game(session, name="Limit Game 1")
            create_test_game(session, name="Limit Game 2")
            create_test_game(session, name="Limit Game 3")
            entities = base_manager.list_entities(Game, limit=2)
            assert len(entities) == 2

    def test_list_entities_combined(
        self,
        session_context: SessionContext,
        create_test_game,
    ) -> None:
        """Test listing entities with combined filters, ordering, and limit."""
        with session_context as session:
            base_manager = BaseManager(session=session)
            create_test_game(session, name="Combo A", description="Keep")
            game_b = create_test_game(session, name="Combo B", description="Keep")
            game_c = create_test_game(session, name="Combo C", description="Keep")
            create_test_game(session, name="Combo D", description="Ignore")

            entities = base_manager.list_entities(
                Game,
                filters={"description": "Keep"},
                order_by="name",
                order_direction="desc",
                limit=2,
            )
            assert len(entities) == 2
            # Should be C and B in descending order
            assert entities[0].id == game_c.id
            assert entities[1].id == game_b.id
