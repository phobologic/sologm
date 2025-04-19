# Detailed Plan: Completing Phase 2 (RichRenderer Implementation)

This document outlines the detailed steps for completing Phase 2, Step 3 of the TDD plan (`features/renderers/tdd.md`), which involves migrating all remaining display functions from `sologm/cli/utils/display.py` into the `sologm/cli/rendering/rich_renderer.py` class.

**Goal:** Ensure `RichRenderer` fully implements the `Renderer` interface by incorporating all existing Rich display logic, passing adapted tests.

**General Red-Green-Refactor Cycle (for each function):**

1.  **(Red) Adapt Test:**
    *   Locate the corresponding test(s) for the function in `sologm/cli/utils/tests/test_display.py`.
    *   Move the test(s) to `sologm/cli/rendering/tests/test_rich_renderer.py`.
    *   Modify the test setup: Instantiate `renderer = RichRenderer(mock_console)`.
    *   Modify the test execution: Call the method on the `renderer` instance (e.g., `renderer.display_game_info(...)`) instead of the old standalone function.
    *   Run *only* the adapted test(s). They should fail (typically with `NotImplementedError` or `AttributeError`).

2.  **(Green) Migrate Code:**
    *   Copy the function's implementation from `sologm/cli/utils/display.py` into the `RichRenderer` class in `sologm/cli/rendering/rich_renderer.py` as a method.
    *   Adapt the method code:
        *   Replace the `console: Console` parameter with `self.console`.
        *   Add all necessary imports to the top of `rich_renderer.py` (e.g., `Panel`, `Table`, `Text`, models like `Game`, `Scene`, `Act`, `Event`, `Interpretation`, `InterpretationSet`, utilities like `StyledText`, `BORDER_STYLES`, `truncate_text`, `SceneStatus`, manager types for type hinting if needed).
        *   If the function internally calls other *display* functions that are also being moved (e.g., `display_interpretation_set` calls `display_interpretation`), update these internal calls to use `self.method_name(...)`.
    *   Run the adapted test(s) again. They should now pass.

3.  **(Refactor) Cleanup:**
    *   Review the newly moved method in `RichRenderer` for code style, clarity, and correct docstring.
    *   Delete the original function definition from `sologm/cli/utils/display.py`.
    *   Delete the original test(s) from `sologm/cli/utils/tests/test_display.py`.

**Migration Order and Specifics:**

We will migrate functions in the following order:

1.  **`display_interpretation`**
    *   **Tests to Move:** `test_display_interpretation`, `test_display_interpretation_selected`.
    *   **Imports Needed:** `Panel`, `StyledText`, `BORDER_STYLES`, `Interpretation`.

2.  **`display_scene_info`**
    *   **Tests to Move:** `test_display_scene_info` (or adapt a general one).
    *   **Imports Needed:** `Panel`, `StyledText`, `BORDER_STYLES`, `Scene`, `Text`.

3.  **`display_game_info`**
    *   **Tests to Move:** `test_display_game_info`, `test_display_game_info_no_scene`.
    *   **Imports Needed:** `Panel`, `StyledText`, `BORDER_STYLES`, `Game`, `Scene`, `Text`.

4.  **`display_act_info`**
    *   **Tests to Move:** `test_display_act_info` (or adapt).
    *   **Imports Needed:** `Panel`, `Table`, `StyledText`, `BORDER_STYLES`, `Act`, `Text`, `truncate_text`.
    *   **Note:** Check internal logic for displaying the scenes table.

5.  **Table Functions (Process one by one):**
    *   `display_events_table`:
        *   **Tests:** `test_display_events_table_*`.
        *   **Imports:** `Table`, `Panel`, `StyledText`, `BORDER_STYLES`, `Event`, `Scene`, `truncate_text`.
    *   `display_games_table`:
        *   **Tests:** `test_display_games_table_*`.
        *   **Imports:** `Table`, `Panel`, `StyledText`, `BORDER_STYLES`, `Game`.
    *   `display_scenes_table`:
        *   **Tests:** `test_display_scenes_table_*`.
        *   **Imports:** `Table`, `Panel`, `StyledText`, `BORDER_STYLES`, `Scene`, `SceneStatus`.
    *   `display_acts_table`:
        *   **Tests:** `test_display_acts_table` (or adapt).
        *   **Imports:** `Table`, `Panel`, `StyledText`, `BORDER_STYLES`, `Act`.
    *   `display_interpretation_sets_table`:
        *   **Tests:** `test_display_interpretation_sets_table`.
        *   **Imports:** `Table`, `Panel`, `StyledText`, `BORDER_STYLES`, `InterpretationSet`, `truncate_text`.

6.  **`display_interpretation_set`**
    *   **Tests to Move:** `test_display_interpretation_set`, `test_display_interpretation_set_no_context`.
    *   **Imports Needed:** `Panel`, `StyledText`, `BORDER_STYLES`, `InterpretationSet`.
    *   **Crucial Adaptation:** Update internal call `display_interpretation(...)` to `self.display_interpretation(...)`.

7.  **`display_interpretation_status`**
    *   **Tests to Move:** `test_display_interpretation_status` (or adapt).
    *   **Imports Needed:** `Panel`, `StyledText`, `BORDER_STYLES`, `InterpretationSet`, `Text`.

8.  **AI Act Functions (Process one by one):**
    *   `display_act_ai_generation_results`:
        *   **Tests:** `test_display_act_ai_generation_results`.
        *   **Imports:** `Panel`, `StyledText`, `BORDER_STYLES`, `Act`.
    *   `display_act_completion_success`:
        *   **Tests:** `test_display_act_completion_success`.
        *   **Imports:** `StyledText`, `Act`.
    *   `display_act_ai_feedback_prompt`:
        *   **Tests:** `test_display_act_ai_feedback_prompt`. Adapt test to mock `rich.prompt.Prompt.ask`.
        *   **Imports:** `StyledText`, `Prompt`. Check if `self.console` is needed for `Prompt.ask`.
    *   `display_act_edited_content_preview`:
        *   **Tests:** `test_display_act_edited_content_preview`.
        *   **Imports:** `Panel`, `StyledText`, `BORDER_STYLES`.

9.  **`display_game_status` (Complex Case)**
    *   **(Red):**
        *   Move all `test_display_game_status_*` tests to `test_rich_renderer.py`. Adapt calls to `renderer.display_game_status(...)`.
        *   Move all helper tests (`test_create_*_panel`, `test_calculate_truncation_length`) to `test_rich_renderer.py`. Adapt calls to instantiate `RichRenderer` and call `renderer._create_*_panel(...)` or `renderer._calculate_truncation_length()`.
        *   Run tests (should fail).
    *   **(Green):**
        *   Move the main `display_game_status` function to `RichRenderer`.
        *   Move *all* its private helper functions (`_calculate_truncation_length`, `_create_act_panel`, `_create_game_header_panel`, `_create_scene_panels_grid`, `_create_events_panel`, `_create_oracle_panel`, `_create_pending_oracle_panel`, `_create_recent_oracle_panel`, `_create_empty_oracle_panel`, `_create_dice_rolls_panel`) into `RichRenderer` as private methods (prefixed with `_`).
        *   Adapt `console` parameter to `self.console` in all moved methods.
        *   Update calls *within* `display_game_status` and its helpers to use `self.` (e.g., `self._create_act_panel(...)`, `self._calculate_truncation_length()`).
        *   Add all necessary imports to `rich_renderer.py`: `Panel`, `Table`, `Text`, `StyledText`, `BORDER_STYLES`, all relevant models (`Game`, `Act`, `Scene`, `Event`, `DiceRoll`, `InterpretationSet`, `Interpretation`), `SceneManager`, `OracleManager`, `SceneStatus`, `TYPE_CHECKING`.
        *   Run tests (should pass).
    *   **(Refactor):** Clean up methods. Remove original function and all helpers from `display.py`. Remove original tests from `test_display.py`.

10. **`display_error` (New Method)**
    *   **(Red):** Write a new test `test_display_error` in `test_rich_renderer.py`. Instantiate `renderer = RichRenderer(mock_console)`. Call `renderer.display_error("Test error")`. Assert `mock_console.print.assert_called_with("[red]Error: Test error[/red]")`. Run test (should fail).
    *   **(Green):** Implement `display_error(self, message: str)` in `RichRenderer` using `self.console.print(f"[red]Error: {message}[/red]")`. Run test (should pass).
    *   **(Refactor):** Ensure style consistency.

**Utilities Check:**

*   After migrating all functions above, verify that `sologm/cli/utils/display.py` only contains shared utilities like `truncate_text`, `format_metadata`, `METADATA_SEPARATOR`, and potentially `get_event_context_header`.
*   Verify that `sologm/cli/utils/tests/test_display.py` only contains tests for these remaining utilities (e.g., `test_truncate_text`, `test_format_metadata`).

**Completion:** Once all steps are done, `RichRenderer` will be fully implemented, and `sologm/cli/utils/display.py` will be significantly reduced, containing only shared helpers.
