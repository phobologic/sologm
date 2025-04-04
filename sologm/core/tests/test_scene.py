"""Tests for the scene management functionality."""

import logging
from pathlib import Path
from typing import Generator

import pytest

from sologm.core.scene import Scene, SceneManager, SceneStatus
from sologm.storage.file_manager import FileManager
from sologm.utils.datetime_utils import format_datetime, get_current_time
from sologm.utils.errors import SceneError

logger = logging.getLogger(__name__)


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def file_manager(temp_dir: Path) -> FileManager:
    """Create a FileManager instance for tests."""
    return FileManager(base_dir=temp_dir)


@pytest.fixture
def scene_manager(file_manager: FileManager) -> SceneManager:
    """Create a SceneManager instance for tests."""
    return SceneManager(file_manager=file_manager)


@pytest.fixture
def test_game(file_manager: FileManager) -> Generator[dict, None, None]:
    """Create a test game for scene operations."""
    game_id = "test-game"
    game_data = {
        "id": game_id,
        "name": "Test Game",
        "description": "A game for testing",
        "status": "active",
        "scenes": [],
        "created_at": format_datetime(get_current_time()),
        "modified_at": format_datetime(get_current_time()),
    }

    game_path = file_manager.get_game_path(game_id)
    file_manager.write_yaml(game_path, game_data)

    yield game_data


class TestScene:
    """Tests for the Scene class."""

    def test_scene_creation(self) -> None:
        """Test creating a Scene object."""
        now = get_current_time()
        scene = Scene(
            id="test-scene",
            game_id="test-game",
            title="Test Scene",
            description="A test scene",
            status=SceneStatus.ACTIVE,
            sequence=1,
            created_at=now,
            modified_at=now,
        )

        assert scene.id == "test-scene"
        assert scene.game_id == "test-game"
        assert scene.title == "Test Scene"
        assert scene.description == "A test scene"
        assert scene.status == SceneStatus.ACTIVE
        assert scene.sequence == 1
        assert scene.created_at == now
        assert scene.modified_at == now


class TestSceneManager:
    """Tests for the SceneManager class."""

    def test_create_scene(self, scene_manager: SceneManager, test_game: dict) -> None:
        """Test creating a new scene."""
        scene = scene_manager.create_scene(
            game_id=test_game["id"],
            title="First Scene",
            description="The beginning",
        )

        assert scene.id.startswith("scene-1-")
        assert scene.game_id == test_game["id"]
        assert scene.title == "First Scene"
        assert scene.description == "The beginning"
        assert scene.status == SceneStatus.ACTIVE
        assert scene.sequence == 1

        # Verify scene was saved
        scene_data = scene_manager.file_manager.read_yaml(
            scene_manager.file_manager.get_scene_path(test_game["id"], scene.id)
        )
        assert scene_data is not None
        assert scene_data["title"] == "First Scene"

    def test_create_scene_duplicate_title(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test creating a scene with a duplicate title fails."""
        # Create first scene
        scene_manager.create_scene(
            game_id=test_game["id"],
            title="First Scene",
            description="The beginning",
        )

        # Try to create another scene with same title
        with pytest.raises(
            SceneError,
            match="A scene with title 'First Scene' already exists in this game",
        ):
            scene_manager.create_scene(
                game_id=test_game["id"],
                title="First Scene",
                description="Another beginning",
            )

    def test_create_scene_duplicate_title_different_case(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test creating a scene with a duplicate title in different case fails."""
        # Create first scene
        scene_manager.create_scene(
            game_id=test_game["id"],
            title="Forest Path",
            description="A dark forest trail",
        )

        # Try to create another scene with same title in different case
        with pytest.raises(
            SceneError,
            match="A scene with title 'FOREST PATH' already exists in this game",
        ):
            scene_manager.create_scene(
                game_id=test_game["id"],
                title="FOREST PATH",
                description="Another forest trail",
            )

    def test_create_scene_nonexistent_game(self, scene_manager: SceneManager) -> None:
        """Test creating a scene in a nonexistent game."""
        with pytest.raises(SceneError, match="Game nonexistent-game not found"):
            scene_manager.create_scene(
                game_id="nonexistent-game",
                title="Test Scene",
                description="Test Description",
            )

    def test_list_scenes(self, scene_manager: SceneManager, test_game: dict) -> None:
        """Test listing scenes in a game."""
        # Create some test scenes
        scene1 = scene_manager.create_scene(
            game_id=test_game["id"],
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            game_id=test_game["id"],
            title="Second Scene",
            description="Scene 2",
        )

        scenes = scene_manager.list_scenes(test_game["id"])
        assert len(scenes) == 2
        assert scenes[0].id == scene1.id
        assert scenes[1].id == scene2.id
        assert scenes[0].sequence < scenes[1].sequence

    def test_list_scenes_empty(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test listing scenes in a game with no scenes."""
        scenes = scene_manager.list_scenes(test_game["id"])
        assert len(scenes) == 0

    def test_get_scene(self, scene_manager: SceneManager, test_game: dict) -> None:
        """Test getting a specific scene."""
        created_scene = scene_manager.create_scene(
            game_id=test_game["id"],
            title="Test Scene",
            description="Test Description",
        )

        retrieved_scene = scene_manager.get_scene(test_game["id"], created_scene.id)
        assert retrieved_scene is not None
        assert retrieved_scene.id == created_scene.id
        assert retrieved_scene.title == created_scene.title

    def test_get_scene_nonexistent(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test getting a nonexistent scene."""
        scene = scene_manager.get_scene(test_game["id"], "nonexistent-scene")
        assert scene is None

    def test_get_active_scene(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test getting the active scene."""
        scene = scene_manager.create_scene(
            game_id=test_game["id"],
            title="Active Scene",
            description="Currently active",
        )

        active_scene = scene_manager.get_active_scene(test_game["id"])
        assert active_scene is not None
        assert active_scene.id == scene.id

    def test_get_active_scene_none(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test getting active scene when none is set."""
        scene_manager.file_manager.set_active_scene_id(test_game["id"], "")
        active_scene = scene_manager.get_active_scene(test_game["id"])
        assert active_scene is None

    def test_complete_scene(self, scene_manager: SceneManager, test_game: dict) -> None:
        """Test completing a scene without changing current scene."""
        scene1 = scene_manager.create_scene(
            game_id=test_game["id"],
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            game_id=test_game["id"],
            title="Second Scene",
            description="Scene 2",
        )

        # Complete scene1 and verify it doesn't change current scene
        completed_scene = scene_manager.complete_scene(test_game["id"], scene1.id)
        assert completed_scene.status == SceneStatus.COMPLETED

        current_scene = scene_manager.get_active_scene(test_game["id"])
        assert (
            current_scene.id == scene2.id
        )  # Should still be scene2 as it was made current on creation

    def test_complete_scene_nonexistent(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test completing a nonexistent scene."""
        with pytest.raises(
            SceneError, match="Scene nonexistent-scene not found in game test-game"
        ):
            scene_manager.complete_scene(test_game["id"], "nonexistent-scene")

    def test_complete_scene_already_completed(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test completing an already completed scene."""
        scene = scene_manager.create_scene(
            game_id=test_game["id"],
            title="Test Scene",
            description="To be completed",
        )

        scene_manager.complete_scene(test_game["id"], scene.id)

        with pytest.raises(SceneError, match=f"Scene {scene.id} is already completed"):
            scene_manager.complete_scene(test_game["id"], scene.id)

    def test_set_current_scene(
        self, scene_manager: SceneManager, test_game: dict
    ) -> None:
        """Test setting which scene is current without changing status."""
        # Create two scenes
        scene1 = scene_manager.create_scene(
            game_id=test_game["id"],
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            game_id=test_game["id"],
            title="Second Scene",
            description="Scene 2",
        )

        # Complete both scenes
        scene_manager.complete_scene(test_game["id"], scene1.id)
        scene_manager.complete_scene(test_game["id"], scene2.id)

        # Make scene2 current
        scene_manager.set_current_scene(test_game["id"], scene2.id)

        current_scene = scene_manager.get_active_scene(test_game["id"])
        assert current_scene.id == scene2.id
        # Status should be completed
        assert current_scene.status == SceneStatus.COMPLETED
