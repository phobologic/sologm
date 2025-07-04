import abc
from typing import TYPE_CHECKING, Dict, List, Optional

from rich.console import Console

# Import necessary models and potentially manager types for type hinting
# Use TYPE_CHECKING to avoid circular imports if managers are needed
# Assuming models are in sologm.models.<model_name>
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene

if TYPE_CHECKING:
    # Assuming managers are in sologm.core.<manager_name>
    from sologm.core.oracle import OracleManager
    from sologm.core.scene import SceneManager


class Renderer(abc.ABC):
    """
    Abstract base class for different output renderers (e.g., Rich, Markdown).

    Defines the interface for all display operations within the CLI.
    """

    def __init__(self, console: Console, markdown_mode: bool = False):
        """
        Initializes the renderer.

        Args:
            console: The Rich Console instance for output.
            markdown_mode: Flag indicating if the renderer is for Markdown output.
        """
        self.console = console
        self.markdown_mode = markdown_mode

    @abc.abstractmethod
    def display_dice_roll(self, roll: DiceRoll) -> None:
        """Displays the results of a dice roll."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_interpretation(
        self,
        interp: Interpretation,
        selected: bool = False,
        sequence: Optional[int] = None,
    ) -> None:
        """Displays a single oracle interpretation."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_events_table(
        self,
        events: List[Event],
        scene: Scene,  # Scene context might be useful for titles etc.
        truncate_descriptions: bool = True,
        max_description_length: int = 80,
    ) -> None:
        """Displays a list of events, typically in a table."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_games_table(
        self, games: List[Game], active_game: Optional[Game] = None
    ) -> None:
        """Displays a list of games, highlighting the active one."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_scenes_table(
        self, scenes: List[Scene], active_scene_id: Optional[str] = None
    ) -> None:
        """Displays a list of scenes, highlighting the active one."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_game_info(
        self, game: Game, active_scene: Optional[Scene] = None
    ) -> None:
        """Displays detailed information about a specific game."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_interpretation_set(
        self, interp_set: InterpretationSet, show_context: bool = True
    ) -> None:
        """Displays a set of oracle interpretations."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_scene_info(self, scene: Scene) -> None:
        """Displays detailed information about a specific scene."""
        raise NotImplementedError

    @abc.abstractmethod
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
        """Displays the overall status of the current game."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_acts_table(
        self, acts: List[Act], active_act_id: Optional[str] = None
    ) -> None:
        """Displays a list of acts, highlighting the active one."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_act_info(self, act: Act, game_name: str) -> None:
        """Displays detailed information about a specific act."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_interpretation_sets_table(
        self, interp_sets: List[InterpretationSet]
    ) -> None:
        """Displays a table of interpretation sets."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_interpretation_status(self, interp_set: InterpretationSet) -> None:
        """Displays the status of an interpretation set."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_act_ai_generation_results(
        self, results: Dict[str, str], act: Act
    ) -> None:
        """Displays the results generated by AI for an act."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_act_completion_success(self, completed_act: Act) -> None:
        """Displays a success message upon act completion."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_act_ai_feedback_prompt(self, console: Console) -> Optional[str]:
        """
        Displays the prompt asking for feedback on AI generation for act completion.

        Args:
            console: The Rich Console instance for interaction.

        Returns:
            The user's choice ("A", "E", "R", "C") or None if cancelled.
        """
        # Note: Implementation might differ based on Rich vs Markdown
        raise NotImplementedError

    @abc.abstractmethod
    def display_act_edited_content_preview(
        self, edited_results: Dict[str, str]
    ) -> None:
        """Displays a preview of edited AI-generated content."""
        raise NotImplementedError

    # --- New Methods for Step 1 ---

    @abc.abstractmethod
    def display_markdown(self, markdown_content: str) -> None:
        """
        Displays content formatted as Markdown.

        Args:
            markdown_content: A string containing Markdown text.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def display_narrative_feedback_prompt(self, console: Console) -> Optional[str]:
        """
        Displays the prompt asking for feedback on AI-generated narrative.

        Expected choices:
        - A: Accept the narrative.
        - E: Edit the narrative manually.
        - R: Regenerate the narrative with feedback.
        - C: Cancel and discard the narrative.

        Args:
            console: The Rich Console instance for interaction
                (primarily for RichRenderer).

        Returns:
            The user's choice ("A", "E", "R", "C") in uppercase, or None if the
            user cancels the operation (e.g., via Ctrl+C).
        """
        raise NotImplementedError

    # --- End New Methods ---

    @abc.abstractmethod
    def display_error(self, message: str) -> None:
        """Displays an error message to the user."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_success(self, message: str) -> None:
        """Displays a success message."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_warning(self, message: str) -> None:
        """Displays a warning message."""
        raise NotImplementedError

    @abc.abstractmethod
    def display_message(self, message: str, style: Optional[str] = None) -> None:
        """Displays a simple informational message, optionally styled."""
        raise NotImplementedError
