"""Structured text block editor utilities for CLI commands."""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)


class EditorError(Exception):
    """Base exception for editor-related errors."""

    pass


class ValidationError(EditorError):
    """Exception raised when validation fails."""

    pass


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


@dataclass
class StructuredEditorConfig:
    """Configuration for structured text editor."""

    fields: List[FieldConfig] = field(default_factory=list)


def format_structured_text(
    data: Dict[str, Any],
    config: StructuredEditorConfig,
    context_info: str = "",
) -> str:
    """Format data as structured text blocks.

    Args:
        data: Dictionary of data to format
        config: Editor configuration
        context_info: Context information to include at the top

    Returns:
        Formatted text with structured blocks
    """
    lines = []

    # Add context information with hash marks
    if context_info:
        for line in context_info.split("\n"):
            lines.append(f"# {line}")
        lines.append("")  # Empty line after context

    # Add each field as a structured block
    for field_config in config.fields:
        field_name = field_config.name
        display_name = field_config.display_name.upper()

        # Add help text as a comment
        if field_config.help_text:
            lines.append(f"# {field_config.help_text}")

        # Add required indicator if the field is required
        if field_config.required:
            lines.append(f"# (Required)")

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


def parse_structured_text(text: str, config: StructuredEditorConfig) -> Dict[str, Any]:
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
    for field in config.fields:
        if field.required and (
            field.name not in result or not result[field.name].strip()
        ):
            missing_fields.append(field.display_name)

    if missing_fields:
        field_list = ", ".join(missing_fields)
        raise ValidationError(f"Required field(s) {field_list} cannot be empty.")

    return result


def edit_text(
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
    if console:
        console.print(f"\n[bold blue]{message}[/bold blue]")
        console.print(text)

    try:
        new_text = click.edit(text)

        # If the user saved changes (didn't abort)
        if new_text is not None:
            edited_text = new_text
            if edited_text != text:
                if console:
                    console.print(f"\n[green]{success_message}[/green]")
                return edited_text, True
            else:
                if console:
                    console.print(f"\n[yellow]{cancel_message}[/yellow]")
                return text, False
        else:
            if console:
                console.print(f"\n[yellow]{cancel_message}[/yellow]")
            return text, False

    except click.UsageError as e:
        logger.error(f"Editor error: {e}")
        if console:
            console.print(f"\n[red]{error_message}: {str(e)}[/red]")
            console.print(
                "[yellow]To use this feature, set the EDITOR environment "
                "variable to your preferred text editor.[/yellow]"
            )
        return text, False


def display_validation_error(console: Console, error: Exception) -> None:
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
    console.print("[yellow]The editor will reopen so you can fix this issue.[/yellow]")


def edit_structured_data(
    data: Optional[Dict[str, Any]],
    console: Console,
    config: StructuredEditorConfig,
    context_info: str = "",
    editor_config: Optional[EditorConfig] = None,
) -> Tuple[Dict[str, Any], bool]:
    """Edit data using structured text blocks in an external editor.

    Args:
        data: Dictionary of data to edit (None or empty dict for new items)
        console: Rich console for output
        config: Configuration for structured text editor
        context_info: Context information to include at the top
        editor_config: Configuration for editor behavior

    Returns:
        Tuple of (edited_data, was_modified)
    """
    # Use default configurations if none provided
    editor_config = editor_config or EditorConfig()

    # Create a working copy of data or initialize empty dict if None
    working_data = {} if data is None else data.copy()

    # Format the data as structured text
    structured_text = format_structured_text(working_data, config, context_info)

    # Track retry attempts
    retry_count = 0
    max_retries = editor_config.max_retries

    while retry_count <= max_retries:
        # Prepare message based on retry status
        current_message = editor_config.edit_message
        if retry_count > 0:
            current_message = f"Editing data (Retry {retry_count}/{max_retries}):"

        # Open editor
        edited_text, was_modified = edit_text(
            structured_text,
            console=console,
            message=current_message,
            success_message="Validating your changes...",
            cancel_message=editor_config.cancel_message,
            error_message=editor_config.error_message,
        )

        # If user canceled, return original data
        if not was_modified:
            if retry_count > 0:
                console.print(
                    "[yellow]No additional changes made. Canceling edit.[/yellow]"
                )
            return data, False

        try:
            # Parse and validate the edited text
            parsed_data = parse_structured_text(edited_text, config)

            # If we got here, validation passed
            console.print(f"[green]{editor_config.success_message}[/green]")
            return parsed_data, True

        except ValidationError as e:
            # Display the error and retry if we haven't exceeded max retries
            display_validation_error(console, e)

            if retry_count < max_retries:
                retry_count += 1
                structured_text = edited_text  # Keep user's edits for the retry
            else:
                console.print(
                    "[bold red]Maximum retry attempts reached. Canceling edit.[/bold red]"
                )
                return data, False

    # This should never be reached
    return data, False


def get_event_context_header(
    game_name: str,
    scene_title: str,
    scene_description: str,
    recent_events: Optional[List[Any]] = None,
) -> str:
    """Create a context header for event editing.

    Args:
        game_name: Name of the current game
        scene_title: Title of the current scene
        scene_description: Description of the current scene
        recent_events: Optional list of recent events

    Returns:
        Formatted context header as a string
    """
    # Create context information for the editor
    context_info = (
        f"Game: {game_name}\n"
        f"Scene: {scene_title}\n\n"
        f"Scene Description:\n{scene_description}\n\n"
    )

    # Add recent events if any
    if recent_events:
        context_info += "Recent Events:\n"
        for i, event in enumerate(recent_events, 1):
            context_info += f"{i}. [{event.source}] {event.description}\n"
        context_info += "\n"

    return context_info
