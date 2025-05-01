"""
Concrete implementation of the Renderer interface using Rich library components.
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt  # Added Prompt import
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
from sologm.models.scene import Scene

# Corrected import based on file structure from Phase 1
from .base import Renderer

# Use TYPE_CHECKING for manager imports to avoid circular dependencies
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
        super().__init__(console, markdown_mode=False)
        logger.debug("RichRenderer initialized")

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

        # Always add the "Rolls:" line
        # Format individual results without brackets
        results_str = ", ".join(map(str, roll.individual_results))
        details.append(
            st.combine(
                st.subtitle("Rolls:"),
                " ",
                st.timestamp(results_str),
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
            # Use a more readable timestamp format (down to the second)
            metadata["Time"] = roll.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Create panel content
        panel_content = Text()

        # Add all details
        for i, detail in enumerate(details):
            if i > 0:
                panel_content.append("\n")
            panel_content.append(detail)

        # Add metadata if available
        if metadata:
            panel_content.append("\n")
            panel_content.append(st.format_metadata(metadata))

        panel = Panel(
            panel_content,
            title=panel_title,
            border_style=BORDER_STYLES["neutral"],
            expand=True,
            title_align="left",
        )
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
        self.console.print(panel)
        self.console.print()  # Ensure trailing newline for spacing.

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
        self.console.print(panel)

    def display_games_table(
        self, games: List[Game], active_game: Optional[Game] = None
    ) -> None:
        """Displays a list of games in a Rich table."""
        logger.debug(f"Displaying games table with {len(games)} games")
        logger.debug(f"Active game: {active_game.id if active_game else 'None'}")
        if not games:
            logger.debug("No games found to display")
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
            # --- MODIFIED: Use hybrid properties for counts ---
            act_count = game.act_count  # Use game's hybrid property
            # Calculate scene count by summing the scene_count of each act
            scene_count = sum(
                act.scene_count for act in game.acts
            )  # Use act's hybrid property
            # --- END MODIFICATION ---

            is_active = active_game and game.id == active_game.id
            active_marker = "✓" if is_active else ""

            # Create game name with appropriate styling
            game_name = st.title(game.name).plain if is_active else game.name

            table.add_row(
                game.id,
                game_name,
                game.description,
                str(act_count),  # Use count from hybrid property
                str(scene_count),  # Use count from hybrid property
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
            self.console.print(
                "No scenes found. Create one with 'sologm scene create'."
            )
            return

        st = StyledText

        # Create table without a title
        table = Table(
            border_style=BORDER_STYLES["game_info"],
        )

        # Add columns with consistent styling.
        # Ensure ID column does not wrap/truncate.
        table.add_column("ID", style=st.STYLES["timestamp"], no_wrap=True)
        table.add_column("Title", style=st.STYLES["category"])
        table.add_column("Description")
        # Removed Status column
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
                # Removed status value
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

        # Display each interpretation with its sequence number.
        for i, interp in enumerate(interp_set.interpretations, 1):
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
            f"Displaying scene info for {scene.id} (active: {scene.is_active})"
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

        # Create metadata with consistent formatting.
        metadata = {
            # Status removed
            "Sequence": scene.sequence,
            "Act": act_info,
            "Created": scene.created_at.strftime("%Y-%m-%d"),
            "Modified": scene.modified_at.strftime("%Y-%m-%d"),
        }

        # Determine border style based on active status.
        border_style = (
            BORDER_STYLES["current"] if scene.is_active else BORDER_STYLES["game_info"]
        )

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

        self.console.print(panel)

    # --- display_game_status and its helpers ---

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
        """Display comprehensive game status in a compact layout using Rich.

        Shows the latest act and scene, indicating their active status.

        Args:
            game: Current game
            latest_act: The most recent act in the game.
            latest_scene: The most recent scene in the latest act.
            recent_events: Recent events (limited list, typically from latest scene).
            scene_manager: Optional scene manager for additional context (like prev scene).
            oracle_manager: Optional oracle manager for interpretation context.
            recent_rolls: Optional list of recent dice rolls (typically from latest scene).
            is_act_active: Whether the latest_act is flagged as active.
            is_scene_active: Whether the latest_scene is flagged as active.
        """
        logger.debug(
            f"Displaying game status for {game.id} with {len(recent_events)} events. "
            f"Latest Act: {latest_act.id if latest_act else 'None'} (Active: {is_act_active}). "
            f"Latest Scene: {latest_scene.id if latest_scene else 'None'} (Active: {is_scene_active})."
        )

        # Calculate display dimensions using self._calculate_truncation_length
        truncation_length = self._calculate_truncation_length()

        # Display game header using self._create_game_header_panel
        self.console.print(self._create_game_header_panel(game))

        # Display act panel using self._create_act_panel
        self.console.print(
            self._create_act_panel(
                game, latest_act, is_act_active, truncation_length=truncation_length
            )
        )

        # Create and display the main grid with scene and events info
        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column("Left", ratio=1)
        grid.add_column("Right", ratio=1)

        # Add scene panels and events panel using self._create_scene_panels_grid and self._create_events_panel
        left_grid = self._create_scene_panels_grid(
            game, latest_scene, scene_manager, is_scene_active
        )
        events_panel = self._create_events_panel(recent_events, truncation_length)
        grid.add_row(left_grid, events_panel)
        self.console.print(grid)

        # Create a new grid for oracle and dice rolls
        logger.debug("Creating bottom grid for oracle and dice rolls")
        bottom_grid = Table.grid(expand=True, padding=(0, 1))
        bottom_grid.add_column("Oracle", ratio=7)  # 70% width
        bottom_grid.add_column("Dice", ratio=3)  # 30% width

        # Create oracle panel using self._create_oracle_panel or self._create_empty_oracle_panel
        logger.debug("Creating oracle panel")
        oracle_panel = (
            self._create_oracle_panel(
                game,
                latest_scene,  # Use latest_scene
                oracle_manager,
                truncation_length,
            )
            or self._create_empty_oracle_panel()
        )
        logger.debug(f"Oracle panel created: {oracle_panel is not None}")

        # Create dice rolls panel using self._create_dice_rolls_panel
        logger.debug(f"Creating dice rolls panel with {len(recent_rolls or [])} rolls")
        dice_panel = self._create_dice_rolls_panel(recent_rolls or [])
        logger.debug(f"Dice panel created: {dice_panel is not None}")

        # Add panels to the bottom grid
        logger.debug("Adding panels to bottom grid")
        bottom_grid.add_row(oracle_panel, dice_panel)
        logger.debug("Printing bottom grid with oracle and dice panels")
        self.console.print(bottom_grid)

    def _calculate_truncation_length(self) -> int:
        """Calculate appropriate truncation length based on console width."""
        logger.debug("Calculating appropriate truncation length for console")
        try:
            # Use self.console
            console_width = self.console.width
            logger.debug(f"Console width detected: {console_width} characters")
            # Calculate appropriate truncation length based on console width
            # Since we're using a two-column layout, each column gets roughly half the width
            # Subtract some space for borders, padding, and formatting
            truncation_length = max(
                40, int(console_width / 2) - 10
            )  # Adjusted calculation for half-width
            logger.debug(
                f"Using truncation length of {truncation_length} "
                f"characters for event descriptions"
            )
            return truncation_length
        except (TypeError, ValueError) as e:
            # Default to a reasonable truncation length if console width is not available
            logger.debug(
                f"Could not determine console width due to error: {e}, using default value."
            )
            return 40

    def _create_act_panel(
        self,
        game: Game,
        latest_act: Optional[Act] = None,
        is_act_active: bool = False,
        truncation_length: int = 80,  # Add parameter with a default
    ) -> Panel:
        """Create a panel showing the latest act information."""
        st = StyledText

        panel_title_text = "Latest Act"  # Always refer to latest
        border_style = BORDER_STYLES["neutral"]  # Default border

        if not latest_act:
            # No acts found
            panel_content = st.subtitle(
                "No acts found in this game. Create one with 'sologm act create'."
            )
            return Panel(
                panel_content,
                title=st.title(panel_title_text),
                border_style=border_style,
                expand=True,
                title_align="left",
            )

        # Set border if active
        if is_act_active:
            border_style = BORDER_STYLES["current"]  # Use current border if active

        # Create panel content with act information
        panel_content = Text()
        # ... (use latest_act to build title_text) ...
        if latest_act.title:
            title_text = st.title(f"Act {latest_act.sequence}: {latest_act.title}")
        else:
            untitled_text = Text("Untitled Act", style="italic")
            title_text = st.combine(
                st.title(f"Act {latest_act.sequence}: "), untitled_text
            )
        panel_content.append(title_text)

        if latest_act.summary:
            # Calculate a max length suitable for a full-width panel
            # Let's use 1.5 times the base truncation length as an example
            max_summary_length = int(truncation_length * 1.5)
            logger.debug(f"Truncating act summary to max length {max_summary_length}")
            truncated_summary = truncate_text(
                latest_act.summary, max_length=max_summary_length
            )
            panel_content.append("\n")
            panel_content.append(truncated_summary)

        # Add metadata including status
        metadata = {
            "Status": st.success("Active") if is_act_active else st.warning("Inactive"),
            "Scenes": len(latest_act.scenes) if hasattr(latest_act, "scenes") else 0,
            "Created": latest_act.created_at.strftime("%Y-%m-%d"),
        }
        panel_content.append("\n")
        panel_content.append(st.format_metadata(metadata))

        return Panel(
            panel_content,
            title=st.title(panel_title_text),
            border_style=border_style,
            expand=True,
            title_align="left",
        )

    def _create_game_header_panel(self, game: Game) -> Panel:
        """Create the game info header panel.

        Args:
            game: The game to display information for

        Returns:
            A Panel containing the game header information
        """
        logger.debug(f"Creating game header panel for game {game.id}")

        st = StyledText

        # Create metadata with consistent formatting
        metadata = {
            "Created": game.created_at.strftime("%Y-%m-%d"),
            "Acts": len(game.acts) if hasattr(game, "acts") else 0,
            "Scenes": sum(len(act.scenes) for act in game.acts)
            if hasattr(game, "acts")
            else len(game.scenes),
        }

        # Create a title with consistent styling
        panel_title = st.combine(
            st.title_blue(game.name),
            " (",
            st.title_timestamp(game.slug),
            ") ",
            st.timestamp(game.id),
        )

        # Create content with consistent styling
        # Truncate description to fit approximately 3 lines based on console width
        console_width = 80  # Default fallback width

        # Use self.console
        console_width = self.console.width
        logger.debug(f"Using self.console width: {console_width}")

        # Calculate chars per line (accounting for margins/padding)
        chars_per_line = max(40, console_width - 10)
        # For 3 lines, allow roughly 3x that many characters
        max_desc_length = chars_per_line * 3

        truncated_description = truncate_text(
            game.description, max_length=max_desc_length
        )
        logger.debug(
            f"Truncated game description from {len(game.description)} to {len(truncated_description)} chars"
        )

        # Create content with styled text
        content = Text()
        content.append(truncated_description)
        content.append("\n")

        # Add metadata with dim style
        metadata_text = st.format_metadata(metadata)
        metadata_text.stylize("dim")  # Dim the metadata for less emphasis.
        content.append(metadata_text)

        logger.debug("Game header panel created")
        return Panel(
            content,
            title=panel_title,
            expand=True,
            border_style=BORDER_STYLES["game_info"],
            title_align="left",
        )

    def _create_scene_panels_grid(
        self,
        game: Game,
        latest_scene: Optional[Scene],
        scene_manager: Optional["SceneManager"],
        is_scene_active: bool = False,
    ) -> Table:
        """Create a grid containing latest and previous scene panels.

        Args:
            game: The game to display information for
            latest_scene: The most recent scene in the latest act.
            scene_manager: Optional scene manager for retrieving previous scene.
            is_scene_active: Whether the latest_scene is flagged as active.

        Returns:
            A Table grid containing the scene panels.
        """
        logger.debug(
            f"Creating scene panels grid for game {game.id} (Latest Scene Active: {is_scene_active})"
        )

        st = StyledText

        # Calculate truncation length for scene descriptions
        console_width = 80  # Default fallback width
        # Use self.console
        console_width = self.console.width
        logger.debug(f"Using self.console width: {console_width}")

        # For scene descriptions in a two-column layout, use about 1/3 of console width
        # This accounts for the panel taking up roughly half the screen, minus borders/padding
        chars_per_line = max(30, int(console_width / 3))
        # Allow for about 4 lines of text
        max_desc_length = chars_per_line * 8

        logger.debug(
            f"Chars per line: {chars_per_line}, Max description length: {max_desc_length}"
        )

        # Determine title and border for the latest scene panel
        latest_scene_title_text = "Latest Scene"
        latest_scene_border_style = BORDER_STYLES["neutral"]  # Default border

        # Create latest scene panel
        scenes_content = Text()
        if latest_scene:
            logger.debug(f"Including latest scene {latest_scene.id} in panel")
            # ... (use latest_scene to build content, act_info, truncated_description) ...
            truncated_description = truncate_text(
                latest_scene.description, max_length=max_desc_length
            )
            logger.debug(
                f"Truncated latest scene description from {len(latest_scene.description)} to {len(truncated_description)} chars."
            )
            act_info = ""
            if hasattr(latest_scene, "act") and latest_scene.act:
                act_title = latest_scene.act.title or "Untitled Act"
                act_info = f"Act {latest_scene.act.sequence}: {act_title}\n"

            scenes_content = st.combine(
                st.subtitle(act_info) if act_info else Text(),
                st.title(latest_scene.title),
                "\n",
                truncated_description,
            )

            # Determine status string and border style based on is_active.
            if is_scene_active:
                status_string = st.success("Active")
                latest_scene_border_style = BORDER_STYLES["current"]
            else:
                status_string = st.warning("Inactive")
                latest_scene_border_style = BORDER_STYLES["neutral"]

            # Add metadata including status.
            metadata = {
                "Status": status_string,  # Reflects active/inactive, not completion.
                "Sequence": latest_scene.sequence,
                "Created": latest_scene.created_at.strftime("%Y-%m-%d")
                if latest_scene.created_at
                else "N/A",
            }
            scenes_content.append("\n")
            scenes_content.append(st.format_metadata(metadata))

        else:
            logger.debug("No latest scene to display")
            scenes_content = st.subtitle("No scenes found in this context")
            latest_scene_title_text = "Scene Status"  # Adjust title if no scene at all

        scenes_panel = Panel(
            scenes_content,
            title=st.title(latest_scene_title_text),
            border_style=latest_scene_border_style,
            title_align="left",
            expand=True,
        )

        # Create previous scene panel (logic remains similar, finds scene before latest_scene)
        prev_scene = None
        if latest_scene and scene_manager:
            logger.debug(
                f"Attempting to get previous scene for latest scene {latest_scene.id}"
            )
            prev_scene = scene_manager.get_previous_scene(latest_scene.id)

        prev_scene_content = Text()
        if prev_scene:
            logger.debug(f"Including previous scene {prev_scene.id} in panel")
            # ... (get truncated_description, act_info for prev_scene) ...
            truncated_description = truncate_text(
                prev_scene.description, max_length=max_desc_length
            )
            logger.debug(
                f"Truncated previous scene description from {len(prev_scene.description)} to {len(truncated_description)} chars."
            )
            act_info = ""
            if hasattr(prev_scene, "act") and prev_scene.act:
                act_title = prev_scene.act.title or "Untitled Act"
                act_info = f"Act {prev_scene.act.sequence}: {act_title}\n"

            prev_scene_content = st.combine(
                st.subtitle(act_info) if act_info else Text(),
                st.title(prev_scene.title),
                "\n",
                truncated_description,
            )
            # Add metadata for previous scene.
            prev_metadata = {
                "Status": "Active"
                if prev_scene.is_active
                else "Inactive",  # Display active/inactive status.
                "Sequence": prev_scene.sequence,
                "Created": prev_scene.created_at.strftime("%Y-%m-%d"),
            }
            prev_scene_content.append("\n")
            prev_scene_content.append(st.format_metadata(prev_metadata))
        else:
            logger.debug("No previous scene to display")
            prev_scene_content = st.subtitle("No previous scene")

        prev_scene_panel = Panel(
            prev_scene_content,
            title=st.title("Previous Scene"),
            border_style=BORDER_STYLES["game_info"],
            title_align="left",
            expand=True,
        )

        # Create a nested grid for the left column to stack the scene panels
        left_grid = Table.grid(padding=(0, 1), expand=True)  # Make the grid expand
        left_grid.add_column(ratio=1)  # Use ratio to ensure column expands
        left_grid.add_row(scenes_panel)
        left_grid.add_row(prev_scene_panel)

        return left_grid

    def _create_events_panel(
        self, recent_events: List[Event], truncation_length: int
    ) -> Panel:
        """Create the recent events panel."""
        logger.debug(f"Creating events panel with {len(recent_events)} events")

        st = StyledText
        events_content = Text()

        if recent_events:
            # Calculate how many events we can reasonably show
            # Each event takes at least 3 lines (timestamp+source, description, blank)
            max_events_to_show = min(3, len(recent_events))  # Show at most 3 events
            logger.debug(f"Showing {max_events_to_show} of {len(recent_events)} events")

            events_shown = recent_events[:max_events_to_show]
            for i, event in enumerate(events_shown):
                # Get the source name instead of the source object
                source_name = (
                    event.source.name
                    if hasattr(event.source, "name")
                    else str(event.source)
                )

                logger.debug(
                    f"Adding event {event.id} to panel (source: {source_name})"
                )

                # Add a newline between events
                if i > 0:
                    events_content.append("\n\n")

                # Truncate long descriptions based on calculated width
                truncated_description = truncate_text(
                    event.description, max_length=truncation_length
                )

                # Add event header with timestamp and source
                events_content.append(
                    st.timestamp(event.created_at.strftime("%Y-%m-%d %H:%M"))
                )
                events_content.append(" ")
                events_content.append(st.category(f"({source_name})"))
                events_content.append("\n")
                events_content.append(truncated_description)
        else:
            logger.debug("No events to display in panel")
            events_content = st.subtitle("No recent events")

        # Create panel title
        panel_title = st.combine(
            st.title("Recent Events"), f" ({len(recent_events)} shown)"
        )

        return Panel(
            events_content,
            title=panel_title,
            border_style=BORDER_STYLES[
                "success"
            ],  # Events represent completed actions.
            title_align="left",
        )

    def _create_oracle_panel(
        self,
        game: Game,
        latest_scene: Optional[Scene],
        oracle_manager: Optional["OracleManager"],
        truncation_length: int,
    ) -> Optional[Panel]:
        """Create the oracle panel if applicable."""
        logger.debug(f"Creating oracle panel for game {game.id}")

        if not oracle_manager or not latest_scene:
            logger.debug("No oracle manager or latest scene, skipping oracle panel")
            return None

        current_interp_set = oracle_manager.get_current_interpretation_set(
            latest_scene.id
        )

        if current_interp_set:
            # Check if any interpretation is selected
            has_selection = any(
                interp.is_selected for interp in current_interp_set.interpretations
            )

            if not has_selection:
                logger.debug("Creating pending oracle panel")
                # Call self._create_pending_oracle_panel
                return self._create_pending_oracle_panel(
                    current_interp_set, truncation_length
                )

        recent_interp = oracle_manager.get_most_recent_interpretation(latest_scene.id)

        if recent_interp:
            logger.debug("Creating recent oracle panel")
            # Call self._create_recent_oracle_panel
            return self._create_recent_oracle_panel(recent_interp[0], recent_interp[1])

        logger.debug("No oracle panel needed, creating empty panel.")
        return self._create_empty_oracle_panel()

    def _create_pending_oracle_panel(
        self,
        interp_set: InterpretationSet,
        truncation_length: int,
    ) -> Panel:
        """Create a panel for pending oracle interpretation."""
        logger.debug(f"Creating pending oracle panel for set {interp_set.id}")

        st = StyledText

        panel_content = Text()

        panel_content.append(st.warning("Open Oracle Interpretation:"))
        panel_content.append("\n")
        panel_content.append(st.subtitle("Context:"))
        panel_content.append(" ")
        panel_content.append(interp_set.context)
        panel_content.append("\n\n")

        # Add interpretation options
        for i, interp in enumerate(interp_set.interpretations, 1):
            logger.debug(f"Adding interpretation option {i}: {interp.id}")

            if i > 1:
                panel_content.append("\n\n")

            panel_content.append(st.title(f"{i}. {interp.title}"))
            panel_content.append("\n")
            # Truncate description here
            truncated_desc = truncate_text(
                interp.description, max_length=truncation_length
            )
            panel_content.append(truncated_desc)

        panel_content.append("\n\n")
        panel_content.append(
            st.subtitle("Use 'sologm oracle select' to choose an interpretation.")
        )

        return Panel(
            panel_content,
            title=st.title("Pending Oracle Decision"),
            border_style=BORDER_STYLES["pending"],
            expand=True,
            title_align="left",
        )

    def _create_recent_oracle_panel(
        self,
        interp_set: InterpretationSet,
        selected_interp: Interpretation,
    ) -> Panel:
        """Create a panel showing the most recent oracle interpretation."""
        logger.debug(
            f"Creating recent oracle panel for set {interp_set.id}, "
            f"interpretation {selected_interp.id}"
        )

        st = StyledText

        panel_content = Text()

        panel_content.append(st.subtitle("Oracle Results:"))
        panel_content.append(" ")
        panel_content.append(interp_set.oracle_results)
        panel_content.append("\n")
        panel_content.append(st.subtitle("Context:"))
        panel_content.append(" ")
        panel_content.append(interp_set.context)
        panel_content.append("\n\n")

        panel_content.append(st.subtitle("Selected Interpretation:"))
        panel_content.append(" ")
        panel_content.append(st.title(selected_interp.title))
        panel_content.append("\n")
        panel_content.append(selected_interp.description)
        panel_content.append("\n\n")

        panel_content.append(st.subtitle("Other options were:"))

        for i, interp in enumerate(interp_set.interpretations, 1):
            if interp.id != selected_interp.id:
                panel_content.append("\n")
                panel_content.append(st.title(f"{i}. {interp.title}"))
                panel_content.append("\n")
                panel_content.append(interp.description)

        return Panel(
            panel_content,
            title=st.title("Previous Oracle Decision"),
            border_style=BORDER_STYLES["success"],
            expand=True,
            title_align="left",
        )

    def _create_empty_oracle_panel(self) -> Panel:
        """Create an empty oracle panel when no oracle information is available."""
        logger.debug("Creating empty oracle panel")

        st = StyledText
        panel_content = st.subtitle("No oracle interpretations yet.")

        return Panel(
            panel_content,
            title=st.title("Oracle"),
            border_style=BORDER_STYLES["neutral"],
            expand=True,
            title_align="left",
        )

    def _create_dice_rolls_panel(self, recent_rolls: List[DiceRoll]) -> Panel:
        """Create a panel showing recent dice rolls.

        Args:
            recent_rolls: List of recent dice rolls to display

        Returns:
            Panel containing formatted dice roll information
        """
        logger.debug(f"Creating dice rolls panel with {len(recent_rolls)} rolls")

        st = StyledText

        if not recent_rolls:
            logger.debug("No dice rolls to display")
            panel_content = st.subtitle("No recent dice rolls.")
        else:
            panel_content = Text()

            for i, roll in enumerate(recent_rolls):
                logger.debug(f"Formatting roll {i + 1}: {roll.notation} = {roll.total}")

                # Add spacing between rolls
                if i > 0:
                    panel_content.append("\n\n")

                # Create roll header with notation and total
                roll_header = st.combine(
                    st.title(roll.notation), " = ", st.success(str(roll.total))
                )
                panel_content.append(roll_header)

                # Add reason if available
                if roll.reason:
                    logger.debug(f"Roll has reason: {roll.reason}")
                    panel_content.append(" (")
                    panel_content.append(st.subtitle(roll.reason))
                    panel_content.append(")")

                logger.debug(f"Roll timestamp: {roll.created_at}")
                panel_content.append("\n")
                formatted_time = roll.created_at.strftime("%Y-%m-%d %H:%M:%S")
                panel_content.append(st.timestamp(formatted_time))

                if len(roll.individual_results) > 1:
                    logger.debug(
                        f"Roll has individual results: {roll.individual_results}"
                    )
                    panel_content.append("\n")
                    panel_content.append(st.category(str(roll.individual_results)))

        return Panel(
            panel_content,
            title=st.title("Recent Rolls"),
            border_style=BORDER_STYLES["neutral"],
            expand=True,
            title_align="left",
        )

    # --- End display_game_status helpers ---

    def display_acts_table(
        self, acts: List[Act], active_act_id: Optional[str] = None
    ) -> None:
        """Displays a list of acts in a Rich table."""
        logger.debug(f"Displaying acts table with {len(acts)} acts")
        logger.debug(f"Active act ID: {active_act_id if active_act_id else 'None'}")
        if not acts:
            logger.debug("No acts found to display")
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

            # Construct the ID cell content with ID and slug on separate lines
            id_cell_content = Text()
            id_cell_content.append(act.id)
            id_cell_content.append("\n")  # Add newline
            id_cell_content.append(
                f"({act.slug})", style="dim"
            )  # Add slug in dim style

            # Use the full summary (or empty string if None)
            summary_content = act.summary or ""

            table.add_row(
                id_cell_content,  # Pass the Text object here
                str(act.sequence),
                act_title_styled,
                summary_content,  # Use full summary
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

        # Display scenes in this act if any.
        if hasattr(act, "scenes") and act.scenes:
            scenes_table = Table(
                border_style=BORDER_STYLES["game_info"],
            )

            # Add columns with consistent styling
            scenes_table.add_column("ID", style=st.STYLES["timestamp"])
            scenes_table.add_column("Sequence", justify="right")
            scenes_table.add_column("Title", style=st.STYLES["category"])
            scenes_table.add_column("Summary")
            # Status column removed
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
                    # Removed status value
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

    def display_act_edited_content_preview(
        self, edited_results: Dict[str, str]
    ) -> None:
        """Display a preview of edited act AI content using Rich.

        Shows a formatted preview of the user-edited AI-generated content
        for an act.

        Args:
            edited_results: Dictionary with edited title and summary
        """
        logger.debug("Displaying edited content preview for act")

        st = StyledText

        # Use self.console
        self.console.print("\n" + st.title("Preview of your edited content:").plain)

        title_panel = Panel(
            edited_results["title"],
            title=st.title("Edited Title"),
            border_style=BORDER_STYLES["success"],
            expand=False,
            title_align="left",
        )
        self.console.print(title_panel)

        summary_panel = Panel(
            edited_results["summary"],
            title=st.title("Edited Summary"),
            border_style=BORDER_STYLES["success"],
            expand=False,
            title_align="left",
        )
        self.console.print(summary_panel)

    def display_act_ai_generation_results(
        self, results: Dict[str, str], act: Act
    ) -> None:
        """Displays the results generated by AI for an act using Rich."""
        logger.debug(f"Displaying AI generation results for act {act.id}")

        st = StyledText

        # Display generated title
        if "title" in results and results["title"]:
            title_panel = Panel(
                results["title"],
                title=st.title("AI-Generated Title"),
                border_style=BORDER_STYLES["success"],
                expand=False,
                title_align="left",
            )
            self.console.print(title_panel)

            if act.title:
                existing_title_panel = Panel(
                    act.title,
                    title=st.title("Current Title"),
                    border_style=BORDER_STYLES["current"],
                    expand=False,
                    title_align="left",
                )
                self.console.print(existing_title_panel)

        if "summary" in results and results["summary"]:
            summary_panel = Panel(
                results["summary"],
                title=st.title("AI-Generated Summary"),
                border_style=BORDER_STYLES["success"],
                expand=False,
                title_align="left",
            )
            self.console.print(summary_panel)

            if act.summary:
                existing_summary_panel = Panel(
                    act.summary,
                    title=st.title("Current Summary"),
                    border_style=BORDER_STYLES["current"],
                    expand=False,
                    title_align="left",
                )
                self.console.print(existing_summary_panel)

    def display_act_completion_success(self, completed_act: Act) -> None:
        """Displays a success message upon act completion using Rich."""
        logger.debug(f"Displaying completion success for act {completed_act.id}")

        st = StyledText

        title_display = (
            f"'{completed_act.title}'" if completed_act.title else "untitled"
        )

        self.console.print(
            st.title_success(f"Act {title_display} completed successfully!")
        )

        metadata = {
            "ID": completed_act.id,
            "Sequence": f"Act {completed_act.sequence}",
            "Status": "Completed",  # Assuming completion implies inactive now.
        }
        self.console.print(st.format_metadata(metadata))

        if completed_act.title:
            self.console.print(
                "\n" + st.combine(st.title("Title:"), " ", completed_act.title).plain
            )
        if completed_act.summary:
            self.console.print(
                "\n"
                + st.combine(st.title("Summary:"), "\n", completed_act.summary).plain
            )

    def display_act_ai_feedback_prompt(self, console: Console) -> str:
        """Displays the prompt asking for feedback on AI generation using Rich Prompt.

        Args:
            console: The Rich Console instance (required by base class,
                     but Prompt.ask handles output).

        Returns:
            User's choice: "A" for Accept, "E" for Edit, or "R" for Regenerate
        """
        # The 'console' parameter is present to match the base class signature,
        # but Rich's Prompt.ask handles the actual console interaction.
        logger.debug("Displaying AI feedback prompt for act")

        st = StyledText
        default_choice = "E"

        prompt_message = st.warning(
            "What would you like to do with this content? (A)ccept / (E)dit / (R)egenerate"
        )

        choice = Prompt.ask(
            prompt_message,
            choices=["A", "E", "R", "a", "e", "r"],
            default=default_choice,
        ).upper()

        logger.debug(f"User chose: {choice}")
        return choice

    def display_error(self, message: str) -> None:
        """Displays an error message to the user using Rich."""
        logger.error(f"Displaying error: {message}")
        self.console.print(f"[red]Error: {message}[/red]")

    def display_success(self, message: str) -> None:
        """Displays a success message using Rich."""
        logger.debug(f"Displaying success: {message}")
        self.console.print(StyledText.success(f"Success: {message}"))

    def display_warning(self, message: str) -> None:
        """Displays a warning message using Rich."""
        logger.debug(f"Displaying warning: {message}")
        self.console.print(StyledText.warning(f"Warning: {message}"))

    def display_message(self, message: str, style: Optional[str] = None) -> None:
        """Displays a simple informational message using Rich, optionally styled."""
        logger.debug(f"Displaying message: {message} (style: {style})")
        if style:
            from rich.text import Text  # Local import is fine here.

            self.console.print(Text(message, style=style))
        else:
            self.console.print(message)
