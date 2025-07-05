"""Factory functions for creating core components."""

import logging
from types import SimpleNamespace
from typing import Optional  # Add Optional

from sqlalchemy.orm import Session

from sologm.core.act import ActManager
from sologm.core.dice import DiceManager
from sologm.core.event import EventManager
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager
from sologm.integrations.anthropic import AnthropicClient  # Ensure import
from sologm.utils.config import get_config

logger = logging.getLogger(__name__)


def create_all_managers(
    session: Session,
    anthropic_client: Optional[AnthropicClient] = None,  # Add parameter
) -> SimpleNamespace:
    """Create instances of all core managers, sharing a session and optionally a client.

    Args:
        session: The SQLAlchemy session to be used by all managers.
        anthropic_client: Optional pre-configured Anthropic client instance.
            If None, managers requiring it will create their own default instance
            using the configured API key.

    Returns:
        A SimpleNamespace containing instances of all managers.
    """
    logger.debug(
        f"Creating all managers with session ID: {id(session)} and "
        f"AnthropicClient: {'Provided' if anthropic_client else 'Default'}"
    )

    # Determine the client to use - prioritize passed-in client
    client_to_use = anthropic_client
    if client_to_use is None:
        # Fallback: Create a default client if none was provided
        logger.debug("No AnthropicClient provided to factory, creating default.")
        config = get_config()  # Keep config import if using this fallback
        client_to_use = AnthropicClient(api_key=config.get("anthropic_api_key"))
    else:
        logger.debug("Using provided AnthropicClient in factory.")

    # Instantiate managers, passing the session and client
    game_manager = GameManager(session=session)
    act_manager = ActManager(
        session=session,
        game_manager=game_manager,
        anthropic_client=client_to_use,  # Pass the determined client
    )
    scene_manager = SceneManager(session=session, act_manager=act_manager)
    event_manager = EventManager(session=session, scene_manager=scene_manager)
    dice_manager = DiceManager(
        session=session, scene_manager=scene_manager
    )  # Assuming DiceManager exists

    oracle_manager = OracleManager(
        session=session,
        scene_manager=scene_manager,
        event_manager=event_manager,  # Pass event_manager if needed
        anthropic_client=client_to_use,  # Pass the determined client
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
