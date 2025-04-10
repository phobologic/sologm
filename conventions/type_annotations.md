# Type Annotations

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
