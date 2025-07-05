# Phase 1: Existence Check Mixin Implementation Plan

**Feature:** Hybrid Property Refactor - Phase 1  
**Focus:** Extract existence check patterns (`has_X` hybrid properties)  
**Target:** ~15 properties across 6 models  
**Strategy:** Pattern-specific mixin with incremental migration  

## Overview

This phase creates an `ExistenceCheckMixin` that generates `has_X` hybrid properties automatically from configuration. **Critically, we first ensure comprehensive test coverage for all target properties before making any changes to the models.** We'll then migrate models one at a time, validate behavior, then remove original properties.

**Target Properties:**
- **Game**: `has_acts`, `has_active_act`, `has_active_scene`, `has_completed_acts` (4 properties)
- **Act**: `has_scenes`, `has_active_scene`, `has_events`, `has_dice_rolls`, `has_interpretations` (5 properties)  
- **Scene**: `has_events`, `has_dice_rolls`, `has_interpretation_sets`, `has_interpretations`, `has_selected_interpretations` (5 properties)
- **Interpretation**: `has_events` (1 property)
- **InterpretationSet**: `has_selection` (1 property)  
- **DiceRoll**: `has_reason` (1 property - special case, not relationship-based)

---

## Phase 1.0: Audit Scene Model Test Coverage

**Files to modify:**
- `sologm/models/tests/test_scene_model.py`

### Sub-step 1.0.1: Audit Scene Hybrid Property Test Coverage
**File:** `sologm/models/tests/test_scene_model.py`  
**Change:** Analyze current test coverage for Scene's 5 existence properties  
**Rationale:** Scene has the most complex existence properties, so we start there to understand our testing gaps  
**Context:** Scene has 5 existence properties that we need to refactor: `has_events`, `has_dice_rolls`, `has_interpretation_sets`, `has_interpretations`, `has_selected_interpretations`. We need to identify which of these have adequate test coverage and which need tests created. Focus only on Scene to keep this phase manageable.

**Audit checklist for each Scene property:**
- **Python context testing**: Verify property works when called on Scene instance
- **SQL context testing**: Verify property works in SQLAlchemy queries/filters  
- **Edge case testing**: Empty relationships, complex scenarios
- **Both positive and negative cases**: Tests for both "has" and "doesn't have"

Document findings in comments at the top of the test file. Look for existing tests that may already cover these properties indirectly.

### Sub-step 1.0.2: Create Missing Scene Hybrid Property Tests
**File:** `sologm/models/tests/test_scene_model.py`  
**Change:** Add comprehensive tests for any Scene existence properties lacking coverage  
**Rationale:** Every property we plan to refactor must have solid tests to catch regressions  
**Context:** Follow the existing test patterns in the file. Use the existing fixtures (session, test scenes, etc.) but ensure both Python and SQL contexts are tested. Pay special attention to `has_interpretations` and `has_selected_interpretations` which involve complex cross-table relationships.

**Key testing patterns to implement:**
- Test both empty and populated relationships
- Test SQL filtering with hybrid properties
- Test complex relationships (interpretations through interpretation_sets)
- Test edge cases (scenes with interpretation_sets but no interpretations)

**Architectural considerations:**
- Use existing test fixtures and factories
- Follow the project's test naming conventions
- Don't create new database setup - use existing session fixtures
- Ensure tests are isolated and don't depend on order

### Testing for Phase 1.0
**Test Cases:**
- All existing Scene tests continue to pass
- All 5 Scene existence properties have comprehensive test coverage
- Both Python and SQL contexts tested for each property
- Complex relationship scenarios covered (interpretation_sets -> interpretations)
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_scene_model.py -v
uv run pytest sologm/core/tests/test_scene.py -v  # Related manager tests
uv run pytest -k "scene" -v  # All scene-related tests
```
**Success Criteria:** 
- All Scene tests pass consistently
- Every Scene existence property has adequate test coverage
- Complex relationship edge cases are tested

---

## Phase 1.1: Audit Act Model Test Coverage

**Files to modify:**
- `sologm/models/tests/test_act_model.py`

### Sub-step 1.1.1: Audit Act Hybrid Property Test Coverage
**File:** `sologm/models/tests/test_act_model.py`  
**Change:** Analyze current test coverage for Act's 5 existence properties  
**Rationale:** Act has cross-scene relationships that need special testing attention  
**Context:** Act has 5 existence properties: `has_scenes`, `has_active_scene`, `has_events`, `has_dice_rolls`, `has_interpretations`. Some of these (`has_events`, `has_dice_rolls`, `has_interpretations`) check relationships through scenes, making them more complex to test and refactor.

Follow the same audit approach as Scene, but pay special attention to properties that navigate through the `scenes` relationship to check for related entities.

### Sub-step 1.1.2: Create Missing Act Hybrid Property Tests
**File:** `sologm/models/tests/test_act_model.py`  
**Change:** Add tests for any missing Act existence property coverage  
**Rationale:** Cross-scene relationship properties need thorough testing before refactoring  
**Context:** Focus especially on the cross-relationship properties (`has_events`, `has_dice_rolls`, `has_interpretations`) which require creating test data across multiple tables. Use existing fixtures but may need to create more complex test scenarios.

**Special considerations:**
- Test acts with no scenes vs acts with scenes
- Test acts with scenes but no events/dice_rolls/interpretations
- Test acts with multiple scenes having different content
- Ensure SQL expressions handle the joins correctly

### Testing for Phase 1.1
**Test Cases:**
- All existing Act tests pass
- All 5 Act existence properties have comprehensive coverage
- Cross-scene relationship properties work in both contexts
- Complex scenarios (multiple scenes with different content) are tested
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_act_model.py -v
uv run pytest sologm/core/tests/test_act.py -v
uv run pytest -k "act" -v
```
**Success Criteria:** Cross-scene relationship properties are thoroughly tested in both Python and SQL contexts

---

## Phase 1.2: Audit Remaining Model Test Coverage

**Files to modify:**
- `sologm/models/tests/test_game_model.py`
- `sologm/models/tests/test_oracle_model.py`
- `sologm/models/tests/test_dice_model.py`

### Sub-step 1.2.1: Audit Game Model Test Coverage
**File:** `sologm/models/tests/test_game_model.py`  
**Change:** Add tests for any missing Game model existence property coverage  
**Rationale:** Game has the most complex hierarchical relationships (through acts to scenes)  
**Context:** Game properties: `has_acts`, `has_active_act`, `has_active_scene`, `has_completed_acts`. These involve multiple relationship levels and active/completed status filtering.

### Sub-step 1.2.2: Audit Oracle Models Test Coverage  
**File:** `sologm/models/tests/test_oracle_model.py`  
**Change:** Add tests for any missing Oracle models existence property coverage  
**Rationale:** These are simpler cases that help validate the mixin approach  
**Context:** InterpretationSet has `has_selection`, Interpretation has `has_events`. These are more straightforward relationship checks.

### Sub-step 1.2.3: Audit DiceRoll Test Coverage
**File:** `sologm/models/tests/test_dice_model.py`  
**Change:** Add tests for any missing DiceRoll models existence property coverage  
**Rationale:** This is a non-relationship existence check (field null/empty) - special case  
**Context:** `has_reason` checks if the reason field is not null/empty rather than checking a relationship. This may require different mixin handling.

### Testing for Phase 1.2
**Test Cases:**
- All remaining model existence properties have test coverage
- Hierarchical relationships tested (Game through Act to Scene)
- Simple relationship checks tested (InterpretationSet, Interpretation)
- Non-relationship existence checks tested (DiceRoll.has_reason)
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_game_model.py -v
uv run pytest sologm/models/tests/test_oracle_model.py -v  
uv run pytest sologm/models/tests/test_dice_model.py -v
uv run pytest sologm/models/tests/ -v  # Full model test suite
```
**Success Criteria:** All 15 target existence properties have comprehensive test coverage

---

## Phase 1.3: Create Core Mixin Infrastructure

**Files to modify:**
- `sologm/models/mixins.py` (new file)
- `sologm/models/__init__.py`

### Sub-step 1.3.1: Create Mixin Foundation
**File:** `sologm/models/mixins.py`  
**Change:** Create the base mixin class and configuration structures  
**Rationale:** Establish the foundation that will generate existence check properties  
**Context:** This is a new file that will house all pattern-specific mixins. The mixin uses `__init_subclass__` to automatically generate properties when a model class is defined. We need to handle potential circular import issues by using string model names where necessary.

Create the following core components:
- `ExistenceConfig` dataclass for property configuration
- `ExistenceCheckMixin` base class with property generation logic
- Property generation methods that create both Python and SQL expressions
- Error handling for misconfigured relationships

Key considerations:
- Use `typing.TYPE_CHECKING` for model imports to avoid circular dependencies
- Generate properties that behave identically to existing manual implementations
- Include proper docstrings and type hints for generated properties
- Handle edge cases like missing relationships gracefully

### Sub-step 1.3.2: Update Model Package Imports
**File:** `sologm/models/__init__.py`  
**Change:** Add import for the new mixins module  
**Rationale:** Make mixins available for import by model files  
**Context:** Follow the existing pattern in the models package where core components are imported. This ensures the mixins are available when models import them.

Add the mixins import after the existing imports but before the relationships import to avoid dependency issues.

### Testing for Phase 1.3
**Test Cases:**
- Mixin can be imported without errors
- `ExistenceConfig` dataclass accepts expected parameters
- Mixin raises appropriate errors for invalid configurations
**How to Test:** 
```bash
cd /Users/mike/git/sologm
python -c "from sologm.models.mixins import ExistenceCheckMixin, ExistenceConfig; print('Import successful')"
uv run pytest sologm/models/tests/ -v
```
**Success Criteria:** No import errors, existing model tests pass, basic mixin instantiation works

---

## Phase 1.4: Create Mixin Tests

**Files to modify:**
- `sologm/models/tests/test_mixins.py` (new file)

### Sub-step 1.4.1: Create Comprehensive Mixin Tests
**File:** `sologm/models/tests/test_mixins.py`  
**Change:** Create isolated tests for the mixin functionality  
**Rationale:** Ensure mixin behavior is correct before applying to real models  
**Context:** Since this is new functionality, we need thorough tests. Create mock model classes to test the mixin in isolation, then test property generation, SQL expression creation, and error handling.

Test scenarios to cover:
- Property generation from valid configurations
- Both Python and SQL expression behavior
- Error handling for missing relationships
- Edge cases like empty relationships
- Multiple properties on the same model
- SQL query generation matches expected patterns

Use the existing test patterns from the project (session fixtures, test model factories) but create simplified mock models to avoid circular dependencies during testing.

### Testing for Phase 1.4
**Test Cases:**
- All mixin test scenarios pass
- Mock models generate expected properties
- SQL expressions match expected patterns
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_mixins.py -v
uv run pytest sologm/models/tests/ -v  # Ensure no regressions
```
**Success Criteria:** New tests pass, no regressions in existing model tests

---

## Phase 1.5: Migrate Scene Model (Highest Property Count)

**Files to modify:**
- `sologm/models/scene.py`

### Sub-step 1.5.1: Add Mixin and Configuration to Scene
**File:** `sologm/models/scene.py`  
**Change:** Add `ExistenceCheckMixin` to Scene's inheritance and define `_existence_configs`  
**Rationale:** Scene has the most existence properties (5), making it a good test case for the mixin  
**Context:** Scene is a complex model with multiple relationship types. This tests the mixin's ability to handle various scenarios. Add the mixin to the inheritance chain and configure it for all 5 existence properties.

Configuration to add:
```python
_existence_configs = {
    'events': ExistenceConfig(model='Event', foreign_key='scene_id'),
    'dice_rolls': ExistenceConfig(model='DiceRoll', foreign_key='scene_id'),
    'interpretation_sets': ExistenceConfig(model='InterpretationSet', foreign_key='scene_id'),
    'interpretations': ExistenceConfig(model='Interpretation', foreign_key='scene_id', relationship_path='interpretation_sets.interpretations'),
    'selected_interpretations': ExistenceConfig(model='Interpretation', foreign_key='scene_id', relationship_path='interpretation_sets.interpretations', filter_condition='is_selected=True')
}
```

Add type hints in `TYPE_CHECKING` block for the generated properties to maintain IDE support.

### Sub-step 1.5.2: Comment Out Original Properties
**File:** `sologm/models/scene.py`  
**Change:** Comment out (don't delete) the original hybrid property implementations  
**Rationale:** Keep originals for comparison during testing, remove after validation  
**Context:** Comment out the manual implementations of `has_events`, `has_dice_rolls`, `has_interpretation_sets`, `has_interpretations`, `has_selected_interpretations`. Add comments indicating they're replaced by the mixin.

This allows for easy rollback if issues are discovered and provides reference for comparing behavior.

### Testing for Phase 1.5
**Test Cases:**
- All Scene model tests pass
- Generated properties behave identically to original properties
- SQL queries generated match expected patterns
- Python property access works correctly
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_scene_model.py -v
uv run pytest sologm/core/tests/test_scene.py -v
uv run pytest -k "scene" -v  # Run all scene-related tests
```
**Success Criteria:** All tests pass, no behavioral changes detected

---

## Phase 1.6: Migrate Act Model

**Files to modify:**
- `sologm/models/act.py`

### Sub-step 1.6.1: Add Mixin to Act Model
**File:** `sologm/models/act.py`  
**Change:** Add mixin inheritance and configure existence properties  
**Rationale:** Act has complex cross-scene relationships, testing mixin's handling of indirect relationships  
**Context:** Act has 5 existence properties, some of which check relationships through scenes (has_events, has_dice_rolls, has_interpretations). This tests the mixin's ability to handle indirect relationships.

Key configurations:
- `has_scenes`: Direct relationship to scenes
- `has_active_scene`: Filtered relationship (is_active=True)
- `has_events`: Cross-scene relationship via scenes.events
- `has_dice_rolls`: Cross-scene relationship via scenes.dice_rolls  
- `has_interpretations`: Complex cross-scene relationship via scenes.interpretation_sets.interpretations

Handle the complex SQL expressions that need to join through multiple tables.

### Sub-step 1.6.2: Update Related Manager Tests
**File:** `sologm/models/act.py`  
**Change:** Comment out original properties and add type hints  
**Rationale:** Maintain consistency with Scene migration approach  
**Context:** Follow the same pattern as Scene - comment out originals, add type hints, prepare for validation.

### Testing for Phase 1.6
**Test Cases:**
- All Act model tests pass
- Cross-scene relationship properties work correctly
- Complex SQL joins generate properly
- Manager classes can still use the hybrid properties
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_act_model.py -v
uv run pytest sologm/core/tests/test_act.py -v
uv run pytest -k "act" -v
```
**Success Criteria:** All tests pass, complex relationship queries work correctly

---

## Phase 1.7: Migrate Remaining Models

**Files to modify:**
- `sologm/models/game.py`
- `sologm/models/oracle.py` (Interpretation and InterpretationSet)
- `sologm/models/dice.py` (DiceRoll)

### Sub-step 1.7.1: Migrate Game Model
**File:** `sologm/models/game.py`  
**Change:** Add mixin for Game's 4 existence properties  
**Rationale:** Game has hierarchical relationships (through acts to scenes), testing deep navigation  
**Context:** Game properties often check through multiple relationship levels. Configure `has_acts`, `has_active_act`, `has_active_scene`, `has_completed_acts`.

### Sub-step 1.7.2: Migrate Oracle Models
**File:** `sologm/models/oracle.py`  
**Change:** Add mixin to both Interpretation and InterpretationSet classes  
**Rationale:** Test mixin on simpler cases and bidirectional relationships  
**Context:** InterpretationSet has `has_selection`, Interpretation has `has_events`. These are simpler cases that validate the mixin works for straightforward relationships.

### Sub-step 1.7.3: Handle DiceRoll Special Case
**File:** `sologm/models/dice.py`  
**Change:** Migrate `has_reason` property (not relationship-based)  
**Rationale:** Test mixin's handling of non-relationship existence checks  
**Context:** `has_reason` checks if a field is not null/empty, not if a relationship exists. This may require a different configuration pattern or a separate method in the mixin.

### Testing for Phase 1.7
**Test Cases:**
- All model tests pass for migrated models
- Hierarchical relationships work correctly (Game through Act to Scene)
- Simple existence checks work (Interpretation, InterpretationSet)
- Non-relationship existence checks work (DiceRoll.has_reason)
**How to Test:** 
```bash
uv run pytest sologm/models/tests/ -v
uv run pytest sologm/core/tests/ -v
uv run pytest -x  # Stop on first failure to catch issues early
```
**Success Criteria:** All tests pass across all migrated models

---

## Phase 1.8: Validation and Cleanup

**Files to modify:**
- `sologm/models/scene.py`
- `sologm/models/act.py` 
- `sologm/models/game.py`
- `sologm/models/oracle.py`
- `sologm/models/dice.py`

### Sub-step 1.8.1: Run Comprehensive Test Suite
**File:** Multiple files  
**Change:** Execute full test suite and validate no regressions  
**Rationale:** Ensure all functionality still works before removing original code  
**Context:** Run the complete test suite including integration tests, manager tests, and CLI tests to ensure the refactoring hasn't broken anything. Pay special attention to any tests that use the hybrid properties in SQL queries.

### Sub-step 1.8.2: Remove Original Property Implementations
**File:** All migrated model files  
**Change:** Delete the commented-out original hybrid property implementations  
**Rationale:** Clean up the codebase now that mixin-generated properties are validated  
**Context:** Remove the original property implementations that were commented out in earlier phases. This should be done carefully, ensuring all imports and references are still valid.

Only remove properties after confirming:
- All tests pass
- SQL queries generate correctly  
- Python property access works
- Manager classes can use the properties
- No references to the original implementations remain

### Sub-step 1.8.3: Update Documentation
**File:** `sologm/models/README.md`  
**Change:** Update model documentation to reflect the new mixin-based approach  
**Rationale:** Keep documentation current with the implementation  
**Context:** Update the model documentation to mention that existence properties are now generated by the ExistenceCheckMixin. Add a section explaining how the mixin system works and how to configure new existence properties.

### Testing for Phase 1.8
**Test Cases:**
- Complete test suite passes
- No dead code remains
- Documentation accurately reflects current implementation
- Performance hasn't regressed (SQL query plans should be identical)
**How to Test:** 
```bash
uv run pytest -v --tb=short  # Full test suite
uv run pytest --cov=sologm.models  # Ensure test coverage maintained
# Manual testing of key functionality
sologm game list
sologm game status  # Should use hybrid properties
```
**Success Criteria:** All tests pass, documentation is current, no performance regression

---

## Phase 1 Completion Criteria

### Functional Requirements
- [ ] All 15 target existence properties migrated to mixin-generated
- [ ] All existing tests pass without modification
- [ ] SQL queries generated are identical to original implementations
- [ ] Python property access behavior unchanged
- [ ] No performance regression in query execution

### Code Quality Requirements  
- [ ] No code duplication for existence check patterns
- [ ] Mixin configuration is clear and maintainable
- [ ] Proper error handling for misconfigured properties
- [ ] Type hints maintained for IDE support
- [ ] Documentation updated to reflect changes

### Safety Requirements
- [ ] Original functionality preserved exactly
- [ ] No breaking changes to public API
- [ ] Rollback plan available (git history + tests)
- [ ] All edge cases handled appropriately

---

## Risk Mitigation

**High Risk: SQL Expression Compatibility**
- Mitigation: Extensive testing against existing test suite, SQL query comparison
- Fallback: Keep original implementations commented until validation complete

**Medium Risk: Circular Import Issues**  
- Mitigation: Use string model names in configurations, careful import ordering
- Fallback: Move mixin to different location if needed

**Low Risk: Type Hint Support**
- Mitigation: Explicit type hints in TYPE_CHECKING blocks
- Fallback: Manual type hint additions if generated ones insufficient

---

## Future Phases Preview

This plan sets up the foundation for subsequent phases:
- **Phase 2**: Count Operations Mixin (`X_count` patterns)
- **Phase 3**: Status Check Mixin (`is_X`, `has_active_X` patterns)  
- **Phase 4**: Navigation Properties (may not need mixin, mostly `@property`)

The mixin infrastructure created in Phase 1 will be extended for other patterns, making subsequent phases faster to implement.
