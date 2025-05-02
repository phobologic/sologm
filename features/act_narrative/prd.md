# Product Requirements Document: Act Narrative Generation

**Version:** 1.0
**Date:** 2025-04-28
**Author:** AI Assistant (acting as PM)
**Status:** Draft

## 1. Introduction

This document outlines the requirements for a new feature in the SoloGM CLI: **AI-Powered Act Narrative Generation**. This feature aims to provide users with a way to transform the structured data of a game act (scenes, events) into a compelling prose narrative, similar to a chapter in a book or a detailed session report. This leverages AI (specifically Anthropic's models via the existing integration) to synthesize the information and user guidance into a creative output.

## 2. Goals

*   Provide users with an engaging way to review and experience the events of a completed or in-progress game act.
*   Offer a starting point for users who wish to write creative fiction or detailed session reports based on their gameplay.
*   Enhance the value of the structured data captured by SoloGM by enabling creative transformation.
*   Leverage existing AI integration and CLI frameworks for efficient implementation.

## 3. User Stories

*   As a SoloGM user, I want to run a command (`sologm act narrative`) for the current active act so that I can get an AI-generated story summarizing its events.
*   As a SoloGM user, before the AI generates the narrative, I want to provide guidance on the desired tone, style, point of view, and key focus points using an interactive editor, so the output better matches my vision.
*   As a SoloGM user, I want the AI to consider the summary of the *previous* act (if available) when generating the narrative for the current act, so there is narrative continuity.
*   As a SoloGM user, I want the generated narrative to be presented in Markdown format, so it's easy to read and copy/paste.
*   As a SoloGM user, after viewing the generated narrative, I want the option to accept it, edit it directly in my text editor, or regenerate it with new guidance, so I have control over the final output.

## 4. Functional Requirements

### 4.1. CLI Command

*   A new subcommand `narrative` shall be added under `sologm act`.
    *   `sologm act narrative`
*   The command shall operate on the currently active game and the currently active act within that game.
*   The command shall fail gracefully with an informative error message if no game is active or no act is active in the current game.

### 4.2. Data Gathering

*   Before calling the AI, the system must gather the following data:
    *   Current active Game details (name, description).
    *   Current active Act details (sequence, title, summary).
    *   Summary of the *immediately preceding* Act in the same game (if one exists).
    *   All Scenes belonging to the active Act, ordered by sequence.
    *   All Events belonging to each Scene, ordered chronologically (by `created_at`).
*   This data shall be structured appropriately for inclusion in the AI prompt.

### 4.3. User Guidance Input

*   Before the *first* AI generation attempt for a given command invocation, the system shall present the user with an interactive editor (leveraging `StructuredEditor`).
*   This editor shall collect user guidance for the AI. Required fields include:
    *   `tone_style`: Text field (e.g., "Gritty noir", "High fantasy epic", "Humorous").
    *   `point_of_view`: Text field (e.g., "Third-person limited on protagonist", "Omniscient narrator").
    *   `key_focus`: Text area (e.g., "Emphasize the party's internal conflicts", "Highlight the discovery").
    *   `other_instructions`: Text area (e.g., "Include descriptions of the weather", "Keep dialogue minimal").
*   The editor interface should clearly explain the purpose of each field.
*   The user must be able to proceed even if some or all guidance fields are left empty.
*   The user must be able to cancel the operation from this editor.

### 4.4. AI Prompt Construction

*   A new prompt template shall be created (e.g., in `sologm.core.prompts.act.ActPrompts`).
*   The prompt shall include:
    *   Clear system instructions defining the AI's role (e.g., "You are a master storyteller writing a narrative chapter based on the following game events...").
    *   The gathered Game data.
    *   The previous Act's summary (if available), clearly labeled as context.
    *   The current Act's data (Scenes, Events in order).
    *   The user guidance collected from the editor, clearly labeled (e.g., `USER GUIDANCE:`).
    *   Explicit instructions to output the narrative in **Markdown format**.
    *   Instructions for handling regeneration requests (incorporating previous narrative and feedback).

### 4.5. AI Interaction

*   The system shall use the existing `AnthropicClient` to send the constructed prompt to the AI.
*   API errors shall be caught and reported gracefully to the user.
*   The system should display an indicator while waiting for the AI response (e.g., "Generating narrative...").

### 4.6. Output Display

*   The AI-generated narrative (in Markdown) shall be displayed to the user in the terminal.
*   The `Renderer` component should be used, potentially adding a `display_markdown` method that utilizes Rich's `Markdown` rendering capabilities.

### 4.7. Post-Generation Feedback Loop

*   After displaying the generated narrative, the system shall prompt the user with the following choices:
    *   `[A]ccept`: Finalize the command, displaying the accepted narrative.
    *   `[E]dit`: Open the user's default text editor (`click.edit`) pre-filled with the generated Markdown narrative. After the editor closes, display the (potentially modified) narrative as the final result and finalize the command.
    *   `[R]egenerate`: Re-enter the AI generation process.
    *   `[C]ancel`: Discard the generated narrative and exit the command gracefully.
*   **Regeneration Flow:**
    *   If the user chooses `[R]egenerate`, the system shall present an editor (similar to the initial guidance editor, but potentially using `_collect_regeneration_feedback` logic).
    *   This editor should allow the user to provide *new* feedback specific to the *last generated* narrative. It should also allow modification of the *original* guidance context.
    *   The system shall construct a *new* prompt including:
        *   Original context (Game, previous Act, current Act data).
        *   The *previous* AI-generated narrative (clearly labeled).
        *   The *new* user feedback/guidance.
    *   The system shall call the AI again with this new prompt.
    *   The newly generated narrative shall be displayed, and the user shall re-enter the feedback loop prompt (`[A]ccept / [E]dit / [R]egenerate / [C]ancel`).

## 5. Non-Functional Requirements

*   **Usability:** The guidance editor and feedback prompts must be clear and intuitive.
*   **Performance:** Provide feedback to the user during potentially long AI generation times. Be mindful of Anthropic API token limits – the prompt construction should aim for conciseness where possible without losing essential context.
*   **Reliability:** Gracefully handle API errors, missing active game/act, and user cancellations at various stages.
*   **Maintainability:** Leverage existing code structures (`ActManager`, `ActPrompts`, `StructuredEditor`, `Renderer`). Code should be well-documented and follow project conventions.

## 6. Out of Scope (Version 1.0)

*   Saving the generated narrative to a file automatically. (Users can copy/paste).
*   Allowing selection of specific AI models or parameters (use defaults from `AnthropicClient`).
*   Generating narratives for anything other than the single, currently active act.
*   Deep analysis or modification of the *content* of events (e.g., interpreting dice rolls within the narrative) beyond including their descriptions.
*   Providing a `--force` flag (the feedback loop handles overwriting/regeneration).

## 7. Open Questions / Future Considerations

*   How to best handle very long acts with numerous events that might exceed token limits? (Potential truncation or summarization strategies for V2).
*   Could we offer different narrative "styles" as presets in the guidance editor?
*   Explore options for saving the output directly (e.g., `sologm act narrative --output file.md`).
*   Investigate using event timestamps more explicitly in the prompt for better temporal flow.
