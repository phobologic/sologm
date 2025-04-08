"""Editor utilities for CLI commands."""

import logging
from typing import Any, Dict, Optional, Tuple

import click
import yaml
from rich.console import Console

logger = logging.getLogger(__name__)


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


def prepare_yaml_for_editing(
    data: Dict[str, Any],
    header_comment: str = "Edit the details below:",
    field_comments: Optional[Dict[str, str]] = None,
    literal_block_fields: Optional[list] = None,
) -> str:
    """Prepare a YAML string for editing with comments and formatting.

    Args:
        data: Dictionary of data to convert to YAML
        header_comment: Comment to place at the top of the file
        field_comments: Optional dict mapping field names to comment strings
        literal_block_fields: List of fields that should use YAML's literal block style

    Returns:
        Formatted YAML string with comments
    """
    # Create a copy of the data to modify
    processed_data = data.copy()

    # Process literal block fields
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


def edit_yaml_data(
    data: Dict[str, Any],
    console: Console,
    header_comment: str = "Edit the details below:",
    field_comments: Optional[Dict[str, str]] = None,
    literal_block_fields: Optional[list] = None,
    required_fields: Optional[list] = None,
    edit_message: str = "Editing data:",
    success_message: str = "Data updated successfully.",
    cancel_message: str = "Data unchanged.",
    error_message: str = "Could not open editor",
    max_retries: int = 2,
) -> Tuple[Dict[str, Any], bool]:
    """Edit data using YAML format in an external editor.

    Args:
        data: Dictionary of data to edit
        console: Rich console for output
        header_comment: Comment to place at the top of the file
        field_comments: Optional dict mapping field names to comment strings
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
    # Create a string representation of the original data for reference
    original_data_yaml = yaml.dump(data, sort_keys=False, default_flow_style=False)
    original_data_lines = original_data_yaml.split("\n")
    original_data_comment = "# Original values (for reference):\n"
    for line in original_data_lines:
        original_data_comment += f"# {line}\n"
    original_data_comment += "#\n"

    # Combine the header comment with the original data reference
    full_header = f"{header_comment}\n\n{original_data_comment}"

    # Prepare YAML for editing
    yaml_text = prepare_yaml_for_editing(
        data, full_header, field_comments, literal_block_fields
    )

    # Track if any edits were made
    any_edits_made = False
    current_text = yaml_text
    retry_count = 0
    current_error = None

    # Save the original data comment to preserve it across retries
    original_comment_block = original_data_comment

    while retry_count <= max_retries:
        # Prepare message with error info if this is a retry
        current_message = edit_message

        if current_error:
            error_header = f"ERROR: {current_error}\n\nPlease fix the YAML format and try again.\nCommon issues include:\n- Incorrect indentation\n- Missing or extra colons\n- Unbalanced quotes\n\n{header_comment}\n\n{original_comment_block}"
            current_message = f"Editing data (Retry {retry_count}/{max_retries}):"

            # For retries, we'll manually construct the text to preserve user's input
            # Extract all comment lines (including original data reference)
            header_lines = []
            in_original_block = False
            for line in current_text.split("\n"):
                if line.strip().startswith("#"):
                    if "Original values (for reference):" in line:
                        in_original_block = True
                    if in_original_block and line.strip() == "#":
                        in_original_block = False
                        header_lines.append(line)
                        continue
                    if (
                        not in_original_block
                        or "Original values (for reference):" in line
                    ):
                        header_lines.append(line)

            # Extract user's edited content (non-comment lines)
            user_lines = [
                line
                for line in current_text.split("\n")
                if not line.strip().startswith("#")
            ]

            # Construct new error header
            error_header_lines = []
            for line in error_header.split("\n"):
                error_header_lines.append(
                    f"# {line}" if not line.startswith("#") and line.strip() else line
                )

            # Combine everything, ensuring proper spacing
            current_text = "\n".join(error_header_lines + [""] + user_lines)

        # Open editor
        edited_text, was_modified = edit_text(
            current_text,
            console=console,
            message=current_message,
            success_message="Validating your changes...",
            cancel_message=cancel_message,
            error_message=error_message,
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

        try:
            # Remove comment lines before parsing
            yaml_text = "\n".join(
                [
                    line
                    for line in edited_text.split("\n")
                    if not line.strip().startswith("#")
                ]
            )

            # Parse the edited YAML
            edited_data = yaml.safe_load(yaml_text)

            # Validate the structure
            if not isinstance(edited_data, dict):
                current_error = "Invalid YAML format. Expected a dictionary."
                console.print(f"[bold yellow]Warning:[/] {current_error}")
                console.print(
                    "[yellow]The editor will reopen so you can fix this issue.[/yellow]"
                )
                retry_count += 1
                current_text = edited_text
                continue

            # Validate required fields
            missing_fields = []
            if required_fields:
                for field in required_fields:
                    if (
                        field not in edited_data
                        or not str(edited_data.get(field, "")).strip()
                    ):
                        missing_fields.append(field)

            if missing_fields:
                field_list = ", ".join(f"'{f}'" for f in missing_fields)
                current_error = f"Required field(s) {field_list} cannot be empty."
                console.print(f"[bold yellow]Warning:[/] {current_error}")
                console.print(
                    "[yellow]The editor will reopen so you can fix this issue.[/yellow]"
                )
                retry_count += 1
                current_text = edited_text
                continue

            # If we got here, validation passed
            console.print(f"[green]{success_message}[/green]")
            return edited_data, True

        except yaml.YAMLError as e:
            # Get a user-friendly error message
            error_msg = str(e)
            # Make the error message more user-friendly if possible
            if "could not find expected ':'" in error_msg:
                error_msg = "Missing colon after a field name"
            elif "found character '\\t'" in error_msg:
                error_msg = "Tab character found. Please use spaces for indentation"

            current_error = f"YAML parsing error: {error_msg}"
            console.print(f"[bold yellow]Warning:[/] {current_error}")

            if retry_count < max_retries:
                console.print(
                    "[yellow]The editor will reopen so you can fix this issue.[/yellow]"
                )
                retry_count += 1
                current_text = edited_text
            else:
                console.print(
                    "[bold red]Maximum retry attempts reached. Canceling edit.[/bold red]"
                )
                return data, False

    # If we've exhausted retries
    console.print(
        "[bold red]Failed to parse YAML after multiple attempts. No changes made.[/bold red]"
    )
    return data, False
