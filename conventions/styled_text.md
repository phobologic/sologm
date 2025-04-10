# Styled Text Conventions

## Overview

SoloGM uses a consistent styling system through the `StyledText` class to ensure visual consistency across the application. This document outlines how to use the styling system correctly.

## StyledText Class

The `StyledText` class provides methods for creating styled text using Rich's native style system. It encapsulates styling logic to ensure consistency across the application.

## Available Styles

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

## Usage Patterns

### Basic Usage

```python
from sologm.cli.utils.styled_text import StyledText

# Create a styled text object
title = StyledText.title("Game Title")
timestamp = StyledText.timestamp("2023-01-01")

# Combine styled elements
header = StyledText.combine(title, " - ", timestamp)
```

### Metadata Formatting

Use the `format_metadata()` method for consistent metadata formatting:

```python
metadata = {
    "Created": "2023-01-01",
    "Modified": "2023-01-15",
    "Items": 5
}

# Format metadata with default separator
formatted = StyledText.format_metadata(metadata)  # "Created: 2023-01-01 • Modified: 2023-01-15 • Items: 5"
```

### Border Styles

Border styles are defined in the `BORDER_STYLES` dictionary:

```python
from sologm.cli.utils.styled_text import BORDER_STYLES
from rich.panel import Panel

panel = Panel(
    "Content",
    title="Title",
    border_style=BORDER_STYLES["game_info"]  # Uses bright_blue
)
```

## Color Palette

The styling system is based on the [Dracula theme](https://draculatheme.com/) with the following color mappings:

- `bright_blue`: Game information (Dracula purple-blue)
- `bright_cyan`: Current/active content (Dracula cyan)
- `bright_green`: Success/completed content (Dracula green)
- `bright_yellow`: Pending actions/decisions (Dracula yellow)
- `bright_magenta`: Neutral information (Dracula pink)

## Best Practices

1. **Always use the StyledText class** instead of raw Rich markup
2. **Use the appropriate method** for the type of content you're displaying
3. **Combine styled elements** with the `combine()` method
4. **Match border styles** to the type of content in the panel
5. **Use consistent metadata formatting** with `format_metadata()`
