"""Tests for the scene management functionality."""

from typing import TYPE_CHECKING, Callable

import pytest
from sqlalchemy.orm import Session

import uuid  # Added for dummy IDs

from sologm.core.factory import create_all_managers
from sologm.database.session import SessionContext
from sologm.models.act import Act
from sologm.models.game import Game
from sologm.models.scene import Scene
from sologm.models.utils import slugify  # Import slugify
from sologm.utils.errors import ActError, SceneError

# Type checking imports
if TYPE_CHECKING:
    from sologm.core.managers import AllManagers


# Helper function to create base test data within a session context
def create_base_test_data(
    session: Session,  # Added session parameter
    create_test_game: Callable[..., Game],
    create_test_act: Callable[..., Act],
    game_active: bool = True,
    act_active: bool = True,
) -> tuple[Game, Act]:
    """Creates a standard game and act for testing.

    Args:
        session: The active SQLAlchemy session for the test.
        create_test_game: Factory fixture for creating games.
        create_test_act: Factory fixture for creating acts.
        game_active: Whether the created game should be active.
        act_active: Whether the created act should be active.

    Returns:
        A tuple containing the created Game and Act objects.
    """
    # Pass session to factory fixtures
    game = create_test_game(session=session, is_active=game_active)
    act = create_test_act(session=session, game_id=game.id, is_active=act_active)
    return game, act


class TestScene:
    """Tests for the Scene model's direct methods (like create)."""

    def test_scene_creation(self, session_context: SessionContext) -> None:
        """Test creating a Scene object using its class method.

        Note: This tests the model's create method directly, not the manager.
        It does not set the scene as active.
        """
        with session_context as session:
            # Create prerequisite Game and Act records to satisfy FK constraints
            dummy_game_id = str(uuid.uuid4())
            dummy_act_id = "test-act"  # Use the ID needed by the scene
            dummy_game_name = "Dummy Game"

            # Provide a slug for the dummy game
            dummy_game = Game(
                id=dummy_game_id,
                name=dummy_game_name,
                slug=slugify(dummy_game_name),  # Generate slug
                description="...",
            )
            session.add(dummy_game)

            # Act needs game_id and sequence
            dummy_act = Act(
                id=dummy_act_id,
                game_id=dummy_game_id,
                title="Dummy Act",
                sequence=1,
                slug=f"act-1-dummy-act",  # Generate a slug
            )
            session.add(dummy_act)
            # Flush prerequisites before creating the scene that depends on them
            session.flush()

            # Use Scene.create directly
            scene = Scene.create(
                act_id=dummy_act_id,  # Use the ID of the created dummy act
                title="Test Scene",
                description="A test scene",
                sequence=1,
            )
            # Manually add to session for testing persistence
            session.add(scene)
            session.flush()  # Ensure DB defaults like created_at are populated

            assert scene.id is not None
            assert scene.act_id == "test-act"
            assert scene.title == "Test Scene"
            assert scene.description == "A test scene"
            # Status was removed, no assertion here
            assert scene.sequence == 1
            assert not scene.is_active  # is_active defaults to False in model
            assert scene.created_at is not None
            assert scene.modified_at is not None


class TestSceneManager:
    """Tests for the SceneManager class."""

    def test_create_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test creating a new scene using the manager (makes active by default)."""
        with session_context as session:
            initialize_event_sources(session)  # Initialize sources within the session
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            scene = managers.scene.create_scene(
                title="First Scene",
                description="The beginning",
                act_id=act.id,
                # make_active=True is the default
            )

            assert scene.id is not None
            assert scene.act_id == act.id
            assert scene.title == "First Scene"
            assert scene.description == "The beginning"
            # Status was removed
            assert scene.sequence == 1
            assert scene.is_active  # Should be active by default

            # Verify scene was saved to database and is active
            db_scene = session.get(Scene, scene.id)
            assert db_scene is not None
            assert db_scene.title == "First Scene"
            assert db_scene.is_active

    def test_create_scene_duplicate_title(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test creating a scene with a duplicate title fails."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
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
        initialize_event_sources: Callable,
    ) -> None:
        """Test creating a scene with a duplicate title in different case fails."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
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
        self, session_context: SessionContext, initialize_event_sources: Callable
    ) -> None:
        """Test creating a scene in a nonexistent act raises ActError."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Attempting to create a scene with an invalid act_id
            # The manager checks if the act exists before creating the scene.
            # This check is done via ActManager, which raises ActError.
            with pytest.raises(
                ActError, match="Act with ID 'nonexistent-act' does not exist"
            ):
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
        initialize_event_sources: Callable,
    ) -> None:
        """Test listing scenes in an act."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Create some test scenes using the manager
            scene1 = managers.scene.create_scene(
                act_id=act.id, title="First Scene", description="Test Description"
            )
            scene2 = managers.scene.create_scene(
                act_id=act.id, title="Second Scene", description="Test Description"
            )

            scenes = managers.scene.list_scenes(act.id)
            assert len(scenes) == 2
            # Scenes should be ordered by sequence
            assert scenes[0].id == scene1.id
            assert scenes[1].id == scene2.id
            assert scenes[0].sequence < scenes[1].sequence

    def test_list_scenes_empty(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test listing scenes in an act with no scenes."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            scenes = managers.scene.list_scenes(act.id)
            assert len(scenes) == 0

    def test_get_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting a specific scene by ID."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create scene using manager
            created_scene = managers.scene.create_scene(
                act_id=act.id, title="Test Scene", description="Test Description"
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
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting a nonexistent scene returns None."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Create base data to ensure active context exists if needed by manager
            # Pass session to helper
            create_base_test_data(session, create_test_game, create_test_act)

            scene = managers.scene.get_scene("nonexistent-scene")
            assert scene is None

    def test_get_active_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting the active scene for an act."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create scene using manager (makes it active)
            scene = managers.scene.create_scene(
                act_id=act.id, title="Active Scene", description="Test Description"
            )

            active_scene = managers.scene.get_active_scene(act.id)
            assert active_scene is not None
            assert active_scene.id == scene.id
            assert active_scene.is_active

    def test_get_active_scene_none(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting active scene when none is set."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create a scene but ensure it's not active using the manager
            managers.scene.create_scene(
                act_id=act.id,
                title="Inactive Scene",
                description="Test Description",
                make_active=False,
            )

            active_scene = managers.scene.get_active_scene(act.id)
            assert active_scene is None

    # --- Removed tests for non-existent complete_scene method ---
    # test_complete_scene
    # test_complete_scene_nonexistent
    # test_complete_scene_already_completed
    # --- End removal ---

    def test_set_current_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test setting which scene is current (active)."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create two scenes using the manager
            # Scene1 is created first, then Scene2 becomes active by default.
            scene1 = managers.scene.create_scene(
                act_id=act.id, title="First Scene", description="Test Description"
            )
            scene2 = managers.scene.create_scene(
                act_id=act.id, title="Second Scene", description="Test Description"
            )

            # Verify scene2 is initially active
            initial_active = managers.scene.get_active_scene(act.id)
            assert initial_active is not None
            assert initial_active.id == scene2.id

            # Make scene1 current
            managers.scene.set_current_scene(scene1.id)

            # Refresh objects to get updated state from DB
            session.refresh(scene1)
            session.refresh(scene2)

            # Verify scene1 is now active
            current_scene = managers.scene.get_active_scene(act.id)
            assert current_scene is not None
            assert current_scene.id == scene1.id
            assert scene1.is_active
            assert not scene2.is_active  # Verify scene2 was deactivated

    def test_scene_sequence_management(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ):
        """Test that scene sequences are managed correctly and previous scene works."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create multiple scenes using the manager
            scene1 = managers.scene.create_scene(
                act_id=act.id, title="First Scene", description="Test Description"
            )
            scene2 = managers.scene.create_scene(
                act_id=act.id, title="Second Scene", description="Test Description"
            )
            scene3 = managers.scene.create_scene(
                act_id=act.id, title="Third Scene", description="Test Description"
            )

            # Verify sequences (fetch from DB to be sure)
            db_scene1 = session.get(Scene, scene1.id)
            db_scene2 = session.get(Scene, scene2.id)
            db_scene3 = session.get(Scene, scene3.id)
            assert db_scene1.sequence == 1
            assert db_scene2.sequence == 2
            assert db_scene3.sequence == 3

            # Test get_previous_scene with scene_id
            prev_scene = managers.scene.get_previous_scene(scene_id=scene3.id)
            assert prev_scene is not None
            assert prev_scene.id == scene2.id

            # Test get_previous_scene for first scene
            prev_scene = managers.scene.get_previous_scene(scene_id=scene1.id)
            assert prev_scene is None

            # Test get_previous_scene with invalid scene_id returns None
            # (get_scene inside get_previous_scene handles this)
            prev_scene = managers.scene.get_previous_scene(scene_id="nonexistent-id")
            assert prev_scene is None

    def test_update_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test updating a scene's title and description."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create a test scene using the manager
            scene = managers.scene.create_scene(
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

            # Verify the returned scene object was updated
            assert updated_scene.id == scene.id
            assert updated_scene.title == "Updated Title"
            assert updated_scene.description == "Updated description"

            # Verify the scene was updated in the database
            retrieved_scene = managers.scene.get_scene(scene.id)
            assert retrieved_scene is not None
            assert retrieved_scene.title == "Updated Title"
            assert retrieved_scene.description == "Updated description"

            # Test updating only title
            updated_scene_title = managers.scene.update_scene(
                scene_id=scene.id,
                title="Only Title Updated",
            )
            assert updated_scene_title.title == "Only Title Updated"
            # Description should remain from previous update
            assert updated_scene_title.description == "Updated description"

            # Test updating only description
            updated_scene_desc = managers.scene.update_scene(
                scene_id=scene.id,
                description="Only description updated",
            )
            # Title should remain from previous update
            assert updated_scene_desc.title == "Only Title Updated"
            assert updated_scene_desc.description == "Only description updated"

    def test_update_scene_duplicate_title(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test updating a scene with a duplicate title fails."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create two scenes
            managers.scene.create_scene(  # scene1 is unused
                act_id=act.id, title="First Scene", description="Test Description"
            )
            scene2 = managers.scene.create_scene(
                act_id=act.id, title="Second Scene", description="Test Description"
            )

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
        initialize_event_sources: Callable,
    ):
        """Test getting active game, act, and scene context."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            game, act = create_base_test_data(
                session, create_test_game, create_test_act
            )
            # Create a scene to be active using the manager
            scene = managers.scene.create_scene(
                act_id=act.id, title="Active Scene", description="Test Description"
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
        initialize_event_sources: Callable,
    ):
        """Test validating active game, act and scene context."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create a scene to be active using the manager
            scene = managers.scene.create_scene(
                act_id=act.id, title="Active Scene", description="Test Description"
            )

            act_id, active_scene = managers.scene.validate_active_context()
            assert act_id == act.id
            assert active_scene.id == scene.id

    def test_get_scene_in_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting a specific scene within a specific act."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create scene using manager
            created_scene = managers.scene.create_scene(
                act_id=act.id, title="Test Scene", description="Test Description"
            )

            retrieved_scene = managers.scene.get_scene_in_act(act.id, created_scene.id)
            assert retrieved_scene is not None
            assert retrieved_scene.id == created_scene.id
            assert retrieved_scene.title == created_scene.title

            # Test with wrong act_id returns None
            wrong_scene = managers.scene.get_scene_in_act(
                "wrong-act-id", created_scene.id
            )
            assert wrong_scene is None

            # Test with wrong scene_id returns None
            wrong_scene = managers.scene.get_scene_in_act(act.id, "wrong-scene-id")
            assert wrong_scene is None

    def test_validate_active_context_no_game(
        self, session_context: SessionContext, initialize_event_sources: Callable
    ):
        """Test validation raises SceneError with no active game."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Ensure no games are active
            session.query(Game).update({"is_active": False})

            with pytest.raises(SceneError, match="No active game"):
                managers.scene.validate_active_context()

    def test_validate_active_context_no_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        initialize_event_sources: Callable,
    ):
        """Test validation raises SceneError with no active act."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Create an active game, but no acts (or ensure acts are inactive)
            # Pass session to factory
            create_test_game(session=session, is_active=True)
            session.query(Act).update({"is_active": False})

            with pytest.raises(SceneError, match="No active act"):
                managers.scene.validate_active_context()

    def test_validate_active_context_no_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ):
        """Test validation raises SceneError with no active scene."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Create active game and act, but ensure no scenes are active
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            session.query(Scene).filter(Scene.act_id == act.id).update(
                {"is_active": False}
            )

            with pytest.raises(SceneError, match="No active scene"):
                managers.scene.validate_active_context()

    def test_session_propagation(
        self, session_context: SessionContext, initialize_event_sources: Callable
    ):
        """Test that the session is properly propagated to lazy-initialized managers."""
        with session_context as session:
            initialize_event_sources(session)
            # Use the factory which initializes all managers with the same session
            managers: "AllManagers" = create_all_managers(session)

            # Access managers via the factory namespace
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

            # Also check managers accessed via properties
            assert id(scene_manager.act_manager._session) == session_id
            assert id(scene_manager.game_manager._session) == session_id
            assert id(scene_manager.oracle_manager._session) == session_id
            assert id(scene_manager.event_manager._session) == session_id
            assert id(scene_manager.dice_manager._session) == session_id

    def test_create_scene_with_active_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test creating a scene using the active act (act_id omitted)."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            scene = managers.scene.create_scene(
                title="Active Act Scene",
                description="Scene in active act",
                # act_id is omitted, should use active act from context
            )

            assert scene.id is not None
            assert scene.act_id == act.id
            assert scene.title == "Active Act Scene"
            assert scene.description == "Scene in active act"
            assert scene.is_active  # Should be active by default

    def test_list_scenes_with_active_act(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test listing scenes using the active act (act_id omitted)."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Create some test scenes using the manager
            scene1 = managers.scene.create_scene(
                act_id=act.id, title="First Scene", description="Test Description"
            )
            scene2 = managers.scene.create_scene(
                act_id=act.id, title="Second Scene", description="Test Description"
            )

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
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting the active scene without providing an act_id."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create a scene to be active using the manager
            scene = managers.scene.create_scene(
                act_id=act.id, title="Active Scene", description="Test Description"
            )

            active_scene = managers.scene.get_active_scene()  # act_id is omitted
            assert active_scene is not None
            assert active_scene.id == scene.id

    def test_create_scene_with_make_active_false(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test creating a scene with make_active=False."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Create a first scene that will be active
            scene1 = managers.scene.create_scene(
                act_id=act.id, title="First Scene", description="Test Description"
            )

            # Create a second scene without making it active
            scene2 = managers.scene.create_scene(
                act_id=act.id,
                title="Second Scene",
                description="Test Description",
                make_active=False,  # Explicitly set make_active to False
            )

            # Verify scene1 is still active
            active_scene = managers.scene.get_active_scene(act.id)
            assert active_scene is not None
            assert active_scene.id == scene1.id

            # Verify scene2 is not active (fetch from DB to be sure)
            db_scene2 = session.get(Scene, scene2.id)
            assert db_scene2 is not None
            assert not db_scene2.is_active

    def test_scene_relationships(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        # create_test_scene: Callable, # Not used directly
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ):
        """Test that scene relationships (like events) can be accessed.

        Note: This primarily tests SQLAlchemy relationship configuration.
        """
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create a scene using the manager
            scene = managers.scene.create_scene(
                act_id=act.id, title="Scene with Events", description="Test Description"
            )

            # Add events to the scene using the event factory, passing the session
            event = create_test_event(
                session=session, scene_id=scene.id, description="Test event"
            )

            # Refresh the scene to load relationships
            # (essential after adding related items)
            session.refresh(scene, attribute_names=["events"])

            # Verify relationships
            assert hasattr(scene, "events")
            assert len(scene.events) == 1
            assert scene.events[0].id == event.id
            assert scene.events[0].description == "Test event"

    def test_get_act_id_or_active(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test the internal _get_act_id_or_active helper method."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Test with provided act_id
            act_id_provided = managers.scene._get_act_id_or_active("test-act-id")
            assert act_id_provided == "test-act-id"

            # Test with no act_id (should use active act)
            act_id_active = managers.scene._get_act_id_or_active(None)
            assert act_id_active == act.id

            # Test raises error if no active game/act
            session.query(Act).update({"is_active": False})
            session.query(Game).update({"is_active": False})
            with pytest.raises(SceneError, match="No active game"):
                managers.scene._get_act_id_or_active(None)

    # --- New Tests for Added Manager Methods ---

    def test_get_scene_by_identifier(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting a scene by ID or slug."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create scene using manager
            scene = managers.scene.create_scene(
                act_id=act.id, title="Find Me", description="Test Description"
            )

            # Find by ID
            found_by_id = managers.scene.get_scene_by_identifier(scene.id)
            assert found_by_id is not None
            assert found_by_id.id == scene.id

            # Find by slug
            found_by_slug = managers.scene.get_scene_by_identifier(scene.slug)
            assert found_by_slug is not None
            assert found_by_slug.id == scene.id

            # Test not found
            not_found = managers.scene.get_scene_by_identifier("nonexistent-slug")
            assert not_found is None

    def test_get_scene_by_identifier_or_error(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting a scene by ID/slug or raising an error."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)
            # Create scene using manager
            scene = managers.scene.create_scene(
                act_id=act.id, title="Find Me Or Error", description="Test Description"
            )

            # Find by ID (should succeed)
            found_by_id = managers.scene.get_scene_by_identifier_or_error(scene.id)
            assert found_by_id.id == scene.id

            # Find by slug (should succeed)
            found_by_slug = managers.scene.get_scene_by_identifier_or_error(scene.slug)
            assert found_by_slug.id == scene.id

            # Test raises error when not found
            with pytest.raises(
                SceneError, match="Scene not found with identifier 'bad-identifier'"
            ):
                managers.scene.get_scene_by_identifier_or_error("bad-identifier")

    def test_get_most_recent_scene(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test getting the most recent scene (highest sequence) in an act."""
        with session_context as session:
            initialize_event_sources(session)
            managers: "AllManagers" = create_all_managers(session)
            # Pass session to helper
            _, act = create_base_test_data(session, create_test_game, create_test_act)

            # Test with no scenes
            most_recent = managers.scene.get_most_recent_scene(act.id)
            assert most_recent is None

            # Create scenes using the manager
            managers.scene.create_scene(  # scene1 is unused
                act_id=act.id, title="Scene One", description="Test Description"
            )
            managers.scene.create_scene(  # scene2 is unused
                act_id=act.id, title="Scene Two", description="Test Description"
            )
            scene3 = managers.scene.create_scene(
                act_id=act.id, title="Scene Three", description="Test Description"
            )

            # Get most recent
            most_recent = managers.scene.get_most_recent_scene(act.id)
            assert most_recent is not None
            assert most_recent.id == scene3.id
            assert most_recent.sequence == 3

            # Test with a different act that has no scenes
            # Deactivate the first act before creating the second one in the same game
            act.is_active = False
            # The 'act' object is managed by this session now.
            session.flush()  # Persist change before the next create call

            # Create the second act using the factory, passing the session
            act2 = create_test_act(
                session=session, game_id=act.game_id, title="Act Two"
            )
            most_recent_act2 = managers.scene.get_most_recent_scene(act2.id)
            assert most_recent_act2 is None
