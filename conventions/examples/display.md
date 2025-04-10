# Display Examples

This document contains code examples demonstrating the display conventions used in SoloGM.

## Panel Structure

```python
from rich.panel import Panel
from sologm.cli.utils.styled_text import StyledText, BORDER_STYLES

# Basic panel with title
panel = Panel(
    "Panel content goes here",
    title="Panel Title",
    title_align="left",
    border_style=BORDER_STYLES["game_info"]
)

# Panel with styled title and content
st = StyledText
panel_title = st.title_blue("Important Information")
panel_content = st.subtitle("This is important content")

panel = Panel(
    panel_content,
    title=panel_title,
    title_align="left",
    border_style=BORDER_STYLES["current"]
)
```

## Styling

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
from sologm.cli.utils.styled_text import StyledText

metadata = {
    "Created": "2023-01-01",
    "Modified": "2023-01-15",
    "Items": 5
}

# Format metadata with default separator
formatted = StyledText.format_metadata(metadata)  # "Created: 2023-01-01 • Modified: 2023-01-15 • Items: 5"
```

## Layout Patterns

### Panel Creation

```python
from rich.panel import Panel
from sologm.cli.utils.styled_text import StyledText, BORDER_STYLES

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

## Text Truncation

```python
from sologm.cli.utils.display import truncate_text

# Basic truncation
long_text = "This is a very long text that needs to be truncated to fit in the available space"
truncated = truncate_text(long_text, max_length=30)  # "This is a very long text that..."

# Dynamic truncation based on console width
from rich.console import Console
console = Console()
console_width = console.width
truncation_length = max(40, int(console_width / 2) - 10)
truncated = truncate_text(long_text, max_length=truncation_length)
```

## Grid Layouts

```python
from rich.table import Table
from rich.panel import Panel

# Create main grid with two columns
main_grid = Table.grid(expand=True, padding=(0, 1))
main_grid.add_column("Left", ratio=1)
main_grid.add_column("Right", ratio=1)

# Create nested grid for left column
left_grid = Table.grid(padding=(0, 1), expand=True)
left_grid.add_column(ratio=1)
left_grid.add_row(Panel("Panel 1 content"))
left_grid.add_row(Panel("Panel 2 content"))

# Add to main grid
main_grid.add_row(left_grid, Panel("Right panel content"))
```

## Table Formatting

```python
from rich.table import Table
from sologm.cli.utils.styled_text import StyledText, BORDER_STYLES

# Creating a table with consistent styling
st = StyledText
table = Table(
    border_style=BORDER_STYLES["game_info"],
)
table.add_column("ID", style=st.STYLES["timestamp"])
table.add_column("Name", style=st.STYLES["category"])
table.add_column("Description")
table.add_column("Status", style=st.STYLES["success"])

# Add rows
table.add_row("1", "Item Name", "Description text", "Active")
```

## Command Output Structure

### Dice Roll Display

```python
from rich.panel import Panel
from sologm.cli.utils.styled_text import StyledText, BORDER_STYLES

# Display dice roll with styled components
st = StyledText
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

### Game Status Display

```python
from rich.panel import Panel
from rich.table import Table
from sologm.cli.utils.styled_text import StyledText, BORDER_STYLES

st = StyledText

# Create game header
game_title = st.combine(
    st.title_blue("My Adventure"),
    " (",
    st.timestamp("my-adventure"),
    ") ",
    st.timestamp("game123")
)

game_content = st.combine(
    "An exciting adventure in a fantasy world",
    "\n",
    st.format_metadata({"Created": "2023-01-01", "Scenes": "5"})
)

header_panel = Panel(
    game_content,
    title=game_title,
    border_style=BORDER_STYLES["game_info"],
    expand=True,
    title_align="left"
)

# Create scene panel
scene_title = st.title("The Dark Forest")
scene_content = st.combine(
    "The heroes enter a mysterious forest",
    "\n",
    st.format_metadata({"Status": "Active", "Sequence": "3"})
)

scene_panel = Panel(
    scene_content,
    title=scene_title,
    border_style=BORDER_STYLES["current"],
    expand=True,
    title_align="left"
)

# Create events panel
events_panel = Panel(
    "Event 1\nEvent 2\nEvent 3",
    title=st.title("Recent Events"),
    border_style=BORDER_STYLES["success"],
    expand=True,
    title_align="left"
)

# Combine in a grid
grid = Table.grid(expand=True)
grid.add_column(ratio=1)
grid.add_row(header_panel)
grid.add_row(scene_panel)
grid.add_row(events_panel)
```
