# Phase 4: Navigation Properties Consolidation Plan

**Feature:** Hybrid Property Refactor - Phase 4  
**Focus:** Consolidate navigation properties (`active_X`, `latest_X`, `first_X`, `current_X`, `all_X` properties)  
**Target:** ~20 navigation properties across 6 models  
**Strategy:** Consolidate repetitive navigation patterns using helper utilities (not mixins)  

## Overview

This final phase addresses the remaining repetitive property patterns in the SoloGM models. Unlike Phases 1-3 which used mixins for `@hybrid_property` patterns, Phase 4 focuses on regular `@property` navigation methods that have repetitive implementations. **We will consolidate these patterns using shared utility functions rather than mixins, as these are Python-only properties.**

**Target Properties:**
- **Game**: `active_act`, `active_scene`, `active_acts`, `latest_act`, `latest_scene` (5 properties)
- **Act**: `active_scene`, `latest_scene`, `first_scene`, `latest_event`, `latest_dice_roll`, `latest_interpretation`, `all_events`, `all_dice_rolls`, `all_interpretations`, `selected_interpretations` (10 properties)
- **Scene**: `latest_event`, `latest_dice_roll`, `latest_interpretation_set`, `latest_interpretation`, `current_interpretation_set`, `selected_interpretations`, `all_interpretations` (7 properties)
- **Interpretation**: `latest_event` (1 property)

**Note:** Unlike previous phases, these are regular `@property` methods, not `@hybrid_property`, so they don't need SQL expressions.

---

## Phase 4.0: Analyze Navigation Property Patterns

**Files to modify:**
- `sologm/models/utils.py`

### Sub-step 4.0.1: Identify Common Navigation Patterns
**File:** `sologm/models/utils.py`  
**Change:** Analyze all navigation properties to identify common patterns for consolidation  
**Rationale:** Before creating utilities, we need to understand the repetitive patterns across all navigation properties  
**Context:** Navigation properties fall into several patterns: active filtering, latest by timestamp, first by sequence, current by flag, and cross-relationship navigation. Understanding these patterns will help us create the right utility functions.

**Identified navigation patterns:**
1. **Active filtering**: Find entity where `is_active = True` (e.g., `active_act`, `active_scene`)
2. **Latest by timestamp**: Find most recent entity by `created_at` (e.g., `latest_event`, `latest_act`)
3. **First by sequence**: Find entity with lowest `sequence` (e.g., `first_scene`)
4. **Current by flag**: Find entity where `is_current = True` (e.g., `current_interpretation_set`)
5. **Cross-relationship navigation**: Navigate through multiple relationships (e.g., `Game.active_scene` through acts)
6. **Collection aggregation**: Collect entities across relationships (e.g., `Act.all_events` across scenes)
7. **Filtered collections**: Filter collections by criteria (e.g., `selected_interpretations`)

### Sub-step 4.0.2: Create Navigation Utility Functions
**File:** `sologm/models/utils.py`  
**Change:** Create reusable utility functions for common navigation patterns  
**Rationale:** Reduce code duplication by providing shared implementations for common navigation patterns  
**Context:** Create utility functions that can be used across models to implement navigation properties consistently. These utilities will handle the common patterns identified in sub-step 4.0.1.

**Utility functions to create:**
```python
def get_active_entity(collection: List[Any]) -> Optional[Any]
def get_latest_entity(collection: List[Any]) -> Optional[Any]
def get_first_entity_by_sequence(collection: List[Any]) -> Optional[Any]
def get_current_entity(collection: List[Any]) -> Optional[Any]
def get_filtered_collection(collection: List[Any], filter_field: str, filter_value: Any) -> List[Any]
def get_cross_relationship_entity(start_entity: Any, relationship_path: List[str], final_filter: Callable) -> Optional[Any]
def aggregate_cross_relationship_collection(start_entity: Any, relationship_path: List[str]) -> List[Any]
```

**Architectural considerations:**
- Use generic typing to work with any model type
- Handle cases where relationships aren't loaded gracefully
- Maintain consistency with existing property behavior
- Keep utilities simple and focused on single responsibilities

### Testing for Phase 4.0
**Test Cases:**
- Navigation utilities can be imported without errors
- Utility functions handle empty collections gracefully
- Utility functions return correct entities for various scenarios
- Performance is maintained (no additional database queries)
**How to Test:** 
```bash
cd /Users/mike/git/sologm
python -c "from sologm.models.utils import get_active_entity, get_latest_entity; print('Import successful')"
uv run pytest sologm/models/tests/ -v
```
**Success Criteria:** 
- Utility functions are implemented and tested
- No regressions in existing functionality
- Foundation is ready for property consolidation

---

## Phase 4.1: Create Comprehensive Utility Tests

**Files to modify:**
- `sologm/models/tests/test_utils.py`

### Sub-step 4.1.1: Create Navigation Utility Tests
**File:** `sologm/models/tests/test_utils.py`  
**Change:** Add comprehensive tests for all navigation utility functions  
**Rationale:** Ensure utility functions work correctly before applying them to model properties  
**Context:** Create tests that cover all navigation patterns and edge cases. These tests will validate that the utility functions can replace the existing property implementations without changing behavior.

**Test scenarios to cover:**
- Active entity finding (single active, no active, multiple active)
- Latest entity finding (single entity, multiple entities, empty collection)
- First entity by sequence (ordered sequences, gaps in sequences, empty collection)
- Current entity finding (single current, no current, multiple current)
- Filtered collections (various filter criteria, empty results)
- Cross-relationship navigation (complex paths, missing intermediate entities)
- Collection aggregation (across multiple relationships, empty intermediate collections)

Use mock model objects to test utility functions in isolation from the actual model complexity.

### Testing for Phase 4.1
**Test Cases:**
- All navigation utility test scenarios pass
- Utility functions handle edge cases gracefully
- Performance characteristics are acceptable
- Utility functions match existing property behavior patterns
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_utils.py -v
uv run pytest sologm/models/tests/ -v  # Ensure no regressions
```
**Success Criteria:** All utility tests pass, functions are ready for use in models

---

## Phase 4.2: Consolidate Game Model Navigation Properties

**Files to modify:**
- `sologm/models/game.py`

### Sub-step 4.2.1: Replace Game Navigation Properties with Utilities
**File:** `sologm/models/game.py`  
**Change:** Replace repetitive navigation property implementations with utility function calls  
**Rationale:** Game has hierarchical navigation properties that demonstrate the utility approach on complex scenarios  
**Context:** Game has 5 navigation properties that can be simplified using the utility functions. Some properties navigate across multiple relationships (active_scene through acts), making this a good test of the utility approach.

**Properties to consolidate:**
```python
# Before: Manual implementation
@property
def active_act(self) -> Optional["Act"]:
    """Get the active act for this game, if any."""
    return next((act for act in self.acts if act.is_active), None)

# After: Using utility
@property
def active_act(self) -> Optional["Act"]:
    """Get the active act for this game, if any."""
    return get_active_entity(self.acts)
```

Apply similar consolidation to `active_scene`, `active_acts`, `latest_act`, `latest_scene`.

### Sub-step 4.2.2: Validate Game Property Behavior
**File:** `sologm/models/game.py`  
**Change:** Ensure consolidated properties maintain identical behavior  
**Rationale:** Navigation properties are used throughout the application and must maintain exact behavior  
**Context:** After consolidating properties, validate that they still return the same results as the original implementations. This is critical for maintaining application functionality.

### Testing for Phase 4.2
**Test Cases:**
- All Game model tests pass
- Navigation properties behave identically to original implementations
- Performance is maintained (no additional queries)
- Complex cross-relationship navigation works correctly (active_scene through acts)
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_game_model.py -v
uv run pytest sologm/core/tests/test_game.py -v
uv run pytest -k "game" -v
```
**Success Criteria:** All tests pass, navigation properties work correctly

---

## Phase 4.3: Consolidate Act Model Navigation Properties

**Files to modify:**
- `sologm/models/act.py`

### Sub-step 4.3.1: Replace Act Navigation Properties with Utilities
**File:** `sologm/models/act.py`  
**Change:** Replace Act's 10 navigation properties with utility function calls  
**Rationale:** Act has the most navigation properties (10), making it the most impactful consolidation  
**Context:** Act has various navigation patterns: active filtering, latest finding, collection aggregation across scenes, and filtered collections. This tests all the utility functions comprehensively.

**Properties to consolidate:**
- `active_scene`: Use `get_active_entity(self.scenes)`
- `latest_scene`: Use `get_latest_entity(self.scenes)`
- `first_scene`: Use `get_first_entity_by_sequence(self.scenes)`
- `latest_event`: Use `get_latest_entity(self.all_events)`
- `latest_dice_roll`: Use `get_latest_entity(self.all_dice_rolls)`
- `latest_interpretation`: Use `get_latest_entity(self.all_interpretations)`
- `all_events`: Use `aggregate_cross_relationship_collection(self, ['scenes', 'events'])`
- `all_dice_rolls`: Use `aggregate_cross_relationship_collection(self, ['scenes', 'dice_rolls'])`
- `all_interpretations`: Use aggregation across `scenes.interpretation_sets.interpretations`
- `selected_interpretations`: Use filtered aggregation with `is_selected = True`

### Sub-step 4.3.2: Handle Complex Aggregation Properties
**File:** `sologm/models/act.py`  
**Change:** Address properties that aggregate across multiple relationship levels  
**Rationale:** Some Act properties are complex and may need specialized utility functions  
**Context:** Properties like `all_interpretations` navigate through scenes → interpretation_sets → interpretations. These may need specialized utilities or custom implementations using the basic utilities.

### Testing for Phase 4.3
**Test Cases:**
- All Act model tests pass
- Complex aggregation properties work correctly
- Cross-scene navigation properties maintain accuracy
- Performance is maintained across all property types
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_act_model.py -v
uv run pytest sologm/core/tests/test_act.py -v
uv run pytest -k "act" -v
```
**Success Criteria:** All tests pass, complex navigation properties work correctly

---

## Phase 4.4: Consolidate Scene Model Navigation Properties

**Files to modify:**
- `sologm/models/scene.py`

### Sub-step 4.4.1: Replace Scene Navigation Properties with Utilities
**File:** `sologm/models/scene.py`  
**Change:** Replace Scene's 7 navigation properties with utility function calls  
**Rationale:** Scene has interpretation-related navigation that tests specialized patterns  
**Context:** Scene navigation properties focus on latest entity finding and interpretation-specific patterns (current, selected). This tests the utility functions on interpretation-related scenarios.

**Properties to consolidate:**
- `latest_event`: Use `get_latest_entity(self.events)`
- `latest_dice_roll`: Use `get_latest_entity(self.dice_rolls)`
- `latest_interpretation_set`: Use `get_latest_entity(self.interpretation_sets)`
- `latest_interpretation`: Use aggregation across interpretation_sets.interpretations
- `current_interpretation_set`: Use `get_current_entity(self.interpretation_sets)`
- `selected_interpretations`: Use filtered aggregation with `is_selected = True`
- `all_interpretations`: Use aggregation across interpretation_sets.interpretations

### Testing for Phase 4.4
**Test Cases:**
- All Scene model tests pass
- Interpretation-related navigation works correctly
- Current and selected filtering works properly
- Aggregation across interpretation sets maintains accuracy
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_scene_model.py -v
uv run pytest sologm/core/tests/test_scene.py -v
uv run pytest -k "scene" -v
```
**Success Criteria:** All tests pass, interpretation navigation works correctly

---

## Phase 4.5: Consolidate Remaining Model Navigation Properties

**Files to modify:**
- `sologm/models/oracle.py` (Interpretation)

### Sub-step 4.5.1: Replace Interpretation Navigation Properties
**File:** `sologm/models/oracle.py`  
**Change:** Replace Interpretation's navigation property with utility function call  
**Rationale:** Complete the consolidation across all models  
**Context:** Interpretation has 1 navigation property (`latest_event`) that can be simplified using the utility functions.

**Property to consolidate:**
- `latest_event`: Use `get_latest_entity(self.events)`

### Testing for Phase 4.5
**Test Cases:**
- All remaining model tests pass
- All navigation properties use utility functions consistently
- No regression in any navigation functionality
**How to Test:** 
```bash
uv run pytest sologm/models/tests/test_oracle_model.py -v
uv run pytest sologm/models/tests/ -v
uv run pytest -x  # Stop on first failure to catch issues early
```
**Success Criteria:** All tests pass across all models

---

## Phase 4.6: Performance and Documentation Review

**Files to modify:**
- `sologm/models/README.md`
- `sologm/models/utils.py`

### Sub-step 4.6.1: Performance Validation
**File:** Multiple files  
**Change:** Validate that navigation property consolidation hasn't impacted performance  
**Rationale:** Ensure the utility approach doesn't introduce performance regressions  
**Context:** Navigation properties are used frequently throughout the application. Validate that the utility function approach maintains the same performance characteristics as the original implementations.

**Performance checks:**
- No additional database queries introduced
- Memory usage patterns remain consistent
- Navigation property access times are similar
- Complex aggregation properties maintain efficiency

### Sub-step 4.6.2: Update Documentation
**File:** `sologm/models/README.md`  
**Change:** Update model documentation to reflect navigation property consolidation  
**Rationale:** Keep documentation current with the implementation  
**Context:** Update the model documentation to mention that navigation properties now use shared utility functions. Add examples of the utility functions and explain the benefits of consolidation.

**Documentation updates:**
- Add section on navigation property utilities
- Update model property documentation
- Add examples of common navigation patterns
- Document the utility function approach and benefits

### Sub-step 4.6.3: Code Quality Review
**File:** `sologm/models/utils.py`  
**Change:** Review utility functions for code quality and documentation  
**Rationale:** Ensure utility functions meet project standards  
**Context:** Review the utility functions for proper documentation, type hints, error handling, and adherence to project conventions.

### Testing for Phase 4.6
**Test Cases:**
- Complete test suite passes
- Performance hasn't regressed
- Documentation accurately reflects current implementation
- Code quality standards are met
**How to Test:** 
```bash
uv run pytest -v --tb=short  # Full test suite
uv run pytest --cov=sologm.models  # Ensure test coverage maintained
# Manual testing of key functionality that uses navigation properties
sologm game status  # Should use navigation properties
sologm act list  # Should work with act navigation
```
**Success Criteria:** All tests pass, documentation is current, performance is maintained

---

## Phase 4 Completion Criteria

### Functional Requirements
- [ ] All ~20 target navigation properties consolidated using utility functions
- [ ] All existing tests pass without modification
- [ ] Navigation property behavior unchanged
- [ ] No performance regression in property access
- [ ] Utility functions handle all identified navigation patterns

### Code Quality Requirements  
- [ ] Significant reduction in code duplication for navigation patterns
- [ ] Utility functions are well-documented and tested
- [ ] Proper error handling for edge cases
- [ ] Type hints maintained for IDE support
- [ ] Documentation updated to reflect consolidation approach

### Safety Requirements
- [ ] Original navigation functionality preserved exactly
- [ ] No breaking changes to public API
- [ ] Navigation accuracy maintained across all scenarios
- [ ] No additional database queries introduced

---

## Risk Mitigation

**High Risk: Behavioral Changes in Navigation Properties**
- Mitigation: Extensive testing to ensure utility functions match original behavior exactly
- Fallback: Git history provides rollback capability, selective rollback of problematic properties

**Medium Risk: Performance Impact**  
- Mitigation: Careful performance testing, benchmark navigation property access times
- Fallback: Revert to original implementations for performance-critical properties

**Low Risk: Utility Function Complexity**
- Mitigation: Keep utility functions simple and focused, comprehensive testing
- Fallback: Use original implementations for complex cases if utilities prove insufficient

---

## Project Completion Summary

Phase 4 completes the hybrid property refactor project that began in Phase 1. The overall project has achieved:

### Phases 1-3: Mixin-Based Refactoring
- **Phase 1**: `ExistenceCheckMixin` - Eliminated ~15 `has_X` hybrid property duplications
- **Phase 2**: `CountingMixin` - Eliminated ~8 `X_count` hybrid property duplications  
- **Phase 3**: `StatusCheckMixin` - Eliminated ~7 `is_X`/`has_active_X` hybrid property duplications

### Phase 4: Utility-Based Consolidation
- **Phase 4**: Navigation utilities - Consolidated ~20 navigation property patterns

### Total Impact
- **~50 repetitive property implementations** consolidated across the codebase
- **Multiple coexisting mixins** demonstrate extensible pattern-based architecture
- **Shared utility functions** eliminate navigation property duplication
- **Maintainability significantly improved** through pattern consolidation
- **Zero functional changes** - all existing behavior preserved
- **Performance maintained** - no additional database queries or performance regressions

The refactoring demonstrates a successful approach to reducing technical debt while maintaining complete backward compatibility and system reliability.
