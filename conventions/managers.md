# Manager Pattern

## Purpose
Managers encapsulate business logic and database operations for specific domain models.

## Base Manager

### Initialization
- Inherit from `BaseManager[T, M]`
- Accept optional `session` parameter for testing and CLI command injection
- Use `super().__init__(session=session)` in constructor

### Session Handling
- Use `self._session` for database operations
- Use `self._get_session()` to retrieve a session
- Lazy-initialize related managers with the same session

## Example Manager Implementation

```python
class SceneManager(BaseManager[Scene, Scene]):
    def __init__(
        self,
        session: Optional[Session] = None,
        act_manager: Optional[ActManager] = None,
    ):
        """Initialize the scene manager.

        Args:
            session: Optional session for testing or CLI command injection
            act_manager: Optional ActManager instance
        """
        super().__init__(session=session)
        self._act_manager: Optional["ActManager"] = act_manager

    @property
    def act_manager(self) -> ActManager:
        """Lazy-initialize act manager if not provided."""
        if self._act_manager is None:
            self._act_manager = ActManager(session=self._session)
        return self._act_manager

    def create_scene(self, act_id: str, title: str, description: str) -> Scene:
        """Create a new scene.

        Args:
            act_id: ID of the act
            title: Scene title
            description: Scene description

        Returns:
            Created Scene instance
        """
        def _operation(session: Session, act_id: str, title: str, description: str) -> Scene:
            scene = Scene.create(
                act_id=act_id,
                title=title,
                description=description,
            )
            session.add(scene)
            return scene

        return self._execute_db_operation(
            "create scene", 
            _operation, 
            act_id, 
            title, 
            description
        )
```

## Best Practices

1. Use inner functions for database operations
2. Use `_execute_db_operation` for all database interactions
3. Keep methods focused on single responsibilities
4. Lazy-initialize related managers
5. Pass sessions through lazy-initialized managers
