"""Tests for cascade delete behavior in SQLAlchemy."""

# Add necessary imports for models and factory fixtures
from typing import Callable

from sqlalchemy.orm import Session

from sologm.models.act import Act
from sologm.models.event import Event
from sologm.models.game import Game  # Import Game model
from sologm.models.scene import Scene


def test_cascade_delete_game(
    session_context,  # Use session_context fixture
    create_test_game,  # Use factory fixtures
    create_test_act,
    create_test_scene: Callable,
    create_test_event: Callable,
    initialize_event_sources: Callable[[Session], None],  # Add fixture
):
    """Test that deleting a game cascades to all related objects."""
    # Wrap logic in session_context
    with session_context as session:
        # Initialize event sources first
        initialize_event_sources(session)  # Call initializer

        # Create the test data within the session context
        game = create_test_game(session, name="Cascade Test Game")
        act1 = create_test_act(session, game_id=game.id, title="Act 1")
        # Explicitly set is_active=False for the second act
        act2 = create_test_act(session, game_id=game.id, title="Act 2", is_active=False)
        scene1_1 = create_test_scene(session, act_id=act1.id, title="Scene 1.1")
        scene1_2 = create_test_scene(session, act_id=act1.id, title="Scene 1.2")
        scene2_1 = create_test_scene(session, act_id=act2.id, title="Scene 2.1")
        event1_1_1 = create_test_event(
            session, scene_id=scene1_1.id, description="Event 1.1.1"
        )
        event1_2_1 = create_test_event(
            session, scene_id=scene1_2.id, description="Event 1.2.1"
        )
        event2_1_1 = create_test_event(
            session, scene_id=scene2_1.id, description="Event 2.1.1"
        )

        # Store IDs for verification after deletion
        game_id = game.id  # Store game_id as well
        act_ids = [act1.id, act2.id]
        scene_ids = [scene1_1.id, scene1_2.id, scene2_1.id]
        event_ids = [event1_1_1.id, event1_2_1.id, event2_1_1.id]

        # Delete the game using the session
        session.delete(game)
        # Flush the session to send the delete operation before querying
        session.flush()
        # No explicit commit needed here, context manager handles it

        # Verify game is deleted (optional but good practice)
        deleted_game = session.get(Game, game_id)
        assert deleted_game is None, f"Game {game_id} was not deleted."

        # Verify acts are deleted using the session
        act_count = session.query(Act).filter(Act.id.in_(act_ids)).count()
        assert act_count == 0, f"Expected 0 Acts, found {act_count}"

        # Verify scenes are deleted using the session
        scene_count = session.query(Scene).filter(Scene.id.in_(scene_ids)).count()
        assert scene_count == 0, f"Expected 0 Scenes, found {scene_count}"

        # Verify events are deleted using the session
        event_count = session.query(Event).filter(Event.id.in_(event_ids)).count()
        assert event_count == 0, f"Expected 0 Events, found {event_count}"

    # The session is automatically committed or rolled back upon exiting the 'with' block
