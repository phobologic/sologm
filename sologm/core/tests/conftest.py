"""Shared test fixtures for core module tests."""

import pytest
from sqlalchemy.orm import Session

from sologm.models.event import Event
from sologm.models.event_source import EventSource

# Import common fixtures from central conftest
from sologm.tests.conftest import (
    # Database fixtures
    db_engine,
    db_session,
    database_session,
    # Mock fixtures
    mock_anthropic_client,
    # Manager fixtures
    game_manager,
    act_manager,
    scene_manager,
    event_manager,
    dice_manager,
    oracle_manager,
    # Model factory fixtures
    create_test_game,
    create_test_act,
    create_test_scene,
    # Common test objects
    test_game,
    test_act,
    test_scene,
    test_events,
    test_interpretation_set,
    test_interpretations,
    test_dice_roll,
    # Helper fixtures
    initialize_event_sources,
    assert_model_properties,
    test_hybrid_expressions,
    # Complex test fixtures
    test_game_with_scenes,
    test_game_with_complete_hierarchy,
    test_hybrid_property_game,
)


# Add core-specific fixtures here
@pytest.fixture
def create_test_event(db_session):
    """Factory fixture to create test events."""

    def _create_event(
        scene_id, description="Test event", source_name="manual", interpretation_id=None
    ):
        # Get the source ID for the specified source
        source_obj = (
            db_session.query(EventSource)
            .filter(EventSource.name == source_name)
            .first()
        )
        if not source_obj:
            # Create it if it doesn't exist
            source_obj = EventSource.create(name=source_name)
            db_session.add(source_obj)
            db_session.commit()

        event = Event.create(
            scene_id=scene_id,
            description=description,
            source_id=source_obj.id,
            interpretation_id=interpretation_id,
        )
        db_session.add(event)
        db_session.commit()
        return event

    return _create_event
