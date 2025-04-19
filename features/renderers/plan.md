# Implementation Plan: Pluggable Renderers & Markdown Output

**Version:** 1.0
**Status:** Proposed
**Date:** 2025-04-19
**Related PRD:** `features/renderers/prd.md`
**Related TDD:** `features/renderers/tdd.md`

This document outlines the phased implementation plan for the pluggable renderer feature, enabling Markdown output via a `--no-ui` flag. Each phase follows the TDD approach where applicable.

## Phase 1: Setup Renderer Structure & Flag

**Goal:** Establish the foundational directory structure, the abstract `Renderer` interface, and the global `--no-ui` flag with basic selection logic in `main.py`.

**Steps:**

1.  **Create Directories:**
    *   `sologm/cli/rendering/`
    *   `sologm/cli/rendering/tests/` (Test directory alongside code)
2.  **Create Init Files:**
    *   `sologm/cli/rendering/__init__.py` (can be empty or add a docstring)
    *   `sologm/cli/rendering/tests/__init__.py` (empty)
3.  **Create Base Renderer Interface (`sologm/cli/rendering/base.py`):**
    *   Define `Renderer` as an `abc.ABC`.
    *   Implement `__init__(self, console: Console, markdown_mode: bool = False)` to store `console` and `markdown_mode`.
    *   Define `@abstractmethod` stubs for *all* public functions currently in `sologm/cli/utils/display.py`. Ensure method signatures match the original functions precisely regarding the data they need (e.g., `game: Game`, `roll: DiceRoll`, `events: List[Event]`, etc.).
        *   `display_dice_roll(self, roll: DiceRoll)`
        *   `display_interpretation(self, interp: Interpretation, selected: bool = False, sequence: Optional[int] = None)`
        *   `display_events_table(self, events: List[Event], scene: Scene, truncate_descriptions: bool = True, max_description_length: int = 80)`
        *   `display_games_table(self, games: List[Game], active_game: Optional[Game] = None)`
        *   `display_scenes_table(self, scenes: List[Scene], active_scene_id: Optional[str] = None)`
        *   `display_game_info(self, game: Game, active_scene: Optional[Scene] = None)`
        *   `display_interpretation_set(self, interp_set: InterpretationSet, show_context: bool = True)`
        *   `display_scene_info(self, scene: Scene)`
        *   `display_game_status(self, game: Game, latest_act: Optional[Act], latest_scene: Optional[Scene], recent_events: List[Event], scene_manager: Optional["SceneManager"] = None, oracle_manager: Optional["OracleManager"] = None, recent_rolls: Optional[List[DiceRoll]] = None, is_act_active: bool = False, is_scene_active: bool = False)`
        *   `display_acts_table(self, acts: List[Act], active_act_id: Optional[str] = None)`
        *   `display_act_info(self, act: Act, game_name: str)`
        *   `display_interpretation_sets_table(self, interp_sets: List[InterpretationSet])`
        *   `display_interpretation_status(self, interp_set: InterpretationSet)`
        *   `display_act_ai_generation_results(self, results: Dict[str, str], act: Act)`
        *   `display_act_completion_success(self, completed_act: Act)`
        *   `display_act_ai_feedback_prompt(self, console: Console)` # Note: May need adjustment if prompt depends on Rich
        *   `display_act_edited_content_preview(self, edited_results: Dict[str, str])`
        *   `display_error(self, message: str)` # Add a dedicated error display method
4.  **Modify `sologm/cli/main.py`:**
    *   Add the `--no-ui: bool = typer.Option(False, "--no-ui", help="Disable rich UI elements and use Markdown output.")` parameter to the `main` callback.
    *   Ensure the `main` callback signature includes `ctx: typer.Context`.
    *   Add placeholder imports for renderers: `from sologm.cli.rendering.base import Renderer # Placeholder imports below`
    *   In the `main` callback (after logger/config setup, before DB init):
        *   Implement the selection logic:
            ```python
            selected_renderer: Optional[Renderer] = None # Local variable
            if no_ui:
                # from sologm.cli.rendering.markdown_renderer import MarkdownRenderer # Placeholder
                # selected_renderer = MarkdownRenderer(console, markdown_mode=True) # Placeholder
                logger.debug("MarkdownRenderer selected (placeholder implementation)")
                pass # Replace with actual instantiation later
            else:
                # from sologm.cli.rendering.rich_renderer import RichRenderer # Placeholder
                # selected_renderer = RichRenderer(console, markdown_mode=False) # Placeholder
                logger.debug("RichRenderer selected (placeholder implementation)")
                pass # Replace with actual instantiation later

            if selected_renderer is None:
                 # This check ensures we don't proceed if instantiation fails later
                 logger.critical("Renderer could not be instantiated!")
                 raise typer.Exit(code=1)

            # Store renderer and console on context object
            if ctx.obj is None:
                ctx.obj = {}
            ctx.obj["renderer"] = selected_renderer # Store the (placeholder) renderer
            ctx.obj["console"] = console # Store the console instance
            logger.debug("Renderer and console stored in Typer context.")
            ```

**Result:** Foundational structure is in place. No tests pass yet, but the framework for the renderers exists. The `--no-ui` flag is available but doesn't fully function.

---

## Phase 2: Implement RichRenderer (Refactor display.py)

**Goal:** Move all existing display logic from `sologm/cli/utils/display.py` into a concrete `RichRenderer` class, ensuring it passes adapted tests from `sologm/cli/utils/tests/test_display.py`.

**Steps:**

1.  **Create Files:**
    *   `sologm/cli/rendering/rich_renderer.py`
    *   `sologm/cli/rendering/tests/test_rich_renderer.py`
2.  **Define `RichRenderer` Class (`rich_renderer.py`):**
    *   `from ..base import Renderer` (Adjust import based on final structure)
    *   `class RichRenderer(Renderer):`
    *   Implement `__init__` calling `super().__init__(...)`.
3.  **Implement TDD Cycle for each display function:**
    *   **Select Function:** Start with a simple function from `display.py` (e.g., `display_dice_roll`).
    *   **(Test - Red):** Copy the corresponding test (e.g., `test_display_dice_roll`) from `sologm/cli/utils/tests/test_display.py` to `sologm/cli/rendering/tests/test_rich_renderer.py`.
        *   Adapt the test: Import `RichRenderer`. Instantiate `renderer = RichRenderer(mock_console)`. Call `renderer.display_dice_roll(test_data)`. Keep assertions (e.g., `mock_console.print.called`). The test should fail (method not implemented).
    *   **(Code - Green):** Copy the *implementation* of the selected function (e.g., `display_dice_roll`) from `sologm/cli/utils/display.py` into the `RichRenderer` class as a method.
        *   Adapt the code: Replace `console` parameter with `self.console`. Add necessary imports to `rich_renderer.py` (`Panel`, `Text`, `StyledText`, models, etc.). Ensure helper functions like `truncate_text` are imported correctly (from `sologm.cli.utils.display` for now).
    *   **(Test - Green):** Run the specific test you adapted. It should now pass.
    *   **(Refactor):** Clean up the moved method (remove redundant comments, ensure style consistency). Remove the original function from `sologm/cli/utils/display.py`.
    *   **Repeat:** Repeat this Red-Green-Refactor cycle for *every* public function remaining in `sologm/cli/utils/display.py`, including helper functions prefixed with `_` if they are complex and tightly coupled to a specific display function (simpler ones might stay in `utils`). Add a `display_error` method implementation using `console.print("[red]...")`.
4.  **Update `main.py`:** Replace the placeholder `RichRenderer` instantiation with the actual one: `from sologm.cli.rendering.rich_renderer import RichRenderer`.
5.  **Shared Utilities:** Identify utilities like `truncate_text` and `StyledText`. Keep them in `sologm/cli/utils/display.py` (or move to a new `sologm/cli/utils/text_helpers.py`) for now, ensuring `RichRenderer` imports them correctly.

**Result:** `RichRenderer` is fully implemented and tested. `sologm/cli/utils/display.py` is significantly smaller or empty (except shared utils). `main.py` correctly instantiates `RichRenderer`. All tests in `sologm/cli/rendering/tests/test_rich_renderer.py` pass. The application should function identically to before when `--no-ui` is *not* used (though commands haven't been updated to use the renderer yet).

---

## Phase 3: Implement MarkdownRenderer

**Goal:** Implement the `MarkdownRenderer` class, ensuring each method produces the correct Markdown output as defined by tests.

**Steps:**

1.  **Create Files:**
    *   `sologm/cli/rendering/markdown_renderer.py`
    *   `sologm/cli/rendering/tests/test_markdown_renderer.py`
2.  **Define `MarkdownRenderer` Class (`markdown_renderer.py`):**
    *   `from ..base import Renderer` (Adjust import)
    *   `class MarkdownRenderer(Renderer):`
    *   Implement `__init__` calling `super().__init__(...)`.
3.  **Implement TDD Cycle for each display method:**
    *   **Select Method:** Start with a simple method from the `Renderer` interface (e.g., `display_dice_roll`).
    *   **(Test - Red):** Write a new test in `sologm/cli/rendering/tests/test_markdown_renderer.py` (e.g., `test_display_dice_roll_markdown`).
        *   Use `pytest` fixtures (`mock_console`, test data). Instantiate `renderer = MarkdownRenderer(mock_console)`. Call `renderer.display_dice_roll(test_data)`.
        *   Use `mock_console.print.assert_called_once_with(...)` or `capsys` to capture output. Assert that the output matches the *exact* expected Markdown string according to the PRD (e.g., using headings, lists, bold, code spans). The test should fail.
    *   **(Code - Green):** Implement the method (e.g., `display_dice_roll`) in `MarkdownRenderer`. Use `self.console.print()` to output the simplest possible string(s) that satisfy the test assertion. Use helper functions like `truncate_text` if needed.
    *   **(Test - Green):** Run the specific test. It should now pass.
    *   **(Refactor):** Refine the Markdown generation logic.
        *   Improve formatting for clarity (newlines, indentation).
        *   Ensure adherence to PRD requirements (headings, lists, tables, blockquotes for errors).
        *   Look at `sologm/cli/utils/markdown.py` for inspiration or potentially extract small, reusable formatting helpers (e.g., a function to format a list item, a function to create a simple table row string). Avoid directly calling the large `generate_*` functions unless the renderer method's purpose *is* to dump a large section (unlikely for most methods).
        *   Ensure the test still passes after refactoring.
    *   **Repeat:** Repeat this Red-Green-Refactor cycle for *every* abstract method defined in the `Renderer` interface. Implement `display_error` using Markdown blockquotes (`> Error: ...`) or code blocks.
4.  **Update `main.py`:** Replace the placeholder `MarkdownRenderer` instantiation with the actual one: `from sologm.cli.rendering.markdown_renderer import MarkdownRenderer`.

**Result:** `MarkdownRenderer` is fully implemented and tested. `main.py` correctly instantiates `MarkdownRenderer`. All tests in `sologm/cli/rendering/tests/test_markdown_renderer.py` pass.

---

## Phase 4: Integrate Renderer into CLI Commands

**Goal:** Refactor all CLI command functions to use the selected renderer instance stored on the Typer context, removing direct calls to old display functions or `console.print` for errors.

**Steps:**

1.  **Ensure Renderer Access:** Verify that command functions accept `ctx: typer.Context` in their signatures.
2.  **Refactor Command Files:** Iterate through each CLI command file (`game.py`, `act.py`, `scene.py`, `event.py`, `dice.py`, `oracle.py`):
    *   Inside each command function, retrieve the renderer: `renderer: Renderer = ctx.obj['renderer']`.
    *   Retrieve the console if needed: `console: Console = ctx.obj['console']`.
    *   Find all calls to functions that were previously in `sologm.cli.utils.display` (e.g., `display_game_info(...)`, `display_games_table(...)`).
    *   Replace these calls with calls to the corresponding method on the retrieved `renderer` instance (e.g., `renderer.display_game_info(...)`, `renderer.display_games_table(...)`). Pass the required data. Remove the `console` argument if the original function took it.
    *   Find all direct `console.print("[red]Error...")` or similar error outputs within `except` blocks.
    *   Replace these with `renderer.display_error("Specific error message...")`.
3.  **Manual Testing:** Perform manual testing for key commands:
    *   Run commands *without* `--no-ui` and verify the output matches the previous Rich output.
    *   Run commands *with* `--no-ui` and verify the output is the expected Markdown format.
    *   Test error conditions with and without `--no-ui` to ensure errors are displayed correctly in both modes via `renderer.display_error`.

**Result:** All CLI commands delegate display logic to the active renderer. The application works correctly in both Rich and Markdown modes. Manual testing confirms functionality.

---

## Phase 5: Final Cleanup & Documentation

**Goal:** Tidy up the codebase, remove obsolete files/code, and update documentation.

**Steps:**

1.  **Review `utils/display.py`:**
    *   If the file now only contains shared helpers (`truncate_text`, `StyledText`, `METADATA_SEPARATOR`, `BORDER_STYLES`), consider renaming it to `sologm/cli/utils/text_helpers.py` or similar. Update all imports accordingly.
    *   If the file is completely empty, remove it.
2.  **Remove Old Tests:** Delete `sologm/cli/utils/tests/test_display.py` as its tests should have been moved/adapted into `sologm/cli/rendering/tests/test_rich_renderer.py`.
3.  **Update Docstrings:** Ensure all new classes (`Renderer`, `RichRenderer`, `MarkdownRenderer`) and their methods have clear, accurate docstrings. Update docstrings of refactored command functions if necessary.
4.  **Update User Documentation:** Add information about the `--no-ui` flag to the main `sologm` help text (in `main.py`) and potentially the project's README.md. Explain its purpose (Markdown output).
5.  **Run Full Test Suite:** Execute `uv run pytest -v --log-cli-level=DEBUG` to ensure all unit tests pass.
6.  **Code Review:** Perform a final review of all changed files for code style, clarity, consistency, and adherence to project conventions.

**Result:** The feature is complete, integrated, tested, documented, and the codebase is clean.
