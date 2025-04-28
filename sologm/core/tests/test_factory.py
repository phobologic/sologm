"""Tests for the core factory functions."""

import logging
from types import SimpleNamespace

from sologm.core.act import ActManager
from sologm.core.dice import DiceManager
from sologm.core.event import EventManager
from sologm.core.factory import create_all_managers
from sologm.core.game import GameManager
from sologm.core.oracle import OracleManager
from sologm.core.scene import SceneManager

logger = logging.getLogger(__name__)


def test_create_all_managers(session_context):
    """Verify that create_all_managers correctly instantiates and wires managers."""
    logger.debug("Starting test_create_all_managers")

    with session_context as session:
        logger.debug(f"Using session ID: {id(session)}")
        managers = create_all_managers(session)

        # 1. Check return type
        assert isinstance(managers, SimpleNamespace), (
            "Factory should return a SimpleNamespace"
        )
        logger.debug("Return type is SimpleNamespace")

        # 2. Check existence and type of each manager
        expected_managers = {
            "game": GameManager,
            "act": ActManager,
            "scene": SceneManager,
            "event": EventManager,
            "dice": DiceManager,
            "oracle": OracleManager,
        }
        for name, manager_class in expected_managers.items():
            assert hasattr(managers, name), (
                f"Managers object should have attribute '{name}'"
            )
            assert isinstance(getattr(managers, name), manager_class), (
                f"managers.{name} should be an instance of {manager_class.__name__}"
            )
            logger.debug(f"managers.{name} is instance of {manager_class.__name__}")

        # 3. Check session propagation
        for name in expected_managers:
            manager_instance = getattr(managers, name)
            assert hasattr(manager_instance, "_session"), (
                f"{name} manager should have a _session attribute"
            )
            assert manager_instance._session is session, (
                f"{name} manager session ID {id(manager_instance._session)} should match factory session ID {id(session)}"
            )
            logger.debug(f"managers.{name} has correct session ID: {id(session)}")

        # 4. Check dependency injection wiring
        assert managers.act.game_manager is managers.game, (
            "ActManager should have GameManager injected"
        )
        assert managers.scene.act_manager is managers.act, (
            "SceneManager should have ActManager injected"
        )
        assert managers.event.scene_manager is managers.scene, (
            "EventManager should have SceneManager injected"
        )
        assert managers.dice.scene_manager is managers.scene, (
            "DiceManager should have SceneManager injected"
        )
        assert managers.oracle.scene_manager is managers.scene, (
            "OracleManager should have SceneManager injected"
        )
        # Check transitive dependencies are accessible
        assert managers.event.act_manager is managers.act, (
            "EventManager should access ActManager via SceneManager"
        )
        assert managers.event.game_manager is managers.game, (
            "EventManager should access GameManager via SceneManager/ActManager"
        )
        logger.debug("Manager dependencies correctly wired")

        logger.debug("Finished test_create_all_managers successfully")
