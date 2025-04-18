# Database Access Pattern Changes

## Core Changes

1. **Session Management**
   - Use a single session per CLI command
   - Keep session open throughout command execution
   - Close session at the end of each command

2. **Manager Initialization**
   - Accept optional `session` parameter in constructor
   - Pass session to lazy-initialized managers
   - Use provided session if available, fallback to singleton

3. **CLI Command Pattern**
   - Use `get_db_context()` context manager in all commands
   - Initialize managers with the session
   - Keep session open for display functions

## Implementation Details

### BaseManager Updates

```python
class BaseManager(Generic[T, M]):
    def __init__(self, session: Optional[Session] = None):
        """Initialize the base manager."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._session = session

    def _get_session(self) -> Tuple[Session, bool]:
        """Get a database session."""
        if self._session is not None:
            # Use provided session (for testing or CLI command)
            return self._session, False
        else:
            # Get a new session from the singleton
            from sologm.database.session import get_session
            return get_session(), False  # Don't close here
```

### Manager Lazy Initialization

```python
def _lazy_init_manager(self, attr_name: str, manager_class_path: str, **kwargs) -> Any:
    """Lazily initialize a manager with the same session."""
    if not hasattr(self, attr_name) or getattr(self, attr_name) is None:
        module_path, class_name = manager_class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        manager_class = getattr(module, class_name)
        
        # Pass our session to the new manager
        kwargs['session'] = self._session
        
        setattr(self, attr_name, manager_class(**kwargs))

    return getattr(self, attr_name)
```

### CLI Command Pattern

```python
@app.command("command_name")
def command_name():
    """Command description."""
    from sologm.database.session import get_db_context
    
    # Use a single session for the entire command
    with get_db_context() as session:
        # Initialize manager with the session
        manager = Manager(session=session)
        
        # Use manager methods
        result = manager.do_something()
        
        # Display results - session still open for lazy loading
        display_result(console, result)
```

### Test Fixtures

```python
@pytest.fixture
def game_manager(db_session):
    """Create a GameManager with test session."""
    return GameManager(session=db_session)

@pytest.fixture
def act_manager(db_session, game_manager):
    """Create an ActManager with test session."""
    return ActManager(session=db_session, game_manager=game_manager)
```

## Benefits

1. **Consistent Session Management**: Clear where session starts and ends
2. **Simplified Lazy Loading**: Relationships can be accessed in display functions
3. **Improved Testing**: Easy to inject test sessions
4. **Reduced Session Leaks**: Sessions are properly closed after each command
5. **Future Flexibility**: Pattern works for both CLI and potential web interfaces
