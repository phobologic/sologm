# Model Examples

## Relationship Examples

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

## Hybrid Property Examples

```python
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import exists, and_, select, func

class Scene(Base, TimestampMixin):
    # ... other fields ...
    
    @hybrid_property
    def has_events(self):
        """Check if scene has events (Python context)
        Can be used in queries: query(Scene).filter(Scene.has_events)"""
        return len(self.events) > 0

    @has_events.expression
    def has_events(cls):
        """SQL expression for has_events"""
        from sologm.models.event import Event
        return exists().where(Event.scene_id == cls.id)
    
    @hybrid_property
    def has_oracle_events(self):
        """Check if scene has oracle-generated events (Python context)
        Can be used in queries: query(Scene).filter(Scene.has_oracle_events)"""
        return any(event.is_oracle_generated for event in self.events)

    @has_oracle_events.expression
    def has_oracle_events(cls):
        """SQL expression for has_oracle_events"""
        from sologm.models.event import Event
        from sologm.models.event_source import EventSource
        return exists().where(
            and_(
                Event.scene_id == cls.id,
                Event.source_id == select(EventSource.id).where(EventSource.name == "oracle").scalar_subquery()
            )
        )
    
    @hybrid_property
    def event_count(self):
        """Count of events in this scene (Python context)
        Can be used in queries: query(Scene).order_by(Scene.event_count)"""
        return len(self.events)
    
    @event_count.expression
    def event_count(cls):
        """SQL expression for event_count"""
        from sologm.models.event import Event
        return select(func.count(Event.id)).where(Event.scene_id == cls.id).scalar_subquery()
```
