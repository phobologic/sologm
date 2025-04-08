"""Editor utilities for CLI commands."""

import contextlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
)

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)


# Custom exceptions for better error handling
class EditorError(Exception):
    """Base exception for editor-related errors."""

    pass


class YamlValidationError(EditorError):
    """Base exception for YAML validation errors."""

    pass


class RequiredFieldError(YamlValidationError):
    """Exception raised when required fields are missing."""

    def __init__(self, missing_fields: List[str]):
        self.missing_fields = missing_fields
        field_list = ", ".join(f"'{f}'" for f in missing_fields)
        super().__init__(f"Required field(s) {field_list} cannot be empty.")


class YamlParseError(YamlValidationError):
    """Exception raised when YAML parsing fails."""

    pass


class EditorMode(Enum):
    """Enum for different editor modes."""

    CREATE = "create"
    EDIT = "edit"


@dataclass
class EditorConfig:
    """Configuration for editor behavior."""

    edit_message: str = "Editing data:"
    success_message: str = "Data updated successfully."
    cancel_message: str = "Data unchanged."
    error_message: str = "Could not open editor"
    max_retries: int = 2


@dataclass
class YamlConfig:
    """Configuration for YAML editing."""

    field_comments: Dict[str, str] = field(default_factory=dict)
    literal_block_fields: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)


def get_event_context_header(
    game_name: str,
    scene_title: str,
    scene_description: str,
    recent_events: Optional[List] = None,
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


# Custom class for handling multi-line strings in YAML
class MultiLineString(str):
    """String subclass that forces YAML to use literal block style (|)."""

    pass


# Custom YAML representer for MultiLineString
def _represent_multiline_string(dumper, data):
    """Tell YAML to use the literal block style (|) for MultiLineString objects."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


# Register the custom representer with PyYAML
yaml.add_representer(MultiLineString, _represent_multiline_string)


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
            edited_text = new_text.strip()
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


def prepare_working_data(
    data: Optional[Dict[str, Any]], yaml_config: YamlConfig
) -> Dict[str, Any]:
    """Prepare working data for editing.

    Args:
        data: Original data or None
        yaml_config: YAML configuration

    Returns:
        Working copy of data with all necessary fields
    """
    # Create a working copy of data or initialize empty dict if None
    working_data = {} if data is None else data.copy()

    # Ensure all fields from field_comments exist in working_data
    for field in yaml_config.field_comments:
        if field not in working_data:
            working_data[field] = ""

    # Process literal block fields for the working data
    for field in yaml_config.literal_block_fields:
        if field in working_data and working_data[field]:
            # Convert to MultiLineString to force literal block style
            working_data[field] = MultiLineString(working_data[field])

    return working_data


def build_header_comment(
    context_info: str,
    data: Optional[Dict[str, Any]],
    mode: EditorMode,
    yaml_config: YamlConfig,
) -> str:
    """Build the header comment for the YAML editor.

    Args:
        context_info: Context information to include
        data: Original data or None
        mode: Editor mode (create or edit)
        yaml_config: YAML configuration

    Returns:
        Formatted header comment
    """
    header_comment = context_info

    # Add appropriate instruction based on action type
    if mode == EditorMode.CREATE:
        header_comment += "Enter the new details below:"
    else:
        header_comment += "Edit the details below:"

        # Only add original data reference for edit mode
        if data:
            # Create a copy of the original data for the reference block
            original_data_for_display = data.copy()

            # Convert literal block fields in the original data for display
            for field in yaml_config.literal_block_fields:
                if (
                    field in original_data_for_display
                    and original_data_for_display[field]
                ):
                    original_data_for_display[field] = MultiLineString(
                        original_data_for_display[field]
                    )

            # Add original data reference for edit actions
            original_data_yaml = yaml.dump(
                original_data_for_display, sort_keys=False, default_flow_style=False
            )
            original_data_lines = original_data_yaml.split("\n")

            header_comment += "\n\n# Original values (for reference):\n"
            for line in original_data_lines:
                header_comment += f"# {line}\n"
            header_comment += "#\n"

    return header_comment


def prepare_yaml_for_editing(
    data: Dict[str, Any],
    header_comment: str = "Edit the details below:",
    field_comments: Optional[Dict[str, str]] = None,
    literal_block_fields: Optional[List[str]] = None,
) -> str:
    """Prepare a YAML string for editing with comments and formatting.

    Args:
        data: Dictionary of data to convert to YAML
        header_comment: Comment to place at the top of the file
        field_comments: Optional dict mapping field names to comment strings
        literal_block_fields: List of fields that should use YAML's literal block style
                             (Note: This is kept for backward compatibility but
                              fields should be converted to MultiLineString before calling)

    Returns:
        Formatted YAML string with comments
    """
    # Create a copy of the data to modify
    processed_data = data.copy()

    # Process literal block fields if provided (for backward compatibility)
    if literal_block_fields:
        for field in literal_block_fields:
            if field in processed_data and processed_data[field]:
                # Convert to MultiLineString to force literal block style
                processed_data[field] = MultiLineString(processed_data[field])

    # Convert to YAML
    yaml_text = yaml.dump(processed_data, sort_keys=False, default_flow_style=False)

    # Add comments
    lines = [f"# {line}" for line in header_comment.split("\n")]

    # Add field-specific comments if provided
    if field_comments:
        yaml_lines = yaml_text.split("\n")
        result_lines = []

        for line in yaml_lines:
            for field, comment in field_comments.items():
                if line.startswith(f"{field}:"):
                    result_lines.append(f"\n# {comment}")
                    break
            result_lines.append(line)

        yaml_text = "\n".join(result_lines)

    # Combine header comments with YAML content
    return "\n".join(lines) + "\n\n" + yaml_text


def validate_yaml_data(
    data: Any, required_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Validate the YAML data structure and required fields.

    Args:
        data: The parsed YAML data
        required_fields: List of fields that cannot be empty

    Returns:
        Validated data dictionary

    Raises:
        YamlValidationError: If validation fails
    """
    # Validate the structure
    if not isinstance(data, dict):
        raise YamlValidationError("Invalid YAML format. Expected a dictionary.")

    # Validate required fields
    if required_fields:
        missing_fields = [
            field
            for field in required_fields
            if field not in data or not str(data.get(field, "")).strip()
        ]
        if missing_fields:
            raise RequiredFieldError(missing_fields)

    return data


def parse_yaml_content(content: str) -> Dict[str, Any]:
    """Parse YAML content, removing comments.

    Args:
        content: YAML content to parse

    Returns:
        Parsed YAML data

    Raises:
        YamlParseError: If parsing fails
    """
    # Remove comment lines before parsing
    yaml_text = "\n".join(
        [line for line in content.split("\n") if not line.strip().startswith("#")]
    )

    try:
        # Parse the edited YAML
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        # Get a user-friendly error message
        error_msg = str(e)
        # Make the error message more user-friendly if possible
        if "could not find expected ':'" in error_msg:
            error_msg = "Missing colon after a field name"
        elif "found character '\\t'" in error_msg:
            error_msg = "Tab character found. Please use spaces for indentation"

        raise YamlParseError(f"YAML parsing error: {error_msg}")


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


@contextlib.contextmanager
def yaml_edit_session(
    console: Console, config: EditorConfig
) -> Iterator[Tuple[int, Optional[str]]]:
    """Context manager for handling YAML editing sessions with retries.

    Args:
        console: Rich console for output
        config: Editor configuration

    Yields:
        Tuple of (retry_count, current_error)
    """
    retry_count = 0
    current_error = None

    while retry_count <= config.max_retries:
        try:
            yield retry_count, current_error
            break  # Success, exit the loop
        except YamlValidationError as e:
            current_error = str(e)
            display_validation_error(console, e)

            if retry_count < config.max_retries:
                retry_count += 1
            else:
                console.print(
                    "[bold red]Maximum retry attempts reached. Canceling edit.[/bold red]"
                )
                raise EditorError("Failed to validate YAML after multiple attempts")

    # If we've exhausted retries
    if retry_count > config.max_retries:
        console.print(
            "[bold red]Failed to parse YAML after multiple attempts. No changes made.[/bold red]"
        )
        raise EditorError("Failed to parse YAML after multiple attempts")


def prepare_retry_text(current_text: str, error: str, original_header: str) -> str:
    """Prepare text for retry with error information.

    Args:
        current_text: Current text in the editor
        error: Error message to display
        original_header: Original header comment

    Returns:
        Text prepared for retry
    """
    error_header = (
        f"ERROR: {error}\n\n"
        "Please fix the YAML format and try again.\n"
        "Common issues include:\n"
        "- Incorrect indentation\n"
        "- Missing or extra colons\n"
        "- Unbalanced quotes\n\n"
        f"{original_header}"
    )

    # Extract user's edited content (non-comment lines)
    user_lines = [
        line for line in current_text.split("\n") if not line.strip().startswith("#")
    ]

    # Construct new error header
    error_header_lines = []
    for line in error_header.split("\n"):
        error_header_lines.append(
            f"# {line}" if not line.startswith("#") and line.strip() else line
        )

    # Combine everything, ensuring proper spacing
    return "\n".join(error_header_lines + [""] + user_lines)


def edit_yaml_data(
    data: Optional[Dict[str, Any]],
    console: Console,
    context_info: str = "",
    field_comments: Optional[Dict[str, str]] = None,
    literal_block_fields: Optional[List[str]] = None,
    required_fields: Optional[List[str]] = None,
    edit_message: str = "Editing data:",
    success_message: str = "Data updated successfully.",
    cancel_message: str = "Data unchanged.",
    error_message: str = "Could not open editor",
    max_retries: int = 2,
) -> Tuple[Dict[str, Any], bool]:
    """Edit data using YAML format in an external editor.

    Args:
        data: Dictionary of data to edit (None or empty dict for new items)
        console: Rich console for output
        context_info: Context information to include in the header (game, scene, etc.)
        field_comments: Dict mapping field names to comment strings
        literal_block_fields: List of fields that should use YAML's literal block style
        required_fields: List of fields that cannot be empty
        edit_message: Message to display before editing
        success_message: Message to display on successful edit
        cancel_message: Message to display when edit is canceled
        error_message: Message to display when editor fails to open
        max_retries: Maximum number of retries for parsing errors

    Returns:
        Tuple of (edited_data, was_modified)
    """
    # Create configuration objects
    editor_config = EditorConfig(
        edit_message=edit_message,
        success_message=success_message,
        cancel_message=cancel_message,
        error_message=error_message,
        max_retries=max_retries,
    )

    yaml_config = YamlConfig(
        field_comments=field_comments or {},
        literal_block_fields=literal_block_fields or [],
        required_fields=required_fields or [],
    )

    # Determine if we're creating or editing based on data
    mode = EditorMode.CREATE if data is None or not data else EditorMode.EDIT

    # Prepare working data
    working_data = prepare_working_data(data, yaml_config)

    # Build header comment
    header_comment = build_header_comment(context_info, data, mode, yaml_config)

    # Prepare YAML for editing
    yaml_text = prepare_yaml_for_editing(
        working_data, header_comment, yaml_config.field_comments
    )

    # Track if any edits were made
    any_edits_made = False
    current_text = yaml_text

    # Save the original header to preserve it across retries
    original_header = header_comment

    try:
        with yaml_edit_session(console, editor_config) as (retry_count, current_error):
            # Prepare message with error info if this is a retry
            current_message = editor_config.edit_message

            if current_error:
                current_message = (
                    f"Editing data (Retry {retry_count}/{editor_config.max_retries}):"
                )
                current_text = prepare_retry_text(
                    current_text, current_error, original_header
                )

            # Open editor
            edited_text, was_modified = edit_text(
                current_text,
                console=console,
                message=current_message,
                success_message="Validating your changes...",
                cancel_message=editor_config.cancel_message,
                error_message=editor_config.error_message,
            )

            # Track if any edits were made in any iteration
            any_edits_made = any_edits_made or was_modified

            # If user canceled, return original data
            if not was_modified:
                if retry_count > 0:
                    console.print(
                        "[yellow]No additional changes made. Canceling edit.[/yellow]"
                    )
                return data, False

            # Parse and validate the edited YAML
            parsed_data = parse_yaml_content(edited_text)
            validated_data = validate_yaml_data(
                parsed_data, yaml_config.required_fields
            )

            # If we got here, validation passed
            console.print(f"[green]{editor_config.success_message}[/green]")
            return validated_data, True

    except EditorError:
        # Error already displayed by the context manager
        return data, False

    # This should never be reached due to the context manager
    return data, False
