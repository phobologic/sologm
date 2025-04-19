"""
Renderer implementation for generating Markdown output.
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from rich.console import Console

# Import base class
from .base import Renderer

# Import necessary models for type hinting
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene

# Import utilities if needed (e.g., truncate_text)
# from sologm.cli.utils.display import truncate_text

if TYPE_CHECKING:
    # Assuming managers are in sologm.core.<manager_name>
    from sologm.core.oracle import OracleManager
    from sologm.core.scene import SceneManager

logger = logging.getLogger(__name__)


class MarkdownRenderer(Renderer):
    """
    Renders CLI output using standard Markdown formatting.
    """

    def __init__(self, console: Console, markdown_mode: bool = True):
        """
        Initializes the MarkdownRenderer.

        Args:
            console: The Rich Console instance for output.
            markdown_mode: Flag indicating Markdown mode (always True here).
        """
        super().__init__(console, markdown_mode=True)
        # No specific MarkdownRenderer initialization needed yet
        logger.debug("MarkdownRenderer initialized")

    # --- Abstract Method Implementations (to be added incrementally via TDD) ---

    def display_dice_roll(self, roll: DiceRoll) -> None:
        """Displays the results of a dice roll as Markdown."""
        logger.debug(f"Displaying dice roll as Markdown: {roll.notation}")

        # Build the Markdown string
        title = f"### Dice Roll: {roll.notation}"
        if roll.reason:
            title += f" (Reason: {roll.reason})"

        details = [f"*   **Result:** `{roll.total}`"]
        if len(roll.individual_results) > 1:
            details.append(f"*   Rolls: `{roll.individual_results}`")
        if roll.modifier != 0:
            details.append(f"*   Modifier: `{roll.modifier:+d}`")

        output = f"{title}\n\n" + "\n".join(details)

        self.console.print(output)

    def display_interpretation(
        self,
        interp: Interpretation,
        selected: bool = False,
        sequence: Optional[int] = None,
    ) -> None:
        """Displays a single oracle interpretation as Markdown."""
        logger.debug(
            f"Displaying interpretation as Markdown: {interp.id} (selected: {selected}, sequence: {sequence})"
        )

        # Build the title
        title_parts = []
        if sequence is not None:
            title_parts.append(f"Interpretation #{sequence}:")
        title_parts.append(interp.title)
        if selected:
            title_parts.append("(**Selected**)")

        title = f"#### {' '.join(title_parts)}"

        # Build the body
        body = interp.description

        # Build the footer (metadata)
        footer = f"*ID: {interp.id} / {interp.slug}*"

        # Combine parts
        output = f"{title}\n\n{body}\n\n{footer}"

        self.console.print(output)

    def display_events_table(
        self,
        events: List[Event],
        scene: Scene,
        truncate_descriptions: bool = True,
        max_description_length: int = 80,
    ) -> None:
        """Displays a list of events as Markdown."""
        raise NotImplementedError

    def display_games_table(
        self, games: List[Game], active_game: Optional[Game] = None
    ) -> None:
        """Displays a list of games as Markdown."""
        raise NotImplementedError

    def display_scenes_table(
        self, scenes: List[Scene], active_scene_id: Optional[str] = None
    ) -> None:
        """Displays a list of scenes as Markdown."""
        raise NotImplementedError

    def display_game_info(
        self, game: Game, active_scene: Optional[Scene] = None
    ) -> None:
        """Displays detailed information about a specific game as Markdown."""
        raise NotImplementedError

    def display_interpretation_set(
        self, interp_set: InterpretationSet, show_context: bool = True
    ) -> None:
        """Displays a set of oracle interpretations as Markdown."""
        raise NotImplementedError

    def display_scene_info(self, scene: Scene) -> None:
        """Displays detailed information about a specific scene as Markdown."""
        raise NotImplementedError

    def display_game_status(
        self,
        game: Game,
        latest_act: Optional[Act],
        latest_scene: Optional[Scene],
        recent_events: List[Event],
        scene_manager: Optional["SceneManager"] = None,
        oracle_manager: Optional["OracleManager"] = None,
        recent_rolls: Optional[List[DiceRoll]] = None,
        is_act_active: bool = False,
        is_scene_active: bool = False,
    ) -> None:
        """Displays the overall status of the current game as Markdown."""
        raise NotImplementedError

    def display_acts_table(
        self, acts: List[Act], active_act_id: Optional[str] = None
    ) -> None:
        """Displays a list of acts as Markdown."""
        raise NotImplementedError

    def display_act_info(self, act: Act, game_name: str) -> None:
        """Displays detailed information about a specific act as Markdown."""
        raise NotImplementedError

    def display_interpretation_sets_table(
        self, interp_sets: List[InterpretationSet]
    ) -> None:
        """Displays a table of interpretation sets as Markdown."""
        raise NotImplementedError

    def display_interpretation_status(self, interp_set: InterpretationSet) -> None:
        """Displays the status of an interpretation set as Markdown."""
        raise NotImplementedError

    def display_act_ai_generation_results(
        self, results: Dict[str, str], act: Act
    ) -> None:
        """Displays the results generated by AI for an act as Markdown."""
        raise NotImplementedError

    def display_act_completion_success(self, completed_act: Act) -> None:
        """Displays a success message upon act completion as Markdown."""
        raise NotImplementedError

    def display_act_ai_feedback_prompt(self, console: Console) -> None:
        """Displays the prompt asking for feedback on AI generation as Markdown."""
        # Note: Markdown renderer might just print instructions instead of interactive prompt
        raise NotImplementedError

    def display_act_edited_content_preview(
        self, edited_results: Dict[str, str]
    ) -> None:
        """Displays a preview of edited AI-generated content as Markdown."""
        raise NotImplementedError

    def display_error(self, message: str) -> None:
        """Displays an error message to the user as Markdown."""
        raise NotImplementedError
