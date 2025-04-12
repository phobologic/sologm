# SoloGM Core Module

## Manager Architecture

### Manager Chain Pattern

Managers are organized in a hierarchical chain that mirrors the data model relationships:

```
GameManager
└── ActManager
    └── SceneManager
        ├── EventManager
        ├── OracleManager
        └── DiceManager
```

Each manager has access to its parent managers through properties, allowing operations to easily access the full context.

### Manager Implementation Guidelines

1. **Inherit from BaseManager**: All managers should inherit from `BaseManager[T, M]` with appropriate type parameters.

2. **Accept Parent Manager**: Managers should accept their parent manager as an optional constructor parameter.

3. **Lazy Initialization**: Use lazy initialization for parent managers to avoid circular dependencies.

4. **Database Operations**: Use `self._execute_db_operation()` for all database operations.

5. **Session Consistency**: Pass the session down the manager chain to ensure consistent transaction boundaries.

### Example Manager Structure

```python
class SceneManager(BaseManager[Scene, Scene]):
    def __init__(
        self,
        act_manager: Optional[ActManager] = None,
        session: Optional[Session] = None,
    ):
        super().__init__(session)
        self._act_manager = act_manager
        
    @property
    def act_manager(self) -> ActManager:
        """Lazy-initialize act manager if not provided."""
        if self._act_manager is None:
            from sologm.core.act import ActManager
            self._act_manager = ActManager(session=self._session)
        return self._act_manager
        
    @property
    def game_manager(self) -> GameManager:
        """Access game manager through act manager."""
        return self.act_manager.game_manager
```

## Database Operations

- Define operations as inner functions that accept a session parameter
- Let `_execute_db_operation` handle session lifecycle
- Don't use `session.commit()` or `session.rollback()` directly
- Use `session.flush()` to execute SQL without committing
- Group atomic operations in single inner functions

## Error Handling

- Raise domain-specific errors (GameError, ActError, etc.)
- Include context in error messages (IDs, operation names)
- Let BaseManager handle session cleanup on errors

## Testing Managers

- Pass explicit session objects for testing
- Mock parent managers when needed
- Test each manager in isolation
- Use fixtures to create test data hierarchies
