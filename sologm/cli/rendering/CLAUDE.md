# Rendering System Guidelines

## Context
This directory implements the pluggable rendering system for CLI output, allowing users to switch between Rich UI and plain text output.

## Parent Guidelines
Follow the CLI conventions at [../../../conventions/cli.md](../../../conventions/cli.md) and display conventions at [../../../conventions/display.md](../../../conventions/display.md).

## Architecture Overview
- **`base.py`**: `Renderer` abstract base class defining the interface
- **`rich_renderer.py`**: Default Rich-based UI renderer with panels, colors, and tables
- **`markdown_renderer.py`**: Plain text renderer for `--no-ui` flag and scripting

## Renderer Interface
All renderers must implement the base `Renderer` interface:

```python
class Renderer(ABC):
    @abstractmethod
    def render_panel(self, content: str, title: str = "", border_style: str = "blue") -> str:
        """Render content in a panel with optional title and border."""
        pass
    
    @abstractmethod
    def render_table(self, headers: List[str], rows: List[List[str]], title: str = "") -> str:
        """Render tabular data with headers and rows."""
        pass
    
    @abstractmethod
    def render_error(self, message: str) -> str:
        """Render error message with appropriate styling."""
        pass
    
    @abstractmethod
    def render_success(self, message: str) -> str:
        """Render success message with appropriate styling."""
        pass
```

## Implementation Patterns

### Rich Renderer
Uses Rich library for enhanced terminal output:
```python
def render_panel(self, content: str, title: str = "", border_style: str = "blue") -> str:
    panel = Panel(
        content,
        title=title,
        border_style=border_style,
        padding=(1, 2)
    )
    return panel
```

Key features:
- Color-coded panels with borders
- Rich tables with proper alignment
- Styled text with markup (`[green]Success[/]`)
- Grid layouts for complex information display

### Markdown Renderer
Produces clean plain text output:
```python
def render_panel(self, content: str, title: str = "", border_style: str = "blue") -> str:
    if title:
        return f"## {title}\n\n{content}\n"
    return f"{content}\n"
```

Key features:
- Markdown-formatted output
- Plain text tables using ASCII formatting
- No colors or special characters
- Suitable for scripting and automation

## Usage in CLI Commands

### Renderer Selection
Global `--no-ui` flag determines renderer:
```python
# In main.py
renderer = MarkdownRenderer() if no_ui else RichRenderer()
```

### Using Renderers in Commands
```python
def display_game_status(game: Game, renderer: Renderer):
    # Content preparation (renderer-agnostic)
    content = f"Game: {game.name}\nStatus: {'Active' if game.is_active else 'Inactive'}"
    
    # Render using selected renderer
    panel = renderer.render_panel(
        content,
        title="Game Status",
        border_style="green" if game.is_active else "red"
    )
    
    console.print(panel)
```

## Content Preparation Patterns

### Renderer-Agnostic Content
Prepare content as plain text, let renderers handle formatting:
```python
def prepare_scene_summary(scene: Scene) -> str:
    lines = [
        f"Title: {scene.title}",
        f"Sequence: {scene.sequence}",
        f"Events: {scene.event_count}",
        f"Dice Rolls: {scene.dice_roll_count}"
    ]
    return "\n".join(lines)
```

### Table Data Preparation
```python
def prepare_scenes_table_data(scenes: List[Scene]) -> tuple[List[str], List[List[str]]]:
    headers = ["Sequence", "Title", "Events", "Dice Rolls", "Status"]
    rows = []
    
    for scene in scenes:
        status = "Active" if scene.is_active else "Inactive"
        rows.append([
            str(scene.sequence),
            scene.title[:30],  # Truncate for display
            str(scene.event_count),
            str(scene.dice_roll_count),
            status
        ])
    
    return headers, rows
```

## Testing Renderers

### Renderer Interface Testing
```python
def test_rich_renderer_panel():
    renderer = RichRenderer()
    result = renderer.render_panel("Test content", "Test Title")
    
    # Rich renderer returns Panel object
    assert isinstance(result, Panel)
    assert "Test content" in str(result)
    assert "Test Title" in str(result)

def test_markdown_renderer_panel():
    renderer = MarkdownRenderer()
    result = renderer.render_panel("Test content", "Test Title")
    
    # Markdown renderer returns formatted string
    assert "## Test Title" in result
    assert "Test content" in result
```

### Output Consistency Testing
```python
def test_renderers_produce_equivalent_information():
    rich_renderer = RichRenderer()
    markdown_renderer = MarkdownRenderer()
    
    # Same data should produce equivalent information
    headers = ["Col1", "Col2"]
    rows = [["Data1", "Data2"]]
    
    rich_output = rich_renderer.render_table(headers, rows)
    markdown_output = markdown_renderer.render_table(headers, rows)
    
    # Both should contain the same data
    assert "Col1" in str(rich_output) and "Col1" in markdown_output
    assert "Data1" in str(rich_output) and "Data1" in markdown_output
```

## Display Conventions Integration

### Color Schemes (Rich Renderer)
Follow display conventions for consistent colors:
- **Success**: `green`
- **Error**: `red` 
- **Warning**: `yellow`
- **Info**: `blue`
- **Active states**: `green`
- **Inactive states**: `dim`

### Panel Styling
```python
# Status panels
success_panel = renderer.render_panel(content, "Success", "green")
error_panel = renderer.render_panel(content, "Error", "red")

# Information panels  
game_panel = renderer.render_panel(content, "Game Status", "blue")
scene_panel = renderer.render_panel(content, "Current Scene", "cyan")
```

## Best Practices

### Content First, Formatting Second
1. Prepare all content as plain text/data structures
2. Pass to renderer for formatting
3. Let renderer handle all styling decisions

### Consistent Information
Both renderers should present the same information:
- Same data in tables
- Same status indicators
- Same hierarchical relationships
- Only formatting should differ

### Error Handling
```python
def safe_render(renderer: Renderer, content: str, title: str = "") -> str:
    try:
        return renderer.render_panel(content, title)
    except Exception as e:
        # Fallback to plain text if rendering fails
        return f"{title}: {content}" if title else content
```

## Related Conventions
- [CLI](../../../conventions/cli.md) - Command structure and user interaction
- [Display](../../../conventions/display.md) - Rich formatting patterns and color schemes
- [Architecture](../../../conventions/architecture.md) - Separation between content and presentation
