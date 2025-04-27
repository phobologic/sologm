"""Tests for the scene management functionality."""

from typing import Callable

import pytest
from sqlalchemy.orm import Session

from sologm.core.factory import create_all_managers
from sologm.database.session import SessionContext
from sologm.models.act import Act
from sologm.models.game import Game
from sologm.models.scene import Scene, SceneStatus
from sologm.utils.errors import SceneError


# Helper function to create base test data within a session context
def create_base_test_data(
    session: Session,
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    game_active: bool = True,
    act_active: bool = True,
) -> tuple[Game, Act]:
    """Creates a standard game and act for testing."""
    game = create_test_game(session, is_active=game_active)
    act = create_test_act(session, game_id=game.id, is_active=act_active)
    return game, act


class TestScene:
    """Tests for the Scene model."""

    def test_scene_creation(self, session_context: SessionContext) -> None:
        """Test creating a Scene object."""
        with session_context as session:
            scene = Scene.create(
                act_id="test-act",
                title="Test Scene",
                description="A test scene",
                sequence=1,
            )
            session.add(scene)
            # No commit needed, context manager handles it

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

    def test_create_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test creating a new scene."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            scene = managers.scene.create_scene(
                title="First Scene",
                description="The beginning",
                act_id=act.id,
            )

            assert scene.id is not None
            assert scene.act_id == act.id
            assert scene.title == "First Scene"
            assert scene.description == "The beginning"
            assert scene.status == SceneStatus.ACTIVE
            assert scene.sequence == 1
            assert scene.is_active

            # Verify scene was saved to database
            db_scene = session.get(Scene, scene.id)
            assert db_scene is not None
            assert db_scene.title == "First Scene"

    def test_create_scene_duplicate_title(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test creating a scene with a duplicate title fails."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Create first scene
            managers.scene.create_scene(
                title="First Scene",
                description="The beginning",
                act_id=act.id,
            )

            # Try to create another scene with same title
            with pytest.raises(
                SceneError,
                match="A scene with title 'First Scene' already exists in this act",
            ):
                managers.scene.create_scene(
                    title="First Scene",
                    description="Another beginning",
                    act_id=act.id,
                )

    def test_create_scene_duplicate_title_different_case(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test creating a scene with a duplicate title in different case fails."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Create first scene
            managers.scene.create_scene(
                title="Forest Path",
                description="A dark forest trail",
                act_id=act.id,
            )

            # Try to create another scene with same title in different case
            with pytest.raises(
                SceneError,
                match="A scene with title 'FOREST PATH' already exists in this act",
            ):
                managers.scene.create_scene(
                    title="FOREST PATH",
                    description="Another forest trail",
                    act_id=act.id,
                )

    def test_create_scene_nonexistent_act(
        self, session_context: SessionContext
    ) -> None:
        """Test creating a scene in a nonexistent act."""
        with session_context as session:
            managers = create_all_managers(session)
            # This will now fail with a SQLAlchemy foreign key constraint error
            # which gets wrapped in a SceneError
            with pytest.raises(SceneError):
                managers.scene.create_scene(
                    title="Test Scene",
                    description="Test Description",
                    act_id="nonexistent-act",
                )

    def test_list_scenes(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test listing scenes in an act."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Create some test scenes using the factory
            scene1 = create_test_scene(session, act_id=act.id, title="First Scene")
            scene2 = create_test_scene(session, act_id=act.id, title="Second Scene")

            scenes = managers.scene.list_scenes(act.id)
            assert len(scenes) == 2
            assert scenes[0].id == scene1.id
            assert scenes[1].id == scene2.id
            assert scenes[0].sequence < scenes[1].sequence

    def test_list_scenes_empty(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test listing scenes in an act with no scenes."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            scenes = managers.scene.list_scenes(act.id)
            assert len(scenes) == 0

    def test_get_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test getting a specific scene."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            created_scene = create_test_scene(
                session, act_id=act.id, title="Test Scene"
            )

            retrieved_scene = managers.scene.get_scene(created_scene.id)
            assert retrieved_scene is not None
            assert retrieved_scene.id == created_scene.id
            assert retrieved_scene.title == created_scene.title

    def test_get_scene_nonexistent(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test getting a nonexistent scene."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create base data to ensure active context exists if needed
            create_base_test_data(session, create_test_game, create_test_act)

            scene = managers.scene.get_scene("nonexistent-scene")
            assert scene is None

    def test_get_active_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test getting the active scene."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create scene using factory (which makes it active by default)
            scene = create_test_scene(
                session, act_id=act.id, title="Active Scene"
            )

            active_scene = managers.scene.get_active_scene(act.id)
            assert active_scene is not None
            assert active_scene.id == scene.id

    def test_get_active_scene_none(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test getting active scene when none is set."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create a scene but ensure it's not active
            create_test_scene(
                session, act_id=act.id, title="Inactive Scene", is_active=False
            )

            # Make sure no scenes are active (redundant if factory works, but safe)
            session.query(Scene).filter(Scene.act_id == act.id).update(
                {"is_active": False}
            )

            active_scene = managers.scene.get_active_scene(act.id)
            assert active_scene is None

    def test_complete_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test completing a scene without changing current scene."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            scene1 = create_test_scene(session, act_id=act.id, title="First Scene")
            scene2 = create_test_scene(session, act_id=act.id, title="Second Scene")

            # Complete scene1 and verify it doesn't change current scene
            completed_scene = managers.scene.complete_scene(scene1.id)
            assert completed_scene.status == SceneStatus.COMPLETED

            current_scene = managers.scene.get_active_scene(act.id)
            assert (
                current_scene.id == scene2.id
            )  # Should still be scene2 as it was made current on creation

    def test_complete_scene_nonexistent(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test completing a nonexistent scene."""
        with session_context as session:
            managers = create_all_managers(session)
            # Create base data to ensure active context exists if needed
            create_base_test_data(session, create_test_game, create_test_act)
            with pytest.raises(SceneError, match="Scene nonexistent-scene not found"):
                managers.scene.complete_scene("nonexistent-scene")

    def test_complete_scene_already_completed(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test completing an already completed scene."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            scene = create_test_scene(
                session, act_id=act.id, title="Test Scene"
            )

            managers.scene.complete_scene(scene.id)

            with pytest.raises(
                SceneError, match=f"Scene {scene.id} is already completed"
            ):
                managers.scene.complete_scene(scene.id)

    def test_set_current_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test setting which scene is current without changing status."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create two scenes
            scene1 = create_test_scene(session, act_id=act.id, title="First Scene")
            scene2 = create_test_scene(session, act_id=act.id, title="Second Scene")

            # Complete both scenes
            managers.scene.complete_scene(scene1.id)
            managers.scene.complete_scene(scene2.id)

            # Make scene1 current (scene2 is currently active)
            managers.scene.set_current_scene(scene1.id)

            current_scene = managers.scene.get_active_scene(act.id)
            assert current_scene.id == scene1.id
            # Status should be completed
            assert current_scene.status == SceneStatus.COMPLETED

    def test_scene_sequence_management(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ):
        """Test that scene sequences are managed correctly."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create multiple scenes
            scene1 = create_test_scene(session, act_id=act.id, title="First Scene")
            scene2 = create_test_scene(session, act_id=act.id, title="Second Scene")
            scene3 = create_test_scene(session, act_id=act.id, title="Third Scene")

            # Verify sequences
            assert scene1.sequence == 1
            assert scene2.sequence == 2
            assert scene3.sequence == 3

            # Test get_previous_scene with scene_id
            prev_scene = managers.scene.get_previous_scene(scene_id=scene3.id)
            assert prev_scene.id == scene2.id

            # Test get_previous_scene for first scene
            prev_scene = managers.scene.get_previous_scene(scene_id=scene1.id)
            assert prev_scene is None

            # Test get_previous_scene with invalid scene_id
            prev_scene = managers.scene.get_previous_scene(scene_id="nonexistent-id")
            assert prev_scene is None

    def test_update_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test updating a scene's title and description."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create a test scene
            scene = create_test_scene(
                session,
                act_id=act.id,
                title="Original Title",
                description="Original description",
            )

            # Update the scene
            updated_scene = managers.scene.update_scene(
                scene_id=scene.id,
                title="Updated Title",
                description="Updated description",
            )

            # Verify the scene was updated
            assert updated_scene.id == scene.id
            assert updated_scene.title == "Updated Title"
            assert updated_scene.description == "Updated description"

            # Verify the scene was updated in the database
            retrieved_scene = managers.scene.get_scene(scene.id)
            assert retrieved_scene.title == "Updated Title"
            assert retrieved_scene.description == "Updated description"

            # Test updating only title
            updated_scene = managers.scene.update_scene(
                scene_id=scene.id,
                title="Only Title Updated",
            )
            assert updated_scene.title == "Only Title Updated"
            assert updated_scene.description == "Updated description"

            # Test updating only description
            updated_scene = managers.scene.update_scene(
                scene_id=scene.id,
                description="Only description updated",
            )
            assert updated_scene.title == "Only Title Updated"
            assert updated_scene.description == "Only description updated"

    def test_update_scene_duplicate_title(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test updating a scene with a duplicate title fails."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create two scenes
            scene1 = create_test_scene(session, act_id=act.id, title="First Scene")
            scene2 = create_test_scene(session, act_id=act.id, title="Second Scene")

            # Try to update scene2 with scene1's title
            with pytest.raises(
                SceneError,
                match="A scene with title 'First Scene' already exists in this act",
            ):
                managers.scene.update_scene(
                    scene_id=scene2.id,
                    title="First Scene",
                )

    def test_get_active_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ):
        """Test getting active game, act, and scene context."""
        with session_context as session:
            managers = create_all_managers(session)
            game, act = create_base_test_data(
                session, create_test_game, create_test_act
            )
            # Create a scene to be active
            scene = create_test_scene(
                session, act_id=act.id, title="Active Scene"
            )

            context = managers.scene.get_active_context()
            assert context["game"].id == game.id
            assert context["act"].id == act.id
            assert context["scene"].id == scene.id

    def test_validate_active_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ):
        """Test validating active game and scene context."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(
                session, create_test_game, create_test_act
            )
            # Create a scene to be active
            scene = create_test_scene(
                session, act_id=act.id, title="Active Scene"
            )

            act_id, active_scene = managers.scene.validate_active_context()
            assert act_id == act.id
            assert active_scene.id == scene.id

    def test_get_scene_in_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test getting a specific scene within an act."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            created_scene = create_test_scene(
                session, act_id=act.id, title="Test Scene"
            )

            retrieved_scene = managers.scene.get_scene_in_act(
                act.id, created_scene.id
            )
            assert retrieved_scene is not None
            assert retrieved_scene.id == created_scene.id
            assert retrieved_scene.title == created_scene.title

            # Test with wrong act_id
            wrong_scene = managers.scene.get_scene_in_act(
                "wrong-act-id", created_scene.id
            )
            assert wrong_scene is None

    def test_validate_active_context_no_game(
        self, session_context: SessionContext
    ):
        """Test validation with no active game."""
        with session_context as session:
            managers = create_all_managers(session)
            # Deactivate all games
            session.query(Game).update({Game.is_active: False})

            with pytest.raises(SceneError) as exc:
                managers.scene.validate_active_context()
            assert "No active game" in str(exc.value)

    def test_session_propagation(self, session_context: SessionContext):
        """Test that the session is properly propagated to lazy-initialized managers."""
        with session_context as session:
            managers = create_all_managers(session)
            # Access lazy-initialized managers via the factory namespace
            scene_manager = managers.scene
            event_manager = managers.event
            dice_manager = managers.dice
            oracle_manager = managers.oracle
            act_manager = managers.act
            game_manager = managers.game

            # Verify they all have the same session ID
            session_id = id(session)
            assert id(scene_manager._session) == session_id
            assert id(event_manager._session) == session_id
            assert id(dice_manager._session) == session_id
            assert id(oracle_manager._session) == session_id
            assert id(act_manager._session) == session_id
            assert id(game_manager._session) == session_id

    def test_create_scene_with_active_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test creating a scene using the active act."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            scene = managers.scene.create_scene(
                title="Active Act Scene",
                description="Scene in active act",
                # act_id is omitted, should use active act
            )

            assert scene.id is not None
            assert scene.act_id == act.id
            assert scene.title == "Active Act Scene"
            assert scene.description == "Scene in active act"
            assert scene.is_active

    def test_list_scenes_with_active_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test listing scenes using the active act."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Create some test scenes
            scene1 = create_test_scene(session, act_id=act.id, title="First Scene")
            scene2 = create_test_scene(session, act_id=act.id, title="Second Scene")

            scenes = managers.scene.list_scenes()  # act_id is omitted
            assert len(scenes) == 2
            assert scenes[0].id == scene1.id
            assert scenes[1].id == scene2.id
            assert scenes[0].sequence < scenes[1].sequence

    def test_get_active_scene_without_act_id(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test getting the active scene without providing an act_id."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(
                session, create_test_game, create_test_act
            )
            # Create a scene to be active
            scene = create_test_scene(
                session, act_id=act.id, title="Active Scene"
            )

            active_scene = managers.scene.get_active_scene()  # act_id is omitted
            assert active_scene is not None
            assert active_scene.id == scene.id

    def test_create_scene_with_make_active_false(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test creating a scene without making it active."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Create a first scene that will be active
            scene1 = create_test_scene(
                session, act_id=act.id, title="First Scene"
            )

            # Create a second scene without making it active
            scene2 = create_test_scene(
                session,
                act_id=act.id,
                title="Second Scene",
                make_active=False,
            )

            # Verify scene1 is still active
            active_scene = managers.scene.get_active_scene(act.id)
            assert active_scene.id == scene1.id

            # Verify scene2 is not active
            assert not scene2.is_active

    def test_scene_relationships(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
    ):
        """Test that scene relationships are properly loaded."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(
                session, create_test_game, create_test_act
            )
            # Create a scene with events
            scene = create_test_scene(
                session, act_id=act.id, title="Scene with Events"
            )

            # Add events to the scene using the factory
            event = create_test_event(
                session, scene_id=scene.id, description="Test event"
            )

            # Refresh the scene to load relationships (might be needed depending on session state)
            session.refresh(scene, attribute_names=["events"])

            # Verify relationships
            assert hasattr(scene, "events")
            assert len(scene.events) > 0
            assert scene.events[0].id == event.id

    def test_get_act_id_or_active(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test the _get_act_id_or_active helper method."""
        with session_context as session:
            managers = create_all_managers(session)
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Test with provided act_id
            act_id_provided = managers.scene._get_act_id_or_active("test-act-id")
            assert act_id_provided == "test-act-id"

            # Test with no act_id (should use active act)
            act_id_active = managers.scene._get_act_id_or_active(None)
            assert act_id_active == act.id
