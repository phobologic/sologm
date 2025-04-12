"""Tests for the Act manager."""

import pytest
from unittest.mock import MagicMock

from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.models.act import ActStatus
from sologm.utils.errors import GameError


class TestActManager:
    """Tests for the ActManager class."""

    def test_manager_relationships(self, db_session, act_manager):
        """Test manager relationships."""
        # Test game_manager property
        assert isinstance(act_manager.game_manager, GameManager)

        # Test scene_manager property
        assert isinstance(act_manager.scene_manager, SceneManager)

        # Test passing explicit game_manager
        mock_game_manager = MagicMock(spec=GameManager)
        from sologm.core.act import ActManager

        act_manager_with_parent = ActManager(
            game_manager=mock_game_manager, session=db_session
        )
        assert act_manager_with_parent.game_manager is mock_game_manager

    def test_create_act(self, db_session, test_game, act_manager):
        """Test creating an act."""
        # Create an act with title and description
        act = act_manager.create_act(
            game_id=test_game.id,
            title="Test Act",
            description="A test act",
        )

        assert act.id is not None
        assert act.game_id == test_game.id
        assert act.title == "Test Act"
        assert act.description == "A test act"
        assert act.sequence == 1
        assert act.status == ActStatus.ACTIVE
        assert act.is_active is True

        # Create an untitled act
        untitled_act = act_manager.create_act(
            game_id=test_game.id,
        )

        assert untitled_act.id is not None
        assert untitled_act.game_id == test_game.id
        assert untitled_act.title is None
        assert untitled_act.description is None
        assert untitled_act.sequence == 2
        assert untitled_act.status == ActStatus.ACTIVE
        assert untitled_act.is_active is True

        # Refresh the first act to see if it was deactivated
        db_session.refresh(act)
        assert act.is_active is False  # Previous act should be deactivated

    def test_create_act_invalid_game(self, db_session, act_manager):
        """Test creating an act with an invalid game ID."""
        with pytest.raises(GameError):
            act_manager.create_act(
                game_id="invalid-id",
                title="Test Act",
            )

    def test_list_acts(
        self, db_session, test_game, test_act, create_test_act, act_manager
    ):
        """Test listing acts."""
        # Create a second act
        second_act = create_test_act(
            game_id=test_game.id,
            title="Second Act",
            sequence=2,
            is_active=False,
        )

        # List acts
        acts = act_manager.list_acts(test_game.id)

        assert len(acts) == 2
        assert acts[0].id == test_act.id
        assert acts[1].id == second_act.id

    def test_get_act(self, db_session, test_act, act_manager):
        """Test getting an act by ID."""
        # Get existing act
        act = act_manager.get_act(test_act.id)

        assert act is not None
        assert act.id == test_act.id

        # Get non-existent act
        act = act_manager.get_act("invalid-id")

        assert act is None

    def test_get_active_act(self, db_session, test_game, test_act, act_manager):
        """Test getting the active act."""
        # Get active act
        active_act = act_manager.get_active_act(test_game.id)

        assert active_act is not None
        assert active_act.id == test_act.id

        # Deactivate all acts
        act_manager._deactivate_all_acts(db_session, test_game.id)
        db_session.commit()

        # Get active act when none is active
        active_act = act_manager.get_active_act(test_game.id)

        assert active_act is None

    def test_edit_act(self, db_session, test_act, act_manager):
        """Test editing an act."""
        # Edit title only
        updated_act = act_manager.edit_act(
            act_id=test_act.id,
            title="Updated Title",
        )

        assert updated_act.title == "Updated Title"
        assert updated_act.description == test_act.description

        # Edit description only
        updated_act = act_manager.edit_act(
            act_id=test_act.id,
            description="Updated description",
        )

        assert updated_act.title == "Updated Title"
        assert updated_act.description == "Updated description"

        # Edit both title and description
        updated_act = act_manager.edit_act(
            act_id=test_act.id,
            title="Final Title",
            description="Final description",
        )

        assert updated_act.title == "Final Title"
        assert updated_act.description == "Final description"

        # Edit non-existent act
        with pytest.raises(GameError):
            act_manager.edit_act(
                act_id="invalid-id",
                title="Invalid",
            )

    def test_complete_act(self, db_session, test_act, act_manager):
        """Test completing an act."""
        # Complete act
        completed_act = act_manager.complete_act(
            act_id=test_act.id,
            title="Completed Title",
            description="Completed description",
        )

        assert completed_act.title == "Completed Title"
        assert completed_act.description == "Completed description"
        assert completed_act.status == ActStatus.COMPLETED

        # Complete non-existent act
        with pytest.raises(GameError):
            act_manager.complete_act(
                act_id="invalid-id",
            )

    def test_set_active(
        self, db_session, test_game, test_act, create_test_act, act_manager
    ):
        """Test setting an act as active."""
        # Create a second act
        second_act = create_test_act(
            game_id=test_game.id,
            title="Second Act",
            sequence=2,
            is_active=True,
        )

        # Refresh first act to see if it was deactivated
        db_session.refresh(test_act)
        assert test_act.is_active is False
        assert second_act.is_active is True

        # Set first act as active
        activated_act = act_manager.set_active(test_act.id)

        assert activated_act.id == test_act.id
        assert activated_act.is_active is True

        # Verify second act is inactive
        db_session.refresh(second_act)
        assert second_act.is_active is False

        # Set non-existent act as active
        with pytest.raises(GameError):
            act_manager.set_active("invalid-id")

        # Create another game and act
        from sologm.models.game import Game

        other_game = Game.create(name="Other Game", description="Another test game")
        db_session.add(other_game)
        db_session.flush()

        other_act = create_test_act(
            game_id=other_game.id,
            title="Other Act",
            sequence=1,
        )

        # Set act from different game as active (should work now since we don't validate game_id)
        other_activated_act = act_manager.set_active(other_act.id)
        assert other_activated_act.id == other_act.id
        assert other_activated_act.is_active is True

    def test_validate_active_act(self, db_session, test_game, test_act, act_manager):
        """Test validating active act."""
        # Valid context
        act = act_manager.validate_active_act(test_game.id)
        assert act.id == test_act.id

        # Deactivate all acts
        act_manager._deactivate_all_acts(db_session, test_game.id)
        db_session.commit()

        # Invalid context - no active act
        with pytest.raises(GameError):
            act_manager.validate_active_act(test_game.id)
