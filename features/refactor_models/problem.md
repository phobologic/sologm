This document details the problem and goals for refactoring the SoloGM SQLAlchemy models to reduce hybrid property complexity through mixin extraction and pattern consolidation. The current codebase contains 60+ hybrid properties across 6 model files with significant code duplication following repetitive patterns.

## 1. Problem Statement

### Current Issues:
- **Code Duplication**: Each model implements similar `has_X`, `X_count`, and relationship navigation patterns
- **Maintenance Burden**: 60+ hybrid properties with duplicate SQL expression logic
- **Readability**: Models are cluttered with repetitive property definitions
- **Inconsistency**: Similar patterns implemented differently across models

### Affected Models:
- `Game`: 5 hybrid properties (has_acts, act_count, has_active_act, has_active_scene, has_completed_acts)
- `Act`: 9 hybrid properties (has_scenes, scene_count, has_active_scene, has_events, event_count, has_dice_rolls, dice_roll_count, has_interpretations, interpretation_count)
- `Scene`: 10 hybrid properties (has_events, event_count, has_dice_rolls, dice_roll_count, has_interpretation_sets, interpretation_set_count, has_interpretations, interpretation_count, has_selected_interpretations, selected_interpretation_count)
- `Event`: 6 hybrid properties (is_from_oracle, is_manual, is_oracle_generated, is_dice_generated)
- `Interpretation`: 2 hybrid properties (event_count, has_events)
- `InterpretationSet`: 2 hybrid properties (has_selection, interpretation_count)
- `DiceRoll`: 1 hybrid property (has_reason)

## 2. Goals

### Primary Goals:
1. **Reduce Code Duplication**: Extract common hybrid property patterns into reusable mixins
2. **Improve Maintainability**: Centralize SQL expression logic for similar operations
3. **Enhance Readability**: Simplify model classes by removing repetitive property definitions
4. **Maintain Functionality**: Preserve all existing hybrid property behavior and SQL generation
5. **Type Safety**: Maintain full type hints and IDE support

### Secondary Goals:
1. **Performance**: Ensure no performance regression in SQL query generation
2. **Testing**: Maintain 100% test coverage through the refactoring
3. **Documentation**: Update model documentation to reflect new structure
