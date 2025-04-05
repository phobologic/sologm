# SoloGM Coding Conventions

## Architecture

### CLI Layer
- Focus solely on user interaction (input/output)
- Delegate all business logic to manager classes
- Handle exceptions with user-friendly messages
- Never interact directly with database sessions

### Manager Layer
- Handle all business logic
- Manage database sessions using `BaseManager`
- Use `self._execute_db_operation()` for all DB operations
- Provide clear domain-specific error messages

## Database Access

### Manager Pattern
- Inherit from `BaseManager[T, M]` with appropriate type parameters
- Use constructor parameter `session` (optional) for testing
- Use `self._execute_db_operation(name, func, *args, **kwargs)` for all DB operations
- Define inner functions for database operations

### Database Operations
```python
# Define operation as inner function
def _operation_name(session: Session, param1: Type1) -> ReturnType:
    # Operation code
    return result

# Execute operation
result = self._execute_db_operation("operation description", _operation_name, param1)
```

### Transaction Management
- Let `_execute_db_operation` handle session lifecycle
- Don't use `session.commit()` or `session.rollback()` directly
- Use `session.flush()` to execute SQL without committing
- Group atomic operations in single inner functions

### Query Patterns
- Single item: `session.query(Model).filter(conditions).first()`
- Multiple items: `session.query(Model).filter(conditions).all()`
- Ordered lists: `session.query(Model).filter().order_by(Model.field).all()`
- Bulk updates: `session.query(Model).update({Model.field: value})`

## Models

### Model Design
- Inherit from `Base` and `TimestampMixin`
- Use UUIDs (as strings) for primary keys
- Include `slug` field for human-readable identifiers where appropriate
- Use SQLAlchemy 2.0 ORM Declarative Models

### Relationships
- Define "owning" relationships in model classes (model with foreign key)
- Define "non-owning" relationships in `relationships.py`
- Use proper type annotations with `Mapped[Type]` or `Mapped[List[Type]]`
- Define cascade behavior explicitly

```python
# In model class
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from sologm.models.other_model import OtherModel

class MyModel(Base, TimestampMixin):
    other_id: Mapped[str] = mapped_column(ForeignKey("other_models.id"))
    other_items: Mapped[List["OtherModel"]] = relationship(
        "OtherModel", back_populates="my_model", cascade="all, delete-orphan"
    )
```

## Error Handling

- Let original exceptions propagate rather than wrapping unnecessarily
- Catch exceptions only when adding context or handling meaningfully
- Use specific exception types in `except` clauses
- Add context: `raise ExceptionType("Context") from original_exception`
- In CLI commands, catch expected exceptions with user-friendly messages
- Document raisable exceptions in docstrings

## Testing

- Do not write tests for CLI commands
- Test managers with session mocks or test databases
- Inject and manage sessions in test fixtures

## Documentation

### Docstrings
- Use Google-style format consistently
- Document purpose, parameters, return values, exceptions, and examples
- For unchanged overridden methods, use `"""See base class."""`

```python
def method(self, param: str) -> ReturnType:
    """Method description.
    
    Args:
        param: Parameter description.
        
    Returns:
        Description of return value.
        
    Raises:
        ErrorType: Error conditions.
    """
```

### Logging
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Never use `print()` for debugging
- Log levels: DEBUG (development), INFO (confirmation), WARNING (unexpected), 
  ERROR (function failure), CRITICAL (application failure)
- Structure messages consistently:
  - Operations: "Starting operation_name for resource_type resource_id"
  - Errors: "Error in operation_name: details"
- Never log credentials

## Type Annotations

- Use annotations for all function definitions
- For containers, specify contained type (e.g., `List[str]`, not just `List`)
- Use `Optional[Type]` for values that may be `None`
- Use `Union[Type1, Type2]` for multiple possible types
- For SQLAlchemy models:

```python
class MyModel(Base, TimestampMixin):
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    relation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("other.id"))
```

- Import types for annotations using:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from other_module import ComplexType
```
