"""
Concrete implementation of the Renderer interface using Rich library components.
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sologm.cli.utils.display import (
    truncate_text,
)  # Assuming this stays in display.py for now

# Import utilities that RichRenderer will use directly
from sologm.cli.utils.styled_text import BORDER_STYLES, StyledText

# Import necessary models
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene, SceneStatus  # Added SceneStatus

# Corrected import based on file structure from Phase 1
from .base import Renderer

# Use TYPE_CHECKING for manager imports to avoid circular dependencies if needed later
if TYPE_CHECKING:
    from sologm.core.oracle import OracleManager
    from sologm.core.scene import SceneManager


logger = logging.getLogger(__name__)


class RichRenderer(Renderer):
    """
    Renders CLI output using Rich library components like Panels, Tables, and styled text.
    """

    def __init__(self, console: Console):
        """
        Initializes the RichRenderer.

        Args:
            console: The Rich Console instance for output.
        """
        # Pass the console and explicitly set markdown_mode to False
        super().__init__(console, markdown_mode=False)
        logger.debug("RichRenderer initialized")

    # --- Method implementations will be moved here from display.py in Step 3 ---

    def display_dice_roll(self, roll: DiceRoll) -> None:
        """Displays the results of a dice roll using Rich."""
        logger.debug(f"Displaying dice roll: {roll.notation} (total: {roll.total})")
        logger.debug(
            f"Individual results: {roll.individual_results}, modifier: {roll.modifier}"
        )

        st = StyledText  # Assuming StyledText is imported

        # Create title with consistent styling
        title_parts = []
        if roll.reason:
            title_parts.extend(
                [st.title(f"{roll.reason}:"), " ", st.title(roll.notation)]
            )
        else:
            title_parts.append(st.title(roll.notation))

        panel_title = st.combine(*title_parts)

        # Build details with consistent styling
        details = []

        if len(roll.individual_results) > 1:
            details.append(
                st.combine(
                    st.subtitle("Rolls:"),
                    " ",
                    st.timestamp(str(roll.individual_results)),
                )
            )

        if roll.modifier != 0:
            details.append(
                st.combine(
                    st.subtitle("Modifier:"), " ", st.warning(f"{roll.modifier:+d}")
                )
            )

        details.append(
            st.combine(st.subtitle("Result:"), " ", st.title_success(str(roll.total)))
        )

        # Add timestamp metadata if available
        metadata = {}
        if roll.created_at:
            metadata["Time"] = roll.created_at.isoformat()

        # Create panel content
        panel_content = Text()  # Assuming Text is imported

        # Add all details
        for i, detail in enumerate(details):
            if i > 0:
                panel_content.append("\n")
            panel_content.append(detail)

        # Add metadata if available
        if metadata:
            panel_content.append("\n")
            panel_content.append(st.format_metadata(metadata))

        # Use consistent border style for dice rolls (neutral information)
        panel = Panel(  # Assuming Panel is imported
            panel_content,
            title=panel_title,
            border_style=BORDER_STYLES["neutral"],  # Assuming BORDER_STYLES is imported
            expand=True,
            title_align="left",
        )
        # Use self.console instead of the console parameter
        self.console.print(panel)

    def display_interpretation(
        self,
        interp: Interpretation,
        selected: bool = False,
        sequence: Optional[int] = None,
    ) -> None:
        """Displays a single oracle interpretation using Rich."""
        logger.debug(
            f"Displaying interpretation {interp.id} (selected: {interp.is_selected or selected})"
        )
        logger.debug(
            f"Interpretation title: '{interp.title}', created: {interp.created_at}"
        )

        st = StyledText

        # Create panel title with sequence number, title, selection indicator, and ID
        sequence_text = f"(#{sequence}) " if sequence is not None else ""

        # Build the title components
        title_parts = [st.title(f"{sequence_text}{interp.title}")]

        # Add selection indicator if selected
        if interp.is_selected or selected:
            title_parts.extend([" ", st.success("(Selected)")])

        # Add ID and slug
        title_parts.extend([" ", st.timestamp(f"({interp.slug} / {interp.id})")])

        # Combine into a single Text object
        panel_title = st.combine(*title_parts)

        # Determine border style based on selection status
        border_style = (
            BORDER_STYLES["success"]
            if (interp.is_selected or selected)
            else BORDER_STYLES["game_info"]
        )

        # Panel content is just the description
        panel = Panel(
            interp.description,
            title=panel_title,
            border_style=border_style,
            title_align="left",
        )
        # Use self.console instead of the console parameter
        self.console.print(panel)
        self.console.print()  # Print the trailing newline

    def display_events_table(
        self,
        events: List[Event],
        scene: Scene,
        truncate_descriptions: bool = True,
        max_description_length: int = 80,
    ) -> None:
        """Display events in a formatted table using Rich.

        Args:
            events: List of events to display
            scene: The Scene to display events from.
            truncate_descriptions: Whether to truncate long descriptions
            max_description_length: Maximum length for descriptions if truncating
        """
        logger.debug(
            f"Displaying events table for scene '{scene.title}' with {len(events)} events"
        )
        if not events:
            logger.debug(f"No events to display for scene '{scene.title}'")
            # Use self.console
            self.console.print(f"\nNo events in scene '{scene.title}'")
            return

        logger.debug(f"Creating table with {len(events)} events")

        st = StyledText

        # Create table without a title
        table = Table(
            border_style=BORDER_STYLES["game_info"],
        )

        # Add columns with consistent styling
        table.add_column("ID", style=st.STYLES["timestamp"])
        table.add_column("Time", style=st.STYLES["timestamp"])
        table.add_column("Source", style=st.STYLES["category"])
        table.add_column("Description")

        # Add rows with consistent formatting
        for event in events:
            # Get the source name instead of the source object
            source_name = (
                event.source.name
                if hasattr(event.source, "name")
                else str(event.source)
            )

            # Truncate description if needed
            description = event.description
            if truncate_descriptions:
                description = truncate_text(
                    description, max_length=max_description_length
                )

            table.add_row(
                event.id,
                event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                source_name,
                description,
            )

        # Create panel title
        panel_title = st.title(
            f"Events in game '{scene.act.game.name}', scene '{scene.title}'"
        )

        # Wrap the table in a panel with a title
        panel = Panel(
            table,
            title=panel_title,
            title_align="left",
            border_style=BORDER_STYLES["game_info"],
        )
        # Use self.console
        self.console.print(panel)

    def display_games_table(
        self, games: List[Game], active_game: Optional[Game] = None
    ) -> None:
        """Displays a list of games in a Rich table."""
        logger.debug(f"Displaying games table with {len(games)} games")
        logger.debug(f"Active game: {active_game.id if active_game else 'None'}")
        if not games:
            logger.debug("No games found to display")
            # Use self.console
            self.console.print("No games found. Create one with 'sologm game create'.")
            return

        st = StyledText

        # Create table without a title
        table = Table(
            border_style=BORDER_STYLES["game_info"],
        )

        # Add columns with consistent styling
        table.add_column("ID", style=st.STYLES["timestamp"])
        table.add_column("Name", style=st.STYLES["category"])
        table.add_column("Description")
        table.add_column("Acts", justify="right")
        table.add_column("Scenes", justify="right")
        table.add_column("Current", style=st.STYLES["success"], justify="center")

        # Add rows with consistent formatting
        for game in games:
            # Get acts and scenes count
            act_count = len(game.acts) if hasattr(game, "acts") else 0
            scene_count = (
                sum(len(act.scenes) for act in game.acts)
                if hasattr(game, "acts")
                else len(game.scenes)
            )

            is_active = active_game and game.id == active_game.id
            active_marker = "✓" if is_active else ""

            # Create game name with appropriate styling
            game_name = st.title(game.name).plain if is_active else game.name

            table.add_row(
                game.id,
                game_name,
                game.description,
                str(act_count),
                str(scene_count),
                active_marker,
            )

        # Create panel title
        panel_title = st.title("Games")

        # Wrap the table in a panel with a title
        panel = Panel(
            table,
            title=panel_title,
            title_align="left",
            border_style=BORDER_STYLES["game_info"],
        )
        # Use self.console
        self.console.print(panel)

    def display_scenes_table(
        self, scenes: List[Scene], active_scene_id: Optional[str] = None
    ) -> None:
        """Displays a list of scenes in a Rich table."""
        logger.debug(f"Displaying scenes table with {len(scenes)} scenes")
        logger.debug(
            f"Active scene ID: {active_scene_id if active_scene_id else 'None'}"
        )
        if not scenes:
            logger.debug("No scenes found to display")
            # Use self.console
            self.console.print(
                "No scenes found. Create one with 'sologm scene create'."
            )
            return

        st = StyledText

        # Create table without a title
        table = Table(
            border_style=BORDER_STYLES["game_info"],
        )

        # Add columns with consistent styling
        table.add_column("ID", style=st.STYLES["timestamp"])
        table.add_column("Title", style=st.STYLES["category"])
        table.add_column("Description")
        table.add_column("Status", style=st.STYLES["success"])
        table.add_column("Current", style=st.STYLES["success"], justify="center")
        table.add_column("Sequence", justify="right")

        # Add rows with consistent formatting
        for scene in scenes:
            is_active = active_scene_id and scene.id == active_scene_id
            active_marker = "✓" if is_active else ""

            # Create scene title with appropriate styling
            scene_title = st.title(scene.title).plain if is_active else scene.title

            table.add_row(
                scene.id,
                scene_title,
                scene.description,
                scene.status.value,
                active_marker,
                str(scene.sequence),
            )

        # Create panel title
        panel_title = st.title("Scenes")

        # Wrap the table in a panel with a title
        panel = Panel(
            table,
            title=panel_title,
            title_align="left",
            border_style=BORDER_STYLES["game_info"],
        )
        # Use self.console
        self.console.print(panel)

    def display_game_info(
        self, game: Game, active_scene: Optional[Scene] = None
    ) -> None:
        """Displays detailed information about a specific game using Rich."""
        logger.debug(
            f"Displaying game info for {game.id} with active scene: "
            f"{active_scene.id if active_scene else 'None'}"
        )

        st = StyledText

        # Get active act if available
        active_act = (
            next((act for act in game.acts if act.is_active), None)
            if hasattr(game, "acts")
            else None
        )

        # Count scenes across all acts
        scene_count = (
            sum(len(act.scenes) for act in game.acts)
            if hasattr(game, "acts")
            else len(game.scenes)
        )
        act_count = len(game.acts) if hasattr(game, "acts") else 0

        logger.debug(
            f"Game details: name='{game.name}', acts={act_count}, scenes={scene_count}"
        )

        # Create metadata with consistent formatting
        metadata = {
            "Created": game.created_at.strftime("%Y-%m-%d"),
            "Modified": game.modified_at.strftime("%Y-%m-%d"),
            "Acts": act_count,
            "Scenes": scene_count,
        }

        # Create panel content
        content = Text()
        content.append(st.subtitle(game.description))
        content.append("\n")
        content.append(st.format_metadata(metadata))

        if active_act:
            act_title = active_act.title or "Untitled Act"
            content.append("\nActive Act: ")
            content.append(st.title(f"Act {active_act.sequence}: {act_title}"))

        if active_scene:
            content.append("\nActive Scene: ")
            content.append(st.title(active_scene.title))

        # Create panel title
        panel_title = st.combine(
            st.title_blue(game.name),
            " (",
            st.title_timestamp(game.slug),
            ") ",
            st.timestamp(game.id),
        )

        panel = Panel(
            content,
            title=panel_title,
            border_style=BORDER_STYLES["game_info"],
            title_align="left",
        )

        # Use self.console instead of the console parameter
        self.console.print(panel)

    def display_interpretation_set(
        self, interp_set: InterpretationSet, show_context: bool = True
    ) -> None:
        """Display a full interpretation set using Rich.

        Args:
            interp_set: InterpretationSet to display
            show_context: Whether to show context information
        """
        st = StyledText

        # Access interpretations relationship directly
        interpretation_count = len(interp_set.interpretations)

        logger.debug(
            f"Displaying interpretation set {interp_set.id} with "
            f"{interpretation_count} interpretations"
        )

        # Show context panel if requested
        if show_context:
            # Create context content
            context_content = st.combine(
                st.subtitle("Context:"),
                " ",
                interp_set.context,
                "\n",
                st.subtitle("Results:"),
                " ",
                interp_set.oracle_results,
            )

            # Create panel title
            panel_title = st.title("Oracle Interpretations")

            context_panel = Panel(
                context_content,
                title=panel_title,
                border_style=BORDER_STYLES["game_info"],
                title_align="left",
            )
            self.console.print(context_panel)
            self.console.print()

        # Display each interpretation with its sequence number
        for i, interp in enumerate(interp_set.interpretations, 1):
            # CRUCIAL: Call the method on self
            self.display_interpretation(interp, sequence=i)

        # Show set ID with instruction
        instruction_panel = Panel(
            "Use this ID to select an interpretation with 'sologm oracle select'",
            title=st.timestamp(f"Interpretation Set: {interp_set.id}"),
            border_style=BORDER_STYLES["pending"],
            expand=False,
            title_align="left",
        )
        self.console.print(instruction_panel)

    def display_scene_info(self, scene: Scene) -> None:
        """Displays detailed information about a specific scene using Rich."""
        logger.debug(
            f"Displaying scene info for {scene.id} (status: {scene.status.value})"
        )
        logger.debug(
            f"Scene details: title='{scene.title}', sequence={scene.sequence}, "
            f"act_id={scene.act_id if hasattr(scene, 'act_id') else 'unknown'}"
        )

        st = StyledText

        # Get act information
        act_info = ""
        if hasattr(scene, "act") and scene.act:
            act_title = scene.act.title or "Untitled Act"
            act_info = f"Act {scene.act.sequence}: {act_title}"

        # Create metadata with consistent formatting
        metadata = {
            "Status": scene.status.value,
            "Sequence": scene.sequence,
            "Act": act_info,
            "Created": scene.created_at.strftime("%Y-%m-%d"),
            "Modified": scene.modified_at.strftime("%Y-%m-%d"),
        }

        # Determine border style based on scene status
        border_style = BORDER_STYLES["current"]
        if scene.status.value == "COMPLETED":
            border_style = BORDER_STYLES["success"]

        # Create panel content
        panel_content = st.combine(
            st.subtitle(scene.description), "\n", st.format_metadata(metadata)
        )

        # Create panel title
        panel_title = st.combine(
            st.title_blue(scene.title), " ", st.timestamp(f"({scene.id})")
        )

        panel = Panel(
            panel_content,
            title=panel_title,
            border_style=border_style,
            title_align="left",
        )

        # Use self.console instead of the console parameter
        self.console.print(panel)

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
        """Displays the overall status of the current game using Rich."""
        raise NotImplementedError

    def display_acts_table(
        self, acts: List[Act], active_act_id: Optional[str] = None
    ) -> None:
        """Displays a list of acts in a Rich table."""
        logger.debug(f"Displaying acts table with {len(acts)} acts")
        logger.debug(f"Active act ID: {active_act_id if active_act_id else 'None'}")
        if not acts:
            logger.debug("No acts found to display")
            # Use self.console
            self.console.print("No acts found. Create one with 'sologm act create'.")
            return

        st = StyledText

        # Create table without a title
        table = Table(
            border_style=BORDER_STYLES["game_info"],
        )

        # Add columns with consistent styling
        table.add_column("ID", style=st.STYLES["timestamp"])
        table.add_column("Sequence", justify="right")
        table.add_column("Title", style=st.STYLES["category"])
        table.add_column("Summary")
        table.add_column("Current", style=st.STYLES["success"], justify="center")

        # Add rows with consistent formatting
        for act in acts:
            is_active = active_act_id and act.id == active_act_id
            active_marker = "✓" if is_active else ""

            # Create act title with appropriate styling
            act_title = act.title if act.title else "[italic]Untitled Act[/italic]"
            act_title_styled = st.title(act_title).plain if is_active else act_title

            table.add_row(
                act.id,
                str(act.sequence),
                act_title_styled,
                act.summary or "",
                active_marker,
            )

        # Create panel title
        panel_title = st.title("Acts")

        # Wrap the table in a panel with a title
        panel = Panel(
            table,
            title=panel_title,
            title_align="left",
            border_style=BORDER_STYLES["game_info"],
        )
        # Use self.console
        self.console.print(panel)

    def display_act_info(self, act: Act, game_name: str) -> None:
        """Displays detailed information about a specific act using Rich."""
        logger.debug(f"Displaying act info for {act.id}")
        logger.debug(
            f"Act details: title='{act.title}', sequence={act.sequence}, "
            f"game_id={act.game_id}"
        )

        st = StyledText

        # Create metadata with consistent formatting
        metadata = {
            "Game": game_name,
            "Sequence": f"Act {act.sequence}",
            "Created": act.created_at.strftime("%Y-%m-%d"),
            "Modified": act.modified_at.strftime("%Y-%m-%d"),
        }

        # Determine border style based on act status
        border_style = (
            BORDER_STYLES["current"] if act.is_active else BORDER_STYLES["game_info"]
        )

        # Create panel content
        panel_content = Text()

        # Add description if available
        if act.summary:
            panel_content.append(st.subtitle(act.summary))
            panel_content.append("\n\n")

        # Add metadata
        panel_content.append(st.format_metadata(metadata))

        # Create panel title
        if act.title:
            title_display = act.title
            panel_title = st.combine(
                st.title_blue(f"Act {act.sequence}: {title_display}"),
                " ",
                st.timestamp(f"({act.id})"),
            )
        else:
            untitled_text = Text("Untitled Act", style="italic")
            panel_title = st.combine(
                st.title_blue(f"Act {act.sequence}: "),
                untitled_text,
                " ",
                st.timestamp(f"({act.id})"),
            )

        panel = Panel(
            panel_content,
            title=panel_title,
            border_style=border_style,
            title_align="left",
        )

        self.console.print(panel)

        # Display scenes in this act if any
        if hasattr(act, "scenes") and act.scenes:
            # Create a table for scenes
            scenes_table = Table(
                border_style=BORDER_STYLES["game_info"],
            )

            # Add columns with consistent styling
            scenes_table.add_column("ID", style=st.STYLES["timestamp"])
            scenes_table.add_column("Sequence", justify="right")
            scenes_table.add_column("Title", style=st.STYLES["category"])
            scenes_table.add_column("Summary")
            scenes_table.add_column(
                "Status", style=st.STYLES["success"]
            )  # Added Status column
            scenes_table.add_column(
                "Current", style=st.STYLES["success"], justify="center"
            )

            # Add rows for each scene
            for scene in act.scenes:
                active_marker = "✓" if scene.is_active else ""

                # Create scene title with appropriate styling
                scene_title = (
                    st.title(scene.title).plain if scene.is_active else scene.title
                )

                # Truncate description for table display
                truncated_description = truncate_text(scene.description, max_length=40)

                scenes_table.add_row(
                    scene.id,
                    str(scene.sequence),
                    scene_title,
                    truncated_description,
                    scene.status.value,  # Display status value
                    active_marker,
                )

            # Create panel title
            panel_title = st.title(f"Scenes in Act {act.sequence}")

            # Wrap the table in a panel with a title
            scenes_panel = Panel(
                scenes_table,
                title=panel_title,
                title_align="left",
                border_style=BORDER_STYLES["game_info"],
            )
            self.console.print(scenes_panel)
        else:
            # Create an empty panel for no scenes
            empty_panel = Panel(
                st.subtitle("No scenes in this act yet."),
                title=st.title("Scenes"),
                title_align="left",
                border_style=BORDER_STYLES["neutral"],
            )
            self.console.print(empty_panel)

    def display_interpretation_sets_table(
        self, interp_sets: List[InterpretationSet]
    ) -> None:
        """Display interpretation sets in a formatted table using Rich.

        Args:
            interp_sets: List of interpretation sets to display
        """
        logger.debug(
            f"Displaying interpretation sets table with {len(interp_sets)} sets"
        )

        st = StyledText

        # Create table without a title
        table = Table(
            border_style=BORDER_STYLES["game_info"],
        )

        # Add columns with consistent styling
        table.add_column("ID", style=st.STYLES["timestamp"], no_wrap=True)
        table.add_column("Scene", style=st.STYLES["category"])
        table.add_column("Context")
        table.add_column("Oracle Results")
        table.add_column("Created", style=st.STYLES["timestamp"])
        table.add_column("Status", style=st.STYLES["success"])
        table.add_column("Count", justify="right")

        # Add rows with consistent formatting
        for interp_set in interp_sets:
            # Get scene title
            scene_title = (
                interp_set.scene.title if hasattr(interp_set, "scene") else "Unknown"
            )

            # Truncate context and oracle results
            context = truncate_text(interp_set.context, max_length=40)
            oracle_results = truncate_text(interp_set.oracle_results, max_length=40)

            # Determine status
            has_selection = any(
                interp.is_selected for interp in interp_set.interpretations
            )
            status = "Resolved" if has_selection else "Pending"
            status_style = "bold green" if has_selection else "bold yellow"

            # Count interpretations
            interp_count = len(interp_set.interpretations)

            # Format created_at
            created_at = interp_set.created_at.strftime("%Y-%m-%d %H:%M")

            table.add_row(
                interp_set.id,
                scene_title,
                context,
                oracle_results,
                created_at,
                f"[{status_style}]{status}[/{status_style}]",
                str(interp_count),
            )

        # Create panel title
        panel_title = st.title("Oracle Interpretation Sets")

        # Wrap the table in a panel with a title
        panel = Panel(
            table,
            title=panel_title,
            title_align="left",
            border_style=BORDER_STYLES["game_info"],
        )
        # Use self.console instead of console parameter
        self.console.print(panel)

    def display_interpretation_status(self, interp_set: InterpretationSet) -> None:
        """Display the status of the current interpretation set using Rich.

        Args:
            interp_set: The current interpretation set to display
        """
        logger.debug(f"Displaying interpretation status for set {interp_set.id}")

        st = StyledText
        panel_title = st.title("Current Oracle Interpretation")

        # Create metadata with consistent formatting
        metadata = {
            "Set ID": interp_set.id,
            "Retry count": interp_set.retry_attempt,
            "Resolved": any(
                interp.is_selected for interp in interp_set.interpretations
            ),
        }

        # Create panel content
        panel_content = st.combine(
            st.subtitle("Context:"),
            " ",
            interp_set.context,
            "\n",
            st.subtitle("Results:"),
            " ",
            interp_set.oracle_results,
            "\n",
            st.format_metadata(metadata),
        )

        # Create and display the panel
        panel = Panel(
            panel_content,
            title=panel_title,
            border_style=BORDER_STYLES["current"],
            title_align="left",
        )
        self.console.print(panel)
        self.console.print()

    def display_act_ai_generation_results(
        self, results: Dict[str, str], act: Act
    ) -> None:
        """Displays the results generated by AI for an act using Rich."""
        raise NotImplementedError

    def display_act_completion_success(self, completed_act: Act) -> None:
        """Displays a success message upon act completion using Rich."""
        raise NotImplementedError

    def display_act_ai_feedback_prompt(self, console: Console) -> None:
        """Displays the prompt asking for feedback on AI generation using Rich Prompt."""
        # Note: This implementation will likely directly use Rich Prompt.
        # The base class signature includes `console` which might be redundant
        # if we always use `self.console`. We'll refine this when implementing.
        raise NotImplementedError

    def display_act_edited_content_preview(
        self, edited_results: Dict[str, str]
    ) -> None:
        """Displays a preview of edited AI-generated content using Rich."""
        raise NotImplementedError

    def display_error(self, message: str) -> None:
        """Displays an error message to the user using Rich."""
        # Implementation will use self.console.print with red styling.
        raise NotImplementedError
