"""Tests for the scene management functionality."""

import pytest

from sologm.core.act import ActManager
from sologm.models.act import Act
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

    @pytest.fixture
    def ensure_active_act(self, test_game, db_session):
        """Ensure there's an active act for each test and return it."""
        from sologm.core.act import ActManager

        act_manager = ActManager(db_session)

        # Check if there's already an active act
        active_act = act_manager.get_active_act(test_game.id)
        if not active_act:
            # Create a new act
            act = Act.create(
                game_id=test_game.id,
                title="Test Act",
                description="Test act description",
                sequence=1,
            )
            act.is_active = True
            db_session.add(act)
            db_session.commit()
            return act

        return active_act

    def test_create_scene(
        self, scene_manager, test_game, db_session, ensure_active_act
    ) -> None:
        """Test creating a new scene."""
        active_act = ensure_active_act
        scene = scene_manager.create_scene(
            title="First Scene",
            description="The beginning",
            act_id=active_act.id,
        )

        assert scene.id is not None
        assert scene.act_id == active_act.id
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
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test creating a scene with a duplicate title fails."""
        active_act = ensure_active_act
        # Create first scene
        scene_manager.create_scene(
            title="First Scene",
            description="The beginning",
            act_id=active_act.id,
        )

        # Try to create another scene with same title
        with pytest.raises(
            SceneError,
            match="A scene with title 'First Scene' already exists in this act",
        ):
            scene_manager.create_scene(
                title="First Scene",
                description="Another beginning",
                act_id=active_act.id,
            )

    def test_create_scene_duplicate_title_different_case(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test creating a scene with a duplicate title in different case fails."""
        active_act = ensure_active_act
        # Create first scene
        scene_manager.create_scene(
            title="Forest Path",
            description="A dark forest trail",
            act_id=active_act.id,
        )

        # Try to create another scene with same title in different case
        with pytest.raises(
            SceneError,
            match="A scene with title 'FOREST PATH' already exists in this act",
        ):
            scene_manager.create_scene(
                title="FOREST PATH",
                description="Another forest trail",
                act_id=active_act.id,
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

    def test_list_scenes(self, scene_manager, test_game, ensure_active_act) -> None:
        """Test listing scenes in an act."""
        active_act = ensure_active_act
        # Create some test scenes
        scene1 = scene_manager.create_scene(
            title="First Scene",
            description="Scene 1",
            act_id=active_act.id,
        )
        scene2 = scene_manager.create_scene(
            title="Second Scene",
            description="Scene 2",
            act_id=active_act.id,
        )

        scenes = scene_manager.list_scenes(active_act.id)
        assert len(scenes) == 2
        assert scenes[0].id == scene1.id
        assert scenes[1].id == scene2.id
        assert scenes[0].sequence < scenes[1].sequence

    def test_list_scenes_empty(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test listing scenes in an act with no scenes."""
        active_act = ensure_active_act
        scenes = scene_manager.list_scenes(active_act.id)
        assert len(scenes) == 0

    def test_get_scene(self, scene_manager, test_game, ensure_active_act) -> None:
        """Test getting a specific scene."""
        active_act = ensure_active_act
        created_scene = scene_manager.create_scene(
            act_id=active_act.id,
            title="Test Scene",
            description="Test Description",
        )

        retrieved_scene = scene_manager.get_scene(created_scene.id)
        assert retrieved_scene is not None
        assert retrieved_scene.id == created_scene.id
        assert retrieved_scene.title == created_scene.title

    def test_get_scene_nonexistent(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test getting a nonexistent scene."""
        scene = scene_manager.get_scene("nonexistent-scene")
        assert scene is None

    def test_get_active_scene(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test getting the active scene."""
        active_act = ensure_active_act
        scene = scene_manager.create_scene(
            act_id=active_act.id,
            title="Active Scene",
            description="Currently active",
        )

        active_scene = scene_manager.get_active_scene(active_act.id)
        assert active_scene is not None
        assert active_scene.id == scene.id

    def test_get_active_scene_none(
        self, scene_manager, test_game, db_session, ensure_active_act
    ) -> None:
        """Test getting active scene when none is set."""
        active_act = ensure_active_act

        scene = Scene.create(
            act_id=active_act.id,
            title="Inactive Scene",
            description="Not active",
            sequence=1,
        )
        scene.is_active = False
        db_session.add(scene)
        db_session.commit()

        # Make sure no scenes are active
        db_session.query(Scene).filter(Scene.act_id == active_act.id).update(
            {"is_active": False}
        )
        db_session.commit()

        active_scene = scene_manager.get_active_scene(active_act.id)
        assert active_scene is None

    def test_complete_scene(self, scene_manager, test_game, ensure_active_act) -> None:
        """Test completing a scene without changing current scene."""
        active_act = ensure_active_act
        scene1 = scene_manager.create_scene(
            act_id=active_act.id,
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            act_id=active_act.id,
            title="Second Scene",
            description="Scene 2",
        )

        # Complete scene1 and verify it doesn't change current scene
        completed_scene = scene_manager.complete_scene(scene1.id)
        assert completed_scene.status == SceneStatus.COMPLETED

        current_scene = scene_manager.get_active_scene(active_act.id)
        assert (
            current_scene.id == scene2.id
        )  # Should still be scene2 as it was made current on creation

    def test_complete_scene_nonexistent(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test completing a nonexistent scene."""
        with pytest.raises(SceneError, match="Scene nonexistent-scene not found"):
            scene_manager.complete_scene("nonexistent-scene")

    def test_complete_scene_already_completed(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test completing an already completed scene."""
        active_act = ensure_active_act
        scene = scene_manager.create_scene(
            act_id=active_act.id,
            title="Test Scene",
            description="To be completed",
        )

        scene_manager.complete_scene(scene.id)

        with pytest.raises(SceneError, match=f"Scene {scene.id} is already completed"):
            scene_manager.complete_scene(scene.id)

    def test_set_current_scene(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test setting which scene is current without changing status."""
        active_act = ensure_active_act
        # Create two scenes
        scene1 = scene_manager.create_scene(
            act_id=active_act.id,
            title="First Scene",
            description="Scene 1",
        )
        scene2 = scene_manager.create_scene(
            act_id=active_act.id,
            title="Second Scene",
            description="Scene 2",
        )

        # Complete both scenes
        scene_manager.complete_scene(scene1.id)
        scene_manager.complete_scene(scene2.id)

        # Make scene1 current (scene2 is currently active)
        scene_manager.set_current_scene(scene1.id)

        current_scene = scene_manager.get_active_scene(active_act.id)
        assert current_scene.id == scene1.id
        # Status should be completed
        assert current_scene.status == SceneStatus.COMPLETED

    def test_scene_sequence_management(
        self, scene_manager, test_game, ensure_active_act
    ):
        """Test that scene sequences are managed correctly."""
        active_act = ensure_active_act
        # Create multiple scenes
        scene1 = scene_manager.create_scene(
            title="First Scene",
            description="Scene 1",
            act_id=active_act.id,
        )
        scene2 = scene_manager.create_scene(
            title="Second Scene",
            description="Scene 2",
            act_id=active_act.id,
        )
        scene3 = scene_manager.create_scene(
            title="Third Scene",
            description="Scene 3",
            act_id=active_act.id,
        )

        # Verify sequences
        assert scene1.sequence == 1
        assert scene2.sequence == 2
        assert scene3.sequence == 3

        # Test get_previous_scene
        prev_scene = scene_manager.get_previous_scene(scene3)
        assert prev_scene.id == scene2.id

    def test_update_scene(self, scene_manager, test_game, ensure_active_act) -> None:
        """Test updating a scene's title and description."""
        active_act = ensure_active_act
        # Create a test scene
        scene = scene_manager.create_scene(
            act_id=active_act.id,
            title="Original Title",
            description="Original description",
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

    def test_update_scene_duplicate_title(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test updating a scene with a duplicate title fails."""
        active_act = ensure_active_act
        # Create two scenes
        scene1 = scene_manager.create_scene(
            act_id=active_act.id,
            title="First Scene",
            description="First description",
        )
        scene2 = scene_manager.create_scene(
            act_id=active_act.id,
            title="Second Scene",
            description="Second description",
        )

        # Try to update scene2 with scene1's title
        with pytest.raises(
            SceneError,
            match="A scene with title 'First Scene' already exists in this act",
        ):
            scene_manager.update_scene(
                scene_id=scene2.id,
                title="First Scene",
                description="Updated description",
            )

    def test_get_active_context(
        self, scene_manager, game_manager, test_game, ensure_active_act, monkeypatch
    ):
        """Test getting active game, act, and scene context."""
        active_act = ensure_active_act
        # Create a scene to be active
        scene = scene_manager.create_scene(
            act_id=active_act.id,
            title="Active Scene",
            description="Currently active",
        )

        # Monkeypatch the game_manager and act_manager properties
        monkeypatch.setattr(scene_manager, "game_manager", game_manager)
        monkeypatch.setattr(
            scene_manager, "act_manager", ActManager(session=scene_manager._session)
        )

        context = scene_manager.get_active_context()
        assert context["game"].id == test_game.id
        assert context["act"].id == active_act.id
        assert context["scene"].id == scene.id

    def test_validate_active_context(
        self, scene_manager, game_manager, test_game, ensure_active_act, monkeypatch
    ):
        """Test validating active game and scene context."""
        active_act = ensure_active_act
        # Create a scene to be active
        scene = scene_manager.create_scene(
            act_id=active_act.id,
            title="Active Scene",
            description="Currently active",
        )

        # Monkeypatch the game_manager and act_manager properties
        monkeypatch.setattr(scene_manager, "game_manager", game_manager)
        monkeypatch.setattr(
            scene_manager, "act_manager", ActManager(session=scene_manager._session)
        )

        act_id, active_scene = scene_manager.validate_active_context()
        assert act_id == active_act.id
        assert active_scene.id == scene.id

    def test_get_scene_in_act(
        self, scene_manager, test_game, ensure_active_act
    ) -> None:
        """Test getting a specific scene within an act."""
        active_act = ensure_active_act
        created_scene = scene_manager.create_scene(
            act_id=active_act.id,
            title="Test Scene",
            description="Test Description",
        )

        retrieved_scene = scene_manager.get_scene_in_act(
            active_act.id, created_scene.id
        )
        assert retrieved_scene is not None
        assert retrieved_scene.id == created_scene.id
        assert retrieved_scene.title == created_scene.title

        # Test with wrong act_id
        wrong_scene = scene_manager.get_scene_in_act("wrong-act-id", created_scene.id)
        assert wrong_scene is None

    def test_validate_active_context_no_game(
        self, scene_manager, game_manager, db_session, monkeypatch
    ):
        """Test validation with no active game."""
        # Deactivate all games
        db_session.query(Game).update({Game.is_active: False})
        db_session.commit()

        # Monkeypatch the game_manager property
        monkeypatch.setattr(scene_manager, "game_manager", game_manager)

        with pytest.raises(SceneError) as exc:
            scene_manager.validate_active_context()
        assert "No active game" in str(exc.value)
    def test_create_scene_in_active_act(
        self, scene_manager, test_game, db_session, ensure_active_act, monkeypatch
    ) -> None:
        """Test creating a scene in the active act."""
        active_act = ensure_active_act
        
        # Monkeypatch the game_manager and act_manager properties
        monkeypatch.setattr(scene_manager, "game_manager", GameManager(session=db_session))
        monkeypatch.setattr(
            scene_manager, "act_manager", ActManager(session=db_session)
        )
        
        scene = scene_manager.create_scene_in_active_act(
            title="Active Act Scene",
            description="Scene in active act",
        )

        assert scene.id is not None
        assert scene.act_id == active_act.id
        assert scene.title == "Active Act Scene"
        assert scene.description == "Scene in active act"
        assert scene.is_active

    def test_list_scenes_in_active_act(
        self, scene_manager, test_game, db_session, ensure_active_act, monkeypatch
    ) -> None:
        """Test listing scenes in the active act."""
        active_act = ensure_active_act
        
        # Monkeypatch the game_manager and act_manager properties
        monkeypatch.setattr(scene_manager, "game_manager", GameManager(session=db_session))
        monkeypatch.setattr(
            scene_manager, "act_manager", ActManager(session=db_session)
        )
        
        # Create some test scenes
        scene1 = scene_manager.create_scene(
            title="First Scene",
            description="Scene 1",
            act_id=active_act.id,
        )
        scene2 = scene_manager.create_scene(
            title="Second Scene",
            description="Scene 2",
            act_id=active_act.id,
        )

        scenes = scene_manager.list_scenes_in_active_act()
        assert len(scenes) == 2
        assert scenes[0].id == scene1.id
        assert scenes[1].id == scene2.id
        assert scenes[0].sequence < scenes[1].sequence
        
    def test_get_active_scene_without_act_id(
        self, scene_manager, test_game, db_session, ensure_active_act, monkeypatch
    ) -> None:
        """Test getting the active scene without providing an act_id."""
        active_act = ensure_active_act
        
        # Monkeypatch the game_manager and act_manager properties
        monkeypatch.setattr(scene_manager, "game_manager", GameManager(session=db_session))
        monkeypatch.setattr(
            scene_manager, "act_manager", ActManager(session=db_session)
        )
        
        # Create a scene to be active
        scene = scene_manager.create_scene(
            title="Active Scene",
            description="Currently active",
            act_id=active_act.id,
        )

        active_scene = scene_manager.get_active_scene()
        assert active_scene is not None
        assert active_scene.id == scene.id
