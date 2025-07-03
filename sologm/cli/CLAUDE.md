# CLI Development Guidelines

## Primary Reference
Follow the CLI conventions at [../../conventions/cli.md](../../conventions/cli.md)

## CLI Architecture Principles
- **Single Responsibility**: CLI handles ONLY user interaction and parameter collection
- **Delegate Business Logic**: All operations go through managers in `sologm/core/`
- **Session Management**: Use `get_db_context()` for all database operations
- **Error Handling**: Catch exceptions and display user-friendly messages

## Command Structure Pattern
```python
@app.command()
def my_command(
    param: str = typer.Option(None, help="Direct parameter"),
    use_editor: bool = typer.Option(False, "--editor", help="Use structured editor")
):
    """Command description following conventions."""
    try:
        with get_db_context() as context:
            # Parameter collection and validation
            if not param and not use_editor:
                param = structured_editor_fallback()
            
            # Delegate ALL business logic to manager
            result = context.managers.my_manager.do_operation(param)
            
            # Display result using renderer
            display_result(result)
            
    except SpecificError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e
```

## Parameter Handling Patterns

### Option vs Editor Pattern
Commands should support both direct parameters and structured editor:
```python
# Direct usage
sologm scene create --title "Forest Path" --description "A winding trail"

# Editor usage  
sologm scene create --editor
```

### Structured Editor Integration
Use `StructuredEditor` for complex input:
```python
from sologm.cli.utils.structured_editor import StructuredEditor

def get_scene_data_via_editor():
    editor = StructuredEditor("Create Scene")
    editor.add_field("title", "Scene Title", required=True)
    editor.add_field("description", "Scene Description", multiline=True)
    return editor.edit()
```

## Display and Rendering

### Renderer System
Commands use pluggable renderers:
- **RichRenderer**: Default Rich-based UI with panels, colors, tables
- **MarkdownRenderer**: Plain text output activated with `--no-ui` flag

### Display Patterns
```python
# Use panels for structured information
panel = Panel(
    content,
    title="Panel Title",
    border_style="blue"
)

# Use tables for list data
table = Table(title="Results")
table.add_column("Column 1")
table.add_column("Column 2")
table.add_row("data1", "data2")

# Use console for simple output
console.print("[green]Success:[/] Operation completed")
```

## Error Handling Patterns

### User-Friendly Error Messages
```python
try:
    result = context.managers.game.get_active_game()
except NoActiveGameError:
    console.print("[red]Error:[/] No active game found. Use 'sologm game activate' first.")
    raise typer.Exit(1)
except DatabaseError as e:
    console.print(f"[red]Database Error:[/] {str(e)}")
    raise typer.Exit(1) from e
```

### Let Managers Handle Business Logic Errors
```python
# DON'T do validation in CLI
if not title:
    console.print("[red]Error:[/] Title required")
    
# DO let manager handle validation
try:
    result = context.managers.scene.create_scene(title="")
except ValidationError as e:
    console.print(f"[red]Error:[/] {str(e)}")
```

## Command Categories

### List Commands
- Use tables with consistent column structure
- Support filtering and sorting through manager parameters
- Show summary information (counts, status)

### Create/Update Commands  
- Support both direct parameters and editor mode
- Validate required fields
- Show confirmation of created/updated resource

### Status Commands
- Use multi-panel layouts with color-coded sections
- Show hierarchical information (game → act → scene)
- Include relevant counts and active states

## Testing Philosophy
**Do NOT test CLI commands directly.** Test the managers they delegate to.

CLI testing focuses on:
- Parameter parsing works correctly
- Error messages are user-friendly  
- Display formatting is consistent

Manager testing handles all business logic validation.

## Common Utilities

### Session Context
```python
from sologm.database.session import get_db_context

with get_db_context() as context:
    # All managers available via context.managers
    result = context.managers.scene.list_scenes()
```

### Display Utilities
```python
from sologm.cli.utils.display import console, create_panel, create_table
from sologm.cli.utils.styled_text import StyledText

# Rich console for output
console.print("[green]Success message[/]")

# Styled text helper
styled = StyledText("Important text", style="bold red")
```

## Related Conventions
- [Architecture](../../conventions/architecture.md) - CLI/Manager separation of concerns
- [Display](../../conventions/display.md) - Rich formatting patterns and color schemes  
- [Error Handling](../../conventions/error_handling.md) - Exception handling and user messages
- [Managers](../../conventions/managers.md) - Business logic delegation patterns
