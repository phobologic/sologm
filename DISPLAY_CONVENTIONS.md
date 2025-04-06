## Display Design Style

### Panel Structure
- Use `Panel` objects for distinct content sections
- Include descriptive titles in panels using the `title` parameter
- Use consistent border colors to indicate content type:
  - Blue: Game information
  - Cyan: Current/active content
  - Green: Success/completed content
  - Yellow: Pending actions/decisions
  - Bright_black: Neutral information (like dice rolls)

### Text Formatting
- Use `[bold]` for titles and important identifiers
- Use `[dim]` for supplementary information and descriptions
- Use color consistently for specific data types:
  - Cyan: Timestamps and IDs
  - Magenta: Categories and sources
  - Green: Success indicators and selected items
  - Yellow: Warnings and pending actions

### Layout Patterns
- Use `Table.grid()` for multi-column layouts
- Stack related panels vertically in content sections
- Truncate long text with ellipsis using `truncate_text()`
- Include metadata in compact format (e.g., "Created: {date} • Scenes: {count}")

### Table Formatting
- Embed table titles in the top border using `title` parameter
- Left-justify table titles with `title_justify="left"`
- Use consistent title styling with TEXT_STYLES["title"]
- Match table border color to content type using BORDER_STYLES

### Command Output Structure
- Start with a header panel showing primary entity information
- Group related information in separate panels
- For list views, use Rich tables with consistent column structure
- For detailed views, use nested panels with clear hierarchy
- For status displays, use multi-column layout with color-coded sections

### Examples
```python
# Header panel with title and metadata
panel = Panel(
    f"[dim]{description}[/dim]\nCreated: {created_at} • Items: {count}",
    title=f"[bold bright_blue]{name}[/bold bright_blue] ([bold cyan]{slug}[/bold cyan])",
    border_style="blue"
)

# Status item with timestamp and category
status_text = (
    f"[cyan]{timestamp}[/cyan] [magenta]({category})[/magenta]\n"
    f"{content}\n\n"
)

# Action prompt in panel
action_panel = Panel(
    f"[yellow]Pending Action:[/yellow]\n{details}\n\n"
    f"[dim]Use 'sologm command action' to proceed[/dim]",
    title="Required Action",
    border_style="yellow"
)

# Table with embedded, left-justified title
table = Table(
    title=f"[{TEXT_STYLES['title']}]Table Title[/{TEXT_STYLES['title']}]",
    title_justify="left",
    border_style=BORDER_STYLES["game_info"],
)
