"""Shared test fixtures for core module tests."""

# Import common fixtures from central conftest
# These imports are used by pytest when running tests
from sologm.tests.conftest import (  # noqa: F401
    act_manager,
    create_test_act,
    create_test_event,
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
