# Implementation Plan for Enhanced Act Completion with AI Summary Generation

## Phase 1: Update Command Parameters
1. Update the `complete_act` function signature in `sologm/cli/act.py` to include:
   - Add `ai` boolean option
   - Add `context` string option
   - Keep existing `title`, `summary`, and `force` parameters
2. Create skeleton structure for the new command flow
3. Update tests to verify the new parameters are properly defined

## Phase 2: Basic AI Integration Flow
1. Implement basic validation logic for active game and act
2. Add conditional logic to check if AI generation is requested
3. Create a simple version of the AI generation call that uses existing `generate_act_summary`
4. Add basic error handling for API errors
5. Update tests to verify basic AI integration works

## Phase 3: Context Collection
1. Implement the `_collect_context` helper method
2. Create the structured editor configuration for context input
3. Add logic to handle user cancellation during context collection
4. Update tests to verify context collection works properly

## Phase 4: Confirmation for Existing Content
1. Add logic to check if act already has title/summary
2. Implement confirmation prompt when replacing existing content
3. Handle user response to confirmation
4. Update tests to verify confirmation flow works correctly

## Phase 5: AI Results Display
1. Implement the `_process_ai_results` helper method
2. Format generated title and summary with appropriate styling
3. Add comparison display for existing content if applicable
4. Update tests to verify results display works correctly

## Phase 6: User Feedback Loop
1. Implement the `_handle_user_feedback` helper method
2. Create the Accept/Edit/Regenerate prompt
3. Add logic to handle each user choice path
4. Update tests to verify user feedback loop works correctly

## Phase 7: Edit Flow Implementation
1. Implement the editor flow for modifying AI-generated content
2. Create structured editor configuration for editing title and summary
3. Handle user cancellation during editing
4. Update tests to verify edit flow works correctly

## Phase 8: Regeneration Flow
1. Implement the `_collect_regeneration_context` helper method
2. Create structured editor configuration for regeneration context
3. Add logic to include previous generation in context
4. Update tests to verify regeneration flow works correctly

## Phase 9: Act Completion
1. Implement the `_complete_act_with_data` helper method
2. Add logic to call `act_manager.complete_act()` with final data
3. Create success message display with act details
4. Update tests to verify act completion works correctly

## Phase 10: Remove Summary Command
1. Remove the `generate_act_summary` function from `sologm/cli/act.py`
2. Update any references to this command
3. Update tests to verify the command is properly removed
4. Add deprecation warning if needed for backward compatibility

## Phase 11: Integration Testing
1. Create integration tests for the complete flow
2. Test with mocked AI responses
3. Verify correct database updates
4. Test error handling and recovery
5. Ensure all test scenarios are covered
