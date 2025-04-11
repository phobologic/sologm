"""Shared test fixtures for core module tests."""

import pytest

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
    create_test_event,
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

# Add any core-specific fixtures here if needed
