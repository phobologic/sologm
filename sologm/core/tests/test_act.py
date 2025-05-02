"""Tests for the Act manager."""

from typing import Callable, Optional  # Make sure Optional is imported if needed
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session  # Add Session import

from sologm.core.act import ActManager
from sologm.core.factory import create_all_managers
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.database.session import SessionContext
from sologm.utils.errors import APIError, GameError


class TestActManager:
    """Tests for the ActManager class."""

    def test_manager_relationships(self, session_context: SessionContext):
        """Test manager relationships."""
        with session_context as session:
            managers = create_all_managers(session)

            # Test game_manager property
            assert isinstance(managers.act.game_manager, GameManager)

            # Test scene_manager property
            assert isinstance(managers.act.scene_manager, SceneManager)

            # Test passing explicit game_manager
            mock_game_manager = MagicMock(spec=GameManager)
            act_manager_with_parent = ActManager(
                game_manager=mock_game_manager, session=session
            )
            assert act_manager_with_parent.game_manager is mock_game_manager

            # Test session is passed correctly
            assert act_manager_with_parent._session is session

    def test_create_act(
        self, session_context: SessionContext, create_test_game: Callable
    ):
        """Test creating an act."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)

            # Create an act with title and summary
            act = managers.act.create_act(
                game_id=test_game.id,
                title="Test Act",
                summary="A test act",
            )

            assert act.id is not None
            assert act.game_id == test_game.id
            assert act.title == "Test Act"
            assert act.summary == "A test act"
            assert act.sequence == 1
            assert act.is_active is True

            # Complete the first act before creating a new one
            managers.act.complete_act(act_id=act.id)

            # Create an untitled act
            untitled_act = managers.act.create_act(
                game_id=test_game.id,
            )

            assert untitled_act.id is not None
            assert untitled_act.game_id == test_game.id
            assert untitled_act.title is None
            assert untitled_act.summary is None
            assert untitled_act.sequence == 2
            assert untitled_act.is_active is True

            # Refresh the first act to see if it was deactivated
            session.refresh(act)
            assert act.is_active is False  # Previous act should be deactivated

            # Test creating an act with make_active=False
            non_active_act = managers.act.create_act(
                game_id=test_game.id,
                title="Non-active Act",
                summary="This act won't be active",
                make_active=False,
            )

            assert non_active_act.id is not None
            assert non_active_act.is_active is False

            # Verify the previous act is still active
            session.refresh(untitled_act)
            assert untitled_act.is_active is True

    def test_create_act_with_context(
        self, session_context: SessionContext, create_test_game: Callable
    ):
        """Test creating an act using session context."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)

            # Create an act with title and summary
            act = managers.act.create_act(
                game_id=test_game.id,
                title="Context Test Act",
                summary="Created with session context",
            )

            # Verify the act was created correctly
            assert act.id is not None
            assert act.game_id == test_game.id
            assert act.title == "Context Test Act"
            assert act.summary == "Created with session context"
            assert act.sequence == 1
            assert act.is_active is True

            # Complete the first act before creating a new one
            managers.act.complete_act(act_id=act.id)

            # Create another act to test deactivation
            second_act = managers.act.create_act(
                game_id=test_game.id,
                title="Second Context Act",
            )

            # Refresh first act to verify it was deactivated
            session.refresh(act)
            assert act.is_active is False
            assert second_act.is_active is True

    def test_create_act_invalid_game(self, session_context: SessionContext):
        """Test creating an act with an invalid game ID."""
        with session_context as session:
            managers = create_all_managers(session)
            with pytest.raises(GameError):
                managers.act.create_act(
                    game_id="invalid-id",
                    title="Test Act",
                )

    def test_list_acts(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test listing acts."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Create a second act
            second_act = create_test_act(
                session,
                game_id=test_game.id,
                title="Second Act",
                sequence=2,
                is_active=False,
            )

            # List acts with explicit game_id
            acts = managers.act.list_acts(test_game.id)

            assert len(acts) == 2
            assert acts[0].id == test_act.id
            assert acts[1].id == second_act.id

            # Test listing acts with active game (requires mocking)
            with patch.object(managers.game, "get_active_game", return_value=test_game):
                acts = managers.act.list_acts()
                assert len(acts) == 2
                assert acts[0].id == test_act.id
                assert acts[1].id == second_act.id

            # Test listing acts with no active game
            with patch.object(managers.game, "get_active_game", return_value=None):
                with pytest.raises(GameError, match="No active game"):
                    managers.act.list_acts()

    def test_get_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test getting an act by ID."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Get existing act
            act = managers.act.get_act(test_act.id)

            assert act is not None
            assert act.id == test_act.id

            # Get non-existent act
            act = managers.act.get_act("invalid-id")

            assert act is None

    def test_get_act_by_identifier_or_error(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test getting an act by ID or slug, raising error if not found."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id, title="Find Me")

            # Get by ID
            act_by_id = managers.act.get_act_by_identifier_or_error(test_act.id)
            assert act_by_id is not None
            assert act_by_id.id == test_act.id

            # Get by slug
            act_by_slug = managers.act.get_act_by_identifier_or_error(test_act.slug)
            assert act_by_slug is not None
            assert act_by_slug.id == test_act.id

            # Get non-existent by ID
            with pytest.raises(GameError, match="Act not found with identifier"):
                managers.act.get_act_by_identifier_or_error("invalid-id")

            # Get non-existent by slug
            with pytest.raises(GameError, match="Act not found with identifier"):
                managers.act.get_act_by_identifier_or_error("invalid-slug")

    def test_get_active_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test getting the active act."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Get active act with explicit game_id
            active_act = managers.act.get_active_act(test_game.id)

            assert active_act is not None
            assert active_act.id == test_act.id

            # Test getting active act with active game (requires mocking)
            with patch.object(managers.game, "get_active_game", return_value=test_game):
                active_act = managers.act.get_active_act()
                assert active_act is not None
                assert active_act.id == test_act.id

            # Deactivate all acts
            managers.act._deactivate_all_acts(session, test_game.id)
            session.flush()  # Flush changes within the context

            # Get active act when none is active
            active_act = managers.act.get_active_act(test_game.id)
            assert active_act is None

            # Test getting active act with no active game
            with patch.object(managers.game, "get_active_game", return_value=None):
                with pytest.raises(GameError, match="No active game"):
                    managers.act.get_active_act()

    def test_edit_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test editing an act."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(
                session, game_id=test_game.id, title="Original Title"
            )

            # Edit title only using ID
            updated_act_by_id = managers.act.edit_act(
                act_id=test_act.id,
                title="Updated Title",
            )

            assert updated_act_by_id.title == "Updated Title"
            assert updated_act_by_id.summary == test_act.summary
            assert "updated-title" in updated_act_by_id.slug

            # Edit summary only using slug
            updated_act_by_slug = managers.act.edit_act(
                act_id=updated_act_by_id.id,  # Still need ID here for the edit method itself
                summary="Updated summary",
            )

            assert (
                updated_act_by_slug.title == "Updated Title"
            )  # Title from previous edit
            assert updated_act_by_slug.summary == "Updated summary"

            # Edit both title and summary using ID again
            final_updated_act = managers.act.edit_act(
                act_id=test_act.id,
                title="Final Title",
                summary="Final summary",
            )

            assert final_updated_act.title == "Final Title"
            assert final_updated_act.summary == "Final summary"
            assert "final-title" in final_updated_act.slug

            # Edit non-existent act
            with pytest.raises(GameError):
                managers.act.edit_act(
                    act_id="invalid-id",
                    title="Invalid",
                )

    def test_edit_act_no_fields(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test editing an act without providing any fields."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            with pytest.raises(ValueError, match="At least one of title or summary"):
                managers.act.edit_act(act_id=test_act.id)

    def test_complete_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test completing an act."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Complete act
            completed_act = managers.act.complete_act(
                act_id=test_act.id,
                title="Completed Title",
                summary="Completed summary",
            )

            assert completed_act.title == "Completed Title"
            assert completed_act.summary == "Completed summary"
            assert completed_act.is_active is False
            assert "completed-title" in completed_act.slug

            # Complete non-existent act
            with pytest.raises(GameError):
                managers.act.complete_act(
                    act_id="invalid-id",
                )

    def test_set_active(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test setting an act as active."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # First, complete the existing active act
            managers.act.complete_act(act_id=test_act.id)

            # Create a second act
            second_act = create_test_act(
                session,
                game_id=test_game.id,
                title="Second Act",
                sequence=2,
                is_active=True,
            )

            # Refresh first act to see if it was deactivated
            session.refresh(test_act)
            assert test_act.is_active is False
            assert second_act.is_active is True

            # Set first act as active
            activated_act = managers.act.set_active(test_act.id)

            assert activated_act.id == test_act.id
            assert activated_act.is_active is True

            # Verify second act is inactive
            session.refresh(second_act)
            assert second_act.is_active is False

            # Set non-existent act as active
            with pytest.raises(GameError):
                managers.act.set_active("invalid-id")

            # Create another game and act
            other_game = create_test_game(
                session, name="Other Game", description="Another test game"
            )
            other_act = create_test_act(
                session,
                game_id=other_game.id,
                title="Other Act",
                sequence=1,
            )

            # Set act from different game as active (should work now since we don't validate game_id)
            other_activated_act = managers.act.set_active(other_act.id)
            assert other_activated_act.id == other_act.id
            assert other_activated_act.is_active is True

    def test_set_active_with_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test setting an act as active using session context."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # First, complete the existing active act
            managers.act.complete_act(act_id=test_act.id)

            # Create a second act
            second_act = create_test_act(
                session,
                game_id=test_game.id,
                title="Second Context Act",
                sequence=2,
                is_active=True,
            )

            # Refresh first act to see if it was deactivated
            session.refresh(test_act)
            assert test_act.is_active is False
            assert second_act.is_active is True

            # Set first act as active
            activated_act = managers.act.set_active(test_act.id)

            assert activated_act.id == test_act.id
            assert activated_act.is_active is True

            # Verify second act is inactive
            session.refresh(second_act)
            assert second_act.is_active is False

    def test_validate_active_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test validating active act."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Valid context with explicit game_id
            act = managers.act.validate_active_act(test_game.id)
            assert act.id == test_act.id

            # Test validating with active game (requires mocking)
            with patch.object(managers.game, "get_active_game", return_value=test_game):
                act = managers.act.validate_active_act()
                assert act.id == test_act.id

            # Deactivate all acts
            managers.act._deactivate_all_acts(session, test_game.id)
            session.flush()

            # Invalid context - no active act
            with pytest.raises(GameError, match="No active act"):
                managers.act.validate_active_act(test_game.id)

            # Test validating with no active game
            with patch.object(managers.game, "get_active_game", return_value=None):
                with pytest.raises(GameError, match="No active game"):
                    managers.act.validate_active_act()

    def test_prepare_act_data_for_summary(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable[[Session], None],  # Add fixture
    ):
        """Test preparing act data for summary."""
        with session_context as session:
            # Initialize event sources first
            initialize_event_sources(session)  # Call initializer

            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)
            test_scene = create_test_scene(session, act_id=test_act.id)

            # Create some events for the scene
            event1 = create_test_event(
                session, scene_id=test_scene.id, description="First event"
            )
            event2 = create_test_event(
                session, scene_id=test_scene.id, description="Second event"
            )

            # Prepare data
            act_data = managers.act.prepare_act_data_for_summary(
                test_act.id, "Additional context"
            )

            # Verify structure
            assert act_data["game"]["name"] == test_game.name
            assert act_data["game"]["description"] == test_game.description
            assert act_data["act"]["sequence"] == test_act.sequence
            assert act_data["act"]["title"] == test_act.title
            assert act_data["act"]["summary"] == test_act.summary
            assert act_data["additional_context"] == "Additional context"

            # Verify scenes
            assert len(act_data["scenes"]) == 1
            scene_data = act_data["scenes"][0]
            assert scene_data["sequence"] == test_scene.sequence
            assert scene_data["title"] == test_scene.title
            assert scene_data["description"] == test_scene.description

            # Verify events
            assert len(scene_data["events"]) == 2
            event_descriptions = [e["description"] for e in scene_data["events"]]
            assert "First event" in event_descriptions
            assert "Second event" in event_descriptions

    def test_create_act_no_active_game(
        self, session_context: SessionContext, monkeypatch
    ):
        """Test creating an act without game_id when no game is active."""
        with session_context as session:
            managers = create_all_managers(session)
            # Mock get_active_game to return None
            monkeypatch.setattr(managers.game, "get_active_game", lambda: None)

            with pytest.raises(GameError, match="No active game"):
                managers.act.create_act(title="Test Act")

    def test_create_act_already_active(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test creating an active act when another is already active."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            # Create an active act using the factory
            create_test_act(session, game_id=test_game.id, is_active=True)

            # Attempt to create another active act
            with pytest.raises(GameError, match="Cannot create a new act"):
                managers.act.create_act(
                    game_id=test_game.id, title="Another Active Act"
                )

    def test_generate_and_update_act_summary(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        monkeypatch,
    ):
        """Test generating and updating act summary."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Mock the generate_act_summary method
            mock_summary = {"title": "Generated Title", "summary": "Generated summary"}
            monkeypatch.setattr(
                managers.act,
                "generate_act_summary",
                lambda *args, **kwargs: mock_summary,
            )

            # Test the method
            result = managers.act.generate_and_update_act_summary(
                test_act.id, "Additional context"
            )

            # Verify results
            assert result["title"] == "Generated Title"
            assert result["summary"] == "Generated summary"
            assert result["act"].id == test_act.id

            # Verify act was updated *in the session*
            # REMOVED: session.refresh(test_act) - Verify state within the session before commit
            assert test_act.title == "Generated Title"
            assert test_act.summary == "Generated summary"

    def test_validate_can_create_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ):
        """Test validating if a new act can be created."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id, is_active=True)

            # Should raise error when there's an active act
            with pytest.raises(GameError, match="Cannot create a new act"):
                managers.act.validate_can_create_act(test_game.id)

            # Deactivate the act
            test_act.is_active = False
            session.add(test_act)
            session.flush()

            # Should not raise error when there's no active act
            managers.act.validate_can_create_act(test_game.id)

    def test_generate_act_summary(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        monkeypatch,
    ):
        """Test generating act summary."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Mock the AnthropicClient and ActPrompts to avoid actual API calls
            mock_client = MagicMock()
            mock_client.send_message.return_value = (
                "TITLE: Test Title\n\nSUMMARY:\nTest summary paragraph."
            )

            mock_prepare_data = MagicMock()
            mock_prepare_data.return_value = {
                "game": {"name": "Test Game", "description": "Test Description"},
                "act": {"sequence": 1, "title": "Test Act", "summary": "Test Summary"},
                "scenes": [],
                "additional_context": "Additional context",
            }

            # Apply mocks
            monkeypatch.setattr(
                managers.act, "prepare_act_data_for_summary", mock_prepare_data
            )
            # Mock the AnthropicClient class in its original module
            # When AnthropicClient() is called inside generate_act_summary, it will use this patched version
            monkeypatch.setattr(
                "sologm.integrations.anthropic.AnthropicClient", lambda: mock_client
            )

            # Test the method
            result = managers.act.generate_act_summary(
                test_act.id, "Additional context"
            )

            # Verify results
            assert result["title"] == "Test Title"
            assert result["summary"] == "Test summary paragraph."

            # Verify mocks were called correctly
            mock_prepare_data.assert_called_once_with(test_act.id, "Additional context")
            mock_client.send_message.assert_called_once()

    def test_generate_act_summary_api_error(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        monkeypatch,
    ):
        """Test handling of API errors during summary generation."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Mock the AnthropicClient to raise an error
            mock_client = MagicMock()
            mock_client.send_message.side_effect = Exception("API connection failed")

            mock_prepare_data = MagicMock()
            mock_prepare_data.return_value = {
                "game": {"name": "Test Game", "description": "Test Description"},
                "act": {"sequence": 1, "title": "Test Act", "summary": "Test Summary"},
                "scenes": [],
                "additional_context": None,
            }

            # Apply mocks
            monkeypatch.setattr(
                managers.act, "prepare_act_data_for_summary", mock_prepare_data
            )
            # Mock the AnthropicClient class in its original module
            monkeypatch.setattr(
                "sologm.integrations.anthropic.AnthropicClient", lambda: mock_client
            )

            # Test the method and assert APIError is raised
            with pytest.raises(APIError, match="Failed to generate act summary"):
                managers.act.generate_act_summary(test_act.id)

    def test_generate_act_summary_with_feedback(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        monkeypatch,
    ):
        """Test generating act summary with feedback on previous generation."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Mock the generate_act_summary method
            mock_generate = MagicMock()
            mock_generate.return_value = {
                "title": "New Test Title",
                "summary": "New test summary paragraph.",
            }

            # Mock prepare_regeneration_context
            mock_prepare_context = MagicMock()
            mock_prepare_context.return_value = "Formatted regeneration context"

            # Apply mocks
            monkeypatch.setattr(managers.act, "generate_act_summary", mock_generate)
            monkeypatch.setattr(
                managers.act, "prepare_regeneration_context", mock_prepare_context
            )

            # Test with previous generation
            previous_gen = {"title": "Old Title", "summary": "Old summary"}

            result = managers.act.generate_act_summary_with_feedback(
                test_act.id, "User feedback", previous_gen
            )

            # Verify results
            assert result["title"] == "New Test Title"
            assert result["summary"] == "New test summary paragraph."

            # Verify mocks were called correctly
            mock_prepare_context.assert_called_once_with(previous_gen, "User feedback")
            mock_generate.assert_called_once_with(
                test_act.id, "Formatted regeneration context"
            )

            # Test without previous generation
            mock_generate.reset_mock()
            mock_prepare_context.reset_mock()

            result = managers.act.generate_act_summary_with_feedback(
                test_act.id, context="Just context"
            )

            # Verify results
            assert result["title"] == "New Test Title"
            assert result["summary"] == "New test summary paragraph."

            # Verify mocks were called correctly
            mock_prepare_context.assert_not_called()
            mock_generate.assert_called_once_with(test_act.id, "Just context")

    def test_prepare_regeneration_context(self, session_context: SessionContext):
        """Test preparing regeneration context."""
        with session_context as session:
            managers = create_all_managers(session)
            previous_gen = {"title": "Old Title", "summary": "Old summary paragraph."}

            # Test with just feedback
            context = managers.act.prepare_regeneration_context(
                previous_gen, "Make it more dramatic"
            )

            # Verify context structure
            assert "PREVIOUS GENERATION:" in context
            assert "Old Title" in context
            assert "Old summary paragraph." in context
            assert "USER FEEDBACK:" in context
            assert "Make it more dramatic" in context
            assert "INSTRUCTIONS:" in context

    def test_complete_act_with_ai(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        monkeypatch,
    ):
        """Test completing an act with AI-generated content."""
        with session_context as session:
            managers = create_all_managers(session)
            test_game = create_test_game(session)
            test_act = create_test_act(session, game_id=test_game.id)

            # Mock the complete_act method
            mock_complete = MagicMock()
            mock_complete.return_value = test_act

            # Apply mock
            monkeypatch.setattr(managers.act, "complete_act", mock_complete)

            # Test the method
            result = managers.act.complete_act_with_ai(
                test_act.id, "AI Title", "AI Summary"
            )

            # Verify result
            assert result is test_act

            # Verify mock was called correctly
            mock_complete.assert_called_once_with(
                act_id=test_act.id, title="AI Title", summary="AI Summary"
            )
