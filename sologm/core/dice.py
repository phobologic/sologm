"""Dice rolling functionality."""

import random
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.core.scene import SceneManager
from sologm.core.act import ActManager
from sologm.core.game import GameManager
from sologm.models.dice import DiceRoll
from sologm.models.scene import Scene
from sologm.utils.errors import DiceError


class DiceManager(BaseManager[DiceRoll, DiceRoll]):
    """Manages dice rolling operations."""

    def __init__(
        self,
        scene_manager: Optional[SceneManager] = None,
        session: Optional[Session] = None,
    ):
        """Initialize with optional scene manager and session.
        
        Args:
            scene_manager: Optional scene manager (primarily for testing)
            session: Optional database session (primarily for testing)
        """
        super().__init__(session)
        self._scene_manager = scene_manager

    @property
    def scene_manager(self) -> SceneManager:
        """Lazy-initialize scene manager."""
        return self._lazy_init_manager(
            "_scene_manager", 
            "sologm.core.scene.SceneManager"
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
        scene_id: Optional[str] = None,
    ) -> DiceRoll:
        """Roll dice according to the specified notation and save to database.
        
        Args:
            notation: Dice notation string (e.g., "2d6+3")
            reason: Optional reason for the roll
            scene_id: Optional ID of the scene this roll belongs to
            
        Returns:
            DiceRoll model with results
            
        Raises:
            DiceError: If notation is invalid
        """
        try:
            # Parse notation and roll dice
            count, sides, modifier = self._parse_notation(notation)
            
            self.logger.debug(
                f"Rolling {count} dice with {sides} sides and modifier {modifier:+d}"
            )
            individual_results = [random.randint(1, sides) for _ in range(count)]
            self.logger.debug(f"Individual dice results: {individual_results}")
            
            total = sum(individual_results) + modifier
            self.logger.debug(
                f"Final result: {individual_results} + {modifier} = {total}"
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
                    scene_id=scene_id,
                )
                
                # Add to session and flush to get ID
                session.add(dice_roll_model)
                session.flush()
                
                return dice_roll_model
            
            # Execute the operation
            return self._execute_db_operation("roll dice", create_roll_operation)
            
        except DiceError:
            # Re-raise DiceError without wrapping
            raise
        except Exception as e:
            self._handle_operation_error(
                "roll dice", e, DiceError
            )

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
        try:
            # Get active scene
            _, active_scene = self.scene_manager.validate_active_context()
            
            # Roll dice for this scene
            return self.roll(notation, reason, active_scene.id)
        except Exception as e:
            if not isinstance(e, DiceError):
                self._handle_operation_error(
                    "roll for active scene", e, DiceError
                )
            raise

    def get_recent_rolls(
        self, scene_id: Optional[str] = None, limit: int = 5
    ) -> List[DiceRoll]:
        """Get recent dice rolls, optionally filtered by scene.
        
        Args:
            scene_id: Optional scene ID to filter by
            limit: Maximum number of rolls to return
            
        Returns:
            List of DiceRoll models
            
        Raises:
            DiceError: If operation fails
        """
        try:
            filters = {}
            if scene_id:
                filters["scene_id"] = scene_id
                
            return self.list_entities(
                DiceRoll,
                filters=filters,
                order_by="created_at",
                order_direction="desc",
                limit=limit
            )
        except Exception as e:
            self._handle_operation_error(
                "get recent dice rolls", e, DiceError
            )

    def get_rolls_for_scene(
        self, scene_id: str, limit: Optional[int] = None
    ) -> List[DiceRoll]:
        """Get dice rolls for a specific scene.
        
        Args:
            scene_id: ID of the scene
            limit: Optional maximum number of rolls to return
            
        Returns:
            List of DiceRoll models
            
        Raises:
            DiceError: If operation fails
        """
        try:
            return self.list_entities(
                DiceRoll,
                filters={"scene_id": scene_id},
                order_by="created_at",
                order_direction="desc",
                limit=limit
            )
        except Exception as e:
            self._handle_operation_error(
                f"get rolls for scene {scene_id}", e, DiceError
            )

    def get_rolls_for_active_scene(
        self, limit: Optional[int] = None
    ) -> List[DiceRoll]:
        """Get dice rolls for the currently active scene.
        
        Args:
            limit: Optional maximum number of rolls to return
            
        Returns:
            List of DiceRoll models
            
        Raises:
            DiceError: If no active scene or operation fails
        """
        try:
            # Get active scene
            _, active_scene = self.scene_manager.validate_active_context()
            
            # Get rolls for this scene
            return self.get_rolls_for_scene(active_scene.id, limit)
        except Exception as e:
            if not isinstance(e, DiceError):
                self._handle_operation_error(
                    "get rolls for active scene", e, DiceError
                )
            raise

    def _parse_notation(self, notation: str) -> tuple[int, int, int]:
        """Parse XdY+Z notation into components.
        
        Args:
            notation: Dice notation string (e.g., "2d6+3")
            
        Returns:
            Tuple of (number of dice, sides per die, modifier)
            
        Raises:
            DiceError: If notation is invalid
        """
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
