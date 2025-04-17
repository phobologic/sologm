"""Tests for cascade delete behavior in SQLAlchemy."""


def test_cascade_delete_game(db_session, test_game_with_complete_hierarchy):
    """Test that deleting a game cascades to all related objects."""
    game, acts, scenes, events = test_game_with_complete_hierarchy

    # Store IDs for verification after deletion
    act_ids = [act.id for act in acts]
    scene_ids = [scene.id for scene in scenes]
    event_ids = [event.id for event in events]

    # Delete the game
    db_session.delete(game)
    db_session.commit()

    # Verify acts are deleted
    from sologm.models.act import Act

    act_count = db_session.query(Act).filter(Act.id.in_(act_ids)).count()
    assert act_count == 0

    # Verify scenes are deleted
    from sologm.models.scene import Scene

    scene_count = db_session.query(Scene).filter(Scene.id.in_(scene_ids)).count()
    assert scene_count == 0

    # Verify events are deleted
    from sologm.models.event import Event

    event_count = db_session.query(Event).filter(Event.id.in_(event_ids)).count()
    assert event_count == 0
