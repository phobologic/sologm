"""Tests for cascade delete behavior in SQLAlchemy."""

import pytest

def test_cascade_delete_game(db_session, test_game_with_scenes):
    """Test that deleting a game cascades to scenes."""
    game, scenes = test_game_with_scenes

    # Add some events to the scenes
    from sologm.models.event import Event

    for scene in scenes:
        event = Event.create(
            game_id=game.id,
            scene_id=scene.id,
            description="Test event",
            source="manual",
        )
        db_session.add(event)

    db_session.commit()

    # Now delete the game
    db_session.delete(game)
    db_session.commit()

    # Verify scenes are deleted
    from sologm.models.scene import Scene

    scene_count = db_session.query(Scene).filter(Scene.game_id == game.id).count()
    assert scene_count == 0

    # Verify events are deleted
    event_count = db_session.query(Event).filter(Event.game_id == game.id).count()
    assert event_count == 0
