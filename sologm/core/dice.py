"""Dice rolling functionality."""

import logging
import random
import re
from dataclasses import dataclass
from typing import List

from sologm.utils.errors import DiceError


@dataclass
class DiceRoll:
    """Represents a dice roll result."""

    notation: str
    individual_results: List[int]
    modifier: int
    total: int
    reason: str | None = None


class DiceManager:
    """Manages dice rolling operations."""

    def __init__(self):
        """Initialize DiceManager."""
        self.logger = logging.getLogger(__name__)

    def roll(self, notation: str, reason: str | None = None) -> DiceRoll:
        """Roll dice according to the specified notation.

        Args:
            notation: Dice notation string (e.g., "2d6+3")
            reason: Optional reason for the roll

        Returns:
            DiceRoll object with results

        Raises:
            DiceError: If notation is invalid
        """
        count, sides, modifier = self._parse_notation(notation)

        self.logger.debug(
            f"Rolling {count} dice with {sides} sides "
            f"and modifier {modifier:+d}"
        )
        individual_results = [random.randint(1, sides) for _ in range(count)]
        self.logger.debug(f"Individual dice results: {individual_results}")

        total = sum(individual_results) + modifier
        self.logger.debug(f"Final result: {individual_results} + {modifier} = {total}")

        return DiceRoll(
            notation=notation,
            individual_results=individual_results,
            modifier=modifier,
            total=total,
            reason=reason,
        )

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
