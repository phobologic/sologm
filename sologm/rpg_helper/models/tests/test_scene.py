"""
Unit tests for scene models.
"""
import pytest
from datetime import datetime
from unittest.mock import patch

from sologm.rpg_helper.models.scene import (
    Scene,
    SceneEvent,
    SceneStatus,
    scenes_by_id
)
from sologm.rpg_helper.models.game import Game, games_by_id


@pytest.fixture
def clean_scene_storage():
    """Fixture to ensure clean scene storage before and after tests."""
    # Setup - clear storage
    scenes_by_id.clear()
    
    # Run the test
    yield
    
    # Teardown - clear storage again
    scenes_by_id.clear()


@pytest.fixture
def basic_game():
    """Fixture to create a basic game for testing."""
    game = Game(
        id="game1",
        name="Test Game",
        creator_id="user1",
        channel_id="channel1"
    )
    games_by_id[game.id] = game
    
    yield game
    
    if game.id in games_by_id:
        del games_by_id[game.id]


@pytest.fixture
def basic_scene(basic_game):
    """Fixture to create a basic scene for testing."""
    return Scene(
        id="scene1",
        title="Test Scene",
        description="A test scene description",
        game=basic_game
    )


@pytest.mark.scene
class TestSceneEvent:
    """Tests for the SceneEvent class."""
    
    def test_init(self):
        """Test SceneEvent initialization."""
        event = SceneEvent("Something happened")
        
        assert event.description == "Something happened"
        assert isinstance(event.timestamp, datetime)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        timestamp = datetime.now()
        event = SceneEvent("Something happened")
        event.timestamp = timestamp
        
        result = event.to_dict()
        
        assert result["description"] == "Something happened"
        assert result["timestamp"] == timestamp.isoformat()
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        timestamp = datetime.now()
        data = {
            "description": "Something happened",
            "timestamp": timestamp.isoformat()
        }
        
        event = SceneEvent.from_dict(data)
        
        assert event.description == "Something happened"
        assert event.timestamp == timestamp


@pytest.mark.scene
class TestScene:
    """Tests for the Scene class."""
    
    def test_init_minimal(self, basic_game):
        """Test Scene initialization with minimal arguments."""
        scene = Scene(id="scene1", game=basic_game)
        
        assert scene.id == "scene1"
        assert scene.game == basic_game
        assert scene.title is None
        assert scene.description is None
        assert scene.status == SceneStatus.ACTIVE
        assert scene.events == []
        assert isinstance(scene.created_at, datetime)
        assert isinstance(scene.updated_at, datetime)
        assert scene.completed_at is None
    
    def test_init_with_title_description(self, basic_game):
        """Test Scene initialization with title and description."""
        scene = Scene(
            id="scene1",
            game=basic_game,
            title="Test Scene",
            description="A test scene description"
        )
        
        assert scene.title == "Test Scene"
        assert scene.description == "A test scene description"
    
    def test_set_title(self, basic_scene):
        """Test setting the scene title."""
        original_updated = basic_scene.updated_at
        
        basic_scene.set_title("New Title")
        
        assert basic_scene.title == "New Title"
        assert basic_scene.updated_at > original_updated
    
    def test_set_description(self, basic_scene):
        """Test setting the scene description."""
        original_updated = basic_scene.updated_at
        
        basic_scene.set_description("New Description")
        
        assert basic_scene.description == "New Description"
        assert basic_scene.updated_at > original_updated
    
    def test_clear_title(self, basic_scene):
        """Test clearing the scene title."""
        basic_scene.set_title("Test Title")
        original_updated = basic_scene.updated_at
        
        basic_scene.clear_title()
        
        assert basic_scene.title is None
        assert basic_scene.updated_at > original_updated
    
    def test_clear_description(self, basic_scene):
        """Test clearing the scene description."""
        basic_scene.set_description("Test Description")
        original_updated = basic_scene.updated_at
        
        basic_scene.clear_description()
        
        assert basic_scene.description is None
        assert basic_scene.updated_at > original_updated
    
    def test_complete_with_title_description(self, basic_scene):
        """Test completing a scene with title and description."""
        basic_scene.complete(
            title="Final Title",
            description="Final Description"
        )
        
        assert basic_scene.status == SceneStatus.COMPLETED
        assert basic_scene.title == "Final Title"
        assert basic_scene.description == "Final Description"
        assert isinstance(basic_scene.completed_at, datetime)
    
    def test_complete_without_title_description(self, basic_scene):
        """Test completing a scene without changing title/description."""
        basic_scene.set_title("Original Title")
        basic_scene.set_description("Original Description")
        
        basic_scene.complete()
        
        assert basic_scene.status == SceneStatus.COMPLETED
        assert basic_scene.title == "Original Title"
        assert basic_scene.description == "Original Description"
    
    def test_add_event(self, basic_scene):
        """Test adding an event to a scene."""
        original_updated = basic_scene.updated_at
        
        event = basic_scene.add_event("Something happened")
        
        assert len(basic_scene.events) == 1
        assert basic_scene.events[0] == event
        assert event.description == "Something happened"
        assert basic_scene.updated_at > original_updated
    
    def test_add_event_to_completed_scene(self, basic_scene):
        """Test adding an event to a completed scene."""
        basic_scene.complete()
        
        with pytest.raises(ValueError) as excinfo:
            basic_scene.add_event("Something happened")
        
        assert "Cannot add events to a completed scene" in str(excinfo.value)
        assert len(basic_scene.events) == 0
    
    def test_add_event_to_abandoned_scene(self, basic_scene):
        """Test adding an event to an abandoned scene."""
        basic_scene.abandon()
        
        with pytest.raises(ValueError) as excinfo:
            basic_scene.add_event("Something happened")
        
        assert "Cannot add events to a abandoned scene" in str(excinfo.value)
        assert len(basic_scene.events) == 0
    
    def test_complete_scene(self, basic_scene):
        """Test completing a scene."""
        original_updated = basic_scene.updated_at
        
        basic_scene.complete()
        
        assert basic_scene.status == SceneStatus.COMPLETED
        assert isinstance(basic_scene.completed_at, datetime)
        assert basic_scene.updated_at > original_updated
    
    def test_complete_already_completed_scene(self, basic_scene):
        """Test completing an already completed scene."""
        basic_scene.complete()
        
        with pytest.raises(ValueError) as excinfo:
            basic_scene.complete()
        
        assert "Cannot complete a completed scene" in str(excinfo.value)
    
    def test_abandon_scene(self, basic_scene):
        """Test abandoning a scene."""
        original_updated = basic_scene.updated_at
        
        basic_scene.abandon()
        
        assert basic_scene.status == SceneStatus.ABANDONED
        assert isinstance(basic_scene.completed_at, datetime)
        assert basic_scene.updated_at > original_updated
    
    def test_abandon_already_abandoned_scene(self, basic_scene):
        """Test abandoning an already abandoned scene."""
        basic_scene.abandon()
        
        with pytest.raises(ValueError) as excinfo:
            basic_scene.abandon()
        
        assert "Cannot abandon a abandoned scene" in str(excinfo.value)
    
    def test_to_dict(self, basic_scene, basic_game):
        """Test conversion to dictionary."""
        basic_scene.add_event("Something happened")
        basic_scene.complete()
        
        result = basic_scene.to_dict()
        
        assert result["id"] == "scene1"
        assert result["title"] == "Test Scene"
        assert result["description"] == "A test scene description"
        assert result["game_id"] == basic_game.id
        assert result["status"] == "completed"
        assert len(result["events"]) == 1
        assert result["events"][0]["description"] == "Something happened"
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert isinstance(result["completed_at"], str)
    
    def test_from_dict(self, basic_game):
        """Test creation from dictionary."""
        timestamp = datetime.now()
        data = {
            "id": "scene1",
            "title": "Test Scene",
            "description": "A test scene description",
            "game_id": basic_game.id,
            "status": "active",
            "events": [
                {
                    "description": "Something happened",
                    "timestamp": timestamp.isoformat()
                }
            ],
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "completed_at": None
        }
        
        scene = Scene.from_dict(data, games_by_id)
        
        assert scene.id == "scene1"
        assert scene.title == "Test Scene"
        assert scene.description == "A test scene description"
        assert scene.game == basic_game
        assert scene.status == SceneStatus.ACTIVE
        assert len(scene.events) == 1
        assert scene.events[0].description == "Something happened"
        assert scene.events[0].timestamp == timestamp
        assert scene.created_at == timestamp
        assert scene.updated_at == timestamp
        assert scene.completed_at is None 