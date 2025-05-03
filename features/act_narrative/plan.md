# Implementation Plan: Act Narrative Generation

**Version:** 1.0
**Date:** 2025-05-03
**Author:** Senior Developer (AI Assistant)
**Target:** Junior Developer / Intern
**Status:** Complete

## Overview

This plan details the implementation of the `sologm act narrative` command, which generates AI-powered prose narratives from structured game data. The feature allows users to transform their act's scenes and events into engaging story format using AI assistance, with options to provide guidance, edit, and regenerate the output.

## Summary

This implementation plan provides a structured approach to adding the Act Narrative Generation feature. The 12 steps are designed to be completed incrementally, with each building on the previous ones. Key aspects include:

1. **Incremental Development**: Each step modifies at most 3 files
2. **Test-Driven**: Comprehensive testing at each stage
3. **Clear Architecture**: Follows existing patterns and conventions
4. **Error Handling**: Robust handling of edge cases and failures
5. **User Experience**: Smooth workflow with clear feedback

The junior developer should complete each step fully before moving to the next, ensuring that tests pass at each stage. This approach minimizes risk and makes debugging easier if issues arise.

## Prerequisites

Before beginning implementation:
1. Familiarize yourself with the existing sologm codebase structure
2. Review the PRD and TDD documents in this directory
3. Understand the following key components:
   - CLI command structure (`sologm.cli`)
   - Manager pattern (`sologm.core`)
   - Database models (`sologm.models`)
   - Rendering system (`sologm.cli.rendering`)
   - Structured editor (`sologm.cli.utils.structured_editor`)

## Architecture Overview

The feature follows sologm's established architecture:
- **CLI Layer**: Handles user interaction and command orchestration
- **Manager Layer**: Contains business logic and data preparation
- **Prompt Layer**: Constructs AI prompts with proper formatting
- **Integration Layer**: Manages external AI service communication
- **Rendering Layer**: Displays output in appropriate format

## Important Patterns to Follow

1. **Database Session Management**: Always use `with get_db_context() as session:`
2. **Error Handling**: Catch specific exceptions and display user-friendly messages
3. **Manager Pattern**: Business logic belongs in managers, not CLI
4. **Abstract Base Classes**: Extend renderer base class for new display methods
5. **Testing**: Each component requires comprehensive unit tests

## General Guidelines

- Follow existing code conventions in the project
- Use type hints for all function parameters and returns
- Include docstrings following Google style format
- Handle edge cases and potential errors gracefully
- Test each step before moving to the next

## Implementation Steps

The following steps are designed to be completed incrementally, with each step building upon the previous ones. Complete and test each step before moving forward.

---

## Step 1: Add Abstract Methods to Base Renderer
**Files to modify:**
- `sologm/cli/rendering/base.py`

### Sub-step 1.1: Add display_markdown Abstract Method
**File:** `sologm/cli/rendering/base.py`  
**Change:** Add an abstract method for displaying markdown content  
**Rationale:** All renderer implementations need to define how they display markdown  
**Context:** 
- This follows the existing pattern of abstract methods like `display_title` and `display_panel`
- The concrete implementations will handle rendering differently (Rich vs. plain text)
- Import statements may need to be added for type hints
- The method should accept a single string parameter containing markdown content

### Sub-step 1.2: Add display_narrative_feedback_prompt Abstract Method
**File:** `sologm/cli/rendering/base.py`  
**Change:** Add an abstract method for displaying narrative feedback prompt and getting user choice  
**Rationale:** Different renderer implementations need different user input handling  
**Context:**
- This method should return user choice ("A", "E", "R", "C") or None if cancelled
- The method needs to accept a Console parameter for Rich compatibility
- Use TYPE_CHECKING import to avoid circular dependencies with Console
- Follow the pattern of existing prompt methods in the base class

### Testing for Step 1
**Test Cases:**
- Verify that base.py still imports successfully
- Check that existing renderer implementations raise NotImplementedError for new methods
- Ensure no circular import issues occur

**How to Test:**
```bash
# Run import checks
python -c "from sologm.cli.rendering.base import Renderer"

# Run existing renderer tests to ensure no breakage
pytest sologm/tests/test_rendering.py
```

**Success Criteria:**
- No import errors occur
- Existing tests still pass
- Abstract methods are properly defined with correct signatures

---

## Step 2: Implement Renderer Methods for Rich Display
**Files to modify:**
- `sologm/cli/rendering/rich_renderer.py`

### Sub-step 2.1: Implement display_markdown Method
**File:** `sologm/cli/rendering/rich_renderer.py`  
**Change:** Implement the display_markdown method using Rich's Markdown component  
**Rationale:** Rich library provides built-in markdown rendering capabilities  
**Context:**
- Import `Markdown` from `rich.markdown`
- Pass markdown content to Markdown constructor and print using console
- Follow existing display method patterns in this class
- Handle any potential rendering exceptions gracefully

### Sub-step 2.2: Implement display_narrative_feedback_prompt Method
**File:** `sologm/cli/rendering/rich_renderer.py`  
**Change:** Implement feedback prompt using Rich's Prompt.ask()  
**Rationale:** Rich provides interactive prompt capabilities with choice validation  
**Context:**
- Use `rich.prompt.Prompt.ask()` with choices ["A", "E", "R", "C"]
- Set appropriate prompt text explaining each option
- Handle InvalidResponse and potential cancellation (Ctrl+C)
- Return uppercase choice letter or None if cancelled
- Consider default choice to be "A" (Accept)

### Testing for Step 2
**Test Cases:**
- Test markdown display with simple markdown content
- Test markdown display with complex markdown (headers, lists, code blocks)
- Test feedback prompt returns correct choice values
- Test feedback prompt handles cancellation properly

**How to Test:**
```bash
# Create a simple test script or run in Python REPL
python -c "from sologm.cli.rendering.rich_renderer import RichRenderer; from rich.console import Console; r = RichRenderer(Console()); r.display_markdown('# Test Header')"

# Run specific renderer tests
pytest sologm/tests/test_rendering.py::test_rich_renderer
```

**Success Criteria:**
- Markdown renders properly in terminal with Rich formatting
- Feedback prompt displays and accepts valid choices
- Invalid input is handled gracefully
- Cancellation returns None as expected

---

## Step 3: Implement Renderer Methods for Markdown Display
**Files to modify:**
- `sologm/cli/rendering/markdown_renderer.py`

### Sub-step 3.1: Implement display_markdown Method
**File:** `sologm/cli/rendering/markdown_renderer.py`  
**Change:** Implement plain text markdown display  
**Rationale:** Markdown renderer outputs plain text, so markdown should be passed through directly  
**Context:**
- Simply use the existing `_print_markdown` method to output the content
- No special formatting needed since this renderer produces plain markdown output
- Consider if any header/footer formatting is needed for consistency

### Sub-step 3.2: Implement display_narrative_feedback_prompt Method
**File:** `sologm/cli/rendering/markdown_renderer.py`  
**Change:** Implement feedback prompt using click.prompt()  
**Rationale:** Click library provides text-based prompt functionality for non-Rich environments  
**Context:**
- Import click if not already imported
- Use `click.prompt()` with `type=click.Choice(["A", "E", "R", "C"], case_sensitive=False)`
- Set appropriate prompt text and show_choices=True
- Handle click.Abort exception (raised on Ctrl+C)
- Return uppercase choice or None if aborted
- Consider setting default to "A" for consistency

### Testing for Step 3
**Test Cases:**
- Test markdown display outputs content unchanged
- Test feedback prompt accepts valid choices
- Test feedback prompt rejects invalid input
- Test cancellation handling

**How to Test:**
```bash
# Test markdown display
python -c "from sologm.cli.rendering.markdown_renderer import MarkdownRenderer; r = MarkdownRenderer(); r.display_markdown('# Test Header')"

# Run renderer tests
pytest sologm/tests/test_rendering.py::test_markdown_renderer
```

**Success Criteria:**
- Markdown content is output as plain text
- Prompt accepts valid choices and rejects invalid ones
- Cancellation is handled properly
- All renderer tests pass

---

## Step 4: Create Act Narrative Prompt Templates
**Files to modify:**
- `sologm/core/prompts/act.py`

### Sub-step 4.1: Add build_narrative_prompt Method
**File:** `sologm/core/prompts/act.py`  
**Change:** Create a method to build the initial narrative generation prompt  
**Rationale:** Structured prompts ensure consistent AI responses for narrative generation  
**Context:**
- Method should accept a dictionary containing game, act, scenes, events, and user guidance
- Follow existing prompt patterns in this file (like build_summary_prompt)
- Include clear sections for: system instruction, game info, previous act context, current act data, scenes/events list, and user guidance
- Ensure prompt instructs AI to output in Markdown format
- Consider proper formatting for readability and token efficiency

### Sub-step 4.2: Add build_narrative_regeneration_prompt Method
**File:** `sologm/core/prompts/act.py`  
**Change:** Create a method to build prompts for regenerating narratives with feedback  
**Rationale:** Regeneration requires including previous narrative and user feedback in the prompt  
**Context:**
- Method should accept same data as build_narrative_prompt plus previous_narrative and feedback
- Include all sections from build_narrative_prompt
- Add sections for: previous narrative (clearly labeled) and user feedback
- Modify task instruction to emphasize generating a NEW narrative based on feedback
- Ensure the AI understands it should incorporate feedback while maintaining context

### Testing for Step 4
**Test Cases:**
- Test build_narrative_prompt with minimal data (no optional fields)
- Test build_narrative_prompt with complete data (all fields populated)
- Test build_narrative_regeneration_prompt with various feedback scenarios
- Verify prompts contain all expected sections and formatting

**How to Test:**
```bash
# Run unit tests for the prompts module
pytest sologm/tests/core/prompts/test_act_prompts.py -v

# Test prompt building manually
python -c "from sologm.core.prompts.act import ActPrompts; print(ActPrompts.build_narrative_prompt({'game': {'name': 'Test'}, 'act': {'title': 'Act 1'}}))"
```

**Success Criteria:**
- Both methods return properly formatted string prompts
- All required sections are present in the output
- Optional fields are handled gracefully when missing
- Prompts are readable and well-structured

---

## Step 5: Implement Act Data Preparation Method
**Files to modify:**
- `sologm/core/act.py`

### Sub-step 5.1: Add prepare_act_data_for_narrative Method
**File:** `sologm/core/act.py`  
**Change:** Create method to gather and structure all data needed for narrative generation  
**Rationale:** Centralizes data collection logic and ensures consistent data structure for prompts  
**Context:**
- Method should accept act_id parameter
- Use self._session directly for queries (not _execute_db_operation)
- Fetch: target act, associated game, previous act (if exists), all scenes, all events per scene
- Import and use scene_manager and event_manager for related data
- Order scenes by sequence, events by created_at
- Return structured dictionary matching prompt template expectations
- Handle missing/optional data gracefully (previous act may not exist)
- Use get_entity_or_error for required entities (act, game)

### Sub-step 5.2: Handle Related Manager Dependencies
**File:** `sologm/core/act.py`  
**Change:** Add lazy initialization for scene and event managers if not already present  
**Rationale:** ActManager needs access to scene and event data through their respective managers  
**Context:**
- Check if scene_manager and event_manager properties exist
- If not, follow lazy initialization pattern used elsewhere in the codebase
- Ensure proper circular import handling
- These managers will be used to fetch related data efficiently

### Testing for Step 5
**Test Cases:**
- Test data preparation with complete game structure (game, acts, scenes, events)
- Test handling of missing previous act
- Test proper ordering of scenes and events
- Test error handling for non-existent act_id

**How to Test:**
```bash
# Run unit tests for ActManager
pytest sologm/tests/core/test_act_manager.py::test_prepare_act_data_for_narrative -v

# Test data structure manually
python -c "from sologm.core.act import ActManager; from sologm.database import get_db_context; with get_db_context() as session: manager = ActManager(session); print(manager.prepare_act_data_for_narrative('test-act-id'))"
```

**Success Criteria:**
- Method returns properly structured dictionary
- All relationships are correctly loaded
- Data is properly ordered
- Missing optional data is handled gracefully
- Appropriate errors are raised for invalid act_id

---

## Step 6: Implement Narrative Generation Method
**Files to modify:**
- `sologm/core/act.py`
- `sologm/integrations/anthropic_integration.py` (minor update)

### Sub-step 6.1: Add generate_act_narrative Method
**File:** `sologm/core/act.py`  
**Change:** Create method to orchestrate the narrative generation process  
**Rationale:** Centralizes AI interaction logic for narrative generation  
**Context:**
- Method accepts: act_id, user_guidance (optional), previous_narrative (optional), feedback (optional)
- Call prepare_act_data_for_narrative to get structured data
- Add user_guidance to the prepared data
- Choose appropriate prompt builder based on presence of previous_narrative/feedback
- Instantiate AnthropicClient and call send_message
- Handle API errors and re-raise as APIError
- Consider appropriate max_tokens value (suggest 2048 or higher)
- Return raw string response from AI

### Sub-step 6.2: Update AnthropicClient Token Limits
**File:** `sologm/integrations/anthropic_integration.py`  
**Change:** Ensure max_tokens parameter supports narrative generation needs  
**Rationale:** Narratives require more tokens than typical summaries  
**Context:**
- Check if send_message method accepts max_tokens parameter
- If not already parameterized, add support for custom max_tokens
- Ensure default remains reasonable for other use cases
- Consider adding a constant for narrative-specific token limit

### Testing for Step 6
**Test Cases:**
- Test initial narrative generation (no previous narrative)
- Test regeneration with feedback
- Test API error handling
- Test with various user guidance combinations
- Mock AnthropicClient to avoid actual API calls in tests

**How to Test:**
```bash
# Run unit tests with mocked API
pytest sologm/tests/core/test_act_manager.py::test_generate_act_narrative -v

# Integration test (requires API key)
SOLOGM_DEBUG=true python -c "from sologm.core.act import ActManager; from sologm.database import get_db_context; with get_db_context() as session: manager = ActManager(session); result = manager.generate_act_narrative('test-act-id'); print(result)"
```

**Success Criteria:**
- Method successfully calls AI and returns narrative
- Correct prompt builder is selected based on parameters
- API errors are properly caught and re-raised
- Token limits are appropriate for narrative length
- Mocked tests pass without actual API calls

---

## Step 7: Create Helper Functions for Narrative Command
**Files to modify:**
- `sologm/cli/act.py`

### Sub-step 7.1: Add _collect_narrative_guidance Helper Function
**File:** `sologm/cli/act.py`  
**Change:** Create helper function to collect initial user guidance for narrative generation  
**Rationale:** Separates UI logic from main command flow and makes code more maintainable  
**Context:**
- Function signature: `_collect_narrative_guidance(act: Act, game: Game, console: Console, renderer: Renderer) -> Optional[Dict]`
- Define FieldConfig list with: tone_style (Text), point_of_view (Text), key_focus (TextArea), other_instructions (TextArea)
- All fields should be optional to allow user flexibility
- Use edit_structured_data with appropriate StructuredEditorConfig
- Return None if user cancels, otherwise return guidance dictionary
- Follow pattern of existing helper functions in this file (e.g., _collect_act_data)

### Sub-step 7.2: Add _collect_narrative_regeneration_feedback Helper Function
**File:** `sologm/cli/act.py`  
**Change:** Create helper function for collecting feedback during regeneration  
**Rationale:** Handles the complex logic of collecting both feedback and updated guidance  
**Context:**
- Function signature: `_collect_narrative_regeneration_feedback(previous_narrative: str, act: Act, game: Game, console: Console, renderer: Renderer, original_guidance: Optional[Dict]) -> Optional[Dict]`
- Should allow user to provide feedback on previous narrative
- Should allow modification of original guidance fields
- Use edit_structured_data with fields for both feedback and guidance
- Return None if cancelled, otherwise return dictionary with both feedback and updated guidance
- Follow pattern of _collect_regeneration_feedback from act complete command

### Testing for Step 7
**Test Cases:**
- Test guidance collection with all fields filled
- Test guidance collection with some fields empty
- Test cancellation handling for both functions
- Test regeneration feedback includes both feedback and guidance

**How to Test:**
```bash
# Run unit tests for the helper functions
pytest sologm/tests/cli/test_act.py::test_collect_narrative_guidance -v
pytest sologm/tests/cli/test_act.py::test_collect_narrative_regeneration_feedback -v

# Manual testing (interactive)
python -m sologm.cli.main act narrative
```

**Success Criteria:**
- Helper functions properly integrate with StructuredEditor
- User can input guidance and feedback through editor interface
- Cancellation is handled gracefully
- Return values match expected dictionary structure

---

## Step 8: Implement the Main Narrative Command
**Files to modify:**
- `sologm/cli/act.py`

### Sub-step 8.1: Add Base Command Structure
**File:** `sologm/cli/act.py`  
**Change:** Create the narrative command function with initial setup and validation  
**Rationale:** Establishes the main command entry point and ensures proper context  
**Context:**
- Add `@act_app.command("narrative")` decorator
- Function signature: `def generate_narrative(ctx: typer.Context) -> None:`
- Include comprehensive docstring explaining command purpose
- Get renderer and console from ctx.obj
- Use `with get_db_context() as session:` for database access
- Instantiate GameManager and ActManager
- Validate active game and act (display errors and exit if missing)
- Follow error handling patterns from other commands in this file

### Sub-step 8.2: Implement Command Logic and Feedback Loop
**File:** `sologm/cli/act.py`  
**Change:** Add the main logic flow including guidance collection, AI generation, and feedback loop  
**Rationale:** Implements the core functionality of narrative generation with user interaction  
**Context:**
- Call _collect_narrative_guidance and handle cancellation
- Display "Generating..." message during AI call
- Call act_manager.generate_act_narrative with try/except for APIError
- Display generated narrative using renderer.display_markdown
- Implement while True feedback loop with proper choice handling
- Choice handling: Accept (break), Edit (click.edit), Regenerate (feedback collection), Cancel (break)
- For Edit: check if result changed before updating
- For Regenerate: call _collect_narrative_regeneration_feedback and generate again
- Include appropriate status messages throughout

### Testing for Step 8
**Note:** Per project conventions, CLI commands are not directly tested. The manager methods and renderer methods used by this command are tested in their respective test files.

### Verification for Step 8
**Manual Verification:**
- Command validates context properly
- User flow works smoothly through all options
- Error messages are clear and helpful
- Generated narrative displays correctly
- Feedback loop functions as expected

**How to Run:**
```bash
# Test with debug output
SOLOGM_DEBUG=true python -m sologm.cli.main act narrative

# Integration test (requires test database)
python -m sologm.cli.main act narrative
```

---

## Step 9: Add Unit Tests for ActPrompts
**Files to modify:**
- `sologm/core/prompts/tests/test_act_prompts.py`

### Sub-step 9.1: Update or Create Test File
**File:** `sologm/core/prompts/tests/test_act_prompts.py`  
**Change:** Ensure the test file exists or update existing file  
**Rationale:** Follows the project's test organization pattern  
**Context:**
- Check if file exists; create if needed
- Import necessary testing utilities and models
- Follow existing test patterns from test_oracle_prompts.py
- Use the TestActPrompts class pattern

### Sub-step 9.2: Implement Tests for build_narrative_prompt
**File:** `sologm/core/prompts/tests/test_act_prompts.py`  
**Change:** Add tests for the narrative prompt builder  
**Rationale:** Ensures prompt construction works correctly with various inputs  
**Context:**
- Test with minimal required data
- Test with all optional fields populated
- Test missing user guidance handling
- Test missing previous act handling
- Verify all expected sections appear in output
- Use string assertions to check prompt content
- No need for database fixtures since prompts work with dictionaries

### Sub-step 9.3: Implement Tests for build_narrative_regeneration_prompt
**File:** `sologm/core/prompts/tests/test_act_prompts.py`  
**Change:** Add tests for the regeneration prompt builder  
**Rationale:** Verifies regeneration prompts include feedback correctly  
**Context:**
- Test with various feedback scenarios
- Test with different previous narrative lengths
- Verify previous narrative is included and labeled
- Verify feedback section is properly formatted
- Check that base narrative data is still included
- Test edge cases (empty feedback, very long feedback)

### Testing for Step 9
**Test Cases:**
- All tests should pass for both prompt methods
- Edge cases should be handled gracefully
- Prompt output should be well-structured and readable

**How to Test:**
```bash
# Run the new tests
pytest sologm/core/prompts/tests/test_act_prompts.py -v

# Run with coverage
pytest --cov=sologm.core.prompts.act sologm/core/prompts/tests/test_act_prompts.py
```

**Success Criteria:**
- All new tests pass
- Tests follow existing patterns from test_oracle_prompts.py
- Prompt outputs are validated for structure and content

---

## Step 10: Add Unit Tests for ActManager Methods
**Files to modify:**
- `sologm/core/tests/test_act.py`

### Sub-step 10.1: Add Tests for prepare_act_data_for_narrative
**File:** `sologm/core/tests/test_act.py`  
**Change:** Add tests for the data preparation method to the existing TestActManager class  
**Rationale:** Ensures the method correctly gathers and structures all required data  
**Context:**
- Add test method `test_prepare_act_data_for_narrative` to TestActManager
- Use session_context fixture with database operations
- Use existing factory fixtures (create_test_game, create_test_act, etc.)
- Create complete data structure (game with multiple acts and scenes)
- Test handling of missing previous act
- Verify proper ordering of scenes and events
- Test error handling for non-existent act_id
- Use initialize_event_sources fixture if creating events

### Sub-step 10.2: Add Tests for generate_act_narrative
**File:** `sologm/core/tests/test_act.py`  
**Change:** Add tests for the narrative generation method using proper mocking  
**Rationale:** Verifies AI interaction and error handling without making actual API calls  
**Context:**
- Add test method `test_generate_act_narrative` to TestActManager
- Mock AnthropicClient class in its original module location
- Do not mock prepare_act_data_for_narrative - let it run with test data
- Test initial generation (no previous narrative)
- Test regeneration with feedback and previous narrative
- Verify correct prompt builder is called based on parameters
- Test APIError handling and re-raising
- Use monkeypatch to mock the AnthropicClient class

### Sub-step 10.3: Add API Error Test Case
**File:** `sologm/core/tests/test_act.py`  
**Change:** Add specific test for API error handling  
**Rationale:** Ensures robust error handling in production  
**Context:**
- Add test method `test_generate_act_narrative_api_error`
- Mock AnthropicClient to raise exception
- Verify APIError is raised with proper message
- Follow pattern from existing test_generate_act_summary_api_error

### Testing for Step 10
**Test Cases:**
- Data preparation returns complete structure
- Data preparation handles missing optional data
- Narrative generation calls AI with correct prompt
- Regeneration includes feedback in prompt
- API errors are properly handled
- Invalid inputs raise appropriate exceptions

**How to Test:**
```bash
# Run new ActManager tests
pytest sologm/core/tests/test_act.py::TestActManager::test_prepare_act_data_for_narrative -v
pytest sologm/core/tests/test_act.py::TestActManager::test_generate_act_narrative -v

# Run with coverage
pytest --cov=sologm.core.act sologm/core/tests/test_act.py

# Run all ActManager tests to ensure no regression
pytest sologm/core/tests/test_act.py -v
```

**Success Criteria:**
- All tests pass without actual API calls
- Tests use session injection pattern
- Follow existing test patterns in the file
- Error conditions are handled appropriately

---

## Step 11: Add Unit Tests for Renderer Methods
**Files to modify:**
- `sologm/cli/rendering/tests/test_rich_renderer.py`
- `sologm/cli/rendering/tests/test_markdown_renderer.py`

### Sub-step 11.1: Test RichRenderer Markdown Display
**File:** `sologm/cli/rendering/tests/test_rich_renderer.py`  
**Change:** Add tests for display_markdown method  
**Rationale:** Verifies Rich-based markdown rendering works correctly  
**Context:**
- Add test function `test_display_markdown`
- Use mock_console fixture
- Test with simple markdown content
- Test with complex markdown (headers, lists, code blocks)
- Verify console.print is called with Rich Markdown object
- Follow existing test patterns from the file

### Sub-step 11.2: Test RichRenderer Feedback Prompt
**File:** `sologm/cli/rendering/tests/test_rich_renderer.py`  
**Change:** Add tests for display_narrative_feedback_prompt method  
**Rationale:** Ensures interactive prompt works properly with Rich  
**Context:**
- Add test function `test_display_narrative_feedback_prompt`
- Use @patch('rich.prompt.Prompt.ask') decorator
- Test all valid choices ("A", "E", "R", "C")
- Test cancellation returns None
- Verify prompt is called with correct parameters
- Follow pattern from test_display_act_ai_feedback_prompt

### Sub-step 11.3: Test MarkdownRenderer Methods
**File:** `sologm/cli/rendering/tests/test_markdown_renderer.py`  
**Change:** Add tests for both markdown display and feedback prompt  
**Rationale:** Verifies plain text rendering and click-based prompts work correctly  
**Context:**
- Add test functions for display_markdown and display_narrative_feedback_prompt
- Use mock_console fixture
- Test display_markdown calls _print_markdown
- Use @patch('click.prompt') for feedback prompt testing
- Test all valid choices and cancellation
- Test that output is plain text without formatting

### Testing for Step 11
**Test Cases:**
- Markdown displays correctly in both renderers
- Feedback prompt accepts valid choices
- Invalid input is handled appropriately  
- Cancellation returns None
- Both renderers handle edge cases

**How to Test:**
```bash
# Run RichRenderer tests
pytest sologm/cli/rendering/tests/test_rich_renderer.py::test_display_markdown -v
pytest sologm/cli/rendering/tests/test_rich_renderer.py::test_display_narrative_feedback_prompt -v

# Run MarkdownRenderer tests
pytest sologm/cli/rendering/tests/test_markdown_renderer.py -v

# Run all renderer tests
pytest sologm/cli/rendering/tests/ -v
```

**Success Criteria:**
- All renderer tests pass
- Mock calls verify correct behavior
- Both renderers handle all input scenarios
- Tests follow existing patterns in the renderer test files

---

## Step 12: Verify Complete Feature Implementation
**Files to review:**
- All files modified in steps 1-11
- No new files needed (CLI commands are not tested per conventions)

### Sub-step 12.1: Run All Tests
**Files:** Various test files  
**Change:** Run comprehensive test suite  
**Rationale:** Ensures all components work together correctly  
**Context:**
- Run all tests modified or created in this feature
- Check for any test failures or regressions
- Verify test coverage meets project standards
- No CLI command tests needed per project conventions

### Sub-step 12.2: Manual Feature Testing
**Files:** N/A  
**Change:** Manually test the feature in development environment  
**Rationale:** Validates the feature works end-to-end  
**Context:**
- Create a test game with acts, scenes, and events
- Run `sologm act narrative` command
- Test all feedback loop options (Accept, Edit, Regenerate, Cancel)
- Verify markdown output renders correctly
- Test with different user guidance inputs
- Document any issues found

### Sub-step 12.3: Documentation Review
**Files:** `README.md`, command help text  
**Change:** Ensure documentation is complete  
**Rationale:** Users need to understand how to use the feature  
**Context:**
- Verify command help text is clear
- Check if README needs updates
- Ensure all parameters are documented
- Add usage examples if needed

### Testing for Step 12
**Test Cases:**
- All unit tests pass
- Manual testing confirms feature works
- Documentation is complete and accurate

**How to Test:**
```bash
# Run all tests for the feature
pytest sologm/core/tests/test_act.py -v
pytest sologm/core/prompts/tests/test_act_prompts.py -v
pytest sologm/cli/rendering/tests/ -v

# Run with coverage
pytest --cov=sologm sologm/

# Manual testing
sologm act narrative
```

**Success Criteria:**
- All tests pass
- Feature works correctly in manual testing
- No regression in existing functionality
- Documentation is clear and complete

---

