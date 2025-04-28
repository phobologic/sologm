# TDD Plan: Pluggable Renderers & Markdown Output

**Version:** 1.0
**Status:** Proposed
**Date:** 2025-04-19
**Related PRD:** `features/renderers/prd.md`

## 1. Overview

This document outlines the steps to implement a pluggable rendering system for the SoloGM CLI, allowing users to switch between the default Rich UI and a Markdown output format using a `--no-ui` flag. We will follow a TDD approach, focusing on testing the renderer implementations directly, as per our testing conventions (`conventions/testing.md`).

The core components involved are:
*   A new global `--no-ui` flag in `sologm/cli/main.py`.
*   A `Renderer` interface (`sologm/cli/rendering/base.py`).
*   A `RichRenderer` implementation (`sologm/cli/rendering/rich_renderer.py`), refactoring existing logic from `sologm/cli/utils/display.py`.
*   A `MarkdownRenderer` implementation (`sologm/cli/rendering/markdown_renderer.py`).
*   Refactoring of CLI command functions (e.g., `sologm/cli/game.py`) to use the selected renderer.
*   New test suites for the renderers (`tests/cli/rendering/`).

## 2. Prerequisites & Assumptions

*   The PRD (`features/renderers/prd.md`) accurately reflects the desired functionality.
*   We will use **Typer's context object (`ctx.obj`)** to hold the selected renderer instance for accessibility in command modules.
*   The `rich.console.Console` instance created in `main.py` will be passed to the chosen renderer during initialization. Both renderers can use it (`console.print`) for consistent output stream handling.
*   Helper functions like `truncate_text` from `sologm/cli/utils/display.py` might be kept in `utils` and used by both renderers. `StyledText` might remain useful for `RichRenderer` and potentially for semantic structuring in `MarkdownRenderer` before final output.
*   We will *not* write direct tests for the CLI command functions themselves, but rather focus on unit-testing the renderer classes thoroughly.

## 3. TDD Steps (Red-Green-Refactor Cycle)

---

### Phase 1: Setup Basic Structure & Flag

**Goal:** Create the rendering directory, the base `Renderer` interface, add the `--no-ui` flag, and implement basic renderer selection in `main.py`.

*   **(Red) Test:** No direct unit test yet. This step is foundational structure.
*   **(Green) Code:**
    *   Create directory `sologm/cli/rendering/`.
    *   Create `sologm/cli/rendering/__init__.py`.
    *   Create `sologm/cli/rendering/base.py`:
        *   Define `Renderer` as an `abc.ABC`.
        *   Add `__init__(self, console: Console, markdown_mode: bool = False)`. Store `console` and `markdown_mode`.
        *   Define abstract methods for *all* current functions in `sologm/cli/utils/display.py` (e.g., `display_game_info`, `display_games_table`, `display_dice_roll`, `display_error`, etc.). Ensure method signatures match the data they need (e.g., `game: Game`, `roll: DiceRoll`).
    *   Modify `sologm/cli/main.py`:
        *   Add the `--no-ui: bool` option to the `main` callback function, defaulting to `False`.
        *   Ensure the `main` callback accepts `ctx: typer.Context` as its first argument.
        *   Import `Renderer`, `RichRenderer`, `MarkdownRenderer` (placeholders for now).
        *   In the `main` callback, *after* logger/config setup but *before* DB init, add logic:
            ```python
            # Instantiate the chosen renderer (placeholder for now) into a local variable
            # selected_renderer = ...
            # Initialize ctx.obj if necessary: if ctx.obj is None: ctx.obj = {}
            # Store the renderer on the context: ctx.obj["renderer"] = selected_renderer
            # Store the console on the context: ctx.obj["console"] = console
            # Add a check if selected_renderer is still None and raise an error
            ```
*   **(Refactor) Code:** Ensure imports are correct. Add basic logging. Rename `plain_mode` to `markdown_mode` in the `Renderer` base class and implementations for clarity.

---

### Phase 2: Implement `RichRenderer` by Refactoring `display.py`

**Goal:** Move all existing display logic from `sologm/cli/utils/display.py` into a concrete `RichRenderer` class, ensuring existing display functionality remains unchanged when `--no-ui` is `False`.

*   **(Red) Test:**
    *   Create `tests/cli/rendering/test_rich_renderer.py`.
    *   Copy/adapt the first test from `sologm/cli/utils/tests/test_display.py`, e.g., `test_display_dice_roll`.
    *   Modify the test setup to instantiate `RichRenderer(mock_console)`.
    *   Call `renderer.display_dice_roll(test_dice_roll)`.
    *   Assert that `mock_console.print` was called (or capture/compare output if necessary). This test should initially fail as `RichRenderer` doesn't exist or implement the method.
*   **(Green) Code:**
    *   Create `sologm/cli/rendering/rich_renderer.py`.
    *   Define `class RichRenderer(Renderer):`.
    *   Implement `__init__`.
    *   Copy the *implementation* of `display_dice_roll` from `sologm/cli/utils/display.py` into `RichRenderer.display_dice_roll`. Adapt it to use `self.console`. Ensure necessary imports (`Panel`, `StyledText`, etc.) are added to `rich_renderer.py`.
    *   Update `sologm/cli/main.py` to instantiate `RichRenderer` correctly in the `else` block.
    *   Run the test; it should now pass.
*   **(Refactor) Code:**
    *   Clean up the moved `display_dice_roll` method in `RichRenderer`.
    *   Remove the original `display_dice_roll` function from `sologm/cli/utils/display.py`.
    *   **Repeat Red-Green-Refactor for *every* function in `sologm/cli/utils/display.py`:**
        *   Adapt the corresponding test from `test_display.py` into `test_rich_renderer.py`.
        *   Move the function's implementation into the `RichRenderer` class.
        *   Make the test pass.
        *   Remove the original function from `display.py`.
    *   Keep shared utilities like `truncate_text` and `StyledText` in `sologm/cli/utils/` for now. Update imports in `RichRenderer` accordingly.

---

### Phase 3: Implement `MarkdownRenderer`

**Goal:** Create the `MarkdownRenderer` class and implement methods to output information in valid Markdown format.

*   **(Red) Test:**
    *   Create `tests/cli/rendering/test_markdown_renderer.py`.
    *   Write a test for the first method, e.g., `test_display_dice_roll_markdown`.
    *   Use `pytest.mark.parametrize` if helpful for different roll scenarios.
    *   Instantiate `MarkdownRenderer(mock_console)`.
    *   Call `renderer.display_dice_roll(test_dice_roll)`.
    *   Use `capsys` fixture (or mock `console.print`) to capture the output.
    *   Assert that the captured output is the *exact* expected Markdown string (e.g., `assert captured.out == "### Dice Roll: 2d6\\n\\n*   **Result:** 7\\n*   Rolls: `[3, 4]`\\n"`). This test will fail.
*   **(Green) Code:**
    *   Create `sologm/cli/rendering/markdown_renderer.py`.
    *   Define `class MarkdownRenderer(Renderer):`.
    *   Implement `__init__`.
    *   Implement `display_dice_roll` to produce the simplest Markdown output that makes the test pass. Use `self.console.print()`.
    *   Update `sologm/cli/main.py` to instantiate `MarkdownRenderer` correctly in the `if no_ui:` block.
    *   Run the test; it should pass.
*   **(Refactor) Code:**
    *   Improve the Markdown formatting for `display_dice_roll` (e.g., use code spans, bold, lists appropriately). Ensure the test still passes after refactoring.
    *   **Repeat Red-Green-Refactor for *every* method defined in the `Renderer` interface:**
        *   Write a test in `test_markdown_renderer.py` asserting the specific Markdown output for that method (e.g., `display_game_info`, `display_games_table`).
        *   Implement the method in `MarkdownRenderer`.
        *   Make the test pass.
        *   Refactor the Markdown output for clarity and adherence to PRD requirements (headings, lists, tables, blockquotes for errors, etc.).
        *   Investigate reusing logic/helpers from `sologm/cli/utils/markdown.py` (e.g., `generate_game_markdown`) where appropriate, potentially refactoring parts of it into helper functions usable by the renderer.

---

### Phase 4: Integrate Renderer into CLI Commands

**Goal:** Refactor all CLI command functions to use the globally selected renderer instance instead of calling `display.*` functions directly.

*   **(Red) Test:** No new unit tests. This relies on the correctness of the renderer unit tests (Steps 2 & 3) and manual/integration testing.
*   **(Green) Code:**
    *   Modify `sologm/cli/game.py`:
        *   Ensure command functions accept `ctx: typer.Context`.
        *   Access the renderer via `renderer: Renderer = ctx.obj['renderer']`.
        *   Access the console via `console: Console = ctx.obj['console']` (if needed directly).
        *   In `game_info`, replace `display_game_info(console, game, latest_scene)` with `renderer.display_game_info(game, latest_scene)`.
        *   In `list_games`, replace `display_games_table(...)` with `renderer.display_games_table(...)`.
        *   In `game_status`, replace `display_game_status(...)` with `renderer.display_game_status(...)`. (Note: `display_game_status` itself likely calls other display methods internally. When moved to `RichRenderer`, it should call `self.display_sub_component`. The `MarkdownRenderer` version will need to construct its Markdown equivalent).
        *   Replace any direct `console.print("[red]Error...")` calls in `except` blocks with `renderer.display_error("Error message...")`.
    *   **Repeat for all other command modules** (`act.py`, `scene.py`, `event.py`, `dice.py`, `oracle.py`):
        *   Import the renderer.
        *   Replace all calls to `display.*` functions with calls to the corresponding `renderer.*` methods.
        *   Replace direct error printing with `renderer.display_error()`.
*   **(Refactor) Code:** Ensure consistency in renderer usage across all commands. Verify imports.

---

### Phase 5: Final Cleanup & Documentation

**Goal:** Tidy up the codebase, remove obsolete files/functions, and update documentation.

*   **(Red) Test:** Run all existing tests (`pytest`). They should pass. Manually test key commands with and without `--no-ui`.
*   **(Green) Code:**
    *   If `sologm/cli/utils/display.py` is now empty (except potentially for shared helpers like `truncate_text`, `StyledText`), consider removing it or renaming it (e.g., `sologm/cli/utils/text_helpers.py`). Update imports if renamed.
    *   Remove `sologm/cli/utils/tests/test_display.py` if all tests have been moved/adapted.
    *   Update docstrings for modified functions and new classes/methods.
    *   Add documentation for the `--no-ui` flag in the main help text or relevant sections.
*   **(Refactor) Code:** Review code for clarity, consistency, and adherence to conventions.

## 4. Future Considerations

*   Consider more advanced dependency injection patterns if application complexity grows significantly beyond `ctx.obj` capabilities.
*   Further unify `MarkdownRenderer` logic with `sologm/cli/utils/markdown.py` if significant overlap exists.
*   Consider adding more renderer types (JSON, HTML) in the future by implementing the `Renderer` interface.
````
