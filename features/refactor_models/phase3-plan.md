[200~# Phase 3: Status Check Mixin Implementation Plan

**Feature:** Hybrid Property Refactor - Phase 3  
**Focus:** Extract status check patterns (`is_X`, `has_active_X`, `has_completed_X` hybrid properties)  
**Target:** ~7 properties across 3 models  
**Strategy:** Extend existing mixin infrastructure with status checking pattern support  

## Overview

This phase builds on the successful Phase 1 `ExistenceCheckMixin` and Phase 2 `CountingMixin` by creating a `StatusCheckMixin` that generates status-based hybrid properties automatically from configuration. **We leverage the existing test coverage and mixin infrastructure, making this phase efficient to implement.**

**Target Properties:**
- **Game**: `has_active_act`, `has_active_scene`, `has_completed_acts` (3 properties)
- **Act**: `has_active_scene` (1 property)
- **Event**: `is_from_oracle`, `is_manual`, `is_oracle_generated`, `is_dice_generated` (4 properties)

**Note:** Some properties like `has_acts` have already been migrated to `ExistenceCheckMixin` in Phase 1.

---

## Phase 3.0: Audit Status Check Properties Test Coverage

**Files to modify:**
- `sologm/models/tests/test_event_model.py`

### Sub-step 3.0.1: Audit Event Status Property Test Coverage
**File:** `sologm/models/tests/test_event_model.py`  
**Change:** Analyze current test coverage for Event's 4 status properties  
**Rationale:** Event has the most status properties (4), and they test different patterns - source-based checks  
**Context:** Event has 4 status properties that we need to refactor: `is_from_oracle`, `is_manual`, `is_oracle_generated`, `is_dice_generated`. These properties check the event's source type and relationships, providing a good test case for source-based status checking.

**Audit checklist for each Event status property:**
- **Python context testing**: Verify property returns correct boolean when called on Event instance
- **SQL context testing**: Verify property works in SQLAlchemy WHERE clauses and filters  
- **Edge case testing**: Events with different source types, missing relationships
- **Join testing**: Ensure SQL expressions use efficient JOIN operations with EventSource

Focus on properties that check different source types and relationship conditions.

### Sub-step 3.0.2: Create Missing Event Status Property Tests
**File:** `sologm/models/tests/test_event_model.py`  
**Change:** Add comprehensive tests for any Event status properties lacking coverage  
**Rationale:** Status properties are critical for filtering operations in managers and queries  
**Context:** Follow existing test patterns but ensure SQL context usage is tested (WHERE clauses with status checks). Pay special attention to join operations with EventSource table.

**Key testing patterns to implement:**
- Test events with different source types (manual, oracle, dice)
- Test SQL filtering with status properties (`WHERE event.is_manual = True`)
- Test complex status combinations (oracle-generated vs from-oracle)
- Test join efficiency with EventSource table

**Architectural considerations:**
- Use existing test fixtures and ensure event sources are properly set up
- Test that status SQL expressions generate efficient JOINs (no N+1)
- Verify status consistency between Python and SQL contexts

### Testing for Phase 3.0
**Test Cases:**
- All existing Event tests continue to pass
- All 4 Event status properties have comprehensive test coverage
- Both Python and SQL contexts tested for each status property
- JOIN operations with EventSource are efficient
- SQL filtering with status properties works correctly
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_event_model.py -v -k "status"
uv run pytest sologm/core/tests/test_event.py -v  # Related manager tests
uv run pytest -k "event and (is_|status)" -v  # All event status tests
```
**Success Criteria:** 
- All Event status tests pass consistently
- Every Event status property has adequate test coverage
- SQL filtering with status properties works correctly

---

## Phase 3.1: Audit Game Model Status Properties Test Coverage

**Files to modify:**
- `sologm/models/tests/test_game_model.py`

### Sub-step 3.1.1: Audit Game Status Property Test Coverage
**File:** `sologm/models/tests/test_game_model.py`  
**Change:** Analyze current test coverage for Game's 3 status properties  
**Rationale:** Game has hierarchical status relationships that need special testing attention  
**Context:** Game has 3 status properties: `has_active_act`, `has_active_scene`, `has_completed_acts`. These check for active/completed status across multiple relationship levels, making them more complex to test and refactor.

Follow the same audit approach as Event, but pay special attention to properties that check status across multiple relationship levels (Game → Act → Scene).

### Sub-step 3.1.2: Create Missing Game Status Property Tests
**File:** `sologm/models/tests/test_game_model.py`  
**Change:** Add tests for any missing Game status property coverage  
**Rationale:** Hierarchical status properties need thorough testing for accuracy across relationship chains  
**Context:** Focus especially on the cross-relationship status properties (`has_active_scene`) which require checking status through multiple tables. Use existing fixtures but may need to create scenarios with different active/completed combinations.

**Special considerations:**
- Test games with no acts vs games with active/inactive acts
- Test games with acts having different scene combinations (active, inactive)
- Test the broken `has_completed_acts` property (documents existing bug)
- Ensure status SQL expressions handle the joins correctly across multiple tables
- Test that status checks remain accurate as entity states change

### Testing for Phase 3.1
**Test Cases:**
- All existing Game tests pass
- All 3 Game status properties have comprehensive coverage
- Cross-relationship status properties work accurately in both contexts
- Hierarchical status scenarios (Game → Act → Scene) are tested
- Broken `has_completed_acts` property is documented (doesn't crash tests)
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_game_model.py -v -k "status"
uv run pytest sologm/core/tests/test_game.py -v
uv run pytest -k "game and (active|completed)" -v
```
**Success Criteria:** Hierarchical status properties are thoroughly tested and accurate

---

## Phase 3.2: Audit Act Model Status Properties Test Coverage

**Files to modify:**
- `sologm/models/tests/test_act_model.py`

### Sub-step 3.2.1: Audit Act Status Property Coverage
**File:** `sologm/models/tests/test_act_model.py`  
**Change:** Add tests for any missing Act model status property coverage  
**Rationale:** Act has direct status relationships that are simpler than Game's hierarchical ones  
**Context:** Act has 1 status property: `has_active_scene`. This checks for active scenes within the act, testing direct filtered relationship status checking.

### Testing for Phase 3.2
**Test Cases:**
- All remaining model status properties have test coverage
- Direct status relationships tested (Act.has_active_scene)
- Status properties work correctly in SQL filtering contexts
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_act_model.py -v -k "active"
uv run pytest sologm/models/tests/ -v -k "status"  # All status tests
```
**Success Criteria:** All 7 target status properties have comprehensive test coverage

---

## Phase 3.3: Extend Mixin Infrastructure for Status Checking

**Files to modify:**
- `sologm/models/mixins.py`

### Sub-step 3.3.1: Add Status Check Configuration Classes
**File:** `sologm/models/mixins.py`  
**Change:** Add `StatusConfig` dataclass and `StatusCheckMixin` class  
**Rationale:** Establish the status checking pattern infrastructure alongside existing mixins  
**Context:** Extend the existing mixins.py file with status check support. The status pattern checks for specific field values or relationship conditions rather than just existence or counts.

Create the following components:
- `StatusConfig` dataclass for status property configuration
- `StatusCheckMixin` base class with status property generation logic
- Property generation methods that create both Python and SQL status expressions
- Handle different status check types (field values, filtered relationships, source types)

Key considerations:
- Reuse patterns established in `ExistenceCheckMixin` and `CountingMixin` for consistency
- Generate SQL expressions using appropriate filtering (WHERE clauses, JOINs)
- Handle field-based status checks (e.g., `is_active = True`)
- Handle source-based status checks (e.g., Event source types)
- Handle cross-table status checks (e.g., Game checking for active scenes through acts)

### Sub-step 3.3.2: Handle Different Status Check Types
**File:** `sologm/models/mixins.py`  
**Change:** Add support for various status checking patterns  
**Rationale:** Status properties have different patterns than existence/counting - they check specific conditions  
**Context:** Status properties vary significantly: Event.is_manual checks source name, Game.has_active_act checks is_active field, Game.has_active_scene checks across multiple tables. The mixin must support these varied patterns.

Handle scenarios like:
- Field-based status: `Act.has_active_scene` (check scenes.is_active = True)
- Source-based status: `Event.is_manual` (check source.name = 'manual')
- Cross-table status: `Game.has_active_scene` (check through acts.scenes.is_active = True)
- Relationship status: `Event.is_from_oracle` (check interpretation_id is not None)

### Testing for Phase 3.3
**Test Cases:**
- Status check mixin can be imported without errors
- `StatusConfig` dataclass accepts expected parameters for different status types
- Mixin generates correct status properties for simple and complex scenarios
- SQL expressions generate efficient queries with appropriate JOINs and WHERE clauses
**How to Test:** 
```bash
cd /Users/mike/git/sologm
python -c "from sologm.models.mixins import StatusCheckMixin, StatusConfig; print('Import successful')"
uv run pytest sologm/models/tests/ -v
```
**Success Criteria:** No import errors, existing tests pass, status check mixin infrastructure is ready

---

## Phase 3.4: Create Status Check Mixin Tests

**Files to modify:**
- `sologm/models/tests/test_mixins.py`

### Sub-step 3.4.1: Add Comprehensive Status Check Mixin Tests
**File:** `sologm/models/tests/test_mixins.py`  
**Change:** Extend existing mixin tests with status checking functionality tests  
**Rationale:** Ensure status check mixin behavior is correct before applying to real models  
**Context:** Add to the existing test_mixins.py file (extended in Phase 1 and 2) to test the new status checking functionality. Create mock model scenarios that test various status checking patterns.

Test scenarios to cover:
- Field-based status property generation (checking boolean fields)
- Source-based status property generation (checking related entity properties)
- Cross-table status property generation (status checks through intermediate relationships)
- Both Python and SQL expression behavior for status checks
- Error handling for misconfigured status relationships
- Performance characteristics of generated status check queries

Use the existing mock model patterns from Phase 1 and 2 tests but extend them to include status scenarios.

### Testing for Phase 3.4
**Test Cases:**
- All status check mixin test scenarios pass
- Mock models generate expected status properties
- SQL status expressions match expected patterns with proper JOINs
- Status accuracy is maintained across different scenarios
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_mixins.py -v -k "status"
uv run pytest sologm/models/tests/test_mixins.py -v  # All mixin tests
```
**Success Criteria:** New status tests pass, no regressions in existing mixin tests

---

## Phase 3.5: Migrate Event Model (Most Status Properties)

**Files to modify:**
- `sologm/models/event.py`

### Sub-step 3.5.1: Add Status Check Mixin to Event
**File:** `sologm/models/event.py`  
**Change:** Add `StatusCheckMixin` to Event's inheritance and define `_status_configs`  
**Rationale:** Event has the most status properties (4), making it a good test case for the status check mixin  
**Context:** Event currently has manual implementations of 4 status check properties. Add `StatusCheckMixin` to the inheritance chain and configure it for all status properties. This tests the mixin's ability to handle source-based status checks.

Configuration to add:
```python
_status_configs = {
    'from_oracle': RelationshipStatusConfig(
        field='interpretation_id',
        condition='is_not_null'
    ),
    'manual': SourceStatusConfig(
        source_field='source_id',
        source_model='EventSource',
        source_name_field='name',
        expected_value='manual'
    ),
    'oracle_generated': SourceStatusConfig(
        source_field='source_id', 
        source_model='EventSource',
        source_name_field='name',
        expected_value='oracle'
    ),
    'dice_generated': SourceStatusConfig(
        source_field='source_id',
        source_model='EventSource', 
        source_name_field='name',
        expected_value='dice'
    )
}
```

Add type hints in `TYPE_CHECKING` block for the generated status properties.

### Sub-step 3.5.2: Remove Original Status Properties
**File:** `sologm/models/event.py`  
**Change:** Delete the original status hybrid property implementations  
**Rationale:** Git history preserves originals for reference if needed  
**Context:** Delete the manual implementations of `is_from_oracle`, `is_manual`, `is_oracle_generated`, `is_dice_generated`. The StatusCheckMixin now provides these properties automatically.

Git history provides rollback capability and reference for comparing behavior.

### Testing for Phase 3.5
**Test Cases:**
- All Event model tests pass
- Generated status properties behave identically to original properties
- Status SQL queries generated match expected patterns with proper JOINs
- Python status property access works correctly
- Multiple mixins coexist without conflicts
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_event_model.py -v
uv run pytest sologm/core/tests/test_event.py -v
uv run pytest -k "event" -v  # Run all event-related tests
```
**Success Criteria:** All tests pass, no behavioral changes detected, status checks are accurate

---

## Phase 3.6: Migrate Game Model

**Files to modify:**
- `sologm/models/game.py`

### Sub-step 3.6.1: Add Status Check Mixin to Game Model
**File:** `sologm/models/game.py`  
**Change:** Add status check mixin inheritance and configure status properties  
**Rationale:** Game has complex hierarchical status relationships, testing mixin's handling of cross-table status checks  
**Context:** Game already has `ExistenceCheckMixin` and `CountingMixin` from previous phases. Add `StatusCheckMixin` to handle the 3 status properties, including the complex cross-table status checks (has_active_scene).

Key configurations:
```python
_status_configs = {
    'active_act': FilteredRelationshipStatusConfig(
        model='Act',
        foreign_key='game_id',
        filter_field='is_active',
        filter_value=True
    ),
    'active_scene': CrossTableStatusConfig(
        model='Scene',
        relationship_path=['acts', 'scenes'],
        filter_field='is_active', 
        filter_value=True
    ),
    'completed_acts': FilteredRelationshipStatusConfig(
        model='Act',
        foreign_key='game_id', 
        filter_field='status',
        filter_value='completed'  # This will document the existing bug
    )
}
```

These configurations test the mixin's ability to handle status checks across multiple relationship levels.

### Sub-step 3.6.2: Remove Original Status Properties
**File:** `sologm/models/game.py`  
**Change:** Delete original status properties and add type hints  
**Rationale:** Maintain consistency with Event migration approach  
**Context:** Follow the same pattern as Event - delete originals, add type hints for generated properties. Note that `has_completed_acts` is currently broken and this will be documented.

### Testing for Phase 3.6
**Test Cases:**
- All Game model tests pass (except documented broken property)
- Cross-table status properties work correctly
- Complex status SQL expressions generate properly
- Manager classes can still use status properties for filtering
- Multiple mixins coexist without conflicts (existence + counting + status)
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_game_model.py -v
uv run pytest sologm/core/tests/test_game.py -v
uv run pytest -k "game" -v
```
**Success Criteria:** All tests pass, complex status relationships work correctly

---

## Phase 3.7: Migrate Act Model

**Files to modify:**
- `sologm/models/act.py`

### Sub-step 3.7.1: Migrate Act Model
**File:** `sologm/models/act.py`  
**Change:** Add status check mixin for Act's status property  
**Rationale:** Act has simple direct status relationship, testing basic status check mixin functionality  
**Context:** Act has 1 status property: `has_active_scene`. This is a direct filtered relationship status check that validates the mixin works for straightforward cases.

Configuration:
```python
_status_configs = {
    'active_scene': FilteredRelationshipStatusConfig(
        model='Scene',
        foreign_key='act_id',
        filter_field='is_active',
        filter_value=True
    )
}
```

### Sub-step 3.7.2: Remove Original Status Properties
**File:** `sologm/models/act.py`  
**Change:** Delete original status property and add type hints  
**Rationale:** Maintain consistency with other model migrations  
**Context:** Follow the same pattern as Event and Game - delete the original `has_active_scene` property implementation and add type hints for the generated property.

### Testing for Phase 3.7
**Test Cases:**
- All model tests pass for migrated models
- Direct status relationships work correctly (Act.has_active_scene)
- Status properties maintain accuracy and efficient SQL generation
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_act_model.py -v
uv run pytest sologm/core/tests/test_act.py -v
uv run pytest -x  # Stop on first failure to catch issues early
```
**Success Criteria:** All tests pass across all migrated models

---

## Phase 3.8: Validation and Cleanup

**Files to modify:**
- `sologm/models/event.py`
- `sologm/models/game.py` 
- `sologm/models/act.py`

### Sub-step 3.8.1: Run Comprehensive Test Suite
**File:** Multiple files  
**Change:** Execute full test suite and validate no regressions  
**Rationale:** Ensure all functionality still works after migration  
**Context:** Run the complete test suite including integration tests, manager tests, and CLI tests. Pay special attention to any code that uses status properties for filtering or conditional logic, as this is common throughout the application.

Validate the following:
- All tests pass
- Status SQL queries generate correctly and efficiently
- Python status property access works
- Manager classes can use the status properties for filtering
- Performance hasn't regressed (JOIN queries should be efficient)

### Sub-step 3.8.2: Update Documentation
**File:** `sologm/models/README.md`  
**Change:** Update model documentation to reflect the new status check mixin approach  
**Rationale:** Keep documentation current with the implementation  
**Context:** Update the model documentation to mention that status properties are now generated by the StatusCheckMixin. Add examples of how to configure new status properties and explain the different status check types (field-based, source-based, cross-table).

### Testing for Phase 3.8
**Test Cases:**
- Complete test suite passes
- No dead code remains
- Documentation accurately reflects current implementation
- Performance hasn't regressed (status queries are efficient)
- Manager filtering with status properties works correctly
**How to Test:** 
```bash
uv run pytest -v --tb=short  # Full test suite
uv run pytest --cov=sologm.models  # Ensure test coverage maintained
# Manual testing of key functionality that uses status checks
sologm game status  # Should use various status properties
sologm event list  # Should work with event status filtering
```
**Success Criteria:** All tests pass, documentation is current, no performance regression

---

## Phase 3 Completion Criteria

### Functional Requirements
- [ ] All 7 target status properties migrated to mixin-generated
- [ ] All existing tests pass without modification
- [ ] Status SQL queries generated are efficient and accurate
- [ ] Python status property access behavior unchanged
- [ ] No performance regression in status query execution
- [ ] Multiple mixins coexist correctly (existence + counting + status)

### Code Quality Requirements  
- [ ] No code duplication for status check patterns
- [ ] Status check mixin configuration is clear and maintainable
- [ ] Proper error handling for misconfigured status properties
- [ ] Type hints maintained for IDE support
- [ ] Documentation updated to reflect status check mixin

### Safety Requirements
- [ ] Original status functionality preserved exactly
- [ ] No breaking changes to public API
- [ ] Status accuracy maintained across all scenarios
- [ ] Efficient status queries generated (proper JOINs, no N+1)

---

## Risk Mitigation

**High Risk: Complex Cross-Table Status Checks**
- Mitigation: Extensive testing of hierarchical status relationships, SQL query analysis
- Fallback: Git history provides rollback capability if issues are found

**Medium Risk: Multiple Status Check Types**  
- Mitigation: Thorough testing of different status patterns, ensure mixin handles variety
- Fallback: Handle complex status checks manually if mixin can't support them

**Low Risk: Multiple Mixin Interactions**
- Mitigation: Test existence + counting + status mixins together, ensure no conflicts
- Fallback: Separate mixin inheritance if conflicts arise

---

## Future Phases Preview

This plan completes the core hybrid property patterns:
- **Phase 4**: Navigation Properties (may not need mixin, mostly `@property` not `@hybrid_property`)

The status check mixin infrastructure created in Phase 3 demonstrates that multiple mixins can coexist successfully and completes the migration of repetitive hybrid property patterns. Phase 4 will address the remaining navigation properties, which may be simpler as they're typically regular `@property` methods rather than `@hybrid_property`.[201~
