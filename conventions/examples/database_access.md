# Database Access Examples

## Database Operations Example

```python
# Define operation as inner function
def _operation_name(session: Session, param1: Type1) -> ReturnType:
    # Operation code
    return result

# Execute operation
result = self._execute_db_operation("operation description", _operation_name, param1)
```

## Query Pattern Examples

### Basic Queries

```python
# Single item
item = session.query(Model).filter(Model.id == item_id).first()

# Multiple items
items = session.query(Model).filter(Model.status == "active").all()

# Ordered lists
items = session.query(Model).filter(Model.is_active).order_by(Model.created_at.desc()).all()

# Bulk updates
session.query(Model).filter(Model.status == "pending").update({Model.status: "active"})
```

### Using Hybrid Properties in Queries

```python
# Using hybrid properties for filtering
active_scenes_with_events = session.query(Scene).filter(
    Scene.is_active_status,
    Scene.has_events
).all()

# Prefer this (using hybrid property)
scenes_with_oracle_events = session.query(Scene).filter(Scene.has_oracle_events).all()

# Over this (manual join/subquery)
oracle_source = session.query(EventSource).filter_by(name="oracle").first()
scenes_with_oracle_events = session.query(Scene).filter(Scene.id.in_(
    session.query(Event.scene_id).filter(Event.source_id == oracle_source.id)
)).all()

# Using hybrid properties for ordering
most_active_scenes = session.query(Scene).order_by(Scene.event_count.desc()).limit(5).all()
```

### Manager Implementation with Hybrid Properties

```python
class SceneManager(BaseManager[Scene, Scene]):
    def get_scenes_with_oracle_events(self, act_id: str) -> List[Scene]:
        def _operation(session: Session, act_id: str) -> List[Scene]:
            return session.query(Scene).filter(
                Scene.act_id == act_id,
                Scene.has_oracle_events
            ).all()
        
        return self._execute_db_operation("get scenes with oracle events", _operation, act_id)
    
    def get_most_active_scenes(self, act_id: str, limit: int = 5) -> List[Scene]:
        def _operation(session: Session, act_id: str, limit: int) -> List[Scene]:
            return session.query(Scene).filter(
                Scene.act_id == act_id
            ).order_by(Scene.event_count.desc()).limit(limit).all()
        
        return self._execute_db_operation("get most active scenes", _operation, act_id, limit)
```
