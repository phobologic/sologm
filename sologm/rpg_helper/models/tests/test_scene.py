"""
Unit tests for scene models.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from sologm.rpg_helper.models.scene import (
    Scene,
    SceneEvent,
    SceneStatus,
    scenes_by_id
)
from sologm.rpg_helper.models.game import Game, games_by_id
from sologm.rpg_helper.models.game.base import Game as BaseGame


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
        event = SceneEvent(description="Something happened")
        
        assert event.description == "Something happened"
        assert isinstance(event.timestamp, datetime)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        event = SceneEvent(description="Something happened")
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        event.timestamp = timestamp
        
        result = event.to_dict()
        
        assert result["description"] == "Something happened"
        assert result["timestamp"] == "2023-01-01T12:00:00"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "description": "Something happened",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        event = SceneEvent.from_dict(data)
        
        assert event.description == "Something happened"
        assert event.timestamp == datetime(2023, 1, 1, 12, 0, 0)
    
    def test_from_dict_no_timestamp(self):
        """Test creation from dictionary without timestamp."""
        data = {
            "description": "Something happened"
        }
        
        event = SceneEvent.from_dict(data)
        
        assert event.description == "Something happened"
        assert isinstance(event.timestamp, datetime)


@pytest.mark.scene
class TestScene:
    """Tests for the Scene class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock game that won't auto-create scenes
        self.game = MagicMock()
        self.game.id = "game1"
        self.game.name = "Test Game"
        
        # Prevent the mock game from auto-creating scenes
        self.game.scenes = []
    
    def test_init(self):
        """Test Scene initialization."""
        scene = Scene(
            game=self.game,
            title="Test Scene",
            description="This is a test scene"
        )
        
        assert scene.game is self.game
        assert scene.title == "Test Scene"
        assert scene.description == "This is a test scene"
        assert isinstance(scene.id, str)
        assert scene.status == SceneStatus.ACTIVE
        assert isinstance(scene.created_at, datetime)
        assert isinstance(scene.updated_at, datetime)
        assert scene.events == []
    
    def test_init_with_defaults(self):
        """Test Scene initialization with default values."""
        scene = Scene(game=self.game)
        
        assert scene.game is self.game
        assert scene.title.startswith("Scene ")
        assert scene.description == f"A new scene in {self.game.name}."
        assert isinstance(scene.id, str)
        assert scene.status == SceneStatus.ACTIVE
    
    def test_add_event(self):
        """Test adding an event to a scene."""
        scene = Scene(
            game=self.game,
            title="Test Scene",
            description="This is a test scene"
        )
        
        event = scene.add_event("Something happened")
        
        assert len(scene.events) == 1
        assert scene.events[0] is event
        assert event.description == "Something happened"
    
    def test_add_event_to_inactive_scene(self):
        """Test adding an event to an inactive scene."""
        scene = Scene(
            game=self.game,
            title="Test Scene",
            description="This is a test scene",
            status=SceneStatus.COMPLETED
        )
        
        with pytest.raises(ValueError) as excinfo:
            scene.add_event("Something happened")
        
        assert "Cannot add events to a completed scene" in str(excinfo.value)
        assert len(scene.events) == 0
    
    def test_is_active(self):
        """Test checking if a scene is active."""
        scene = Scene(
            game=self.game,
            title="Test Scene",
            description="This is a test scene"
        )
        
        assert scene.is_active() is True
        
        scene.status = SceneStatus.COMPLETED
        assert scene.is_active() is False
    
    def test_is_completed(self):
        """Test checking if a scene is completed."""
        scene = Scene(
            game=self.game,
            title="Test Scene",
            description="This is a test scene",
            status=SceneStatus.COMPLETED
        )
        
        assert scene.is_completed() is True
        
        scene.status = SceneStatus.ACTIVE
        assert scene.is_completed() is False
    
    def test_is_abandoned(self):
        """Test checking if a scene is abandoned."""
        scene = Scene(
            game=self.game,
            title="Test Scene",
            description="This is a test scene",
            status=SceneStatus.ABANDONED
        )
        
        assert scene.is_abandoned() is True
        
        scene.status = SceneStatus.ACTIVE
        assert scene.is_abandoned() is False
    
    def test_complete(self):
        """Test completing a scene."""
        scene = Scene(
            game=self.game,
            title="Test Scene",
            description="This is a test scene"
        )
        
        scene.complete()
        
        assert scene.status == SceneStatus.COMPLETED
        assert scene.completed_at is not None
    
    def test_abandon(self):
        """Test abandoning a scene."""
        scene = Scene(
            game=self.game,
            title="Test Scene",
            description="This is a test scene"
        )
        
        scene.abandon()
        
        assert scene.status == SceneStatus.ABANDONED
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        scene = Scene(
            id="scene1",
            game=self.game,
            title="Test Scene",
            description="This is a test scene",
            status=SceneStatus.ACTIVE
        )
        
        # Add an event
        scene.add_event("Something happened")
        
        # Set timestamps
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        updated_at = datetime(2023, 1, 1, 12, 30, 0)
        scene.created_at = created_at
        scene.updated_at = updated_at
        
        result = scene.to_dict()
        
        assert result["id"] == "scene1"
        assert result["game_id"] == "game1"
        assert result["title"] == "Test Scene"
        assert result["description"] == "This is a test scene"
        assert result["status"] == "active"
        assert result["created_at"] == "2023-01-01T12:00:00"
        assert result["updated_at"] == "2023-01-01T12:30:00"
        assert len(result["events"]) == 1
        assert result["events"][0]["description"] == "Something happened"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        # Create a dictionary of games by ID
        games_by_id = {"game1": self.game}
        
        data = {
            "id": "scene1",
            "game_id": "game1",
            "title": "Test Scene",
            "description": "This is a test scene",
            "status": "active",
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:30:00",
            "events": [
                {
                    "description": "Something happened",
                    "timestamp": "2023-01-01T12:15:00"
                }
            ]
        }
        
        scene = Scene.from_dict(data, games_by_id)
        
        assert scene.id == "scene1"
        assert scene.game is self.game
        assert scene.title == "Test Scene"
        assert scene.description == "This is a test scene"
        assert scene.status == SceneStatus.ACTIVE
        assert scene.created_at == datetime(2023, 1, 1, 12, 0, 0)
        assert scene.updated_at == datetime(2023, 1, 1, 12, 30, 0)
        assert len(scene.events) == 1
        assert scene.events[0].description == "Something happened"
    
    def test_from_dict_game_not_found(self):
        """Test creation from dictionary with non-existent game."""
        # Create an empty dictionary of games by ID
        games_by_id = {}
        
        data = {
            "id": "scene1",
            "game_id": "game1",
            "title": "Test Scene",
            "description": "This is a test scene",
            "status": "active"
        }
        
        with pytest.raises(ValueError) as excinfo:
            Scene.from_dict(data, games_by_id)
        
        assert "Game with ID game1 not found" in str(excinfo.value)


class TestSceneWithRealGame:
    """Tests for Scene with a real Game instance."""
    
    def test_scene_creation_with_real_game(self):
        """Test creating a scene with a real Game instance."""
        # Create a real game (which will auto-create an initial scene)
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Verify the game has an initial scene
        assert len(game.scenes) == 1
        assert game.current_scene is not None
        
        # Complete the initial scene so we can create a new one
        game.complete_current_scene()
        
        # Create a new scene directly
        scene = Scene(
            game=game,
            title="Test Scene",
            description="This is a test scene"
        )
        
        # Add the scene to the game
        game.scenes.append(scene)
        game.current_scene = scene
        
        # Verify the scene was added
        assert len(game.scenes) == 2
        assert game.current_scene is scene
        assert scene in game.scenes
    
    def test_scene_creation_through_game(self):
        """Test creating a scene through the Game.create_scene method."""
        # Create a real game (which will auto-create an initial scene)
        game = Game(
            id="game1",
            name="Test Game",
            creator_id="user1",
            channel_id="channel1"
        )
        
        # Complete the initial scene so we can create a new one
        game.complete_current_scene()
        
        # Create a new scene through the game
        scene = game.create_scene(
            title="Test Scene",
            description="This is a test scene"
        )
        
        # Verify the scene was created and added to the game
        assert len(game.scenes) == 2
        assert game.current_scene is scene
        assert scene in game.scenes
        assert scene.title == "Test Scene"
        assert scene.description == "This is a test scene" 