"""Dice rolling functionality."""

import random
import re
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.dice import DiceRoll as DiceRollModel
from sologm.utils.errors import DiceError


@dataclass
class DiceRoll:
    """Represents a dice roll result."""
    id: str
    notation: str
    individual_results: List[int]
    modifier: int
    total: int
    reason: Optional[str] = None
    scene_id: Optional[str] = None
    created_at: Optional[str] = None


class DiceManager(BaseManager[DiceRoll, DiceRollModel]):
    """Manages dice rolling operations."""

    def roll(self, notation: str, reason: Optional[str] = None,
             scene_id: Optional[str] = None) -> DiceRoll:
        """Roll dice according to the specified notation and save to database.

        Args:
            notation: Dice notation string (e.g., "2d6+3")
            reason: Optional reason for the roll
            scene_id: Optional ID of the scene this roll belongs to

        Returns:
            DiceRoll object with results

        Raises:
            DiceError: If notation is invalid
        """
        try:
            # Parse notation and roll dice
            count, sides, modifier = self._parse_notation(notation)

            self.logger.debug(
                f"Rolling {count} dice with {sides} sides "
                f"and modifier {modifier:+d}"
            )
            individual_results = [random.randint(1, sides) for _ in range(count)]
            self.logger.debug(f"Individual dice results: {individual_results}")

            total = sum(individual_results) + modifier
            self.logger.debug(f"Final result: {individual_results} + "
                              f"{modifier} = {total}")

            # Define the database operation
            def create_roll_operation(session: Session) -> DiceRoll:
                # Create the model instance
                dice_roll_model = DiceRollModel.create(
                    notation=notation,
                    individual_results=individual_results,
                    modifier=modifier,
                    total=total,
                    reason=reason,
                    scene_id=scene_id
                )

                # Add to session and flush to get ID
                session.add(dice_roll_model)
                session.flush()

                # Convert to domain model
                return self._convert_to_domain(dice_roll_model)

            # Execute the operation
            return self._execute_db_operation("roll dice", create_roll_operation)

        except DiceError:
            raise
        except Exception as e:
            raise DiceError(f"Unexpected error during dice roll: {str(e)}") from e

    def get_recent_rolls(
        self, scene_id: Optional[str] = None, limit: int = 5
    ) -> List[DiceRoll]:
        """Get recent dice rolls, optionally filtered by scene.

        Args:
            scene_id: Optional scene ID to filter by
            limit: Maximum number of rolls to return

        Returns:
            List of DiceRoll objects
        """
        def get_rolls_operation(session: Session) -> List[DiceRoll]:
            # Build query
            query = session.query(DiceRollModel)
            if scene_id:
                query = query.filter(DiceRollModel.scene_id == scene_id)

            # Order by creation time and limit results
            dice_roll_models = query.order_by(
                DiceRollModel.created_at.desc()
            ).limit(limit).all()

            # Convert to domain models
            return [self._convert_to_domain(model) for model in dice_roll_models]

        try:
            return self._execute_db_operation("get recent dice rolls", get_rolls_operation)
        except Exception as e:
            raise DiceError(f"Failed to get recent dice rolls: {str(e)}") from e

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

    def _convert_to_domain(self, db_model: DiceRollModel) -> DiceRoll:
        """Convert database model to domain model."""
        return DiceRoll(
            id=db_model.id,
            notation=db_model.notation,
            individual_results=db_model.individual_results,
            modifier=db_model.modifier,
            total=db_model.total,
            reason=db_model.reason,
            scene_id=db_model.scene_id,
            created_at=db_model.created_at.isoformat() if db_model.created_at else None
        )

    def _convert_to_db_model(self, domain_model: DiceRoll, db_model: Optional[DiceRollModel] = None) -> DiceRollModel:
        """Convert domain model to database model."""
        if db_model is None:
            return DiceRollModel(
                id=domain_model.id,
                notation=domain_model.notation,
                individual_results=domain_model.individual_results,
                modifier=domain_model.modifier,
                total=domain_model.total,
                reason=domain_model.reason,
                scene_id=domain_model.scene_id
            )
        else:
            db_model.notation = domain_model.notation
            db_model.individual_results = domain_model.individual_results
            db_model.modifier = domain_model.modifier
            db_model.total = domain_model.total
            db_model.reason = domain_model.reason
            db_model.scene_id = domain_model.scene_id
            return db_model
