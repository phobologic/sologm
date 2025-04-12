"""Shared test fixtures for core module tests."""

import logging

import pytest

from sologm.models.event import Event
from sologm.models.event_source import EventSource

# Import common fixtures from central conftest
# These imports are used by pytest when running tests
from sologm.tests.conftest import (  # noqa: F401
    act_manager,
    create_test_act,
    create_test_game,
    create_test_scene,
    database_session,
    db_engine,
    db_session,
    dice_manager,
    event_manager,
    game_manager,
    mock_anthropic_client,
    oracle_manager,
    scene_manager,
    test_act,
    test_dice_roll,
    test_events,
    test_game,
    test_interpretation_set,
    test_interpretations,
    test_scene,
)

# Add core-specific fixtures here
@pytest.fixture
def create_test_event(db_session):
    """Factory fixture to create test events."""

    def _create_event(
        scene_id, description="Test event", source_name="manual", interpretation_id=None
    ):
        logging.debug(
            f"create_test_event called with scene_id={scene_id}, "
            f"description={description}, source_name={source_name}"
        )

        # Get the source ID for the specified source
        source_obj = (
            db_session.query(EventSource)
            .filter(EventSource.name == source_name)
            .first()
        )
        if not source_obj:
            # Create it if it doesn't exist
            logging.debug(f"Creating new event source: {source_name}")
            source_obj = EventSource.create(name=source_name)
            db_session.add(source_obj)
            db_session.commit()

        logging.debug(
            f"Using source_obj with id={source_obj.id}, name={source_obj.name}"
        )

        event = Event.create(
            scene_id=scene_id,
            description=description,
            source_id=source_obj.id,
            interpretation_id=interpretation_id,
        )
        logging.debug(
            f"Created event with id={event.id}, description={description}, "
            f"source_id={source_obj.id}"
        )

        db_session.add(event)
        db_session.commit()

        # Verify the event was created correctly
        created_event = db_session.query(Event).filter(Event.id == event.id).first()
        logging.debug(
            f"Verified event in DB: id={created_event.id}, "
            f"description={created_event.description}, "
            f"source_id={created_event.source_id}"
        )

        return event

    return _create_event
