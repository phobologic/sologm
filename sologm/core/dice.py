"""Dice rolling functionality."""

import random
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from sologm.core.act import ActManager
from sologm.core.base_manager import BaseManager
from sologm.core.game import GameManager
from sologm.core.scene import SceneManager
from sologm.models.dice import DiceRoll
from sologm.models.scene import Scene
from sologm.utils.errors import DiceError


class DiceManager(BaseManager[DiceRoll, DiceRoll]):
    """Manages dice rolling operations."""

    def __init__(
        self,
        session: Optional[Session] = None,
        scene_manager: Optional[SceneManager] = None,
    ):
        """Initialize with optional session and scene manager.

        Args:
            session: Optional database session (for testing or CLI command)
            scene_manager: Optional scene manager (primarily for testing)
        """
        super().__init__(session=session)
        self._scene_manager = scene_manager
        self.logger.debug("DiceManager initialized")

    @property
    def scene_manager(self) -> SceneManager:
        """Lazy-initialize scene manager with the same session."""
        return self._lazy_init_manager(
            "_scene_manager", "sologm.core.scene.SceneManager"
        )

    @property
    def act_manager(self) -> ActManager:
        """Access act manager through scene manager."""
        return self.scene_manager.act_manager

    @property
    def game_manager(self) -> GameManager:
        """Access game manager through act manager."""
        return self.act_manager.game_manager

    def roll(
        self,
        notation: str,
        reason: Optional[str] = None,
        scene: Optional[Scene] = None,
    ) -> DiceRoll:
        """Roll dice according to the specified notation and save to database.

        Args:
            notation: Dice notation string (e.g., "2d6+3")
            reason: Optional reason for the roll
            scene: Optional scene this roll belongs to

        Returns:
            DiceRoll model with results

        Raises:
            DiceError: If notation is invalid
        """
        self.logger.debug(
            f"Rolling dice with notation: {notation}, reason: {reason}, scene: {scene}"
        )

        try:
            # Parse notation and roll dice
            count, sides, modifier = self._parse_notation(notation)
            self.logger.debug(f"Parsed notation: {count}d{sides}{modifier:+d}")

            individual_results = [random.randint(1, sides) for _ in range(count)]
            self.logger.debug(f"Individual dice results: {individual_results}")

            total = sum(individual_results) + modifier
            self.logger.debug(
                f"Final result: {sum(individual_results)} + {modifier} = {total}"
            )

            # Define the database operation
            def create_roll_operation(session: Session) -> DiceRoll:
                # Create the model instance
                dice_roll_model = DiceRoll.create(
                    notation=notation,
                    individual_results=individual_results,
                    modifier=modifier,
                    total=total,
                    reason=reason,
                    scene_id=scene.id if scene else None,
                )

                session.add(dice_roll_model)
                session.flush()

                return dice_roll_model

            # Execute the operation
            result = self._execute_db_operation("roll dice", create_roll_operation)
            self.logger.debug(f"Created dice roll with ID: {result.id}")
            return result

        except DiceError:
            self.logger.error(f"Dice notation error: {notation}")
            raise
        except Exception:
            raise

    def roll_for_active_scene(
        self, notation: str, reason: Optional[str] = None
    ) -> DiceRoll:
        """Roll dice for the currently active scene.

        Args:
            notation: Dice notation string (e.g., "2d6+3")
            reason: Optional reason for the roll

        Returns:
            DiceRoll model with results

        Raises:
            DiceError: If notation is invalid or no active scene
        """
        self.logger.debug(
            f"Rolling dice for active scene with notation: {notation}, reason: {reason}"
        )
        # Get active scene
        _, active_scene = self.scene_manager.validate_active_context()
        self.logger.debug(
            f"Found active scene: {active_scene.id} - {active_scene.title}"
        )

        # Roll dice for this scene
        result = self.roll(notation, reason, active_scene)
        self.logger.debug(f"Created dice roll with ID: {result.id} for active scene")
        return result

    def get_recent_rolls(
        self, scene: Optional[Scene] = None, limit: int = 5
    ) -> List[DiceRoll]:
        """Get recent dice rolls, optionally filtered by scene.

        Args:
            scene: Optional scene to filter by
            limit: Maximum number of rolls to return

        Returns:
            List of DiceRoll models

        Raises:
            DiceError: If operation fails
        """
        scene_desc = f"{scene.id} - {scene.title}" if scene else "any scene"
        self.logger.debug(f"Getting recent dice rolls for {scene_desc}, limit: {limit}")
        filters = {}
        if scene:
            filters["scene_id"] = scene.id

        result = self.list_entities(
            DiceRoll,
            filters=filters,
            order_by="created_at",
            order_direction="desc",
            limit=limit,
        )
        self.logger.debug(f"Found {len(result)} recent dice rolls")
        return result

    def get_rolls_for_scene(
        self, scene: Scene, limit: Optional[int] = None
    ) -> List[DiceRoll]:
        """Get dice rolls for a specific scene.

        Args:
            scene: The scene to get rolls for
            limit: Optional maximum number of rolls to return

        Returns:
            List of DiceRoll models

        Raises:
            DiceError: If operation fails
        """
        self.logger.debug(
            f"Getting dice rolls for scene: {scene.id} - {scene.title}, limit: {limit}"
        )

        result = self.list_entities(
            DiceRoll,
            filters={"scene_id": scene.id},
            order_by="created_at",
            order_direction="desc",
            limit=limit,
        )
        self.logger.debug(f"Found {len(result)} dice rolls for scene {scene.id}")
        return result

    def get_rolls_for_active_scene(self, limit: Optional[int] = None) -> List[DiceRoll]:
        """Get dice rolls for the currently active scene.

        Args:
            limit: Optional maximum number of rolls to return

        Returns:
            List of DiceRoll models

        Raises:
            DiceError: If no active scene or operation fails
        """
        self.logger.debug(f"Getting dice rolls for active scene, limit: {limit}")
        # Get active scene
        _, active_scene = self.scene_manager.validate_active_context()
        self.logger.debug(
            f"Found active scene: {active_scene.id} - {active_scene.title}"
        )

        # Get rolls for this scene
        result = self.get_rolls_for_scene(active_scene, limit)
        self.logger.debug(f"Found {len(result)} dice rolls for active scene")
        return result

    def _parse_notation(self, notation: str) -> tuple[int, int, int]:
        """Parse XdY+Z notation into components.

        Args:
            notation: Dice notation string (e.g., "2d6+3")

        Returns:
            Tuple of (number of dice, sides per die, modifier)

        Raises:
            DiceError: If notation is invalid
        """
        self.logger.debug(f"Parsing dice notation: {notation}")

        pattern = r"^(\d+)d(\d+)([+-]\d+)?$"
        match = re.match(pattern, notation)

        if not match:
            self.logger.error(f"Invalid dice notation: {notation}")
            raise DiceError(f"Invalid dice notation: {notation}")

        count = int(match.group(1))
        sides = int(match.group(2))
        modifier = int(match.group(3) or 0)

        self.logger.debug(
            f"Parsing dice notation - count: {count}, "
            f"sides: {sides}, modifier: {modifier}"
        )

        if count < 1:
            self.logger.error(f"Invalid dice count: {count}")
            raise DiceError("Must roll at least 1 die")
        if sides < 2:
            self.logger.error(f"Invalid sides count: {sides}")
            raise DiceError("Die must have at least 2 sides")

        self.logger.debug(f"Parsed {notation} as {count}d{sides}{modifier:+d}")
        return count, sides, modifier
