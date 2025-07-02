# Technical Design Document: Hybrid Property Refactor

**Version:** 1.0  
**Date:** January 2025  

## 1. Executive Summary

This document outlines the technical design for refactoring SoloGM's 60+ hybrid properties to reduce code duplication and improve maintainability. We will extract common patterns into reusable mixins using a phased approach, starting with the simplest and most repetitive patterns.

### Goals
- **Reduce Code Duplication**: Eliminate repetitive hybrid property implementations
- **Improve Maintainability**: Centralize common SQL expression logic  
- **Enhance Readability**: Simplify model classes
- **Maintain Functionality**: Preserve all existing behavior and performance
- **Ensure Safety**: Use phased approach to minimize risk

### Non-Goals
- Changing the external API of any models
- Modifying database schema or migrations
- Altering test behavior (tests should continue to pass)

## 2. Current State Analysis

### Problem Statement
Our SQLAlchemy models contain repetitive hybrid property patterns:

```python
# Repeated across 6+ models
@hybrid_property
def has_events(self) -> bool:
    return len(self.events) > 0

@has_events.expression
def has_events(cls):
    return select(1).where(Event.scene_id == cls.id).exists().label("has_events")
```

### Affected Models & Pattern Distribution
- **Game**: 5 hybrid properties (`has_acts`, `act_count`, `has_active_act`, etc.)
- **Act**: 9 hybrid properties (`has_scenes`, `scene_count`, `has_active_scene`, etc.)  
- **Scene**: 10 hybrid properties (`has_events`, `event_count`, `has_dice_rolls`, etc.)
- **Event**: 6 hybrid properties (`is_from_oracle`, `is_manual`, etc.)
- **Interpretation**: 2 hybrid properties (`event_count`, `has_events`)
- **InterpretationSet**: 2 hybrid properties (`has_selection`, `interpretation_count`)
- **DiceRoll**: 1 hybrid property (`has_reason`)

### Identified Patterns
1. **Existence Checks** (`has_X`) - Check if related entities exist
2. **Count Operations** (`X_count`) - Count related entities
3. **Status Checks** (`is_X`, `has_active_X`) - Check specific states  
4. **Navigation Properties** (`active_X`, `latest_X`) - Find specific related entities

## 3. Design Overview

### Architecture Decision: Pattern-Specific Mixins

We will create **pattern-specific mixins** rather than relationship-specific or monolithic mixins:

```python
# Target architecture
class Scene(ExistenceCheckMixin, CountingMixin, NavigationMixin, Base):
    _existence_configs = { ... }
    _counting_configs = { ... }
    _navigation_configs = { ... }
```

**Why this approach?**
- **Limited mixin count**: ~4 mixins total vs. dozens of relationship-specific mixins
- **Explicit configuration**: Clear control over which properties are generated
- **Pattern isolation**: Each mixin handles one type of operation
- **Incremental adoption**: Can add mixins one pattern at a time

### Phased Implementation Strategy

**Phase 1: Existence Checks** (`has_X` patterns) - ~15 properties across models  
**Phase 2: Count Operations** (`X_count` patterns) - ~8 properties across models  
**Phase 3: Status Checks** (`is_X`, `has_active_X` patterns) - ~12 properties across models  
**Phase 4: Navigation Properties** (`active_X`, `latest_X` patterns) - ~25 properties across models  

## 4. Phase 1 Detailed Design: Existence Check Mixin

### 4.1 Core Components

#### Configuration Classes
```python
@dataclass
class ExistenceConfig:
    """Configuration for existence check properties."""
    model: Type[Base]  # Related model class (e.g., Event)
    foreign_key: str   # Foreign key column name (e.g., 'scene_id')
    relationship_name: Optional[str] = None  # Defaults to config key
```

#### Mixin Class Structure
```python
class ExistenceCheckMixin:
    """Mixin providing has_X hybrid properties for relationship existence checks."""
    
    # Configuration attribute (defined by implementing classes)
    _existence_configs: Dict[str, ExistenceConfig]
    
    def __init_subclass__(cls, **kwargs):
        """Generate hybrid properties when class is created."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, '_existence_configs'):
            cls._generate_existence_properties()
    
    @classmethod  
    def _generate_existence_properties(cls):
        """Generate has_X properties from configuration."""
        # Implementation details in Phase 1
        
    @classmethod
    def _create_existence_property(cls, name: str, config: ExistenceConfig):
        """Create individual has_X hybrid property."""
        # Implementation details in Phase 1
```

### 4.2 Usage Pattern

#### Before Refactor
```python
class Scene(Base, TimestampMixin):
    # ... other properties ...
    
    @hybrid_property
    def has_events(self) -> bool:
        return len(self.events) > 0
    
    @has_events.expression  
    def has_events(cls):
        return select(1).where(Event.scene_id == cls.id).exists().label("has_events")
        
    @hybrid_property
    def has_dice_rolls(self) -> bool:
        return len(self.dice_rolls) > 0
        
    @has_dice_rolls.expression
    def has_dice_rolls(cls):
        return select(1).where(DiceRoll.scene_id == cls.id).exists().label("has_dice_rolls")
```

#### After Refactor
```python
class Scene(ExistenceCheckMixin, Base, TimestampMixin):
    # ... other properties ...
    
    _existence_configs = {
        'events': ExistenceConfig(
            model=Event,
            foreign_key='scene_id'
        ),
        'dice_rolls': ExistenceConfig(
            model=DiceRoll, 
            foreign_key='scene_id'
        ),
        'interpretation_sets': ExistenceConfig(
            model=InterpretationSet,
            foreign_key='scene_id'
        ),
    }
    # has_events, has_dice_rolls, has_interpretation_sets properties
    # are automatically generated by the mixin
```

### 4.3 Generated Property Behavior

Each configuration entry generates a hybrid property with this pattern:

```python
# For config key 'events':
@hybrid_property
def has_events(self) -> bool:
    """Check if this scene has any events."""
    return bool(self.events)  # Uses loaded relationship

@has_events.expression  
def has_events(cls):
    """SQL expression for has_events."""
    return select(1).where(Event.scene_id == cls.id).exists().label("has_events")
```

### 4.4 Type Safety Considerations

To maintain IDE support and type hints:

```python
# In the model file, add type hints for generated properties
if TYPE_CHECKING:
    # Generated by ExistenceCheckMixin
    has_events: bool
    has_dice_rolls: bool
    has_interpretation_sets: bool
```

## 5. Implementation Guidelines

### 5.1 Safety First Approach

**Rule #1: No Functionality Changes**
- Generated properties must behave identically to existing properties
- All existing tests must continue to pass without modification
- SQL queries generated must be equivalent

**Rule #2: Incremental Migration**  
- Migrate one model at a time within each phase
- Keep original properties alongside generated ones initially
- Remove original properties only after validation

**Rule #3: Comprehensive Testing**
- Test the mixin in isolation with mock models
- Test each migrated model individually  
- Run full test suite after each model migration

### 5.2 Development Workflow

For each model migration:

1. **Add mixin and configuration** to the model class
2. **Verify generated properties** work correctly (may require debugging)
3. **Run model-specific tests** to ensure behavior matches
4. **Deprecate original properties** (comment out but don't delete)
5. **Run full test suite** to catch integration issues
6. **Remove original properties** after confidence is high

### 5.3 Error Handling

Common issues and solutions:

**Import Circular Dependencies**
- Use string model names in configurations when needed
- Import models within methods rather than module level

**Missing Relationships**
- Validate that configured relationship names exist on the model
- Provide clear error messages for misconfigurations

**SQL Expression Complexity**
- Start with simple EXISTS queries  
- Handle edge cases like self-referential relationships carefully

## 6. Testing Strategy

### 6.1 Mixin Testing
- **Unit tests** for configuration parsing
- **Property generation tests** with mock models
- **SQL expression validation** against known queries

### 6.2 Integration Testing  
- **Model behavior tests** comparing original vs. generated properties
- **Performance tests** ensuring no query regression
- **Edge case tests** for complex relationships

### 6.3 Migration Validation
- **Before/after comparison tests** for each migrated model
- **Full application tests** with migrated models
- **Database query logging** to verify SQL equivalence

## 7. Future Phases Preview

### Phase 2: Counting Mixin
```python
class CountingMixin:
    _counting_configs: Dict[str, CountConfig]
    # Generates: event_count, dice_roll_count, etc.
```

### Phase 3: Status Check Mixin  
```python
class StatusCheckMixin:
    _status_configs: Dict[str, StatusConfig] 
    # Generates: is_active, has_active_scene, etc.
```

### Phase 4: Navigation Mixin
```python
class NavigationMixin:
    _navigation_configs: Dict[str, NavigationConfig]
    # Generates: active_scene, latest_event, etc.
```

## 8. Risks and Mitigations

### High Risk Issues

**Risk**: Breaking existing functionality  
**Mitigation**: Comprehensive testing, incremental migration, keep original properties during transition

**Risk**: Performance regression in SQL queries  
**Mitigation**: Query logging, performance benchmarks, SQL plan analysis

**Risk**: Complex debugging due to dynamic property generation  
**Mitigation**: Clear error messages, good logging, comprehensive documentation

### Medium Risk Issues

**Risk**: Type hint and IDE support degradation  
**Mitigation**: Explicit TYPE_CHECKING blocks, consider stub file generation

**Risk**: Increased complexity for new team members  
**Mitigation**: Excellent documentation, clear examples, training materials

## 9. Success Metrics

- **Code Reduction**: Eliminate 15+ duplicated `has_X` properties in Phase 1
- **Test Coverage**: Maintain 100% test coverage throughout refactor  
- **Performance**: No measurable query performance regression
- **Maintainability**: New relationship existence checks require only configuration, not code

## 10. Conclusion

This refactor will significantly improve code maintainability while preserving all existing functionality. The phased approach minimizes risk, and the pattern-specific mixin design provides a good balance of reusability and explicitness.

The success of Phase 1 will validate our approach and provide confidence for the remaining phases, ultimately eliminating most of the 60+ duplicate hybrid properties across the codebase.
