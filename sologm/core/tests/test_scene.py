"""Tests for the scene management functionality."""

import pytest

from sologm.models.game import Game
from sologm.models.scene import Scene, SceneStatus
from sologm.utils.errors import SceneError


class TestScene:
    """Tests for the Scene model."""

    def test_scene_creation(self, db_session) -> None:
        """Test creating a Scene object."""
        scene = Scene.create(
            game_id="test-game",
            title="Test Scene",
            description="A test scene",
            sequence=1,
        )
        db_session.add(scene)
        db_session.commit()

        assert scene.id is not None
        assert scene.game_id == "test-game"
        assert scene.title == "Test Scene"
        assert scene.description == "A test scene"
        assert scene.status == SceneStatus.ACTIVE
        assert scene.sequence == 1
        assert scene.created_at is not None
        assert scene.modified_at is not None


class TestSceneManager:
    """Tests for the SceneManager class."""

    def test_create_scene(self, scene_manager, test_game, db_session) -> None:
        """Test creating a new scene."""
        scene = scene_manager.create_scene(
            game_id=test_game.id,
            title="First Scene",
            description="The beginning",
        )

        assert scene.id is not None
        assert scene.game_id == test_game.id
        assert scene.title == "First Scene"
        assert scene.description == "The beginning"
        assert scene.status == SceneStatus.ACTIVE
        assert scene.sequence == 1
        assert scene.is_active

        # Verify scene was saved to database
        db_scene = db_session.query(Scene).filter(Scene.id == scene.id).first()
        assert db_scene is not None
        assert db_scene.title == "First Scene"

    def test_create_scene_duplicate_title(self, scene_manager, test_game) -> None:
        """Test creating a scene with a duplicate title fails."""
        # Create first scene
        scene_manager.create_scene(
            game_id=test_game.id,
            title="First Scene",
            description="The beginning",
        )

        # Try to create another scene with same title
        with pytest.raises(
            SceneError,
            match="A scene with title 'First Scene' already exists in this game",
        ):
            scene_manager.create_scene(
                game_id=test_game.id,
                title="First Scene",
                description="Another beginning",
            )

    def test_create_scene_duplicate_title_different_case(
        self, scene_manager, test_game
    ) -> None:
        """Test creating a scene with a duplicate title in different case fails."""
        # Create first scene
        scene_manager.create_scene(
            game_id=test_game.id,
            title="Forest Path",
            description="A dark forest trail",
        )

        # Try to create another scene with same title in different case
        with pytest.raises(
            SceneError,
            match="A scene with title 'FOREST PATH' already exists in this game",
        ):
            scene_manager.create_scene(
                game_id=test_game.id,
                title="FOREST PATH",
                description="Another forest trail",
            )

    def test_create_scene_nonexistent_game(self, scene_manager) -> None:
        """Test creating a scene in a nonexistent game."""
        # This will now fail with a SQLAlchemy foreign key constraint error
        # which gets wrapped in a SceneError
        with pytest.raises(SceneError):
            scene_manager.create_scene(
                game_id="nonexistent-game",
                title="Test Scene",
                description="Test Description",
            )

    def test_list_scenes(self, scene_manager, test_game) -> None:
        """Test listing scenes in a game."""
        # Create some test scenes
        scene1 = scene_manager.create_scene(
            game_id=test_game.id,
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            game_id=test_game.id,
            title="Second Scene",
            description="Scene 2",
        )

        scenes = scene_manager.list_scenes(test_game.id)
        assert len(scenes) == 2
        assert scenes[0].id == scene1.id
        assert scenes[1].id == scene2.id
        assert scenes[0].sequence < scenes[1].sequence

    def test_list_scenes_empty(self, scene_manager, test_game) -> None:
        """Test listing scenes in a game with no scenes."""
        scenes = scene_manager.list_scenes(test_game.id)
        assert len(scenes) == 0

    def test_get_scene(self, scene_manager, test_game) -> None:
        """Test getting a specific scene."""
        created_scene = scene_manager.create_scene(
            game_id=test_game.id,
            title="Test Scene",
            description="Test Description",
        )

        retrieved_scene = scene_manager.get_scene(test_game.id, created_scene.id)
        assert retrieved_scene is not None
        assert retrieved_scene.id == created_scene.id
        assert retrieved_scene.title == created_scene.title

    def test_get_scene_nonexistent(self, scene_manager, test_game) -> None:
        """Test getting a nonexistent scene."""
        scene = scene_manager.get_scene(test_game.id, "nonexistent-scene")
        assert scene is None

    def test_get_active_scene(self, scene_manager, test_game) -> None:
        """Test getting the active scene."""
        scene = scene_manager.create_scene(
            game_id=test_game.id,
            title="Active Scene",
            description="Currently active",
        )

        active_scene = scene_manager.get_active_scene(test_game.id)
        assert active_scene is not None
        assert active_scene.id == scene.id

    def test_get_active_scene_none(self, scene_manager, test_game, db_session) -> None:
        """Test getting active scene when none is set."""
        # Create a scene but don't set it as active
        scene = Scene.create(
            game_id=test_game.id,
            title="Inactive Scene",
            description="Not active",
            sequence=1,
        )
        scene.is_active = False
        db_session.add(scene)
        db_session.commit()

        # Make sure no scenes are active
        db_session.query(Scene).filter(Scene.game_id == test_game.id).update(
            {"is_active": False}
        )
        db_session.commit()

        active_scene = scene_manager.get_active_scene(test_game.id)
        assert active_scene is None

    def test_complete_scene(self, scene_manager, test_game) -> None:
        """Test completing a scene without changing current scene."""
        scene1 = scene_manager.create_scene(
            game_id=test_game.id,
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            game_id=test_game.id,
            title="Second Scene",
            description="Scene 2",
        )

        # Complete scene1 and verify it doesn't change current scene
        completed_scene = scene_manager.complete_scene(test_game.id, scene1.id)
        assert completed_scene.status == SceneStatus.COMPLETED

        current_scene = scene_manager.get_active_scene(test_game.id)
        assert (
            current_scene.id == scene2.id
        )  # Should still be scene2 as it was made current on creation

    def test_complete_scene_nonexistent(self, scene_manager, test_game) -> None:
        """Test completing a nonexistent scene."""
        with pytest.raises(
            SceneError, match="Scene nonexistent-scene not found in game"
        ):
            scene_manager.complete_scene(test_game.id, "nonexistent-scene")

    def test_complete_scene_already_completed(self, scene_manager, test_game) -> None:
        """Test completing an already completed scene."""
        scene = scene_manager.create_scene(
            game_id=test_game.id,
            title="Test Scene",
            description="To be completed",
        )

        scene_manager.complete_scene(test_game.id, scene.id)

        with pytest.raises(SceneError, match=f"Scene {scene.id} is already completed"):
            scene_manager.complete_scene(test_game.id, scene.id)

    def test_set_current_scene(self, scene_manager, test_game) -> None:
        """Test setting which scene is current without changing status."""
        # Create two scenes
        scene1 = scene_manager.create_scene(
            game_id=test_game.id,
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            game_id=test_game.id,
            title="Second Scene",
            description="Scene 2",
        )

        # Complete both scenes
        scene_manager.complete_scene(test_game.id, scene1.id)
        scene_manager.complete_scene(test_game.id, scene2.id)

        # Make scene1 current (scene2 is currently active)
        scene_manager.set_current_scene(test_game.id, scene1.id)

        current_scene = scene_manager.get_active_scene(test_game.id)
        assert current_scene.id == scene1.id
        # Status should be completed
        assert current_scene.status == SceneStatus.COMPLETED

    def test_scene_sequence_management(self, scene_manager, test_game):
        """Test that scene sequences are managed correctly."""
        # Create multiple scenes
        scene1 = scene_manager.create_scene(
            game_id=test_game.id,
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            game_id=test_game.id,
            title="Second Scene",
            description="Scene 2",
        )
        scene3 = scene_manager.create_scene(
            game_id=test_game.id,
            title="Third Scene",
            description="Scene 3",
        )

        # Verify sequences
        assert scene1.sequence == 1
        assert scene2.sequence == 2
        assert scene3.sequence == 3

        # Test get_previous_scene
        prev_scene = scene_manager.get_previous_scene(test_game.id, scene3)
        assert prev_scene.id == scene2.id

    def test_update_scene(self, scene_manager, test_game) -> None:
        """Test updating a scene's title and description."""
        # Create a test scene
        scene = scene_manager.create_scene(
            game_id=test_game.id,
            title="Original Title",
            description="Original description",
        )

        # Update the scene
        updated_scene = scene_manager.update_scene(
            game_id=test_game.id,
            scene_id=scene.id,
            title="Updated Title",
            description="Updated description",
        )

        # Verify the scene was updated
        assert updated_scene.id == scene.id
        assert updated_scene.title == "Updated Title"
        assert updated_scene.description == "Updated description"

        # Verify the scene was updated in the database
        retrieved_scene = scene_manager.get_scene(test_game.id, scene.id)
        assert retrieved_scene.title == "Updated Title"
        assert retrieved_scene.description == "Updated description"

    def test_update_scene_duplicate_title(self, scene_manager, test_game) -> None:
        """Test updating a scene with a duplicate title fails."""
        # Create two scenes
        scene1 = scene_manager.create_scene(
            game_id=test_game.id,
            title="First Scene",
            description="First description",
        )
        scene2 = scene_manager.create_scene(
            game_id=test_game.id,
            title="Second Scene",
            description="Second description",
        )

        # Try to update scene2 with scene1's title
        with pytest.raises(
            SceneError,
            match="A scene with title 'First Scene' already exists in this game",
        ):
            scene_manager.update_scene(
                game_id=test_game.id,
                scene_id=scene2.id,
                title="First Scene",
                description="Updated description",
            )

    def test_validate_active_context(self, scene_manager, game_manager, test_game):
        """Test validating active game and scene context."""
        # Create a scene to be active
        scene = scene_manager.create_scene(
            game_id=test_game.id,
            title="Active Scene",
            description="Currently active",
        )

        game_id, active_scene = scene_manager.validate_active_context(game_manager)
        assert game_id == test_game.id
        assert active_scene.id == scene.id

    def test_validate_active_context_no_game(
        self, scene_manager, game_manager, db_session
    ):
        """Test validation with no active game."""
        # Deactivate all games
        db_session.query(Game).update({Game.is_active: False})
        db_session.commit()

        with pytest.raises(SceneError) as exc:
            scene_manager.validate_active_context(game_manager)
        assert "No active game" in str(exc.value)
