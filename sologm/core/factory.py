"""Factory functions for creating core components."""

import logging
from types import SimpleNamespace

from sqlalchemy.orm import Session

from sologm.core.act import ActManager
from sologm.core.dice import DiceManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
from sologm.integrations.anthropic import AnthropicClient
from sologm.utils.config import get_config

logger = logging.getLogger(__name__)


def create_all_managers(session: Session) -> SimpleNamespace:
    """Create instances of all core managers with the given session.

    This helper function centralizes the instantiation of managers, ensuring they
    all share the same database session and dependencies are correctly injected.
    It's primarily intended for use in tests and potentially complex CLI commands
    to reduce boilerplate.

    Args:
        session: The active SQLAlchemy session to be used by all managers.

    Returns:
        A SimpleNamespace object containing instances of all managers.
        Access managers like `managers.game`, `managers.act`, etc.
    """
    logger.debug(f"Creating all managers with session ID: {id(session)}")

    # Instantiate managers in dependency order
    game_manager = GameManager(session=session)
    act_manager = ActManager(session=session, game_manager=game_manager)
    scene_manager = SceneManager(session=session, act_manager=act_manager)
    event_manager = EventManager(session=session, scene_manager=scene_manager)
    dice_manager = DiceManager(session=session, scene_manager=scene_manager)

    # OracleManager requires AnthropicClient, which needs config
    config = get_config()
    anthropic_client = AnthropicClient(api_key=config.get("anthropic_api_key"))
    oracle_manager = OracleManager(
        session=session,
        scene_manager=scene_manager,
        anthropic_client=anthropic_client,
    )

    managers = SimpleNamespace(
        game=game_manager,
        act=act_manager,
        scene=scene_manager,
        event=event_manager,
        dice=dice_manager,
        oracle=oracle_manager,
    )
    logger.debug("Finished creating all managers.")
    return managers
