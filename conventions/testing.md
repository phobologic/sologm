# Testing

- Do not write tests for CLI commands
- Test managers with session injection
- Use consistent session handling in test fixtures

## Test Fixtures

### Session Fixtures

```python
@pytest.fixture
def db_engine():
    """Create a new in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Create a new database session for a test."""
    session = Session(bind=db_engine)
    yield session
    session.close()
```

### Manager Fixtures

```python
@pytest.fixture
def game_manager(db_session):
    """Create a GameManager with test session."""
    return GameManager(session=db_session)

@pytest.fixture
def act_manager(db_session, game_manager):
    """Create an ActManager with test session."""
    return ActManager(session=db_session, game_manager=game_manager)

@pytest.fixture
def scene_manager(db_session, act_manager):
    """Create a SceneManager with test session."""
    return SceneManager(session=db_session, act_manager=act_manager)
```

## Test Patterns

### Testing Manager Methods

```python
def test_create_scene(scene_manager, test_game, ensure_active_act):
    """Test creating a new scene."""
    active_act = ensure_active_act
    scene = scene_manager.create_scene(
        title="Test Scene",
        description="Test description",
        act_id=active_act.id,
    )
    
    # Assertions
    assert scene.id is not None
    assert scene.title == "Test Scene"
    assert scene.act_id == active_act.id
```

### Testing Database Operations

```python
def test_scene_relationships(scene_manager, db_session, test_scene):
    """Test scene relationships."""
    # Create related objects
    event = Event.create(
        scene_id=test_scene.id,
        description="Test event",
        source_id=1,
    )
    db_session.add(event)
    db_session.commit()
    
    # Refresh the scene to load relationships
    db_session.refresh(test_scene)
    
    # Test relationships
    assert len(test_scene.events) == 1
    assert test_scene.events[0].description == "Test event"
```

### Testing Hybrid Properties

```python
def test_scene_hybrid_properties(scene_manager, db_session, test_scene):
    """Test scene hybrid properties."""
    # Create related objects
    event = Event.create(
        scene_id=test_scene.id,
        description="Test event",
        source_id=1,
    )
    db_session.add(event)
    db_session.commit()
    
    # Test Python-side hybrid property
    assert test_scene.has_events is True
    
    # Test SQL-side hybrid property
    scenes_with_events = db_session.query(Scene).filter(
        Scene.has_events
    ).all()
    assert len(scenes_with_events) == 1
    assert scenes_with_events[0].id == test_scene.id
```
