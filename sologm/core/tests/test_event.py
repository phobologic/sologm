"""Tests for event management functionality."""

import pytest
from datetime import datetime
from pathlib import Path
from typing import Generator

from sologm.storage.file_manager import FileManager
from sologm.core.event import Event, EventManager
from sologm.utils.errors import EventError

@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for testing."""
    return tmp_path

@pytest.fixture
def file_manager(temp_dir: Path) -> FileManager:
    """Create a FileManager instance for testing."""
    return FileManager(base_dir=temp_dir)

@pytest.fixture
def event_manager(file_manager: FileManager) -> EventManager:
    """Create an EventManager instance for testing."""
    return EventManager(file_manager=file_manager)

@pytest.fixture
def test_scene(file_manager: FileManager) -> Generator[dict, None, None]:
    """Create a test scene for testing."""
    game_id = "test-game"
    scene_id = "test-scene"
    
    # Create game
    game_data = {
        "id": game_id,
        "name": "Test Game",
        "description": "A test game",
        "created_at": datetime.now().isoformat(),
        "modified_at": datetime.now().isoformat(),
        "scenes": [scene_id]
    }
    file_manager.write_yaml(file_manager.get_game_path(game_id), game_data)
    
    # Create scene
    scene_data = {
        "id": scene_id,
        "game_id": game_id,
        "title": "Test Scene",
        "description": "A test scene",
        "status": "active",
        "sequence": 1,
        "created_at": datetime.now().isoformat(),
        "modified_at": datetime.now().isoformat()
    }
    file_manager.write_yaml(file_manager.get_scene_path(game_id, scene_id), scene_data)
    
    yield {"game_id": game_id, "scene_id": scene_id}

class TestEvent:
    """Tests for the Event class."""
    
    def test_event_creation(self) -> None:
        """Test creating an Event object."""
        event = Event(
            id="test-event",
            scene_id="test-scene",
            game_id="test-game",
            description="Test event",
            source="manual",
            created_at=datetime.now()
        )
        
        assert event.id == "test-event"
        assert event.scene_id == "test-scene"
        assert event.game_id == "test-game"
        assert event.description == "Test event"
        assert event.source == "manual"
        assert isinstance(event.created_at, datetime)

class TestEventManager:
    """Tests for the EventManager class."""
    
    def test_add_event(
        self,
        event_manager: EventManager,
        test_scene: dict
    ) -> None:
        """Test adding an event."""
        event = event_manager.add_event(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"],
            description="Test event",
            source="manual"
        )
        
        assert event.scene_id == test_scene["scene_id"]
        assert event.game_id == test_scene["game_id"]
        assert event.description == "Test event"
        assert event.source == "manual"
        
        # Verify event was saved
        events = event_manager.list_events(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"]
        )
        assert len(events) == 1
        assert events[0].id == event.id
    
    def test_add_event_nonexistent_scene(
        self,
        event_manager: EventManager,
        test_scene: dict
    ) -> None:
        """Test adding an event to a nonexistent scene."""
        with pytest.raises(EventError) as exc:
            event_manager.add_event(
                game_id=test_scene["game_id"],
                scene_id="nonexistent-scene",
                description="Test event"
            )
        assert "Scene nonexistent-scene not found" in str(exc.value)
    
    def test_list_events_empty(
        self,
        event_manager: EventManager,
        test_scene: dict
    ) -> None:
        """Test listing events when none exist."""
        events = event_manager.list_events(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"]
        )
        assert len(events) == 0
    
    def test_list_events(
        self,
        event_manager: EventManager,
        test_scene: dict
    ) -> None:
        """Test listing multiple events."""
        # Add some events
        event_manager.add_event(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"],
            description="First event"
        )
        event_manager.add_event(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"],
            description="Second event"
        )
        
        events = event_manager.list_events(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"]
        )
        assert len(events) == 2
        # Events should be in reverse chronological order
        assert events[0].description == "Second event"
        assert events[1].description == "First event"
    
    def test_list_events_with_limit(
        self,
        event_manager: EventManager,
        test_scene: dict
    ) -> None:
        """Test listing events with a limit."""
        # Add some events
        event_manager.add_event(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"],
            description="First event"
        )
        event_manager.add_event(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"],
            description="Second event"
        )
        event_manager.add_event(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"],
            description="Third event"
        )
        
        events = event_manager.list_events(
            game_id=test_scene["game_id"],
            scene_id=test_scene["scene_id"],
            limit=2
        )
        assert len(events) == 2
        assert events[0].description == "Third event"
        assert events[1].description == "Second event"
    
    def test_list_events_nonexistent_scene(
        self,
        event_manager: EventManager,
        test_scene: dict
    ) -> None:
        """Test listing events for a nonexistent scene."""
        with pytest.raises(EventError) as exc:
            event_manager.list_events(
                game_id=test_scene["game_id"],
                scene_id="nonexistent-scene"
            )
        assert "Scene nonexistent-scene not found" in str(exc.value)
