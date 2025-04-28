# Implementation Plan: Pluggable Renderers & Plain Text Output Mode

**Version:** 1.1
**Status:** Ready
**Date:** 2025-04-20

## 1. Overview

This plan outlines the steps required to implement a pluggable renderer system for the SoloGM CLI. The goal is to allow users to switch between the default Rich-based UI and a plain Markdown output format using a `--no-ui` flag. This involves creating a renderer abstraction, implementing Rich and Markdown versions, integrating the selection mechanism, and refactoring existing commands to use the new system.

**Reference Documents:**

*   **Product Requirements:** `features/renderers/prd.md`
*   **Technical Design:** `features/renderers/tdd.md`

**Target Audience:** This plan is designed for an implementer (e.g., an intern) familiar with Python and the project's structure.

## 2. Implementation Steps

Follow these steps in order. Test frequently after each major step, especially during the command refactoring phase. Commit your changes incrementally with clear messages.

---

### **Phase 1: One-Time Setup & Core Implementation**

**(These steps are performed once to set up the rendering framework.)**

#### Step 1.1: Setup Core Renderer Structure

**(Goal: Create the necessary files and define the base interface)**

*   **Action:** Create/verify the following file structure:
    *   `sologm/cli/rendering/` (Directory)
    *   `sologm/cli/rendering/__init__.py` (Empty File)
    *   `sologm/cli/rendering/base.py` (File)
    *   `sologm/cli/rendering/rich_renderer.py` (File)
    *   `sologm/cli/rendering/markdown_renderer.py` (File)
*   **Action:** Review `sologm/cli/rendering/base.py`.
    *   Ensure it defines the `Renderer` Abstract Base Class (ABC).
    *   Verify all necessary display methods are present as `@abc.abstractmethod`s.
    *   Confirm the `__init__` signature accepts `console: Console`.
*   **Action:** Review `sologm/cli/rendering/rich_renderer.py`.
    *   Ensure `RichRenderer` class inherits from `Renderer`.
    *   Ensure `__init__` takes `console: Console`.
    *   Verify necessary imports.
*   **Action:** Review `sologm/cli/rendering/markdown_renderer.py`.
    *   Ensure `MarkdownRenderer` class inherits from `Renderer`.
    *   Ensure `__init__` takes `console: Console`.
    *   Verify necessary imports.

#### Step 1.2: Complete Renderer Method Implementations

**(Goal: Ensure both renderers fully implement the `Renderer` interface)**

*   **File:** `sologm/cli/rendering/rich_renderer.py`
    *   **Action:** Implement any methods currently marked with `raise NotImplementedError` or `pass`. Use Rich components and styling conventions.
    *   **Specific Methods:** `display_act_completion_success`, `display_act_ai_feedback_prompt`, `display_act_edited_content_preview`, `display_act_ai_generation_results`.
*   **File:** `sologm/cli/rendering/markdown_renderer.py`
    *   **Action:** Implement any methods currently marked with `raise NotImplementedError` or `pass`. Generate standard Markdown output.
    *   **Specific Methods:** `display_game_status`. Review `display_act_ai_feedback_prompt` for clarity.

#### Step 1.3: Implement Flag and Renderer Injection

**(Goal: Add the `--no-ui` flag and logic to select/inject the renderer)**

*   **File:** `sologm/cli/main.py`
    *   **Action:** Add the `--no-ui` boolean `typer.Option` to the `main()` callback.
    *   **Action:** Ensure a single `console = Console()` instance is created.
    *   **Action:** Add the conditional logic (`if no_ui: ... else: ...`) to instantiate the correct `Renderer`.
    *   **Action:** Define the `AppContext` class (or use a dictionary).
    *   **Action:** Store the selected renderer instance onto `ctx.obj`. Ensure this happens early, before potential errors needing display.

---

### **Phase 2: Iterative Command Refactoring**

**(This phase involves repeating the same process for multiple command files.)**

#### Step 2.1: Refactor CLI Commands

**(Goal: Modify all commands to use the injected renderer)**

*   **Action:** Perform the following sub-steps **iteratively** for each file provided.

    *   **Sub-steps for *each* command function within the current file:**
        1.  **Add Context Parameter:** Add `ctx: typer.Context` as the first parameter.
        2.  **Remove Old Imports:** Remove imports from `sologm.cli.utils.display` and direct `Console` imports if applicable.
        3.  **Get Renderer:** Add `renderer = ctx.obj["renderer"]` (adjust if using dict).
        4.  **Replace Display Calls:** Replace old `display_*()` calls with `renderer.display_*()` calls, passing data arguments.
        5.  **Replace Direct Prints:** Replace `console.print("[style]...")` for success, error, warning with `renderer.display_success()`, `renderer.display_error()`, `renderer.display_warning()`. Use `renderer.display_message()` for simple info.
        6.  **Error Handling:** Ensure `renderer.display_error()` is called in `except` blocks, followed by `raise typer.Exit(code=1)`.
        7.  **Exception:** Do *not* modify the `dump_game` command's direct `print()` call in `game.py`.

    *   **Testing (After *each* file refactor):**
        1.  Run all commands in the *modified file* without `--no-ui`. Verify Rich output.
        2.  Run all commands in the *modified file* with `--no-ui`. Verify Markdown output.
        3.  Test error conditions for the commands in the modified file.

    *   **Commit:** Commit the changes for the refactored file with a clear message (e.g., "refactor: Use renderer in game commands").

---

### **Phase 3: Finalization**

**(These steps are performed once after all implementation and refactoring are complete.)**

#### Step 3.1: Final Testing and Documentation

**(Goal: Ensure the feature works correctly and is documented)**

*   **Action:** Perform comprehensive manual testing of *all* SoloGM commands with and without `--no-ui`. Check formatting, consistency, edge cases, and error display.
*   **Action (Optional):** Request a code review.
*   **Action:** Update user documentation (README, help text) to mention the `--no-ui` flag.
*   **Action:** Update developer documentation (e.g., `conventions/display.md`, architecture docs) if necessary.

---

## 3. Guidance for Implementer

*   **Understand the Goal:** Read the PRD and TDD carefully.
*   **Work Incrementally:** Follow the phases and steps. Focus on one file at a time during Phase 2.
*   **Test Often:** Especially after refactoring each command file in Phase 2.
*   **Refer to TDD:** Use `features/renderers/tdd.md` for technical details.
*   **Renderer Methods:** Use `sologm/cli/rendering/base.py` to find the correct renderer method names.
*   **Ask Questions:** Clarify any doubts about the plan, TDD, or code.
*   **Commit Frequently:** Save progress regularly, especially after completing each file in Phase 2.

## 4. Definition of Done

*   All steps in this plan are completed.
*   Phase 1 setup is done.
*   `RichRenderer` and `MarkdownRenderer` fully implement the `Renderer` interface.
*   `--no-ui` flag works, and renderer injection is correct in `main.py`.
*   All command files listed in Step 2.1 are refactored.
*   All commands produce correct output in both Rich and Markdown modes.
*   Error handling uses the renderer system.
*   User documentation is updated.
*   Code adheres to project style conventions.
