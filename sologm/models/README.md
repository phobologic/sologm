# SoloGM Database Model Documentation

## Overview of Models and Relationships

```
Game
 └── Acts
     └── Scenes
         ├── Events
         ├── InterpretationSets
         │    └── Interpretations
         │         └── Events (optional link)
         └── DiceRolls
```

## Model Signatures and Fields

### Game
```python
class Game(Base, TimestampMixin):
    id: Mapped[str]
    name: Mapped[str]
    slug: Mapped[str]
    description: Mapped[str]
    is_active: Mapped[bool]
    
    # Relationships
    acts: Mapped[List["Act"]]
```

### Act
```python
class Act(Base, TimestampMixin):
    id: Mapped[str]
    slug: Mapped[str]
    game_id: Mapped[str]
    title: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    status: Mapped[ActStatus]  # Enum: ACTIVE, COMPLETED
    sequence: Mapped[int]
    is_active: Mapped[bool]
    
    # Relationships
    game: Mapped["Game"]
    scenes: Mapped[List["Scene"]]
```

### Scene
```python
class Scene(Base, TimestampMixin):
    id: Mapped[str]
    slug: Mapped[str]
    act_id: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    status: Mapped[SceneStatus]  # Enum: ACTIVE, COMPLETED
    sequence: Mapped[int]
    is_active: Mapped[bool]
    
    # Relationships
    act: Mapped["Act"]
    events: Mapped[List["Event"]]
    interpretation_sets: Mapped[List["InterpretationSet"]]
    dice_rolls: Mapped[List["DiceRoll"]]
```

### Event
```python
class Event(Base, TimestampMixin):
    id: Mapped[str]
    scene_id: Mapped[str]
    game_id: Mapped[str]  # Redundant for query performance
    description: Mapped[str]
    source_id: Mapped[int]
    interpretation_id: Mapped[Optional[str]]
    
    # Relationships
    scene: Mapped["Scene"]
    source: Mapped["EventSource"]
    interpretation: Mapped["Interpretation"]
```

### EventSource
```python
class EventSource(Base):
    id: Mapped[int]
    name: Mapped[str]
```

### InterpretationSet
```python
class InterpretationSet(Base, TimestampMixin):
    id: Mapped[str]
    scene_id: Mapped[str]
    context: Mapped[str]
    oracle_results: Mapped[str]
    retry_attempt: Mapped[int]
    is_current: Mapped[bool]
    
    # Relationships
    scene: Mapped["Scene"]
    interpretations: Mapped[List["Interpretation"]]
```

### Interpretation
```python
class Interpretation(Base, TimestampMixin):
    id: Mapped[str]
    set_id: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    slug: Mapped[str]
    is_selected: Mapped[bool]
    
    # Relationships
    interpretation_set: Mapped["InterpretationSet"]
    events: Mapped[List["Event"]]
```

### DiceRoll
```python
class DiceRoll(Base, TimestampMixin):
    id: Mapped[str]
    notation: Mapped[str]
    individual_results: Mapped[List[int]]  # Stored as JSON
    modifier: Mapped[int]
    total: Mapped[int]
    reason: Mapped[Optional[str]]
    scene_id: Mapped[Optional[str]]
    
    # Relationships
    scene: Mapped["Scene"]
```

## Key Relationship Chains

1. **Game → Act → Scene**:
   - `Game.acts` → `Act.scenes`

2. **Scene → Events**:
   - `Scene.events` ← `Event.scene_id`

3. **Scene → InterpretationSet → Interpretation**:
   - `Scene.interpretation_sets` → `InterpretationSet.interpretations`

4. **Interpretation → Event** (optional):
   - `Interpretation.events` ← `Event.interpretation_id`

5. **Scene → DiceRoll**:
   - `Scene.dice_rolls` ← `DiceRoll.scene_id`

## Notable Design Patterns

1. **Redundant Foreign Keys**: `Event.game_id` provides direct access to the game for performance.

2. **Ownership Hierarchy**: Clear ownership through `cascade="all, delete-orphan"` parameter.

3. **Timestamps**: All models include `created_at` and `modified_at` through `TimestampMixin`.

4. **Slugs**: Most models include a `slug` field for URL-friendly identifiers.

5. **Active Flags**: `is_active` flags track currently active game, act, and scene.

6. **Status Enums**: Act and Scene use status enums (ACTIVE, COMPLETED).
