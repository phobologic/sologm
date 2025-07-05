"""Test fixtures for model tests."""

# Import all necessary fixtures from the main test conftest
from sologm.tests.conftest import (
    auto_mock_anthropic_client,
    cli_test,
    # Mock entity fixtures for navigation utils
    create_mock_entity,
    create_mock_entity_with_relationships,
    create_test_act,
    create_test_event,
    # Factory fixtures
    create_test_game,
    create_test_interpretation,
    create_test_interpretation_set,
    create_test_scene,
    database_manager,
    # Database fixtures
    db_engine,
    # Helper fixtures
    initialize_event_sources,
    # Mock fixtures
    mock_anthropic_client,
    mock_config_no_api_key,
    session_context,
)

# Re-export all fixtures so they're available to model tests
__all__ = [
    "db_engine",
    "database_manager",
    "session_context",
    "mock_anthropic_client",
    "auto_mock_anthropic_client",
    "mock_config_no_api_key",
    "create_mock_entity",
    "create_mock_entity_with_relationships",
    "create_test_game",
    "create_test_act",
    "create_test_scene",
    "create_test_event",
    "create_test_interpretation_set",
    "create_test_interpretation",
    "initialize_event_sources",
    "cli_test",
]
