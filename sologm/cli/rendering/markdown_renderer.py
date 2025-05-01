"""
Renderer implementation for generating Markdown output.
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from rich.console import Console

# Import necessary models for type hinting
from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene

# Import base class
from .base import Renderer

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

    def _print_markdown(self, text: str) -> None:
        """Prints text to the console without Rich highlighting or markup."""
        self.console.print(text, highlight=False, markup=False)

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

        self._print_markdown(output)

    def display_interpretation(
        self,
        interp: Interpretation,
        selected: bool = False,
        sequence: Optional[int] = None,
    ) -> None:
        """Displays a single oracle interpretation as Markdown."""
        logger.debug(
            f"Displaying interpretation as Markdown: {interp.id} (selected: "
            f"{selected}, sequence: {sequence})"
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

        self._print_markdown(output)

    def display_events_table(self, events: List[Event], scene: Scene) -> None:
        """Displays a list of events as a Markdown table."""
        logger.debug(
            f"Displaying events table as Markdown for scene '{scene.title}' "
            f"with {len(events)} events"
        )

        if not events:
            logger.debug(f"No events to display for scene '{scene.title}'")
            self._print_markdown(f"\nNo events in scene '{scene.title}'")
            return

        output_lines = []
        output_lines.append(f"### Events in Scene: {scene.title}")
        output_lines.append("")
        output_lines.append("| ID | Time | Source | Description |")
        output_lines.append("|---|---|---|---|")

        for event in events:
            # Use the full description directly
            description = event.description

            # Escape pipe characters within the description to avoid breaking the table
            description = description.replace("|", "\\|")

            # Format row
            row = (
                f"| `{event.id}` "
                f"| {event.created_at.strftime('%Y-%m-%d %H:%M')} "
                f"| {event.source_name} "
                f"| {description} |"
            )
            output_lines.append(row)

        self._print_markdown("\n".join(output_lines))

    def display_games_table(
        self, games: List[Game], active_game: Optional[Game] = None
    ) -> None:
        """Displays a list of games as a Markdown table."""
        logger.debug(f"Displaying games table as Markdown with {len(games)} games")
        logger.debug(f"Active game: {active_game.id if active_game else 'None'}")

        if not games:
            logger.debug("No games found to display")
            self._print_markdown(
                "No games found. Create one with 'sologm game create'."
            )
            return

        output_lines = []
        output_lines.append("### Games")
        output_lines.append("")
        output_lines.append("| ID | Name | Description | Acts | Scenes | Current |")
        output_lines.append("|---|---|---|---|---|---|")

        for game in games:
            # Get acts and scenes count (handle potential missing attributes)
            act_count = len(game.acts) if hasattr(game, "acts") else 0
            scene_count = (
                sum(len(act.scenes) for act in game.acts)
                if hasattr(game, "acts") and game.acts
                else (len(game.scenes) if hasattr(game, "scenes") else 0)
            )

            is_active = active_game and game.id == active_game.id
            active_marker = "✓" if is_active else ""
            game_name = f"**{game.name}**" if is_active else game.name

            # Escape pipe characters in description
            description = game.description.replace("|", "\\|")

            row = (
                f"| `{game.id}` "
                f"| {game_name} "
                f"| {description} "
                f"| {act_count} "
                f"| {scene_count} "
                f"| {active_marker} |"
            )
            output_lines.append(row)

        self._print_markdown("\n".join(output_lines))

    def display_scenes_table(
        self, scenes: List[Scene], active_scene_id: Optional[str] = None
    ) -> None:
        """Displays a list of scenes as a Markdown table."""
        logger.debug(f"Displaying scenes table as Markdown with {len(scenes)} scenes")
        logger.debug(
            f"Active scene ID: {active_scene_id if active_scene_id else 'None'}"
        )

        if not scenes:
            logger.debug("No scenes found to display")
            self._print_markdown(
                "No scenes found. Create one with 'sologm scene create'."
            )
            return

        output_lines = []
        output_lines.append("### Scenes")
        output_lines.append("")
        # Removed Status column
        output_lines.append("| ID | Title | Description | Current | Sequence |")
        output_lines.append("|---|---|---|---|---|")

        for scene in scenes:
            is_active = active_scene_id and scene.id == active_scene_id
            active_marker = "✓" if is_active else ""
            scene_title = f"**{scene.title}**" if is_active else scene.title

            # Escape pipe characters in description
            description = (scene.description or "").replace("|", "\\|")

            # Removed Status data
            row = (
                f"| `{scene.id}` "
                f"| {scene_title} "
                f"| {description} "
                f"| {active_marker} "
                f"| {scene.sequence} |"
            )
            output_lines.append(row)

        self._print_markdown("\n".join(output_lines))

    def display_game_info(
        self, game: Game, active_scene: Optional[Scene] = None
    ) -> None:
        """Displays detailed information about a specific game as Markdown."""
        logger.debug(
            f"Displaying game info as Markdown for {game.id} with active scene: "
            f"{active_scene.id if active_scene else 'None'}"
        )

        output_lines = []

        # Header
        output_lines.append(f"## {game.name} (`{game.slug}` / `{game.id}`)")
        output_lines.append("")

        # Description
        output_lines.append(game.description)
        output_lines.append("")

        # Metadata
        act_count = len(game.acts) if hasattr(game, "acts") else 0
        scene_count = (
            sum(len(act.scenes) for act in game.acts)
            if hasattr(game, "acts") and game.acts
            else (len(game.scenes) if hasattr(game, "scenes") else 0)
        )

        output_lines.append(f"*   **Created:** {game.created_at.strftime('%Y-%m-%d')}")
        output_lines.append(
            f"*   **Modified:** {game.modified_at.strftime('%Y-%m-%d')}"
        )
        output_lines.append(f"*   **Acts:** {act_count}")
        output_lines.append(f"*   **Scenes:** {scene_count}")

        if active_scene:
            output_lines.append(f"*   **Active Scene:** {active_scene.title}")

        self._print_markdown("\n".join(output_lines))

    def display_interpretation_set(
        self, interp_set: InterpretationSet, show_context: bool = True
    ) -> None:
        """Displays a set of oracle interpretations as Markdown."""
        logger.debug(
            f"Displaying interpretation set as Markdown: {interp_set.id} "
            f"(show_context: {show_context})"
        )
        output_lines = []

        if show_context:
            output_lines.append("### Oracle Interpretations")
            output_lines.append("")
            output_lines.append(f"**Context:** {interp_set.context}")
            output_lines.append(f"**Results:** {interp_set.oracle_results}")
            output_lines.append("")
            output_lines.append("---")
            self._print_markdown("\n".join(output_lines))
            output_lines = []  # Reset for interpretations

        # Display each interpretation
        for i, interp in enumerate(interp_set.interpretations, 1):
            # Call self.display_interpretation which handles its own printing
            self.display_interpretation(interp, sequence=i)
            self._print_markdown("")  # Add a newline between interpretations

        # Display instruction footer
        instruction = (
            f"Interpretation Set ID: `{interp_set.id}`\n"
            f"(Use 'sologm oracle select' to choose)"
        )
        self._print_markdown(instruction)

    def display_scene_info(self, scene: Scene) -> None:
        """Displays detailed information about a specific scene as Markdown."""
        logger.debug(f"Displaying scene info as Markdown for {scene.id}")
        output_lines = []

        # Header (removed status indicator)
        output_lines.append(f"### Scene {scene.sequence}: {scene.title} (`{scene.id}`)")
        output_lines.append("")

        # Description
        output_lines.append(scene.description or "*No description provided.*")
        output_lines.append("")

        # Metadata
        act_info = "Unknown Act"
        if hasattr(scene, "act") and scene.act:
            act_title = scene.act.title or "Untitled Act"
            act_info = f"Act {scene.act.sequence}: {act_title}"

        # Removed Status line
        output_lines.append(f"*   **Act:** {act_info}")
        output_lines.append(f"*   **Created:** {scene.created_at.strftime('%Y-%m-%d')}")
        output_lines.append(
            f"*   **Modified:** {scene.modified_at.strftime('%Y-%m-%d')}"
        )

        self._print_markdown("\n".join(output_lines))

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
        logger.debug(f"Displaying game status as Markdown for game {game.id}")
        output_lines = []

        # Game Header
        output_lines.append(
            f"## Game Status: {game.name} (`{game.slug}` / `{game.id}`)"
        )
        output_lines.append("")
        act_count = len(game.acts) if hasattr(game, "acts") else 0
        scene_count = (
            sum(len(act.scenes) for act in game.acts)
            if hasattr(game, "acts") and game.acts
            else 0
        )
        output_lines.append(f"*   **Acts:** {act_count}")
        output_lines.append(f"*   **Scenes:** {scene_count}")
        output_lines.append(f"*   **Created:** {game.created_at.strftime('%Y-%m-%d')}")
        output_lines.append("---")

        # Latest Act Info
        output_lines.append("### Latest Act")
        if latest_act:
            act_title = latest_act.title or "*Untitled Act*"
            output_lines.append(f"**Title:** {act_title} (Act {latest_act.sequence})")
            status = "**Active**" if is_act_active else "Inactive"
            output_lines.append(f"**Status:** {status}")
            if latest_act.summary:
                # Use full summary
                summary_preview = latest_act.summary
                output_lines.append(f"**Summary:** {summary_preview}")
        else:
            output_lines.append("*No acts found in this game.*")
        output_lines.append("---")

        # Scene Context (Latest & Previous)
        output_lines.append("### Scene Context")
        if latest_scene:
            scene_title = latest_scene.title or "*Untitled Scene*"
            output_lines.append(
                f"**Latest Scene:** {scene_title} (Scene {latest_scene.sequence})"
            )
            # Simplified status based only on is_scene_active flag
            if is_scene_active:
                status = "**Active**"
            else:
                status = "Inactive"
            output_lines.append(f"*   Status: {status}")

            if latest_scene.description:
                # Use full description for latest scene
                desc_preview = latest_scene.description
                output_lines.append(f"*   Description: {desc_preview}")

            # Previous Scene Logic
            prev_scene = None
            if scene_manager:
                try:
                    prev_scene = scene_manager.get_previous_scene(latest_scene.id)
                except Exception as e:
                    logger.warning(f"Could not retrieve previous scene: {e}")

            # Only add previous scene info if it exists
            if prev_scene:
                output_lines.append("\n**Previous Scene:**")  # Header for previous
                prev_title = prev_scene.title or "*Untitled Scene*"
                output_lines.append(
                    f"*   Title: {prev_title} (Scene {prev_scene.sequence})"
                )
                # Removed status line for previous scene
                if prev_scene.description:
                    # Use full description for previous scene
                    prev_desc_preview = prev_scene.description
                    output_lines.append(
                        f"*   Description: {prev_desc_preview}"
                    )  # Use list item
            # No "else" needed here, just don't print anything if no previous scene

        else:
            output_lines.append("*No scenes found in this context.*")
        output_lines.append("---")

        # Recent Events
        output_lines.append("### Recent Events")
        if recent_events:
            max_events_to_show = 5
            max_events_to_show = 5  # Keep limiting the *number* shown
            # for brevity
            for event in recent_events[:max_events_to_show]:
                source_name = event.source_name
                timestamp = event.created_at.strftime("%Y-%m-%d %H:%M")
                # Use full description here too, but escape pipes
                desc = event.description.replace("|", "\\|")
                output_lines.append(
                    f"*   `{timestamp}` (source: {source_name}): {desc}"
                )
            if len(recent_events) > max_events_to_show:
                output_lines.append(
                    f"*   ... ({len(recent_events) - max_events_to_show} "
                    "more not shown)"
                )
        else:
            output_lines.append("*No recent events.*")
        output_lines.append("---")

        # Oracle Status
        output_lines.append("### Oracle Status")
        pending_interp_set = None
        recent_interp_tuple = None
        if oracle_manager and latest_scene:
            try:
                current_set = oracle_manager.get_current_interpretation_set(
                    latest_scene.id
                )
                if current_set and not any(
                    i.is_selected for i in current_set.interpretations
                ):
                    pending_interp_set = current_set
                else:
                    recent_interp_tuple = oracle_manager.get_most_recent_interpretation(
                        latest_scene.id
                    )
            except Exception as e:
                logger.warning(f"Could not retrieve oracle status: {e}")

        if pending_interp_set:
            output_lines.append("**Pending Decision:**")
            # Use full context
            output_lines.append(f"*   Context: {pending_interp_set.context}")
            output_lines.append(
                f"*   Options: {len(pending_interp_set.interpretations)}"
            )
            output_lines.append("*   Use `sologm oracle select` to choose.")
        elif recent_interp_tuple:
            interp_set, selected_interp = recent_interp_tuple
            output_lines.append("**Last Decision:**")
            # Use full context
            output_lines.append(f"*   Context: {interp_set.context}")
            # Use full title
            output_lines.append(f"*   Selected: {selected_interp.title}")
        else:
            output_lines.append("*No pending or recent oracle interpretations.*")
        output_lines.append("---")

        # Recent Dice Rolls
        output_lines.append("### Recent Dice Rolls")
        if recent_rolls:
            max_rolls_to_show = 3  # Keep limiting the *number* shown for brevity
            for roll in recent_rolls[:max_rolls_to_show]:
                # Use full reason
                reason_text = f" (Reason: {roll.reason})" if roll.reason else ""
                timestamp = roll.created_at.strftime("%Y-%m-%d %H:%M")
                output_lines.append(
                    f"*   `{timestamp}`: {roll.notation} = **{roll.total}**{reason_text}"
                )
            if len(recent_rolls) > max_rolls_to_show:
                output_lines.append(
                    f"*   ... ({len(recent_rolls) - max_rolls_to_show} more not shown)"
                )
        else:
            output_lines.append("*No recent dice rolls.*")

        # Print final output
        self._print_markdown("\n".join(output_lines))

    def display_acts_table(
        self, acts: List[Act], active_act_id: Optional[str] = None
    ) -> None:
        """Displays a list of acts as a Markdown table."""
        logger.debug(f"Displaying acts table as Markdown with {len(acts)} acts")
        logger.debug(f"Active act ID: {active_act_id if active_act_id else 'None'}")

        if not acts:
            logger.debug("No acts found to display")
            self._print_markdown("No acts found. Create one with 'sologm act create'.")
            return

        output_lines = []
        output_lines.append("### Acts")
        output_lines.append("")
        output_lines.append("| ID | Seq | Title | Summary | Current |")
        output_lines.append("|---|---|---|---|---|")

        for act in acts:
            is_active = active_act_id and act.id == active_act_id
            active_marker = "✓" if is_active else ""
            act_title = act.title or "*Untitled Act*"
            act_title_display = f"**{act_title}**" if is_active else act_title
            summary = (act.summary or "").replace("|", "\\|")

            row = (
                f"| `{act.id}` "
                f"| {act.sequence} "
                f"| {act_title_display} "
                f"| {summary} "
                f"| {active_marker} |"
            )
            output_lines.append(row)

        self._print_markdown("\n".join(output_lines))

    def display_act_info(self, act: Act, game_name: str) -> None:
        """Displays detailed information about a specific act as Markdown."""
        logger.debug(f"Displaying act info as Markdown for {act.id}")
        output_lines = []

        # Header
        act_title = act.title or "*Untitled Act*"
        output_lines.append(f"## Act {act.sequence}: {act_title} (`{act.id}`)")
        output_lines.append("")

        # Summary
        if act.summary:
            output_lines.append(act.summary)
            output_lines.append("")

        # Metadata
        output_lines.append(f"*   **Game:** {game_name}")
        output_lines.append(f"*   **Created:** {act.created_at.strftime('%Y-%m-%d')}")
        output_lines.append(f"*   **Modified:** {act.modified_at.strftime('%Y-%m-%d')}")

        self._print_markdown("\n".join(output_lines))
        self._print_markdown("")  # Add a blank line before scenes

        # Display scenes in this act
        if hasattr(act, "scenes") and act.scenes:
            # Sort scenes by sequence for consistent output
            sorted_scenes = sorted(act.scenes, key=lambda s: s.sequence)
            # Use display_scenes_table for consistency
            # Need to determine the active scene ID within this act
            active_scene_id = next((s.id for s in sorted_scenes if s.is_active), None)
            self.display_scenes_table(sorted_scenes, active_scene_id=active_scene_id)
        else:
            # Print a specific message if no scenes exist
            self._print_markdown(f"### Scenes in Act {act.sequence}")
            self._print_markdown("")
            self._print_markdown("No scenes in this act yet.")

    def display_interpretation_sets_table(
        self, interp_sets: List[InterpretationSet]
    ) -> None:
        """Displays a table of interpretation sets as Markdown."""
        logger.debug(
            f"Displaying interpretation sets table as Markdown with {len(interp_sets)} sets"
        )

        if not interp_sets:
            self._print_markdown("No interpretation sets found.")
            return

        output_lines = []
        output_lines.append("### Oracle Interpretation Sets")
        output_lines.append("")
        output_lines.append(
            "| ID | Scene | Context | Oracle Results | Created | Status | Count |"
        )
        output_lines.append("|---|---|---|---|---|---|---|")

        for interp_set in interp_sets:
            scene_title = (
                interp_set.scene.title
                if hasattr(interp_set, "scene") and interp_set.scene
                else "Unknown"
            )
            # Use full context, escape pipes
            context = interp_set.context.replace("|", "\\|")
            # Use full oracle results, escape pipes
            oracle_results = interp_set.oracle_results.replace("|", "\\|")
            created_at = interp_set.created_at.strftime("%Y-%m-%d %H:%M")
            has_selection = any(
                interp.is_selected for interp in interp_set.interpretations
            )
            status = "Resolved" if has_selection else "Pending"
            interp_count = len(interp_set.interpretations)

            row = (
                f"| `{interp_set.id}` "
                f"| {scene_title} "
                f"| {context} "
                f"| {oracle_results} "
                f"| {created_at} "
                f"| {status} "
                f"| {interp_count} |"
            )
            output_lines.append(row)

        self._print_markdown("\n".join(output_lines))

    def display_interpretation_status(self, interp_set: InterpretationSet) -> None:
        """Displays the status of an interpretation set as Markdown."""
        logger.debug(
            f"Displaying interpretation status as Markdown for set {interp_set.id}"
        )
        output_lines = []

        output_lines.append("### Current Oracle Interpretation Status")
        output_lines.append("")
        output_lines.append(f"**Context:** {interp_set.context}")
        output_lines.append(f"**Results:** {interp_set.oracle_results}")
        output_lines.append("")
        output_lines.append(f"*   **Set ID:** `{interp_set.id}`")
        output_lines.append(f"*   **Retry Count:** {interp_set.retry_attempt}")
        resolved = any(interp.is_selected for interp in interp_set.interpretations)
        output_lines.append(f"*   **Resolved:** {resolved}")

        self._print_markdown("\n".join(output_lines))

    def display_act_ai_generation_results(
        self, results: Dict[str, str], act: Act
    ) -> None:
        """Displays the results generated by AI for an act as Markdown."""
        logger.debug(f"Displaying AI generation results as Markdown for act {act.id}")
        output_lines = ["### AI Generation Results", ""]

        if "title" in results and results["title"]:
            output_lines.append("**AI-Generated Title:**")
            output_lines.append(f"> {results['title']}")
            output_lines.append("")
            if act.title:
                output_lines.append("**Current Title:**")
                output_lines.append(f"> {act.title}")
                output_lines.append("")
            output_lines.append("---")
            output_lines.append("")

        if "summary" in results and results["summary"]:
            output_lines.append("**AI-Generated Summary:**")
            # Use blockquote for multi-line summary
            summary_lines = results["summary"].split("\n")
            for line in summary_lines:
                output_lines.append(f"> {line}")
            output_lines.append("")
            if act.summary:
                output_lines.append("**Current Summary:**")
                current_summary_lines = act.summary.split("\n")
                for line in current_summary_lines:
                    output_lines.append(f"> {line}")
                output_lines.append("")

        self._print_markdown("\n".join(output_lines))

    def display_act_completion_success(self, completed_act: Act) -> None:
        """Displays a success message upon act completion as Markdown."""
        logger.debug(
            f"Displaying act completion success as Markdown for act {completed_act.id}"
        )
        output_lines = []
        title_display = (
            f"'{completed_act.title}'" if completed_act.title else "*Untitled Act*"
        )

        output_lines.append(f"## Act {title_display} Completed Successfully!")
        output_lines.append("")
        output_lines.append(f"*   **ID:** `{completed_act.id}`")
        output_lines.append(f"*   **Sequence:** Act {completed_act.sequence}")
        output_lines.append("*   **Status:** Completed")
        output_lines.append("")

        if completed_act.title:
            output_lines.append("**Final Title:**")
            output_lines.append(f"> {completed_act.title}")
            output_lines.append("")

        if completed_act.summary:
            output_lines.append("**Final Summary:**")
            summary_lines = completed_act.summary.split("\n")
            for line in summary_lines:
                output_lines.append(f"> {line}")
            output_lines.append("")

        self._print_markdown("\n".join(output_lines).strip())

    def display_act_ai_feedback_prompt(self, console: Console) -> None:
        """Displays instructions for AI feedback as Markdown."""
        # Note: This doesn't actually prompt interactively in Markdown mode.
        logger.debug("Displaying AI feedback instructions as Markdown")
        output = (
            "\n---\n"
            "**Next Step:**\n"
            "Review the generated content above.\n"
            "*   To **accept** it, run: `sologm act accept`\n"
            "*   To **edit** it, run: `sologm act edit`\n"
            "*   To **regenerate** it, run: `sologm act generate --retry`\n"
            "---"
        )
        self._print_markdown(output)

    def display_act_edited_content_preview(
        self, edited_results: Dict[str, str]
    ) -> None:
        """Displays a preview of edited AI-generated content as Markdown."""
        logger.debug("Displaying edited content preview as Markdown")
        output_lines = ["\n### Preview of Edited Content:", ""]

        if "title" in edited_results:
            output_lines.append("**Edited Title:**")
            output_lines.append(f"> {edited_results['title']}")
            output_lines.append("")

        if "summary" in edited_results:
            output_lines.append("**Edited Summary:**")
            summary_lines = edited_results["summary"].split("\n")
            for line in summary_lines:
                output_lines.append(f"> {line}")
            output_lines.append("")

        self._print_markdown("\n".join(output_lines).strip())

    def display_error(self, message: str) -> None:
        """Displays an error message to the user as a Markdown blockquote."""
        logger.error(f"Displaying error as Markdown: {message}")
        # Use blockquote for errors
        self._print_markdown(f"> **Error:** {message}")

    def display_success(self, message: str) -> None:
        """Displays a success message as Markdown."""
        logger.debug(f"Displaying success as Markdown: {message}")
        self._print_markdown(f"**Success:** {message}")

    def display_warning(self, message: str) -> None:
        """Displays a warning message as Markdown."""
        logger.debug(f"Displaying warning as Markdown: {message}")
        self._print_markdown(f"**Warning:** {message}")

    def display_message(self, message: str, style: Optional[str] = None) -> None:
        """Displays a simple informational message as plain text (Markdown)."""
        # Style parameter is generally ignored in Markdown mode
        logger.debug(
            f"Displaying message as Markdown: {message} (style: {style} - ignored)"
        )
        self._print_markdown(message)
