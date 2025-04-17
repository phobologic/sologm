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
            act_id="test-act",
            title="Test Scene",
            description="A test scene",
            sequence=1,
        )
        db_session.add(scene)
        db_session.commit()

        assert scene.id is not None
        assert scene.act_id == "test-act"
        assert scene.title == "Test Scene"
        assert scene.description == "A test scene"
        assert scene.status == SceneStatus.ACTIVE
        assert scene.sequence == 1
        assert scene.created_at is not None
        assert scene.modified_at is not None


class TestSceneManager:
    """Tests for the SceneManager class."""

    def test_create_scene(self, scene_manager, test_game, db_session, test_act) -> None:
        """Test creating a new scene."""
        scene = scene_manager.create_scene(
            title="First Scene",
            description="The beginning",
            act_id=test_act.id,
        )

        assert scene.id is not None
        assert scene.act_id == test_act.id
        assert scene.title == "First Scene"
        assert scene.description == "The beginning"
        assert scene.status == SceneStatus.ACTIVE
        assert scene.sequence == 1
        assert scene.is_active

        # Verify scene was saved to database
        db_scene = db_session.query(Scene).filter(Scene.id == scene.id).first()
        assert db_scene is not None
        assert db_scene.title == "First Scene"

    def test_create_scene_duplicate_title(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test creating a scene with a duplicate title fails."""
        # Create first scene
        scene_manager.create_scene(
            title="First Scene",
            description="The beginning",
            act_id=test_act.id,
        )

        # Try to create another scene with same title
        with pytest.raises(
            SceneError,
            match="A scene with title 'First Scene' already exists in this act",
        ):
            scene_manager.create_scene(
                title="First Scene",
                description="Another beginning",
                act_id=test_act.id,
            )

    def test_create_scene_duplicate_title_different_case(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test creating a scene with a duplicate title in different case fails."""
        # Create first scene
        scene_manager.create_scene(
            title="Forest Path",
            description="A dark forest trail",
            act_id=test_act.id,
        )

        # Try to create another scene with same title in different case
        with pytest.raises(
            SceneError,
            match="A scene with title 'FOREST PATH' already exists in this act",
        ):
            scene_manager.create_scene(
                title="FOREST PATH",
                description="Another forest trail",
                act_id=test_act.id,
            )

    def test_create_scene_nonexistent_act(self, scene_manager) -> None:
        """Test creating a scene in a nonexistent act."""
        # This will now fail with a SQLAlchemy foreign key constraint error
        # which gets wrapped in a SceneError
        with pytest.raises(SceneError):
            scene_manager.create_scene(
                title="Test Scene",
                description="Test Description",
                act_id="nonexistent-act",
            )

    def test_list_scenes(self, scene_manager, test_game, test_act) -> None:
        """Test listing scenes in an act."""
        # Create some test scenes
        scene1 = scene_manager.create_scene(
            title="First Scene",
            description="Scene 1",
            act_id=test_act.id,
        )
        scene2 = scene_manager.create_scene(
            title="Second Scene",
            description="Scene 2",
            act_id=test_act.id,
        )

        scenes = scene_manager.list_scenes(test_act.id)
        assert len(scenes) == 2
        assert scenes[0].id == scene1.id
        assert scenes[1].id == scene2.id
        assert scenes[0].sequence < scenes[1].sequence

    def test_list_scenes_empty(self, scene_manager, test_game, test_act) -> None:
        """Test listing scenes in an act with no scenes."""
        scenes = scene_manager.list_scenes(test_act.id)
        assert len(scenes) == 0

    def test_get_scene(self, scene_manager, test_game, test_act) -> None:
        """Test getting a specific scene."""
        created_scene = scene_manager.create_scene(
            act_id=test_act.id,
            title="Test Scene",
            description="Test Description",
        )

        retrieved_scene = scene_manager.get_scene(created_scene.id)
        assert retrieved_scene is not None
        assert retrieved_scene.id == created_scene.id
        assert retrieved_scene.title == created_scene.title

    def test_get_scene_nonexistent(self, scene_manager, test_game, test_act) -> None:
        """Test getting a nonexistent scene."""
        scene = scene_manager.get_scene("nonexistent-scene")
        assert scene is None

    def test_get_active_scene(self, scene_manager, test_game, test_act) -> None:
        """Test getting the active scene."""
        scene = scene_manager.create_scene(
            act_id=test_act.id,
            title="Active Scene",
            description="Currently active",
        )

        active_scene = scene_manager.get_active_scene(test_act.id)
        assert active_scene is not None
        assert active_scene.id == scene.id

    def test_get_active_scene_none(
        self, scene_manager, test_game, db_session, test_act
    ) -> None:
        """Test getting active scene when none is set."""

        scene = Scene.create(
            act_id=test_act.id,
            title="Inactive Scene",
            description="Not active",
            sequence=1,
        )
        scene.is_active = False
        db_session.add(scene)
        db_session.commit()

        # Make sure no scenes are active
        db_session.query(Scene).filter(Scene.act_id == test_act.id).update(
            {"is_active": False}
        )
        db_session.commit()

        active_scene = scene_manager.get_active_scene(test_act.id)
        assert active_scene is None

    def test_complete_scene(self, scene_manager, test_game, test_act) -> None:
        """Test completing a scene without changing current scene."""
        scene1 = scene_manager.create_scene(
            act_id=test_act.id,
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            act_id=test_act.id,
            title="Second Scene",
            description="Scene 2",
        )

        # Complete scene1 and verify it doesn't change current scene
        completed_scene = scene_manager.complete_scene(scene1.id)
        assert completed_scene.status == SceneStatus.COMPLETED

        current_scene = scene_manager.get_active_scene(test_act.id)
        assert (
            current_scene.id == scene2.id
        )  # Should still be scene2 as it was made current on creation

    def test_complete_scene_nonexistent(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test completing a nonexistent scene."""
        with pytest.raises(SceneError, match="Scene nonexistent-scene not found"):
            scene_manager.complete_scene("nonexistent-scene")

    def test_complete_scene_already_completed(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test completing an already completed scene."""
        scene = scene_manager.create_scene(
            act_id=test_act.id,
            title="Test Scene",
            description="To be completed",
        )

        scene_manager.complete_scene(scene.id)

        with pytest.raises(SceneError, match=f"Scene {scene.id} is already completed"):
            scene_manager.complete_scene(scene.id)

    def test_set_current_scene(self, scene_manager, test_game, test_act) -> None:
        """Test setting which scene is current without changing status."""
        # Create two scenes
        scene1 = scene_manager.create_scene(
            act_id=test_act.id,
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            act_id=test_act.id,
            title="Second Scene",
            description="Scene 2",
        )

        # Complete both scenes
        scene_manager.complete_scene(scene1.id)
        scene_manager.complete_scene(scene2.id)

        # Make scene1 current (scene2 is currently active)
        scene_manager.set_current_scene(scene1.id)

        current_scene = scene_manager.get_active_scene(test_act.id)
        assert current_scene.id == scene1.id
        # Status should be completed
        assert current_scene.status == SceneStatus.COMPLETED

    def test_scene_sequence_management(self, scene_manager, test_game, test_act):
        """Test that scene sequences are managed correctly."""
        # Create multiple scenes
        scene1 = scene_manager.create_scene(
            title="First Scene",
            description="Scene 1",
            act_id=test_act.id,
        )
        scene2 = scene_manager.create_scene(
            title="Second Scene",
            description="Scene 2",
            act_id=test_act.id,
        )
        scene3 = scene_manager.create_scene(
            title="Third Scene",
            description="Scene 3",
            act_id=test_act.id,
        )

        # Verify sequences
        assert scene1.sequence == 1
        assert scene2.sequence == 2
        assert scene3.sequence == 3

        # Test get_previous_scene with scene_id
        prev_scene = scene_manager.get_previous_scene(scene_id=scene3.id)
        assert prev_scene.id == scene2.id

        # Test get_previous_scene for first scene
        prev_scene = scene_manager.get_previous_scene(scene_id=scene1.id)
        assert prev_scene is None

        # Test get_previous_scene with invalid scene_id
        prev_scene = scene_manager.get_previous_scene(scene_id="nonexistent-id")
        assert prev_scene is None

    def test_update_scene(self, scene_manager, test_game, test_act) -> None:
        """Test updating a scene's title and description."""
        # Create a test scene
        scene = scene_manager.create_scene(
            title="Original Title",
            description="Original description",
            act_id=test_act.id,
        )

        # Update the scene
        updated_scene = scene_manager.update_scene(
            scene_id=scene.id,
            title="Updated Title",
            description="Updated description",
        )

        # Verify the scene was updated
        assert updated_scene.id == scene.id
        assert updated_scene.title == "Updated Title"
        assert updated_scene.description == "Updated description"

        # Verify the scene was updated in the database
        retrieved_scene = scene_manager.get_scene(scene.id)
        assert retrieved_scene.title == "Updated Title"
        assert retrieved_scene.description == "Updated description"

        # Test updating only title
        updated_scene = scene_manager.update_scene(
            scene_id=scene.id,
            title="Only Title Updated",
        )
        assert updated_scene.title == "Only Title Updated"
        assert updated_scene.description == "Updated description"

        # Test updating only description
        updated_scene = scene_manager.update_scene(
            scene_id=scene.id,
            description="Only description updated",
        )
        assert updated_scene.title == "Only Title Updated"
        assert updated_scene.description == "Only description updated"

    def test_update_scene_duplicate_title(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test updating a scene with a duplicate title fails."""
        # Create two scenes
        scene1 = scene_manager.create_scene(
            title="First Scene",
            description="First description",
            act_id=test_act.id,
        )
        scene2 = scene_manager.create_scene(
            title="Second Scene",
            description="Second description",
            act_id=test_act.id,
        )

        # Try to update scene2 with scene1's title
        with pytest.raises(
            SceneError,
            match="A scene with title 'First Scene' already exists in this act",
        ):
            scene_manager.update_scene(
                scene_id=scene2.id,
                title="First Scene",
            )

    def test_get_active_context(self, scene_manager, test_game, test_act):
        """Test getting active game, act, and scene context."""
        # Create a scene to be active
        scene = scene_manager.create_scene(
            act_id=test_act.id,
            title="Active Scene",
            description="Currently active",
        )

        context = scene_manager.get_active_context()
        assert context["game"].id == test_game.id
        assert context["act"].id == test_act.id
        assert context["scene"].id == scene.id

    def test_validate_active_context(self, scene_manager, test_game, test_act):
        """Test validating active game and scene context."""
        # Create a scene to be active
        scene = scene_manager.create_scene(
            act_id=test_act.id,
            title="Active Scene",
            description="Currently active",
        )

        act_id, active_scene = scene_manager.validate_active_context()
        assert act_id == test_act.id
        assert active_scene.id == scene.id

    def test_get_scene_in_act(self, scene_manager, test_game, test_act) -> None:
        """Test getting a specific scene within an act."""
        created_scene = scene_manager.create_scene(
            act_id=test_act.id,
            title="Test Scene",
            description="Test Description",
        )

        retrieved_scene = scene_manager.get_scene_in_act(test_act.id, created_scene.id)
        assert retrieved_scene is not None
        assert retrieved_scene.id == created_scene.id
        assert retrieved_scene.title == created_scene.title

        # Test with wrong act_id
        wrong_scene = scene_manager.get_scene_in_act("wrong-act-id", created_scene.id)
        assert wrong_scene is None

    def test_validate_active_context_no_game(self, scene_manager, db_session):
        """Test validation with no active game."""
        # Deactivate all games
        db_session.query(Game).update({Game.is_active: False})
        db_session.commit()

        with pytest.raises(SceneError) as exc:
            scene_manager.validate_active_context()
        assert "No active game" in str(exc.value)

    def test_session_propagation(self, scene_manager, db_session):
        """Test that the session is properly propagated to lazy-initialized managers."""
        # Access lazy-initialized managers
        event_manager = scene_manager.event_manager
        dice_manager = scene_manager.dice_manager
        oracle_manager = scene_manager.oracle_manager

        # Verify they all have the same session
        assert id(scene_manager._session) == id(db_session)
        assert id(event_manager._session) == id(db_session)
        assert id(dice_manager._session) == id(db_session)
        assert id(oracle_manager._session) == id(db_session)

    def test_create_scene_with_active_act(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test creating a scene using the active act."""

        scene = scene_manager.create_scene(
            title="Active Act Scene",
            description="Scene in active act",
        )

        assert scene.id is not None
        assert scene.act_id == test_act.id
        assert scene.title == "Active Act Scene"
        assert scene.description == "Scene in active act"
        assert scene.is_active

    def test_list_scenes_with_active_act(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test listing scenes using the active act."""

        # Create some test scenes
        scene1 = scene_manager.create_scene(
            title="First Scene",
            description="Scene 1",
            act_id=test_act.id,
        )
        scene2 = scene_manager.create_scene(
            title="Second Scene",
            description="Scene 2",
            act_id=test_act.id,
        )

        scenes = scene_manager.list_scenes()
        assert len(scenes) == 2
        assert scenes[0].id == scene1.id
        assert scenes[1].id == scene2.id
        assert scenes[0].sequence < scenes[1].sequence

    def test_get_active_scene_without_act_id(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test getting the active scene without providing an act_id."""

        # Create a scene to be active
        scene = scene_manager.create_scene(
            title="Active Scene",
            description="Currently active",
            act_id=test_act.id,
        )

        active_scene = scene_manager.get_active_scene()
        assert active_scene is not None
        assert active_scene.id == scene.id

    def test_create_scene_with_make_active_false(
        self, scene_manager, test_game, test_act
    ) -> None:
        """Test creating a scene without making it active."""

        # Create a first scene that will be active
        scene1 = scene_manager.create_scene(
            title="First Scene",
            description="This will be active",
            act_id=test_act.id,
        )

        # Create a second scene without making it active
        scene2 = scene_manager.create_scene(
            title="Second Scene",
            description="This won't be active",
            act_id=test_act.id,
            make_active=False,
        )

        # Verify scene1 is still active
        active_scene = scene_manager.get_active_scene(test_act.id)
        assert active_scene.id == scene1.id

        # Verify scene2 is not active
        assert not scene2.is_active

    def test_scene_relationships(self, scene_manager, test_scene, session_context):
        """Test that scene relationships are properly loaded."""
        # Create a scene with events
        scene = scene_manager.create_scene(
            title="Scene with Events",
            description="A scene that will have events",
        )

        # Add events to the scene
        event_manager = scene_manager.event_manager
        event = event_manager.add_event(
            description="Test event",
            scene_id=scene.id,
            source="manual",
        )

        # Use session_context to ensure relationships are loaded
        with session_context as session:
            # Refresh the scene to load relationships
            session.refresh(scene)

            # Verify relationships
            assert hasattr(scene, "events")
            assert len(scene.events) > 0
            assert scene.events[0].id == event.id

    def test_get_act_id_or_active(self, scene_manager, test_game, test_act) -> None:
        """Test the _get_act_id_or_active helper method."""

        # Test with provided act_id
        act_id = scene_manager._get_act_id_or_active("test-act-id")
        assert act_id == "test-act-id"

        # Test with no act_id (should use active act)
        act_id = scene_manager._get_act_id_or_active(None)
        assert act_id == test_act.id
