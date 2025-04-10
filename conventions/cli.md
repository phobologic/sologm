# CLI Conventions

## Architecture

- CLI commands should follow the [architecture conventions](architecture.md)
- Focus solely on user interaction (input/output)
- Never interact directly with database sessions

## Command Structure

- Group related commands into Typer apps (e.g., `game_app`, `scene_app`)
- Use consistent command naming across the application
- Provide detailed help text for all commands and options
- Include examples in docstrings where appropriate
- Use `no_args_is_help=True` for subcommands to show help when no arguments are provided

## Command Parameter Pattern

- Commands should support both direct parameter specification and interactive editing
- Provide explicit parameters via `typer.Option` for scripting and quick usage
- Fall back to structured editor when required parameters are not provided
- Use consistent parameter naming across commands (e.g., `--id`, `--name`, etc.)
- Use short options (`-i`, `-n`) for frequently used parameters
- [See command parameter examples](examples/cli.md#command-parameter-pattern)

## Structured Editor Usage

- Use the structured editor (`structured_editor.py`) for complex data entry
- When a required parameter is missing, launch the editor with appropriate context
- Display relevant context information in the editor (e.g., game/scene details, recent events)
- Ensure validation is consistent between direct parameters and editor input
- Provide clear success/error messages for both input methods
- Use `get_event_context_header()` or similar functions to create consistent context headers
- [See structured editor examples](examples/cli.md#structured-editor-usage)

## Error Handling

- Follow the [error handling conventions](error_handling.md)
- Use `console.print()` with Rich formatting for error messages
- Use `typer.Exit(1)` to exit with error code when appropriate
- Use consistent error message formatting: `[red]Error:[/] {error_message}`
- [See error handling examples](examples/cli.md#error-handling)

## Display Conventions

- Follow the [display design conventions](display.md) for all output formatting
- Create a `Console` instance at the module level for consistent styling
- Delegate complex display logic to functions in `display.py`
- Log display operations at debug level for troubleshooting

### Command-Specific Display Patterns

- Display success messages in green: `[bold green]Success message![/]`
- Show detailed entity information after creation/update operations
- For list commands, use tables with consistent column structure
- For status commands, use multi-panel layouts with color-coded sections
- [See command display examples](examples/cli.md#command-display-patterns)
