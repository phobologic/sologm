"""Tests for transaction isolation in SQLAlchemy."""

import pytest
from sqlalchemy.orm import sessionmaker

from sologm.models.game import Game


def test_transaction_isolation(db_engine):
    """Test that transactions are properly isolated."""
    # Create two separate sessions
    Session = sessionmaker(bind=db_engine)
    session1 = Session()
    session2 = Session()

    try:
        # In session1, create a game but don't commit
        game = Game.create(name="Isolated Game", description="Test isolation")
        session1.add(game)
        session1.flush()  # Flush but don't commit

        # Verify game is visible in session1
        game_in_session1 = (
            session1.query(Game).filter(Game.name == "Isolated Game").first()
        )
        assert game_in_session1 is not None

        # Verify game is NOT visible in session2
        game_in_session2 = (
            session2.query(Game).filter(Game.name == "Isolated Game").first()
        )
        assert game_in_session2 is None
    finally:
        session1.rollback()
        session1.close()
        session2.close()


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
