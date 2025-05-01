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
    
    # Hybrid Properties (work in both Python and SQL)
    @hybrid_property
    def has_acts(self) -> bool  # Checks if the game has any acts
    
    @hybrid_property
    def act_count(self) -> int  # Returns the number of acts
    
    @hybrid_property
    def has_active_act(self) -> bool  # Checks if the game has an active act
    
    @hybrid_property
    def has_active_scene(self) -> bool  # Checks if the game has an active scene
    
    @hybrid_property
    def has_completed_acts(self) -> bool  # Checks if the game has any completed acts
    
    # Regular Properties (Python-only)
    @property
    def active_act(self) -> Optional["Act"]  # Returns the active act for this game
    
    @property
    def active_scene(self) -> Optional["Scene"]  # Returns the active scene via active act
    
    @property
    def completed_acts(self) -> List["Act"]  # Returns all completed acts
    
    @property
    def active_acts(self) -> List["Act"]  # Returns all active acts
    
    @property
    def latest_act(self) -> Optional["Act"]  # Returns the most recently created act
    
    @property
    def latest_scene(self) -> Optional["Scene"]  # Returns the most recently created scene
```

### Act
```python
class Act(Base, TimestampMixin):
    id: Mapped[str]
    slug: Mapped[str]
    game_id: Mapped[str]
    title: Mapped[Optional[str]]
    summary: Mapped[Optional[str]]
    sequence: Mapped[int]
    is_active: Mapped[bool]
    # Status field removed
    # Relationships
    game: Mapped["Game"]
    scenes: Mapped[List["Scene"]]
    
    # Hybrid Properties (work in both Python and SQL)
    @hybrid_property
    def has_scenes(self) -> bool  # Checks if the act has any scenes
    
    @hybrid_property
    def scene_count(self) -> int  # Returns the number of scenes
    
    @hybrid_property
    def has_active_scene(self) -> bool  # Checks if the act has an active scene

    # Removed has_completed_scenes

    @hybrid_property
    def has_events(self) -> bool  # Checks if the act has any events across all scenes
    
    @hybrid_property
    def event_count(self) -> int  # Returns the total number of events across all scenes
    
    @hybrid_property
    def has_dice_rolls(self) -> bool  # Checks if the act has any dice rolls
    
    @hybrid_property
    def dice_roll_count(self) -> int  # Returns the total number of dice rolls
    
    @hybrid_property
    def has_interpretations(self) -> bool  # Checks if the act has any interpretations
    
    @hybrid_property
    def interpretation_count(self) -> int  # Returns the total number of interpretations
    
    # Regular Properties (Python-only)
    @property
    def active_scene(self) -> Optional["Scene"]  # Returns the active scene for this act

    # Removed completed_scenes
    # Removed active_scenes

    @property
    def latest_scene(self) -> Optional["Scene"]  # Returns the most recently created scene
    
    @property
    def first_scene(self) -> Optional["Scene"]  # Returns the first scene by sequence
    
    @property
    def latest_event(self) -> Optional["Event"]  # Returns the most recent event across all scenes
    
    @property
    def latest_dice_roll(self) -> Optional["DiceRoll"]  # Returns the most recent dice roll
    
    @property
    def latest_interpretation(self) -> Optional["Interpretation"]  # Returns the most recent interpretation
    
    @property
    def all_events(self) -> List["Event"]  # Returns all events across all scenes
    
    @property
    def all_dice_rolls(self) -> List["DiceRoll"]  # Returns all dice rolls across all scenes
    
    @property
    def all_interpretations(self) -> List["Interpretation"]  # Returns all interpretations
    
    @property
    def selected_interpretations(self) -> List["Interpretation"]  # Returns all selected interpretations
```

### Scene
```python
class Scene(Base, TimestampMixin):
    id: Mapped[str]
    slug: Mapped[str]
    act_id: Mapped[str]
    title: Mapped[str]
    description: Mapped[Optional[str]]
    sequence: Mapped[int]
    is_active: Mapped[bool]
    # Status field removed
    # Relationships
    act: Mapped["Act"]
    events: Mapped[List["Event"]]
    interpretation_sets: Mapped[List["InterpretationSet"]]
    dice_rolls: Mapped[List["DiceRoll"]]
    
    # Hybrid Properties (work in both Python and SQL)
    @hybrid_property
    def has_events(self) -> bool  # Checks if the scene has any events
    
    @hybrid_property
    def event_count(self) -> int  # Returns the number of events
    
    @hybrid_property
    def has_dice_rolls(self) -> bool  # Checks if the scene has any dice rolls
    
    @hybrid_property
    def dice_roll_count(self) -> int  # Returns the number of dice rolls
    
    @hybrid_property
    def has_interpretation_sets(self) -> bool  # Checks if the scene has any interpretation sets
    
    @hybrid_property
    def interpretation_set_count(self) -> int  # Returns the number of interpretation sets
    
    @hybrid_property
    def has_interpretations(self) -> bool  # Checks if the scene has any interpretations
    
    @hybrid_property
    def interpretation_count(self) -> int  # Returns the total number of interpretations
    
    @hybrid_property
    def has_selected_interpretations(self) -> bool  # Checks if the scene has any selected interpretations
    
    @hybrid_property
    def selected_interpretation_count(self) -> int  # Returns the number of selected interpretations
    
    # Regular Properties (Python-only)
    @property
    def game(self) -> "Game"  # Returns the game this scene belongs to
    
    @property
    def game_id(self) -> str  # Returns the game ID this scene belongs to
    
    @property
    def latest_event(self) -> Optional["Event"]  # Returns the most recent event
    
    @property
    def latest_dice_roll(self) -> Optional["DiceRoll"]  # Returns the most recent dice roll
    
    @property
    def latest_interpretation_set(self) -> Optional["InterpretationSet"]  # Returns the most recent interpretation set
    
    @property
    def latest_interpretation(self) -> Optional["Interpretation"]  # Returns the most recent interpretation
    
    @property
    def current_interpretation_set(self) -> Optional["InterpretationSet"]  # Returns the current interpretation set
    
    @property
    def selected_interpretations(self) -> List["Interpretation"]  # Returns all selected interpretations
    
    @property
    def all_interpretations(self) -> List["Interpretation"]  # Returns all interpretations

    # Removed is_completed
    # Removed is_active_status
```

### Event
```python
class Event(Base, TimestampMixin):
    id: Mapped[str]
    scene_id: Mapped[str]
    description: Mapped[str]
    source_id: Mapped[int]
    interpretation_id: Mapped[Optional[str]]
    
    # Relationships
    scene: Mapped["Scene"]
    source: Mapped["EventSource"]
    interpretation: Mapped["Interpretation"]
    
    # Hybrid Properties (work in both Python and SQL)
    @hybrid_property
    def is_from_oracle(self) -> bool  # Checks if this event was created from an oracle interpretation
    
    @hybrid_property
    def is_manual(self) -> bool  # Checks if this event was manually created
    
    @hybrid_property
    def is_oracle_generated(self) -> bool  # Checks if this event was generated by an oracle
    
    @hybrid_property
    def is_dice_generated(self) -> bool  # Checks if this event was generated by a dice roll
    
    # Regular Properties (Python-only)
    @property
    def game(self) -> "Game"  # Returns the game this event belongs to
    
    @property
    def game_id(self) -> str  # Returns the game ID this event belongs to
    
    @property
    def act(self) -> "Act"  # Returns the act this event belongs to
    
    @property
    def act_id(self) -> str  # Returns the act ID this event belongs to
    
    @property
    def source_name(self) -> str  # Returns the name of the event source
    
    @property
    def short_description(self) -> str  # Returns a shortened version of the description
```

### EventSource
```python
class EventSource(Base):
    id: Mapped[int]
    name: Mapped[str]
    
    # No helper properties
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
    
    # Hybrid Properties (work in both Python and SQL)
    @hybrid_property
    def has_selection(self) -> bool  # Checks if any interpretation is selected
    
    @hybrid_property
    def interpretation_count(self) -> int  # Returns the number of interpretations
    
    # Regular Properties (Python-only)
    @property
    def act(self) -> "Act"  # Returns the act this interpretation set belongs to
    
    @property
    def act_id(self) -> str  # Returns the act ID this interpretation set belongs to
    
    @property
    def game(self) -> "Game"  # Returns the game this interpretation set belongs to
    
    @property
    def game_id(self) -> str  # Returns the game ID this interpretation set belongs to
    
    @property
    def selected_interpretation(self) -> Optional["Interpretation"]  # Returns the selected interpretation
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
    
    # Hybrid Properties (work in both Python and SQL)
    @hybrid_property
    def event_count(self) -> int  # Returns the number of associated events
    
    @hybrid_property
    def has_events(self) -> bool  # Checks if there are any associated events
    
    # Regular Properties (Python-only)
    @property
    def scene(self) -> "Scene"  # Returns the scene this interpretation belongs to
    
    @property
    def scene_id(self) -> str  # Returns the scene ID this interpretation belongs to
    
    @property
    def act(self) -> "Act"  # Returns the act this interpretation belongs to
    
    @property
    def act_id(self) -> str  # Returns the act ID this interpretation belongs to
    
    @property
    def game(self) -> "Game"  # Returns the game this interpretation belongs to
    
    @property
    def game_id(self) -> str  # Returns the game ID this interpretation belongs to
    
    @property
    def short_description(self) -> str  # Returns a shortened version of the description
    
    @property
    def latest_event(self) -> Optional["Event"]  # Returns the most recent associated event
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
    
    # Hybrid Properties (work in both Python and SQL)
    @hybrid_property
    def has_reason(self) -> bool  # Checks if this dice roll has a reason
    
    # Regular Properties (Python-only)
    @property
    def act(self) -> Optional["Act"]  # Returns the act this dice roll belongs to
    
    @property
    def act_id(self) -> Optional[str]  # Returns the act ID this dice roll belongs to
    
    @property
    def game(self) -> Optional["Game"]  # Returns the game this dice roll belongs to
    
    @property
    def game_id(self) -> Optional[str]  # Returns the game ID this dice roll belongs to
    
    @property
    def formatted_results(self) -> str  # Returns a formatted string of the dice roll results
    
    @property
    def short_reason(self) -> Optional[str]  # Returns a shortened version of the reason
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

1. **Ownership Hierarchy**: Clear ownership through `cascade="all, delete-orphan"` parameter.

2. **Timestamps**: All models include `created_at` and `modified_at` through `TimestampMixin`.

3. **Slugs**: Most models include a `slug` field for URL-friendly identifiers.

4. **Active Flags**: `is_active` flags track currently active game, act, and scene.

# Removed mention of Status Enums
