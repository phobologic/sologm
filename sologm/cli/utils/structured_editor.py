"""Structured text block editor utilities for CLI commands."""

import logging
import re
import textwrap
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)


class EditorError(Exception):
    """Base exception for editor-related errors."""

    pass


class EditorAbortedError(EditorError):
    """Exception raised when the user aborts the editor session."""

    pass


class ValidationError(EditorError):
    """Exception raised when validation fails."""

    pass


class EditorStatus(Enum):
    """Represents the outcome of the structured editor session."""

    SAVED_MODIFIED = auto()  # Saved, content changed from original
    SAVED_UNCHANGED = auto()  # Saved, content identical to original
    ABORTED = auto()  # User explicitly cancelled/quit editor without saving
    VALIDATION_ERROR = auto()  # Validation failed after retries
    EDITOR_ERROR = auto()  # Failed to launch editor or other editor issue


@dataclass
class EditorConfig:
    """Configuration for editor behavior."""

    edit_message: str = "Editing data:"
    success_message: str = "Data updated successfully."
    cancel_message: str = "Data unchanged."
    error_message: str = "Could not open editor"
    max_retries: int = 2


@dataclass
class FieldConfig:
    """Configuration for a field in the structured editor."""

    name: str
    display_name: str
    help_text: Optional[str] = None
    required: bool = False
    multiline: bool = True
    enum_values: Optional[List[str]] = None  # Available options for this field


@dataclass
class StructuredEditorConfig:
    """Configuration for structured text editor."""

    fields: List[FieldConfig] = field(default_factory=list)
    wrap_width: int = 70  # Default width for text wrapping


class TextFormatter:
    """Handles formatting data into structured text."""

    @staticmethod
    def wrap_text(text: str, width: int = 70, indent: str = "  ") -> List[str]:
        """Wrap text at specified width with proper indentation.

        Args:
            text: Text to wrap
            width: Maximum width for each line
            indent: String to use for indentation of continuation lines

        Returns:
            List of wrapped lines
        """
        wrapped_lines = []
        for line in text.split("\n"):
            # If the line is already short enough, just add it
            if len(line) <= width:
                wrapped_lines.append(line)
            else:
                # Wrap the line and add proper indentation for continuation lines
                wrapped = textwrap.wrap(line, width=width)
                for i, wrapped_line in enumerate(wrapped):
                    if i == 0:
                        # First line has no additional indent
                        wrapped_lines.append(wrapped_line)
                    else:
                        # Continuation lines get indentation
                        wrapped_lines.append(f"{indent}{wrapped_line}")

        return wrapped_lines

    def format_structured_text(
        self,
        data: Dict[str, Any],
        config: StructuredEditorConfig,
        context_info: str = "",
        original_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format data as structured text blocks.

        Args:
            data: Dictionary of data to format
            config: Editor configuration
            context_info: Context information to include at the top
            original_data: Optional original data for reference in edit mode

        Returns:
            Formatted text with structured blocks
        """
        lines = []
        wrap_width = config.wrap_width

        # Add context information with hash marks and proper wrapping
        if context_info:
            # Split context info into sections
            sections = context_info.split("\n\n")
            for section in sections:
                if section.strip():
                    # Wrap each section and add comment markers
                    for line in self.wrap_text(section, width=wrap_width):
                        lines.append(f"# {line}")
                    lines.append("")  # Empty line after each section

        # Add each field as a structured block
        for field_config in config.fields:
            field_name = field_config.name
            display_name = field_config.display_name.upper()

            # Add help text as a comment with wrapping
            if field_config.help_text:
                for line in self.wrap_text(field_config.help_text, width=wrap_width):
                    lines.append(f"# {line}")

            # Add enum values as options if provided
            if field_config.enum_values:
                options_text = (
                    f"Available options: {', '.join(field_config.enum_values)}"
                )
                for line in self.wrap_text(options_text, width=wrap_width):
                    lines.append(f"# {line}")

            # Add required indicator if the field is required
            if field_config.required:
                lines.append("# (Required)")

            # Add original value as a comment if we're in edit mode
            if original_data and field_name in original_data:
                original_value = original_data[field_name]
                if original_value:
                    lines.append("# Original value:")
                    # Wrap each line of the original value
                    for orig_line in str(original_value).split("\n"):
                        for wrapped_line in self.wrap_text(orig_line, width=wrap_width):
                            lines.append(f"# {wrapped_line}")
                    lines.append("#")

            # Add field header
            lines.append(f"--- {display_name} ---")

            # Add field value or empty line
            value = data.get(field_name, "")
            if value:
                # For multiline values, ensure each line is included
                for line in str(value).split("\n"):
                    lines.append(line)
            else:
                # Add an empty line for empty fields
                lines.append("")

            # Add field footer
            lines.append(f"--- END {display_name} ---")
            lines.append("")  # Empty line between fields

        return "\n".join(lines)


class TextParser:
    """Handles parsing structured text into data."""

    def parse_structured_text(
        self, text: str, config: StructuredEditorConfig
    ) -> Dict[str, Any]:
        """Parse structured text blocks into a dictionary.

        Args:
            text: Structured text to parse
            config: Editor configuration

        Returns:
            Dictionary of parsed data

        Raises:
            ValidationError: If validation fails
        """
        result = {}

        # Create a mapping of display names to field names
        field_map = {field.display_name.upper(): field.name for field in config.fields}

        # Find all blocks using regex
        pattern = r"--- ([A-Z ]+) ---\n(.*?)--- END \1 ---"
        matches = re.findall(pattern, text, re.DOTALL)

        # Process each matched block
        for display_name, content in matches:
            if display_name in field_map:
                field_name = field_map[display_name]
                # Store the content, stripping trailing whitespace from each line
                # but preserving line breaks
                cleaned_content = "\n".join(
                    line.rstrip() for line in content.split("\n")
                ).strip()
                result[field_name] = cleaned_content

        # Validate required fields
        missing_fields = []
        for f in config.fields:
            if f.required and (f.name not in result or not result[f.name].strip()):
                missing_fields.append(f.display_name)

        if missing_fields:
            field_list = ", ".join(missing_fields)
            raise ValidationError(f"Required field(s) {field_list} cannot be empty.")

        # Validate enum values
        for f in config.fields:
            if (
                f.enum_values
                and f.name in result
                and result[f.name]
                and result[f.name] not in f.enum_values
            ):
                raise ValidationError(
                    f"Invalid value for {f.display_name}. "
                    f"Must be one of: {', '.join(f.enum_values)}"
                )

        return result


class EditorStrategy(Protocol):
    """Protocol for editor strategies."""

    def edit_text(
        self,
        text: str,
        console: Optional[Console] = None,
        message: str = "Edit the text below:",
        success_message: str = "Text updated.",
        cancel_message: str = "Text unchanged.",
        error_message: str = "Could not open editor.",
    ) -> Tuple[str, bool]:
        """Open an editor to modify text.

        Args:
            text: The initial text to edit
            console: Optional Rich console for output
            message: Message to display before editing
            success_message: Message to display on successful edit
            cancel_message: Message to display when edit is canceled
            error_message: Message to display when editor fails to open

        Returns:
            Tuple of (edited_text, was_modified)
        """
        ...


class ClickEditorStrategy:
    """Editor strategy using click.edit."""

    def edit_text(
        self,
        text: str,
        console: Optional[Console] = None,
        message: str = "Edit the text below:",
        success_message: str = "Text updated.",
        cancel_message: str = "Text unchanged.",
        error_message: str = "Could not open editor.",
    ) -> Tuple[str, bool]:
        """Open an editor to modify text using click.edit.

        Args:
            text: The initial text to edit
            console: Optional Rich console for output
            message: Message to display before editing
            success_message: Message to display on successful edit
            cancel_message: Message to display when edit is canceled
            error_message: Message to display when editor fails to open

        Returns:
            Tuple of (edited_text, was_modified)
        """
        if console:
            # Display message before opening editor
            console.print(f"\n[bold blue]{message}[/bold blue]")
            # The editor will show the text, no need to print it here.

        try:
            new_text = click.edit(text)

            if new_text is None:
                # User aborted the editor session
                raise EditorAbortedError("Editor session aborted by user.")
            else:
                # User saved the editor
                edited_text = new_text
                content_changed = edited_text != text
                # Success/cancel messages are handled by StructuredEditor after validation
                return edited_text, content_changed

        except click.UsageError as e:
            logger.error(f"Editor error: {e}", exc_info=True)
            if console:
                console.print(f"\n[red]{error_message}: {str(e)}[/red]")
                console.print(
                    "[yellow]To use this feature, set the EDITOR environment "
                    "variable to your preferred text editor.[/yellow]"
                )
            # Raise a general editor error if click fails
            raise EditorError(f"Failed to launch editor: {e}") from e


class UIManager:
    """Manages UI interactions."""

    def display_validation_error(self, console: Console, error: Exception) -> None:
        """Display a validation error in a user-friendly way.

        Args:
            console: Rich console for output
            error: The exception to display
        """
        error_msg = str(error)

        # Create a panel with the error message
        panel = Panel(
            Text.from_markup(f"[bold red]Error:[/] {error_msg}"),
            title="Validation Failed",
            border_style="red",
        )

        console.print(panel)
        console.print(
            "[yellow]The editor will reopen so you can fix this issue.[/yellow]"
        )


class StructuredEditor:
    """Main class for structured text editing."""

    def __init__(
        self,
        config: StructuredEditorConfig,
        editor_config: Optional[EditorConfig] = None,
        formatter: Optional[TextFormatter] = None,
        parser: Optional[TextParser] = None,
        editor_strategy: Optional[EditorStrategy] = None,
        ui_manager: Optional[UIManager] = None,
    ):
        """Initialize the structured editor.

        Args:
            config: Configuration for the structured editor
            editor_config: Configuration for editor behavior
            formatter: Text formatter instance
            parser: Text parser instance
            editor_strategy: Strategy for text editing
            ui_manager: UI manager instance
        """
        self.config = config
        self.editor_config = editor_config or EditorConfig()
        self.formatter = formatter or TextFormatter()
        self.parser = parser or TextParser()
        self.editor_strategy = editor_strategy or ClickEditorStrategy()
        self.ui_manager = ui_manager or UIManager()

    def edit_data(
        self,
        data: Optional[Dict[str, Any]],
        console: Console,
        context_info: str = "",
        is_new: bool = False,
        original_data_for_comments: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], EditorStatus]:
        """Edit data using structured text blocks in an external editor.

        Args:
            data: Dictionary of data to edit (None or empty dict for new items).
                  This is the *original* data for comparison and return on failure.
            console: Rich console for output
            context_info: Context information to include at the top
            is_new: Whether this is a new item (affects validation and comments).
            original_data_for_comments: Optional data to show as comments (e.g., AI results).

        Returns:
            Tuple of (result_data, status).
            `result_data` contains:
                - The parsed data if status is SAVED_MODIFIED or SAVED_UNCHANGED.
                - The original input `data` (or empty dict) otherwise.
            `status` is an EditorStatus enum indicating the outcome.
        """
        # Store original data for return on failure/abort
        original_data = {} if data is None else data.copy()
        # Create a working copy for the editor
        working_data = original_data.copy()

        # Determine what data to show as comments (original value)
        # If original_data_for_comments is provided, use that.
        # Otherwise, if not a new item, use the original `data`.
        comments_data = (
            original_data_for_comments
            if original_data_for_comments is not None
            else (data if not is_new else None)
        )

        # Format the initial text for the editor
        structured_text = self.formatter.format_structured_text(
            working_data, self.config, context_info, comments_data
        )

        # Track retry attempts
        retry_count = 0
        max_retries = self.editor_config.max_retries

        while retry_count <= max_retries:
            current_message = self.editor_config.edit_message
            if retry_count > 0:
                current_message = f"Editing data (Retry {retry_count}/{max_retries}):"

            try:
                # Open editor using the strategy
                edited_text, was_content_modified = self.editor_strategy.edit_text(
                    structured_text,
                    console=console,
                    message=current_message,
                    # Success/cancel messages handled below after validation/parsing
                )

                # --- Editor was SAVED ---
                try:
                    # Parse and validate the edited text
                    parsed_data = self.parser.parse_structured_text(
                        edited_text, self.config
                    )

                    # --- Validation Passed ---
                    data_changed_compared_to_original = parsed_data != original_data

                    if data_changed_compared_to_original:
                        console.print(
                            f"[green]{self.editor_config.success_message}[/green]"
                        )
                        return parsed_data, EditorStatus.SAVED_MODIFIED
                    else:
                        # Saved, but no effective change compared to original data
                        console.print(
                            f"[yellow]{self.editor_config.cancel_message}[/yellow]"
                        )  # Or "No changes detected."
                        # Return the parsed data (which is same as original), but signal unchanged
                        return parsed_data, EditorStatus.SAVED_UNCHANGED

                except ValidationError as e:
                    # --- Validation Failed ---
                    self.ui_manager.display_validation_error(console, e)
                    if retry_count < max_retries:
                        retry_count += 1
                        structured_text = edited_text  # Keep user's edits for retry
                        continue  # Go to next retry iteration
                    else:
                        console.print(
                            "[bold red]Maximum retry attempts reached. "
                            "Edit cancelled.[/bold red]"
                        )
                        # Return original data, validation failed
                        return original_data, EditorStatus.VALIDATION_ERROR

            except EditorAbortedError:
                # --- Editor was ABORTED ---
                console.print(f"\n[yellow]{self.editor_config.cancel_message}[/yellow]")
                # Return original data, aborted
                return original_data, EditorStatus.ABORTED

            except (
                EditorError
            ) as e:  # Catch errors from editor strategy (e.g., UsageError)
                # Error message already printed by strategy or here if needed
                logger.error(f"Editor strategy failed: {e}", exc_info=True)
                # Error message already printed by strategy
                # Return original data, editor error
                return original_data, EditorStatus.EDITOR_ERROR

        # Fallback if loop finishes unexpectedly (shouldn't happen)
        logger.error("Structured editor loop finished unexpectedly.")
        return original_data, EditorStatus.EDITOR_ERROR


# Backward compatibility functions
def wrap_text(text: str, width: int = 70, indent: str = "  ") -> List[str]:
    """Wrap text at specified width with proper indentation (compatibility function)."""
    return TextFormatter().wrap_text(text, width, indent)


def format_structured_text(
    data: Dict[str, Any],
    config: StructuredEditorConfig,
    context_info: str = "",
    original_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Format data as structured text blocks (compatibility function)."""
    return TextFormatter().format_structured_text(
        data, config, context_info, original_data
    )


def parse_structured_text(text: str, config: StructuredEditorConfig) -> Dict[str, Any]:
    """Parse structured text blocks into a dictionary (compatibility function)."""
    return TextParser().parse_structured_text(text, config)


def edit_text(
    text: str,
    console: Optional[Console] = None,
    message: str = "Edit the text below:",
    success_message: str = "Text updated.",
    cancel_message: str = "Text unchanged.",
    error_message: str = "Could not open editor.",
) -> Tuple[str, bool]:
    """Open an editor to modify text (compatibility function)."""
    return ClickEditorStrategy().edit_text(
        text, console, message, success_message, cancel_message, error_message
    )


def display_validation_error(console: Console, error: Exception) -> None:
    """Display a validation error in a user-friendly way (compatibility function)."""
    UIManager().display_validation_error(console, error)


def edit_structured_data(
    data: Optional[Dict[str, Any]],
    console: Console,
    config: StructuredEditorConfig,
    context_info: str = "",
    editor_config: Optional[EditorConfig] = None,
    is_new: bool = False,
    # Add original_data_for_comments if needed
    original_data_for_comments: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], EditorStatus]:
    """Edit data using structured text blocks (compatibility function)."""
    editor = StructuredEditor(config, editor_config)
    # Pass original_data_for_comments if provided
    return editor.edit_data(
        data, console, context_info, is_new, original_data_for_comments
    )


def get_event_context_header(
    game_name: str,
    scene_title: str,
    scene_description: str,
    recent_events: Optional[List[Any]] = None,
    act_info: Optional[str] = None,
) -> str:
    """Create a context header for event editing.

    Args:
        game_name: Name of the current game
        scene_title: Title of the current scene
        scene_description: Description of the current scene
        recent_events: Optional list of recent events
        act_info: Optional act information string

    Returns:
        Formatted context header as a string
    """
    # Create context information for the editor
    context_info = [
        f"Game: {game_name}",
    ]

    # Add act information if provided
    if act_info:
        context_info.append(act_info)

    context_info.extend(
        [
            f"Scene: {scene_title}",
            "",
            "Scene Description:",
            scene_description,
            "",
        ]
    )

    # Add recent events if any
    if recent_events:
        context_info.append("Recent Events:")
        for i, event in enumerate(recent_events, 1):
            context_info.append(f"{i}. [{event.source.name}] {event.description}")
        context_info.append("")

    return "\n".join(context_info)
