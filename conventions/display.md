# Display Design Style

## Panel Structure
- Use `rich.panel.Panel` objects for distinct content sections
- Include descriptive titles in panels using the `title` parameter
- Use `title_align="left"` for consistent title alignment
- [See panel structure examples](examples/display.md#panel-structure)

## Styling System

The SoloGM styling system is loosely based on the [Dracula theme](https://draculatheme.com/), a dark theme known for its distinctive color palette.

### StyledText Class

The `sologm.cli.utils.styled_text.StyledText` class provides methods for creating styled text using Rich's native style system. It encapsulates styling logic to ensure consistency across the application.

### Available Styles

The following styles are available through the `sologm.cli.utils.styled_text.StyledText` class:

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

[See styling examples](examples/display.md#styling)

### Border Styles

Border styles are defined in the `sologm.cli.utils.styled_text.BORDER_STYLES` dictionary:

- Game information: `BORDER_STYLES["game_info"]` (bright_blue)
- Current/active content: `BORDER_STYLES["current"]` (bright_cyan)
- Success/completed content: `BORDER_STYLES["success"]` (bright_green)
- Pending actions/decisions: `BORDER_STYLES["pending"]` (bright_yellow)
- Neutral information: `BORDER_STYLES["neutral"]` (bright_magenta)

### Best Practices

1. **Always use the `sologm.cli.utils.styled_text.StyledText` class** instead of raw Rich markup
2. **Use the appropriate method** for the type of content you're displaying
3. **Combine styled elements** with the `sologm.cli.utils.styled_text.StyledText.combine()` method
4. **Match border styles** to the type of content in the panel
5. **Use consistent metadata formatting** with `sologm.cli.utils.styled_text.StyledText.format_metadata()`

## Layout Patterns
- Use `rich.table.Table.grid()` for multi-column layouts
- Stack related panels vertically in content sections
- Truncate long text with ellipsis using `sologm.cli.utils.display.truncate_text()`
- Include metadata in compact format (e.g., "Created: {date} • Scenes: {count}")
- [See layout examples](examples/display.md#layout-patterns)

## Text Truncation
- Use the `sologm.cli.utils.display.truncate_text()` function to handle long text:
  - Specify a reasonable `max_length` based on display context
  - For multi-column layouts, calculate appropriate truncation length
  - Use console width to dynamically adjust truncation length when possible
- [See truncation examples](examples/display.md#text-truncation)

## Grid Layouts
- Use nested grids for complex layouts
- [See grid layout examples](examples/display.md#grid-layouts)

## Table Formatting
- Use consistent column styling with `sologm.cli.utils.styled_text.StyledText.STYLES`
- Match table border color to content type using `sologm.cli.utils.styled_text.BORDER_STYLES`
- Add columns with appropriate styles
- [See table formatting examples](examples/display.md#table-formatting)

## Command Output Structure
- Start with a header panel showing primary entity information
- Group related information in separate panels
- For list views, use `rich.table.Table` with consistent column structure
- For detailed views, use nested panels with clear hierarchy
- For status displays, use multi-column layout with color-coded sections
- [See command output examples](examples/display.md#command-output-structure)

