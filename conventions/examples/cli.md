# CLI Examples

## Command Parameter Pattern

Example of a command with both direct parameters and structured editor fallback:

```python
@app.command("add")
def add_item(
    name: Optional[str] = typer.Option(
        None,  # None allows falling back to editor
        "--name", 
        "-n",
        help="Name of the item (opens editor if not provided)",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Description of the item",
    ),
):
    """Add a new item.
    
    If required parameters are not provided, opens an editor.
    """
    # Implementation...
```

## Structured Editor Usage

Example of structured editor configuration and usage:

```python
# Import the structured editor
from sologm.cli.utils.structured_editor import (
    EditorConfig,
    FieldConfig,
    StructuredEditorConfig,
    edit_structured_data,
    get_event_context_header,
)

# Create context information
context_info = get_event_context_header(
    game_name=game.name,
    scene_title=scene.title,
    scene_description=scene.description,
    recent_events=recent_events,
)

# Create editor configurations
editor_config = EditorConfig(
    edit_message="Creating new item:",
    success_message="Item created successfully.",
    cancel_message="Item creation canceled.",
    error_message="Could not open editor",
)

# Configure the structured editor fields
structured_config = StructuredEditorConfig(
    fields=[
        FieldConfig(
            name="name",
            display_name="Item Name",
            help_text="The name of the item",
            required=True,
            multiline=False,
        ),
        FieldConfig(
            name="description",
            display_name="Description",
            help_text="Detailed description of the item",
            required=True,
            multiline=True,
        ),
    ]
)

# Use the structured editor with initial data
initial_data = {}
if name:
    initial_data["name"] = name
if description:
    initial_data["description"] = description
    
edited_data, was_modified = edit_structured_data(
    data=initial_data,
    console=console,
    config=structured_config,
    context_info=context_info,
    editor_config=editor_config,
    is_new=True,
)

# Check if the user made changes
if not was_modified:
    return
```

## Error Handling

Example of error handling in CLI commands:

```python
try:
    # Attempt operation
    result = manager.perform_operation(param1, param2)
    
    # Display success
    console.print("[bold green]Operation completed successfully![/]")
    display_result(console, result)
    
except SpecificError as e:
    # Handle specific error with user-friendly message
    console.print(f"[red]Error:[/] {str(e)}")
    raise typer.Exit(1) from e
except Exception as e:
    # Log unexpected errors
    logger.exception("Unexpected error")
    console.print("[red]An unexpected error occurred.[/]")
    raise typer.Exit(1) from e
```

## Command Display Patterns

Example of displaying entity information after creation:

```python
# Create entity
entity = entity_manager.create_entity(name, description)

# Display success message
console.print("[bold green]Entity created successfully![/]")

# Display detailed entity information
display_entity_info(console, entity)
```

Example of list command with table display:

```python
@app.command("list")
def list_entities():
    """List all entities."""
    try:
        # Get entities from manager
        entities = entity_manager.list_entities()
        
        # Display entities in a table
        display_entities_table(console, entities)
        
    except EntityError as e:
        console.print(f"[red]Error:[/] {str(e)}")
        raise typer.Exit(1) from e
```
