# Display Design Style

## Panel Structure
- Use `Panel` objects for distinct content sections
- Include descriptive titles in panels using the `title` parameter
- Use `title_align="left"` for consistent title alignment

## Styling System

The SoloGM styling system is loosely based on the [Dracula theme](https://draculatheme.com/), a dark theme known for its distinctive color palette.

### StyledText Class

The `StyledText` class provides methods for creating styled text using Rich's native style system. It encapsulates styling logic to ensure consistency across the application.

### Available Styles

The following styles are available through the `StyledText` class:

| Method | Purpose | Visual Style |
|--------|---------|--------------|
| `title()` | Main titles and headings | Bold |
| `title_blue()` | Blue-colored titles | Bold, bright blue |
| `timestamp()` | Timestamps and IDs | Bright cyan |
| `subtitle()` | Section subtitles | Magenta |
| `success()` | Success messages and selected items | Bright green |
| `warning()` | Warnings and pending actions | Bright yellow |
| `category()` | Categories and sources | Bright magenta |
| `title_timestamp()` | Combined title and timestamp | Bold, bright cyan |
| `title_success()` | Combined title and success | Bold, bright green |

### Border Styles

Border styles are defined in the `BORDER_STYLES` dictionary:

- Game information: `BORDER_STYLES["game_info"]` (bright_blue)
- Current/active content: `BORDER_STYLES["current"]` (bright_cyan)
- Success/completed content: `BORDER_STYLES["success"]` (bright_green)
- Pending actions/decisions: `BORDER_STYLES["pending"]` (bright_yellow)
- Neutral information: `BORDER_STYLES["neutral"]` (bright_magenta)

### Best Practices

1. **Always use the StyledText class** instead of raw Rich markup
2. **Use the appropriate method** for the type of content you're displaying
3. **Combine styled elements** with the `combine()` method
4. **Match border styles** to the type of content in the panel
5. **Use consistent metadata formatting** with `format_metadata()`

## Layout Patterns
- Use `Table.grid()` for multi-column layouts
- Stack related panels vertically in content sections
- Truncate long text with ellipsis using `truncate_text()`
- Include metadata in compact format (e.g., "Created: {date} • Scenes: {count}")

## Text Truncation
- Use the `truncate_text()` function to handle long text:
  - Specify a reasonable `max_length` based on display context
  - For multi-column layouts, calculate appropriate truncation length
  - Use console width to dynamically adjust truncation length when possible

## Grid Layouts
- Use nested grids for complex layouts:
  ```python
  # Create main grid with two columns
  main_grid = Table.grid(expand=True, padding=(0, 1))
  main_grid.add_column("Left", ratio=1)
  main_grid.add_column("Right", ratio=1)
  
  # Create nested grid for left column
  left_grid = Table.grid(padding=(0, 1), expand=True)
  left_grid.add_column(ratio=1)
  left_grid.add_row(panel1)
  left_grid.add_row(panel2)
  
  # Add to main grid
  main_grid.add_row(left_grid, right_panel)
  ```

## Table Formatting
- Use consistent column styling with `StyledText.STYLES`
- Match table border color to content type using `BORDER_STYLES`
- Add columns with appropriate styles:
  ```python
  table.add_column("ID", style=st.STYLES["timestamp"])
  table.add_column("Name", style=st.STYLES["category"])
  ```

## Command Output Structure
- Start with a header panel showing primary entity information
- Group related information in separate panels
- For list views, use Rich tables with consistent column structure
- For detailed views, use nested panels with clear hierarchy
- For status displays, use multi-column layout with color-coded sections

## Usage Examples

### Basic Styling

```python
from sologm.cli.utils.styled_text import StyledText

# Create a styled text object
title = StyledText.title("Game Title")
timestamp = StyledText.timestamp("2023-01-01")

# Combine styled elements
header = StyledText.combine(title, " - ", timestamp)
```

### Metadata Formatting

```python
metadata = {
    "Created": "2023-01-01",
    "Modified": "2023-01-15",
    "Items": 5
}

# Format metadata with default separator
formatted = StyledText.format_metadata(metadata)  # "Created: 2023-01-01 • Modified: 2023-01-15 • Items: 5"
```

### Panel Creation

```python
# Using StyledText for panel titles
st = StyledText
panel_title = st.combine(
    st.title_blue("Game Title"),
    " (",
    st.timestamp("game-slug"),
    ") ",
    st.timestamp("game-id")
)

# Creating a panel with styled content
panel_content = st.combine(
    st.subtitle("Description goes here"),
    "\n",
    st.format_metadata({"Created": "2023-01-01", "Items": "5"})
)

panel = Panel(
    panel_content,
    title=panel_title,
    border_style=BORDER_STYLES["game_info"],
    title_align="left"
)
```

### Table Creation

```python
# Creating a table with consistent styling
table = Table(
    border_style=BORDER_STYLES["game_info"],
)
table.add_column("ID", style=st.STYLES["timestamp"])
table.add_column("Name", style=st.STYLES["category"])
```

### Dice Roll Display

```python
# Display dice roll with styled components
roll_title = st.combine(st.title("Roll Reason:"), " ", st.title("2d6"))
roll_content = st.combine(
    st.subtitle("Result:"), " ", st.title_success("8")
)
roll_panel = Panel(
    roll_content,
    title=roll_title,
    border_style=BORDER_STYLES["neutral"],
    expand=True,
    title_align="left"
)
```
