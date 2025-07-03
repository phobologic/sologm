# Core/Manager Development Guidelines

## Primary Reference
Follow the manager conventions at [../../conventions/managers.md](../../conventions/managers.md)

## Manager Pattern Architecture
Managers encapsulate ALL business logic and database operations. CLI commands delegate everything to managers.

```python
class MyManager(BaseManager):
    def __init__(self, session: Session):
        super().__init__(session)
        self._related_manager = None
    
    @property  
    def related_manager(self) -> RelatedManager:
        """Lazy initialization of related managers."""
        if self._related_manager is None:
            self._related_manager = RelatedManager(self.session)
        return self._related_manager
    
    def do_operation(self, param: str) -> Result:
        """Public method that wraps database operations."""
        def _operation() -> Result:
            # All database operations go here
            model = self.session.query(Model).filter(...).first()
            # Business logic and validation
            return result
        
        return self._execute_db_operation("operation description", _operation, param)
```

## Key Manager Principles

### Session Management
- **Accept session in constructor**: `def __init__(self, session: Session)`
- **Pass session to related managers**: Keep everything in same transaction
- **Never create sessions inside managers**: Session lifecycle managed externally

### Lazy Initialization Pattern
```python
@property
def scene_manager(self) -> SceneManager:
    if self._scene_manager is None:
        self._scene_manager = SceneManager(self.session)
    return self._scene_manager
```

### Database Operation Wrapper
Always use `_execute_db_operation` for database operations:
```python
def create_scene(self, title: str, description: str) -> Scene:
    def _operation() -> Scene:
        # Validation
        if not title.strip():
            raise ValidationError("Scene title cannot be empty")
            
        # Business logic
        act = self._get_active_act()
        sequence = self._get_next_scene_sequence(act.id)
        
        # Database operation
        scene = Scene.create(
            act_id=act.id,
            title=title,
            description=description,
            sequence=sequence
        )
        self.session.add(scene)
        self.session.flush()
        return scene
    
    return self._execute_db_operation("create scene", _operation, title, description)
```

## Manager Hierarchy and Relationships

### Factory Pattern
Managers are accessed through the factory:
```python
with get_db_context() as context:
    # All managers available via context.managers
    game = context.managers.game.get_active_game()
    scene = context.managers.scene.create_scene(title, description)
```

### Cross-Manager Operations
```python
class ActManager(BaseManager):
    @property
    def scene_manager(self) -> SceneManager:
        if self._scene_manager is None:
            self._scene_manager = SceneManager(self.session)
        return self._scene_manager
    
    def complete_act_with_summary(self, summary: str) -> Act:
        def _operation() -> Act:
            act = self._get_active_act()
            
            # Use related manager for scene operations
            scenes = self.scene_manager.get_scenes_for_act(act.id)
            
            # Business logic
            act.summary = summary
            act.is_active = False
            
            return act
        
        return self._execute_db_operation("complete act", _operation, summary)
```

## Error Handling and Validation

### Business Logic Validation
Managers handle all validation and business rules:
```python
def activate_game(self, game_id: str) -> Game:
    def _operation() -> Game:
        # Validation
        game = self.session.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise GameNotFoundError(f"Game with ID {game_id} not found")
        
        # Business logic - deactivate other games
        self.session.query(Game).update({Game.is_active: False})
        game.is_active = True
        
        return game
    
    return self._execute_db_operation("activate game", _operation, game_id)
```

### Exception Context
Use `_execute_db_operation` to add context to exceptions:
```python
# The wrapper automatically adds context:
# "Error in create scene with parameters: ('My Scene', 'Description'): Original error message"
```

## Query Patterns

### Using Model Hybrid Properties
Leverage hybrid properties for both Python and SQL contexts:
```python
def get_acts_with_scenes(self) -> List[Act]:
    def _operation() -> List[Act]:
        return self.session.query(Act).filter(
            Act.has_scenes == True
        ).order_by(Act.sequence).all()
    
    return self._execute_db_operation("get acts with scenes", _operation)
```

### Complex Queries with Relationships
```python
def get_most_active_scenes(self, act_id: str, limit: int = 5) -> List[Scene]:
    def _operation() -> List[Scene]:
        return self.session.query(Scene).filter(
            Scene.act_id == act_id
        ).order_by(Scene.event_count.desc()).limit(limit).all()
    
    return self._execute_db_operation("get most active scenes", _operation, act_id, limit)
```

## Integration with External Services

### Service Integration Pattern
```python
class OracleManager(BaseManager):
    def __init__(self, session: Session):
        super().__init__(session)
        self._anthropic_client = None
    
    @property
    def anthropic_client(self) -> AnthropicClient:
        if self._anthropic_client is None:
            self._anthropic_client = AnthropicClient()
        return self._anthropic_client
    
    def generate_interpretation(self, context: str) -> Interpretation:
        def _operation() -> Interpretation:
            # External service call
            response = self.anthropic_client.send_message(context)
            
            # Create database record
            scene = self.scene_manager.get_active_scene()
            interpretation_set = self._get_or_create_interpretation_set(scene.id)
            
            interpretation = Interpretation.create(
                interpretation_set_id=interpretation_set.id,
                content=response,
                is_selected=False
            )
            self.session.add(interpretation)
            return interpretation
        
        return self._execute_db_operation("generate interpretation", _operation, context)
```

## Testing Manager Classes

### Session Injection Testing
```python
def test_create_scene(session_context, create_test_act):
    with session_context as session:
        # Create test data
        act = create_test_act(session=session, is_active=True)
        
        # Test manager operation
        manager = SceneManager(session)
        scene = manager.create_scene("Test Scene", "Test Description")
        
        # Verify results
        assert scene.title == "Test Scene"
        assert scene.act_id == act.id
        assert scene.sequence == 1
```

## Related Conventions
- [Database Access](../../conventions/database_access.md) - Session management and query patterns
- [Architecture](../../conventions/architecture.md) - Manager responsibilities and CLI delegation
- [Error Handling](../../conventions/error_handling.md) - Exception handling and context
- [Models](../../conventions/models.md) - How managers interact with model layer
