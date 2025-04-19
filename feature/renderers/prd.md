# PRD: Pluggable Renderers & Plain Text Output Mode

**Version:** 1.0
**Status:** Proposed
**Date:** 2025-04-19
**Author:** AI Product Manager

## 1. Introduction / Problem Statement

SoloGM currently relies heavily on the Rich library to provide a visually appealing and structured command-line interface (CLI) using panels, tables, and styled text. While this enhances the experience for many users, it presents challenges for:

1.  **Accessibility:** Users with screen readers or specific accessibility needs may find complex Rich layouts difficult to parse.
2.  **Terminal Compatibility:** Some terminals or environments (e.g., basic SSH sessions, CI/CD pipelines) may not fully support Rich's rendering capabilities, leading to garbled output.
3.  **Scripting:** Users attempting to parse SoloGM's output for scripting or integration with other tools find Rich's formatting codes and layouts obstructive. A structured, plain-text format like Markdown is preferable.
4.  **User Preference:** Some users simply prefer a cleaner interface without visual embellishments, and Markdown is a widely understood format.

This document proposes adding a mechanism to switch between the default Rich UI and a standard Markdown output mode.

## 2. Goals

*   Provide a fully functional Markdown alternative for all user-facing output from SoloGM commands.
*   Allow users to easily select the Markdown mode via a global command-line flag (`--no-ui`).
*   Implement this feature in a way that improves or maintains code structure and maintainability, avoiding complex conditional logic within display functions (using the Strategy Pattern).
*   Ensure the Markdown output conveys the same essential information as the Rich output, prioritizing clarity and standard Markdown syntax.
*   Ensure error messages are also displayed appropriately in Markdown mode (e.g., as code blocks or blockquotes).

## 3. Non-Goals

*   Implementing other output formats like JSON, HTML, or YAML in this iteration.
*   Providing granular control to disable *specific* UI elements (e.g., only disable panels but keep colors). The `--no-ui` flag is intended as an all-or-nothing switch to basic text.
*   Changing the core data or logic of the commands; this feature only affects the presentation layer.

## 4. User Stories

*   **As a user with a basic terminal emulator (e.g., in a restricted environment),** I want to run SoloGM commands and receive output that renders correctly and legibly, so that I can use the tool effectively.
*   **As a user writing a script to automate parts of my solo play,** I want to get predictable, Markdown-formatted output from SoloGM commands, so that I can more easily parse game state, event lists, etc., compared to Rich output.
*   **As a user who prefers minimal interfaces (or uses screen readers),** I want an option to disable the rich formatting, panels, and tables in favor of standard Markdown, so that I can interact with SoloGM in a way that suits my preferences or needs.

## 5. Requirements

### 5.1. Global Flag

*   A new global command-line option `--no-ui` shall be added to the main `sologm` command entry point (`sologm/cli/main.py`).
*   This flag should default to `False`.
*   When `True`, all subsequent output for that command invocation should use the Markdown Renderer.

### 5.2. Renderer Strategy Implementation

*   A Renderer Strategy pattern shall be implemented.
*   An abstract base class or `Protocol` named `Renderer` shall define the interface for all display operations (e.g., `display_game_info`, `display_scenes_table`, `display_error`, etc.).
*   A `RichRenderer` class shall implement the `Renderer` interface using the existing Rich components (panels, tables, styled text). This will be the default renderer.
*   A `MarkdownRenderer` class shall implement the `Renderer` interface using standard `print()` statements or `console.print()` outputting valid Markdown.

### 5.3. Renderer Selection and Usage

*   The appropriate renderer instance (`RichRenderer` or `MarkdownRenderer`) shall be selected and instantiated early in the application lifecycle (likely in `main()`), based on the value of the `--no-ui` flag.
*   This renderer instance must be accessible to all CLI command functions that produce output. (Mechanism TBD - e.g., global state, context object, dependency injection).
*   All CLI command functions (e.g., `game_info`, `game_status`, `scene_list`, `event_list`, etc.) must be refactored to delegate their display logic to the currently active renderer instance. They should no longer call specific `display_*` functions directly from `sologm.cli.utils.display` but rather methods like `renderer.display_game_info(...)`.

### 5.4. Markdown Output Format

*   The `MarkdownRenderer` must output information using standard Markdown syntax (CommonMark preferred).
*   It should use headings (`#`, `##`, etc.), lists (`*`, `-`, `1.`), bold (`**text**`), italics (`*text*`), code spans (`` `text` ``), code blocks (``` ```), blockquotes (`> text`), and horizontal rules (`---`) appropriately to structure the information logically.
*   Tabular data should be presented using Markdown tables where feasible, or as formatted lists otherwise.
*   The essential information content must match the Rich output. For example, if the Rich view shows game name, description, counts, and active scene, the Markdown view must also represent these elements using appropriate Markdown.
*   Text truncation logic (`truncate_text`) should still be applied where appropriate before formatting as Markdown to keep output concise.

### 5.5. Refactoring Existing Display Logic

*   Existing functions in `sologm.cli.utils.display.py` that generate Rich output should be moved into the `RichRenderer` class as methods.
*   Existing functions in `sologm.cli.utils.markdown.py` that generate Markdown might be reusable or adaptable for the `MarkdownRenderer`.
*   Helper functions like `truncate_text` or potentially `StyledText` (if used carefully for semantic meaning before converting to plain text) might remain in `utils` or be moved to a shared rendering utility module.

## 6. Design Considerations (High-Level)

*   **Renderer Access:** Determine the best way to make the selected renderer instance available to command functions (e.g., storing it on Typer's context, using a simple global variable managed in `main.py`, or a more formal dependency injection approach). For simplicity, a module-level variable in `main.py` might be sufficient initially.
*   **Console Usage:** Both renderers might still benefit from using the `rich.console.Console` instance (passed during initialization) for consistent output handling, even if `MarkdownRenderer` primarily uses `console.print()` with Markdown strings.
*   **Error Handling:** Error messages displayed to the user should also go through the renderer's `display_error` method to ensure they are formatted appropriately (e.g., as Markdown blockquotes or code blocks) when `--no-ui` is active.
*   **Code Organization:** Place renderer-related code in a dedicated `sologm/cli/rendering` directory with `base.py`, `rich_renderer.py`, and `markdown_renderer.py`.

## 7. Future Considerations

*   This architecture paves the way for adding other renderers in the future, such as `JsonRenderer` or `HtmlRenderer`, if needed.
*   The `MarkdownRenderer` could potentially leverage or unify with the existing `generate_game_markdown` logic in `sologm.cli.utils.markdown`.

## 8. Success Metrics

*   The `--no-ui` flag successfully switches output to Markdown for all relevant commands.
*   Markdown output is valid, readable, accurate, and contains the necessary information.
*   The codebase related to display logic is demonstrably cleaner and easier to maintain (e.g., command functions are simpler, rendering logic is encapsulated).
*   Positive user feedback regarding accessibility, scripting capabilities, or preference for Markdown output.
```
