features/act_narrative/tdd.md# Technical Design Document: Act Narrative Generation

**Version:** 1.0
**Date:** 2025-05-02
**Author:** AI Assistant (acting as Developer)
**Status:** Draft
**Related PRD:** features/act_narrative/prd.md

## 1. Introduction

This document details the technical design for implementing the AI-Powered Act Narrative Generation feature as specified in the corresponding PRD. The goal is to generate a prose narrative in Markdown format based on the structured data of a game's active act, incorporating user guidance and allowing for iterative refinement.

## 2. Goals

*   Implement the `sologm act narrative` CLI command.
*   Integrate user guidance collection via `StructuredEditor`.
*   Develop AI prompt engineering for narrative generation.
*   Implement the core logic in `ActManager` for data preparation and AI interaction.
*   Add rendering capabilities for Markdown output.
*   Implement the post-generation feedback loop (Accept/Edit/Regenerate/Cancel).

## 3. Proposed Solution Overview

The feature will be implemented by adding a new command to `sologm.cli.act`. This command will orchestrate the process:
1.  Validate the active game and act context.
2.  Collect user guidance for tone, style, focus, etc., using `StructuredEditor`.
3.  Call a new method in `ActManager` to prepare data (including previous act summary) and generate the narrative via `AnthropicClient`.
4.  Display the generated Markdown using the `Renderer`.
5.  Enter a feedback loop allowing the user to accept, edit (using `click.edit`), or regenerate (collecting new feedback via `StructuredEditor` and calling the manager again).

## 4. Implementation Details

### 4.1. `sologm.cli.act` (`act_app`)

*   **New Command:** Add `@act_app.command("narrative")`.
    *   Function signature: `def generate_narrative(ctx: typer.Context) -> None:`
    *   Docstring: Explain the command's purpose, referencing the PRD user stories.
*   **Context Validation:**
    *   Get `renderer` and `console` from `ctx.obj`.
    *   Use `with get_db_context() as session:` for session management.
    *   Instantiate `GameManager` and `ActManager` with the session.
    *   Validate active game using `game_manager.get_active_game()`. Display error via `renderer` and exit if none.
    *   Validate active act using `act_manager.validate_active_act()`. Display error via `renderer` and exit if none.
*   **User Guidance Collection:**
    *   Define `FieldConfig` list for the guidance editor:
        *   `tone_style` (Text, Optional)
        *   `point_of_view` (Text, Optional)
        *   `key_focus` (TextArea, Optional)
        *   `other_instructions` (TextArea, Optional)
    *   Create `StructuredEditorConfig` with these fields.
    *   Call a new helper function `_collect_narrative_guidance(act, game, console, renderer)` which uses `edit_structured_data` to get the guidance dictionary. Return `None` if cancelled. Exit command if `None`.
*   **Initial AI Call:**
    *   Call a new `act_manager.generate_act_narrative(act_id, user_guidance)` method (see 4.3).
    *   Wrap the call in a `try...except APIError` block, displaying errors via `renderer`.
    *   Display a "Generating..." message via `renderer`.
*   **Output Display:**
    *   Call a new `renderer.display_markdown(generated_markdown_string)` method (see 4.5).
*   **Feedback Loop:**
    *   Implement a `while True:` loop.
    *   Inside the loop, call a new `renderer.display_narrative_feedback_prompt(console)` method which returns "A", "E", "R", or "C".
    *   **Accept (`A`):** Break the loop.
    *   **Edit (`E`):**
        *   Call `click.edit(generated_markdown_string)`.
        *   If the result is not `None` and different from the original, update `generated_markdown_string`. Display the edited version using `renderer.display_markdown()`. Break the loop.
        *   If `None` or unchanged, display a message via `renderer` and continue the loop.
    *   **Regenerate (`R`):**
        *   Call a new helper function `_collect_narrative_regeneration_feedback(previous_narrative, act, game, console, renderer, original_guidance)` similar to the one in `complete --ai`. This function uses `edit_structured_data` to get feedback and potentially updated guidance. Return `None` if cancelled.
        *   If feedback is collected:
            *   Call `act_manager.generate_act_narrative(act_id, updated_guidance, previous_narrative, feedback)`.
            *   Update `generated_markdown_string` with the new result.
            *   Display the new result via `renderer.display_markdown()`.
            *   Continue the loop.
        *   If feedback collection is cancelled, continue the loop.
    *   **Cancel (`C`):** Display cancellation message via `renderer`. Break the loop.
*   **Final Output:** After the loop breaks (Accept or Edit), potentially display a final confirmation message via `renderer`.

### 4.2. `sologm.core.prompts.act.ActPrompts`

*   **New Method:** `build_narrative_prompt(narrative_data: Dict) -> str`:
    *   Accepts a dictionary containing `game`, `act`, `previous_act_summary` (Optional), `scenes` (with ordered `events`), and `user_guidance` (Optional Dict).
    *   Construct the prompt string:
        *   System instruction: "You are a master storyteller..."
        *   Game Information section.
        *   Previous Act Summary section (if provided), clearly labeled as context.
        *   Current Act Information section (title, sequence).
        *   Scenes section: Iterate through scenes, listing title, description, and chronologically ordered events. Include event timestamps if available and useful.
        *   User Guidance section (if provided): Clearly label and include `tone_style`, `point_of_view`, etc.
        *   Task Instruction: "Write a compelling narrative in Markdown format..."
*   **New Method (for Regeneration):** `build_narrative_regeneration_prompt(narrative_data: Dict, previous_narrative: str, feedback: str) -> str`:
    *   Similar to `build_narrative_prompt` but adds:
        *   Previous Narrative section (labeled).
        *   User Feedback section (labeled).
        *   Modified Task Instruction: "Generate a *new* narrative incorporating the user feedback..."

### 4.3. `sologm.core.act.ActManager`

*   **New Method:** `prepare_act_data_for_narrative(self, act_id: str) -> Dict`:
    *   Similar to `prepare_act_data_for_summary`, but fetches additional data:
        *   Fetch the `Act` instance.
        *   Fetch the associated `Game`.
        *   Fetch the *previous* act in sequence for the same game (`session.query(Act).filter(...).order_by(Act.sequence.desc()).first()`). Get its summary.
        *   Fetch all `Scenes` for the act, ordered by `sequence`.
        *   For each scene, fetch all `Events`, ordered by `created_at`. Include `source_name` and `timestamp`.
    *   Return a dictionary containing structured `game`, `act`, `previous_act_summary`, and `scenes` (with nested `events`).
*   **New Method:** `generate_act_narrative(self, act_id: str, user_guidance: Optional[Dict] = None, previous_narrative: Optional[str] = None, feedback: Optional[str] = None) -> str`:
    *   Call `prepare_act_data_for_narrative(act_id)`.
    *   Add `user_guidance` to the prepared data dictionary.
    *   If `previous_narrative` and `feedback` are provided:
        *   Call `ActPrompts.build_narrative_regeneration_prompt(...)`.
    *   Else:
        *   Call `ActPrompts.build_narrative_prompt(...)`.
    *   Instantiate `AnthropicClient`.
    *   Call `client.send_message(...)` with the generated prompt. Use appropriate `max_tokens` (e.g., 2048 or higher, consider making configurable later).
    *   Return the raw string response from the AI.
    *   Handle potential `AnthropicClient` exceptions and re-raise as `APIError`.

### 4.4. `sologm.cli.utils.structured_editor`

*   No changes strictly required, but ensure the `FieldConfig` and `StructuredEditorConfig` used by the new CLI command are correctly defined as per section 4.1.
*   The existing `edit_structured_data` function will be used for collecting initial guidance and regeneration feedback.

### 4.5. `sologm.cli.rendering`

*   **`base.Renderer`:**
    *   Add abstract method: `@abc.abstractmethod def display_markdown(self, markdown_content: str) -> None:`
    *   Add abstract method: `@abc.abstractmethod def display_narrative_feedback_prompt(self, console: "Console") -> Optional[str]:` (Returns "A", "E", "R", "C", or None if cancelled).
*   **`rich_renderer.RichRenderer`:**
    *   Implement `display_markdown`:
        *   Import `from rich.markdown import Markdown`.
        *   `self.console.print(Markdown(markdown_content))`.
    *   Implement `display_narrative_feedback_prompt`:
        *   Use `rich.prompt.Prompt.ask()` with choices `["A", "E", "R", "C"]` and appropriate text. Handle `InvalidResponse` and potential cancellation. Return the uppercase choice or `None`.
*   **`markdown_renderer.MarkdownRenderer`:**
    *   Implement `display_markdown`:
        *   Simply print the `markdown_content` string directly using `_print_markdown`.
    *   Implement `display_narrative_feedback_prompt`:
        *   Use `click.prompt()` with `type=click.Choice(...)` and `show_choices=True`. Handle potential `Abort`. Return the uppercase choice or `None`.

## 5. Data Structures

*   **User Guidance Dictionary (Input to Manager):**
    ```python
    {
        "tone_style": Optional[str],
        "point_of_view": Optional[str],
        "key_focus": Optional[str],
        "other_instructions": Optional[str]
    }
    ```
*   **Narrative Data Dictionary (Input to Prompt Builder):**
    ```python
    {
        "game": {"id": str, "name": str, "description": str},
        "act": {"id": str, "sequence": int, "title": Optional[str], "summary": Optional[str]},
        "previous_act_summary": Optional[str],
        "scenes": [
            {
                "id": str,
                "sequence": int,
                "title": Optional[str],
                "description": Optional[str],
                "events": [
                    {
                        "id": str,
                        "description": str,
                        "source_name": str,
                        "created_at": str # ISO format
                    },
                    # ... more events
                ]
            },
            # ... more scenes
        ],
        "user_guidance": Optional[Dict] # Structure from above
    }
    ```

## 6. Error Handling

*   **CLI:** Catch `GameError` during context validation and `APIError` during AI calls. Display user-friendly messages via the `renderer`. Handle editor cancellations gracefully.
*   **Manager:** Catch `AnthropicClient` errors and raise `APIError`. `prepare_act_data_for_narrative` should raise `GameError` if act/game not found.
*   **Editor:** `edit_structured_data` handles validation errors and editor launch issues internally, returning appropriate `EditorStatus`.

## 7. Testing Strategy

*   **Unit Tests:**
    *   `ActManager.prepare_act_data_for_narrative`: Test data structure, inclusion of previous act summary, ordering of scenes/events.
    *   `ActManager.generate_act_narrative`: Mock `prepare_act_data_for_narrative`, `ActPrompts`, and `AnthropicClient`. Verify correct prompt builder is called based on args, client is called, and response is returned. Test `APIError` handling.
    *   `ActPrompts`: Test `build_narrative_prompt` and `build_narrative_regeneration_prompt` output structure with various inputs (with/without optional fields).
    *   `cli.act`: Mock manager methods, editor functions (`edit_structured_data`, `click.edit`), and renderer methods. Test command flow, context validation, argument handling, editor calls, manager calls, and feedback loop logic.
    *   `Renderer` implementations: Test `display_markdown` and `display_narrative_feedback_prompt` methods.
*   **Integration Tests:**
    *   Test the full `sologm act narrative` command flow using test fixtures (`session_context`, factories) and mocking only the `AnthropicClient` to simulate AI responses and errors. Verify data persistence and flow through different feedback loop choices (Accept, Edit, Regenerate, Cancel).

## 8. Future Considerations (from PRD)

*   Handling token limits for very long acts.
*   Preset narrative styles.
*   Saving output to file (`--output`).
*   Using event timestamps more explicitly.

This design provides a detailed roadmap for implementing the Act Narrative Generation feature.
