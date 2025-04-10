# Models

## Model Design
- Inherit from `Base` and `TimestampMixin`
- Use UUIDs (as strings) for primary keys
- Include `slug` field for human-readable identifiers where appropriate
- Use SQLAlchemy 2.0 ORM Declarative Models

## Relationships
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
