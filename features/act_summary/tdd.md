# Feature: Enhanced Act Completion with AI Summary Generation

## Overview
This TDD outlines the implementation of an enhanced `sologm act complete` command that incorporates AI-generated summaries and titles, with interactive user feedback and editing capabilities. The implementation will consolidate the functionality currently split between `complete` and `summary` commands.

## Architecture Considerations
Following the architecture guidelines in `conventions/architecture.md`:

1. **CLI Layer**:
   - The CLI command will focus solely on user interaction
   - All business logic will be delegated to the ActManager
   - Database sessions will be managed with `get_db_context()`
   - Managers will be initialized with the session from context

2. **Manager Layer**:
   - ActManager will handle all business logic
   - Database operations will use `self._execute_db_operation()`
   - Clear domain-specific error messages will be provided

3. **Session Management**:
   - One session per CLI command
   - Session will remain open throughout command execution
   - Context manager pattern with `get_db_context()` will be used

## Requirements
1. Consolidate the functionality of `sologm act summary` into `sologm act complete --ai`
2. Allow users to provide additional context for AI generation
3. Implement an interactive flow for accepting, editing, or regenerating AI content
4. Remove the separate `summary` command
5. Add confirmation prompt when replacing existing title/summary

## Implementation Plan

### 1. Update Command Parameters

```python
@act_app.command("complete")
def complete_act(
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="Title for the completed act"
    ),
    summary: Optional[str] = typer.Option(
        None, "--summary", "-s", help="Summary for the completed act"
    ),
    ai: bool = typer.Option(
        False, "--ai", help="Use AI to generate title and summary"
    ),
    context: Optional[str] = typer.Option(
        None,
        "--context",
        "-c",
        help="Additional context to include in the summary generation",
    ),
):
    # Implementation
```

### 2. Code Organization

Break down the implementation into smaller, focused methods:

1. `_handle_ai_generation`: Manages the AI generation process
2. `_collect_context`: Handles collecting context from the user
3. `_collect_regeneration_context`: Specialized context collection for regeneration
4. `_process_ai_results`: Processes and displays AI-generated content
5. `_handle_user_feedback`: Manages the accept/edit/regenerate flow
6. `_complete_act_with_data`: Finalizes the act completion

This approach improves readability, maintainability, and testability.

### 3. Expected Flow

#### Basic Flow
1. User runs `sologm act complete --ai`
2. System validates active game and act
3. If no context is provided, system prompts user for context
4. System generates title and summary using AI
5. System displays generated content
6. System prompts user to (A)ccept, (E)dit, or (R)egenerate
7. Based on user choice:
   - Accept: Use content as-is
   - Edit: Open editor to modify content
   - Regenerate: Collect new context and regenerate
8. System completes the act with final title and summary
9. System displays success message and act details

#### Detailed Flow

**Context Collection**:
1. If `--ai` is specified but no `--context` is provided:
   - Open structured editor for context input following the Command Parameter Pattern
   - Display relevant information about the act being completed using `get_event_context_header()`
   - Allow user to enter additional context
   - If user cancels, proceed with empty context

**Confirmation for Existing Content**:
1. If `--ai` is specified and the act already has a title or summary:
   - Display a confirmation prompt: "This will replace your existing title/summary. Continue? (y/N)"
   - If user selects "No" (default), exit the command
   - If user selects "Yes", proceed with AI generation

**AI Generation**:
1. Display "Generating summary with AI..." message using `StyledText.title()`
2. Call `act_manager.generate_act_summary()` with act ID and context
   - For regeneration, include previous AI output and request for differentiation
3. Handle potential API errors with user-friendly messages following error handling conventions

**User Feedback Loop**:
1. Display generated title and summary in panels with appropriate border styles from `BORDER_STYLES`
2. If the act had existing title/summary, display them for comparison
3. Prompt user with "(A)ccept, (E)dit, or (R)egenerate" (default: Edit)
4. For "Accept":
   - Use generated content as-is
   - Proceed to act completion
5. For "Edit":
   - Open structured editor with generated content
   - Include original title/summary as comments for reference (similar to other edit commands)
   - Allow user to modify title and summary
   - If user cancels, return to prompt
   - If user saves, proceed with modified content
6. For "Regenerate":
   - Open structured editor with current context
   - Add guidance in the comments explaining that they should provide feedback on how they want the new generation to differ from the previous one
   - Include the previously generated title and summary in the comments for reference
   - Allow user to modify context
   - If user cancels, return to prompt
   - If user saves, regenerate with new context that includes information about the previous generation
   - When calling the AI, include the previously generated content and instructions to generate something different
   - Display new content and repeat feedback loop

**Act Completion**:
1. Call `act_manager.complete_act()` with final title and summary
2. Display success message using `StyledText.success()` and act details with metadata formatted using `StyledText.format_metadata()`

### 4. Error Handling

1. Let original exceptions propagate rather than wrapping unnecessarily
2. Catch exceptions only when adding context or handling meaningfully
3. Use specific exception types in `except` clauses
4. Format error messages as `[red]Error:[/] {error_message}`
5. Handle API errors during generation
6. Handle user cancellation at various points
7. Validate required inputs before proceeding
8. Provide clear error messages for all failure cases

### 5. Remove Summary Command

Delete the `generate_act_summary` function from `sologm/cli/act.py`.

## Testing Plan

1. **Unit Tests**:
   - Test each helper method independently
   - Mock user input and API responses
   - Verify correct behavior for all code paths

2. **Integration Tests**:
   - Test complete flow with mocked AI responses
   - Verify correct database updates
   - Test error handling and recovery

3. **Test Scenarios**:
   - Complete act with AI generation (both title and summary)
   - Complete act with partial AI generation (title only or summary only)
   - Test with and without initial context
   - Test accept/edit/regenerate flows
   - Test error conditions and cancellations

## UI/UX Considerations

1. **Clear Prompts**:
   - Format: "(A)ccept, (E)dit, or (R)egenerate"
   - Default to Edit (highlighted)
   - Consistent styling with other commands

2. **Visual Feedback**:
   - Show generated content with clear formatting using appropriate `StyledText` methods
   - Indicate when AI is generating content with `StyledText.title()`
   - Provide clear success messages with `StyledText.success()`
   - Use error messages with format `[red]Error:[/] {error_message}`
   - Use consistent border styles from `BORDER_STYLES` based on content type

3. **Editor Experience**:
   - Pre-populate editors with AI-generated content
   - Show original content in comments for reference (consistent with other edit commands)
   - Provide clear context and instructions using `get_event_context_header()`
   - Consistent editor behavior with other commands
   - Fall back to structured editor when required parameters are missing

## Implementation Notes

1. Use Rich's `Prompt` for interactive choices
2. Leverage existing `edit_structured_data` for all editor interactions
3. Ensure proper error handling for API failures
4. Maintain backward compatibility with non-AI completion
5. Follow project coding style and documentation standards
6. Add comprehensive Google-style docstrings to all new methods
7. Include proper type annotations for all new methods following conventions in `type_annotations.md`
8. Use `StyledText` methods consistently for all styled output
9. Use panels with appropriate border styles from `BORDER_STYLES` for different content types
10. Enhance the ActManager's `generate_act_summary` method to accept previous generation results
11. Create clear guidance for users when regenerating content
12. Use a different prompt template for regeneration vs. initial generation
