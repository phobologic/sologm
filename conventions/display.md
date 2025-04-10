# Display Design Style

## Panel Structure
- Use `Panel` objects for distinct content sections
- Include descriptive titles in panels using the `title` parameter
- Use `title_align="left"` for consistent title alignment

## Styling System

The SoloGM styling system is loosely based on the [Dracula theme](https://draculatheme.com/), a dark theme known for its distinctive color palette.

### Border and Text Styles
- Use the `StyledText` class and `BORDER_STYLES` for consistent styling:
  - Game information: `BORDER_STYLES["game_info"]` (bright_blue)
  - Current/active content: `BORDER_STYLES["current"]` (bright_cyan)
  - Success/completed content: `BORDER_STYLES["success"]` (bright_green)
  - Pending actions/decisions: `BORDER_STYLES["pending"]` (bright_yellow)
  - Neutral information: `BORDER_STYLES["neutral"]` (bright_magenta)

### StyledText Methods
- Use these methods instead of raw markup:
  - `title()`: For main titles and headings
  - `title_blue()`: For blue-colored titles
  - `timestamp()`: For timestamps and IDs (bright_cyan)
  - `subtitle()`: For section subtitles (magenta)
  - `success()`: For success messages and selected items (bright_green)
  - `warning()`: For warnings and pending actions (bright_yellow)
  - `category()`: For categories and sources (bright_magenta)
  - `combine()`: For combining multiple styled elements
  - `format_metadata()`: For consistent metadata formatting

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

## Examples
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

# Creating a table with consistent styling
table = Table(
    border_style=BORDER_STYLES["game_info"],
)
table.add_column("ID", style=st.STYLES["timestamp"])
table.add_column("Name", style=st.STYLES["category"])

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
