"""Shared test fixtures for CLI utility tests."""

from unittest.mock import Mock, MagicMock

import pytest
from rich.console import Console

# Import fixtures from core tests to reuse them
from sologm.core.tests.conftest import (
    db_engine,
    db_session,
    database_session,
    game_manager,
    scene_manager,
    event_manager,
    dice_manager,
    test_game,
    test_scene,
    test_events,
    test_interpretation_set,
    test_interpretations,
    test_dice_roll,
)
from sologm.integrations.anthropic import AnthropicClient


@pytest.fixture
def mock_console():
    """Create a mocked Rich console."""
    mock = Mock(spec=Console)
    # Set a default width for the console to avoid type errors
    mock.width = 80
    return mock


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    return MagicMock(spec=AnthropicClient)


@pytest.fixture
def oracle_manager(mock_anthropic_client, db_session):
    """Create an OracleManager with a test session."""
    from sologm.core.oracle import OracleManager

    return OracleManager(anthropic_client=mock_anthropic_client, session=db_session)
