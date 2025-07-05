# Phase 2: Count Operations Mixin Implementation Plan

**Feature:** Hybrid Property Refactor - Phase 2  
**Focus:** Extract count operations patterns (`X_count` hybrid properties)  
**Target:** ~8 properties across 5 models  
**Strategy:** Extend existing mixin infrastructure with counting pattern support  

## Overview

This phase builds on the successful Phase 1 `ExistenceCheckMixin` by creating a `CountingMixin` that generates `X_count` hybrid properties automatically from configuration. **We leverage the existing test coverage and mixin infrastructure from Phase 1, making this phase faster to implement.**

**Target Properties:**
- **Game**: `act_count` (1 property)
- **Act**: `scene_count`, `event_count`, `dice_roll_count`, `interpretation_count` (4 properties)
- **Scene**: `event_count`, `dice_roll_count`, `interpretation_set_count`, `interpretation_count`, `selected_interpretation_count` (5 properties)
- **Interpretation**: `event_count` (1 property)
- **InterpretationSet**: `interpretation_count` (1 property)

**Note:** DiceRoll has no count properties to migrate.

---

## Phase 2.0: Audit Count Properties Test Coverage

**Files to modify:**
- `sologm/models/tests/test_scene_model.py`

### Sub-step 2.0.1: Audit Scene Count Property Test Coverage
**File:** `sologm/models/tests/test_scene_model.py`  
**Change:** Analyze current test coverage for Scene's 5 count properties  
**Rationale:** Scene has the most count properties (5), so we start there to understand testing gaps  
**Context:** Scene has 5 count properties that we need to refactor: `event_count`, `dice_roll_count`, `interpretation_set_count`, `interpretation_count`, `selected_interpretation_count`. We need to identify which of these have adequate test coverage for both Python and SQL contexts.

**Audit checklist for each Scene count property:**
- **Python context testing**: Verify property returns correct count when called on Scene instance
- **SQL context testing**: Verify property works in SQLAlchemy ORDER BY clauses and comparisons  
- **Edge case testing**: Empty relationships, zero counts, large counts
- **Performance testing**: Ensure SQL expressions use efficient COUNT queries

Focus on count properties that aggregate across relationships, especially complex ones like `interpretation_count` and `selected_interpretation_count`.

### Sub-step 2.0.2: Create Missing Scene Count Property Tests
**File:** `sologm/models/tests/test_scene_model.py`  
**Change:** Add comprehensive tests for any Scene count properties lacking coverage  
**Rationale:** Count properties are critical for ordering and filtering operations in managers  
**Context:** Follow existing test patterns but ensure SQL context usage is tested (ORDER BY, WHERE clauses with counts). Pay special attention to complex count properties that traverse multiple relationships.

**Key testing patterns to implement:**
- Test zero, one, and multiple count scenarios
- Test SQL ordering with count properties (`ORDER BY scene.event_count DESC`)
- Test SQL filtering with count properties (`WHERE scene.event_count > 5`)
- Test complex count relationships (interpretations through interpretation_sets)

**Architectural considerations:**
- Use existing test fixtures and ensure counts reflect actual relationship sizes
- Test that count SQL expressions generate efficient queries (no N+1)
- Verify count consistency between Python and SQL contexts

### Testing for Phase 2.0
**Test Cases:**
- All existing Scene tests continue to pass
- All 5 Scene count properties have comprehensive test coverage
- Both Python and SQL contexts tested for each count property
- Complex relationship count scenarios covered (interpretation_sets -> interpretations)
- SQL ordering and filtering with count properties works correctly
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_scene_model.py -v -k "count"
uv run pytest sologm/core/tests/test_scene.py -v  # Related manager tests
uv run pytest -k "scene and count" -v  # All scene count tests
```
**Success Criteria:** 
- All Scene count tests pass consistently
- Every Scene count property has adequate test coverage
- SQL ordering/filtering with counts works correctly

---

## Phase 2.1: Audit Act Model Count Properties Test Coverage

**Files to modify:**
- `sologm/models/tests/test_act_model.py`

### Sub-step 2.1.1: Audit Act Count Property Test Coverage
**File:** `sologm/models/tests/test_act_model.py`  
**Change:** Analyze current test coverage for Act's 4 count properties  
**Rationale:** Act has cross-scene count relationships that need special testing attention  
**Context:** Act has 4 count properties: `scene_count`, `event_count`, `dice_roll_count`, `interpretation_count`. Some of these (`event_count`, `dice_roll_count`, `interpretation_count`) count relationships through scenes, making them more complex to test and refactor.

Follow the same audit approach as Scene, but pay special attention to properties that count entities across multiple scenes.

### Sub-step 2.1.2: Create Missing Act Count Property Tests
**File:** `sologm/models/tests/test_act_model.py`  
**Change:** Add tests for any missing Act count property coverage  
**Rationale:** Cross-scene count properties need thorough testing for accuracy and performance  
**Context:** Focus especially on the cross-relationship count properties (`event_count`, `dice_roll_count`, `interpretation_count`) which require aggregating across multiple tables. Use existing fixtures but may need to create more complex test scenarios.

**Special considerations:**
- Test acts with no scenes vs acts with scenes containing different numbers of entities
- Test acts with multiple scenes having varying numbers of events/dice_rolls/interpretations
- Ensure count SQL expressions handle the joins correctly and efficiently
- Test that counts remain accurate as entities are added/removed from scenes

### Testing for Phase 2.1
**Test Cases:**
- All existing Act tests pass
- All 4 Act count properties have comprehensive coverage
- Cross-scene count properties work accurately in both contexts
- Complex scenarios (multiple scenes with different entity counts) are tested
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_act_model.py -v -k "count"
uv run pytest sologm/core/tests/test_act.py -v
uv run pytest -k "act and count" -v
```
**Success Criteria:** Cross-scene count properties are thoroughly tested and accurate

---

## Phase 2.2: Audit Remaining Model Count Properties Test Coverage

**Files to modify:**
- `sologm/models/tests/test_game_model.py`
- `sologm/models/tests/test_oracle_model.py`

### Sub-step 2.2.1: Audit Game Model Count Property Coverage
**File:** `sologm/models/tests/test_game_model.py`  
**Change:** Add tests for any missing Game model count property coverage  
**Rationale:** Game has hierarchical count relationships (through acts)  
**Context:** Game has 1 count property: `act_count`. This is a direct relationship count, simpler than the cross-table counts in Act and Scene.

### Sub-step 2.2.2: Audit Oracle Models Count Property Coverage  
**File:** `sologm/models/tests/test_oracle_model.py`  
**Change:** Add tests for any missing Oracle models count property coverage  
**Rationale:** These are simpler cases that help validate the counting mixin approach  
**Context:** InterpretationSet has `interpretation_count`, Interpretation has `event_count`. These are straightforward relationship counts that test basic counting mixin functionality.

### Testing for Phase 2.2
**Test Cases:**
- All remaining model count properties have test coverage
- Direct relationship counts tested (Game.act_count)
- Simple relationship counts tested (InterpretationSet, Interpretation)
- Count properties work correctly in SQL ordering and filtering contexts
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_game_model.py -v -k "count"
uv run pytest sologm/models/tests/test_oracle_model.py -v -k "count"
uv run pytest sologm/models/tests/ -v -k "count"  # All count tests
```
**Success Criteria:** All 8 target count properties have comprehensive test coverage

---

## Phase 2.3: Extend Mixin Infrastructure for Counting

**Files to modify:**
- `sologm/models/mixins.py`

### Sub-step 2.3.1: Add Counting Configuration Classes
**File:** `sologm/models/mixins.py`  
**Change:** Add `CountConfig` dataclass and `CountingMixin` class  
**Rationale:** Establish the counting pattern infrastructure alongside the existing existence check mixin  
**Context:** Extend the existing mixins.py file with counting support. The counting pattern is similar to existence checks but generates COUNT() SQL expressions instead of EXISTS() expressions.

Create the following components:
- `CountConfig` dataclass for count property configuration
- `CountingMixin` base class with count property generation logic
- Property generation methods that create both Python and SQL count expressions
- Handle complex cross-table counting scenarios

Key considerations:
- Reuse patterns established in `ExistenceCheckMixin` for consistency
- Generate SQL expressions using `func.count()` from SQLAlchemy
- Handle relationship paths for cross-table counts (e.g., Act counting events through scenes)
- Support filtering in count operations (e.g., `selected_interpretation_count`)
- Maintain performance with efficient COUNT queries

### Sub-step 2.3.2: Handle Cross-Table Count Scenarios
**File:** `sologm/models/mixins.py`  
**Change:** Add support for counting across relationship paths  
**Rationale:** Many count properties need to count entities through intermediate relationships  
**Context:** Some count properties are complex: Act.event_count counts events across all scenes, Scene.interpretation_count counts interpretations across all interpretation_sets. The mixin must support these relationship paths.

Handle scenarios like:
- Direct counts: `Game.act_count` (count direct relationship)
- Cross-table counts: `Act.event_count` (count through scenes.events)
- Filtered counts: `Scene.selected_interpretation_count` (count with WHERE clause)
- Complex paths: `Scene.interpretation_count` (count through interpretation_sets.interpretations)

### Testing for Phase 2.3
**Test Cases:**
- Counting mixin can be imported without errors
- `CountConfig` dataclass accepts expected parameters
- Mixin generates correct count properties for simple and complex scenarios
- SQL expressions generate efficient COUNT queries
**How to Test:** 
```bash
cd /Users/mike/git/sologm
python -c "from sologm.models.mixins import CountingMixin, CountConfig; print('Import successful')"
uv run pytest sologm/models/tests/ -v
```
**Success Criteria:** No import errors, existing tests pass, counting mixin infrastructure is ready

---

## Phase 2.4: Create Counting Mixin Tests

**Files to modify:**
- `sologm/models/tests/test_mixins.py`

### Sub-step 2.4.1: Add Comprehensive Counting Mixin Tests
**File:** `sologm/models/tests/test_mixins.py`  
**Change:** Extend existing mixin tests with counting functionality tests  
**Rationale:** Ensure counting mixin behavior is correct before applying to real models  
**Context:** Add to the existing test_mixins.py file (created in Phase 1) to test the new counting functionality. Create mock model scenarios that test various counting patterns.

Test scenarios to cover:
- Simple count property generation (direct relationship counts)
- Cross-table count property generation (counts through intermediate relationships)
- Filtered count properties (counts with WHERE clauses)
- Both Python and SQL expression behavior for counts
- Error handling for misconfigured count relationships
- Performance characteristics of generated COUNT queries

Use the existing mock model patterns from Phase 1 tests but extend them to include count scenarios.

### Testing for Phase 2.4
**Test Cases:**
- All counting mixin test scenarios pass
- Mock models generate expected count properties
- SQL count expressions match expected patterns
- Count accuracy is maintained across different scenarios
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_mixins.py -v -k "count"
uv run pytest sologm/models/tests/test_mixins.py -v  # All mixin tests
```
**Success Criteria:** New counting tests pass, no regressions in existing mixin tests

---

## Phase 2.5: Migrate Scene Model (Highest Count Property Count)

**Files to modify:**
- `sologm/models/scene.py`

### Sub-step 2.5.1: Add Counting Mixin to Scene
**File:** `sologm/models/scene.py`  
**Change:** Add `CountingMixin` to Scene's inheritance and define `_counting_configs`  
**Rationale:** Scene has the most count properties (5), making it a good test case for the counting mixin  
**Context:** Scene already has `ExistenceCheckMixin` from Phase 1. Add `CountingMixin` to the inheritance chain and configure it for all 5 count properties. This tests the mixin's ability to coexist with other mixins.

Configuration to add:
```python
_counting_configs = {
    'events': DirectCountConfig(model=Event, foreign_key='scene_id'),
    'dice_rolls': DirectCountConfig(model=DiceRoll, foreign_key='scene_id'),
    'interpretation_sets': DirectCountConfig(model=InterpretationSet, foreign_key='scene_id'),
    'interpretations': CrossTableCountConfig(
        model=Interpretation,
        foreign_key='set_id',
        relationship_path=['interpretation_sets', 'interpretations']
    ),
    'selected_interpretations': FilteredCrossTableCountConfig(
        model=Interpretation,
        foreign_key='set_id', 
        relationship_path=['interpretation_sets', 'interpretations'],
        filter_condition=FilterCondition(field='is_selected', value=True)
    )
}
```

Add type hints in `TYPE_CHECKING` block for the generated count properties.

### Sub-step 2.5.2: Remove Original Count Properties
**File:** `sologm/models/scene.py`  
**Change:** Delete the original count hybrid property implementations  
**Rationale:** Git history preserves originals for reference if needed  
**Context:** Delete the manual implementations of `event_count`, `dice_roll_count`, `interpretation_set_count`, `interpretation_count`, `selected_interpretation_count`. The CountingMixin now provides these properties automatically.

Git history provides rollback capability and reference for comparing behavior.

### Testing for Phase 2.5
**Test Cases:**
- All Scene model tests pass
- Generated count properties behave identically to original properties
- Count SQL queries generated match expected patterns
- Python count property access works correctly
- Multiple mixins coexist without conflicts (existence + counting)
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_scene_model.py -v
uv run pytest sologm/core/tests/test_scene.py -v
uv run pytest -k "scene" -v  # Run all scene-related tests
```
**Success Criteria:** All tests pass, no behavioral changes detected, counts are accurate

---

## Phase 2.6: Migrate Act Model

**Files to modify:**
- `sologm/models/act.py`

### Sub-step 2.6.1: Add Counting Mixin to Act Model
**File:** `sologm/models/act.py`  
**Change:** Add counting mixin inheritance and configure count properties  
**Rationale:** Act has complex cross-scene count relationships, testing mixin's handling of aggregated counts  
**Context:** Act already has `ExistenceCheckMixin` from Phase 1. Add `CountingMixin` to handle the 4 count properties, including the complex cross-scene counts (event_count, dice_roll_count, interpretation_count).

Key configurations:
```python
_counting_configs = {
    'scenes': DirectCountConfig(model=Scene, foreign_key='act_id'),
    'events': CrossTableCountConfig(
        model=Event,
        foreign_key='scene_id',
        relationship_path=['scenes', 'events']
    ),
    'dice_rolls': CrossTableCountConfig(
        model=DiceRoll,
        foreign_key='scene_id', 
        relationship_path=['scenes', 'dice_rolls']
    ),
    'interpretations': FilteredCrossTableCountConfig(
        model=Interpretation,
        foreign_key='set_id',
        relationship_path=['scenes', 'interpretation_sets', 'interpretations']
    )
}
```

These configurations test the mixin's ability to handle aggregated counts across multiple tables.

### Sub-step 2.6.2: Remove Original Count Properties
**File:** `sologm/models/act.py`  
**Change:** Delete original count properties and add type hints  
**Rationale:** Maintain consistency with Scene migration approach  
**Context:** Follow the same pattern as Scene - delete originals, add type hints for generated properties.

### Testing for Phase 2.6
**Test Cases:**
- All Act model tests pass
- Cross-scene count properties work correctly
- Complex count SQL expressions generate properly
- Manager classes can still use the count properties for ordering/filtering
- Multiple mixins coexist without conflicts
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_act_model.py -v
uv run pytest sologm/core/tests/test_act.py -v
uv run pytest -k "act" -v
```
**Success Criteria:** All tests pass, complex count relationships work correctly

---

## Phase 2.7: Migrate Remaining Models

**Files to modify:**
- `sologm/models/game.py`
- `sologm/models/oracle.py` (Interpretation and InterpretationSet)

### Sub-step 2.7.1: Migrate Game Model
**File:** `sologm/models/game.py`  
**Change:** Add counting mixin for Game's count property  
**Rationale:** Game has simple direct count relationship, testing basic counting mixin functionality  
**Context:** Game has 1 count property: `act_count`. This is a straightforward direct relationship count that validates the mixin works for simple cases.

Configuration:
```python
_counting_configs = {
    'acts': DirectCountConfig(model=Act, foreign_key='game_id')
}
```

### Sub-step 2.7.2: Migrate Oracle Models
**File:** `sologm/models/oracle.py`  
**Change:** Add counting mixin to both Interpretation and InterpretationSet classes  
**Rationale:** Test counting mixin on simpler cases and bidirectional relationships  
**Context:** InterpretationSet has `interpretation_count`, Interpretation has `event_count`. These are simple direct relationship counts that ensure the mixin works correctly for basic scenarios.

Configurations:
```python
# InterpretationSet
_counting_configs = {
    'interpretations': DirectCountConfig(model=Interpretation, foreign_key='set_id')
}

# Interpretation  
_counting_configs = {
    'events': DirectCountConfig(model=Event, foreign_key='interpretation_id')
}
```

### Testing for Phase 2.7
**Test Cases:**
- All model tests pass for migrated models
- Direct relationship counts work correctly (Game.act_count)
- Simple relationship counts work (Interpretation, InterpretationSet)
- All count properties maintain accuracy and performance
**How to Test:** 
```bash
uv run pytest sologm/models/tests/ -v -k "count"
uv run pytest sologm/core/tests/ -v
uv run pytest -x  # Stop on first failure to catch issues early
```
**Success Criteria:** All tests pass across all migrated models

---

## Phase 2.8: Validation and Cleanup

**Files to modify:**
- `sologm/models/scene.py`
- `sologm/models/act.py` 
- `sologm/models/game.py`

### Sub-step 2.8.1: Run Comprehensive Test Suite
**File:** Multiple files  
**Change:** Execute full test suite and validate no regressions  
**Rationale:** Ensure all functionality still works before removing original code  
**Context:** Run the complete test suite including integration tests, manager tests, and CLI tests. Pay special attention to any code that uses count properties for ordering or filtering, as this is common in the manager layer.

### Sub-step 2.8.2: Final Validation of Count Property Migration
**File:** All migrated model files  
**Change:** Validate that all count properties have been successfully migrated to CountingMixin  
**Rationale:** Ensure complete migration is successful across all models  
**Context:** Verify that all original count property implementations have been removed and replaced with CountingMixin-generated properties. Confirm all functionality is preserved.

Validation checklist:
- All tests pass across all migrated models
- Count SQL queries generate correctly and efficiently  
- Python count property access works consistently
- Manager classes can use the count properties for ordering/filtering
- Performance hasn't regressed (COUNT queries should be efficient)
- No orphaned or duplicate count properties remain

### Sub-step 2.8.3: Update Documentation
**File:** `sologm/models/README.md`  
**Change:** Update model documentation to reflect the new counting mixin approach  
**Rationale:** Keep documentation current with the implementation  
**Context:** Update the model documentation to mention that count properties are now generated by the CountingMixin. Add examples of how to configure new count properties and explain the relationship path syntax for complex counts.

### Testing for Phase 2.8
**Test Cases:**
- Complete test suite passes
- No dead code remains
- Documentation accurately reflects current implementation
- Performance hasn't regressed (COUNT queries are efficient)
- Manager ordering/filtering with count properties works correctly
**How to Test:** 
```bash
uv run pytest -v --tb=short  # Full test suite
uv run pytest --cov=sologm.models  # Ensure test coverage maintained
# Manual testing of key functionality that uses counts
sologm game list  # Should use act_count for display
sologm game status  # Should use various count properties
```
**Success Criteria:** All tests pass, documentation is current, no performance regression

---

## Phase 2 Completion Criteria

### Functional Requirements
- [ ] All 8 target count properties migrated to mixin-generated
- [ ] All existing tests pass without modification
- [ ] Count SQL queries generated are efficient and accurate
- [ ] Python count property access behavior unchanged
- [ ] No performance regression in count query execution
- [ ] Multiple mixins coexist correctly (existence + counting)

### Code Quality Requirements  
- [ ] No code duplication for count operation patterns
- [ ] Counting mixin configuration is clear and maintainable
- [ ] Proper error handling for misconfigured count properties
- [ ] Type hints maintained for IDE support
- [ ] Documentation updated to reflect counting mixin

### Safety Requirements
- [ ] Original count functionality preserved exactly
- [ ] No breaking changes to public API
- [ ] Count accuracy maintained across all scenarios
- [ ] Efficient COUNT queries generated (no performance regression)

---

## Risk Mitigation

**High Risk: Count Accuracy and Performance**
- Mitigation: Extensive testing of count accuracy, SQL query analysis for performance
- Fallback: Validate thoroughly before deletion, use git history for rollback if needed

**Medium Risk: Complex Cross-Table Counts**  
- Mitigation: Thorough testing of relationship path configurations, SQL inspection
- Fallback: Handle complex counts manually if mixin can't support them

**Low Risk: Multiple Mixin Interactions**
- Mitigation: Test existence + counting mixins together, ensure no conflicts
- Fallback: Separate mixin inheritance if conflicts arise

---

## Future Phases Preview

This plan continues building the mixin infrastructure:
- **Phase 3**: Status Check Mixin (`is_X`, `has_active_X` patterns)  
- **Phase 4**: Navigation Properties (may not need mixin, mostly `@property`)

The counting mixin infrastructure created in Phase 2 demonstrates that multiple mixins can coexist and provides patterns for Phase 3's status check mixin.
