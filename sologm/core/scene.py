"""Scene management functionality."""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.core.game import GameManager
from sologm.models.scene import Scene, SceneStatus
from sologm.utils.errors import SceneError

logger = logging.getLogger(__name__)


class SceneManager(BaseManager[Scene, Scene]):
    """Manages scene operations."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize the scene manager.

        Args:
            session: Optional SQLAlchemy session. If not provided,
                a new one will be created for each operation.
        """
        super().__init__(session)
        logger.debug("Initialized SceneManager")

    def create_scene(self, game_id: str, title: str, description: str) -> Scene:
        """Create a new scene in the specified game.

        Args:
            game_id: ID of the game to create the scene in.
            title: Title of the scene.
            description: Description of the scene.

        Returns:
            The created Scene object.

        Raises:
            SceneError: If there's an error creating the scene or if title is
                        not unique.
        """
        logger.debug(f"Creating new scene in game {game_id} with title '{title}'")

        def _create_scene(
            session: Session, game_id: str, title: str, description: str
        ) -> Scene:
            # Check for duplicate titles
            existing = (
                session.query(Scene)
                .filter(and_(Scene.game_id == game_id, Scene.title.ilike(title)))
                .first()
            )

            if existing:
                raise SceneError(
                    f"A scene with title '{title}' already exists in this game"
                )

            # Get the next sequence number
            max_sequence = (
                session.query(Scene.sequence)
                .filter(Scene.game_id == game_id)
                .order_by(desc(Scene.sequence))
                .first()
            )

            sequence = 1
            if max_sequence:
                sequence = max_sequence[0] + 1

            # Create new scene
            scene = Scene.create(
                game_id=game_id, title=title, description=description, sequence=sequence
            )

            # Deactivate all other scenes
            session.query(Scene).filter(
                and_(Scene.game_id == game_id, Scene.is_active)
            ).update({"is_active": False})

            # Set this scene as active
            scene.is_active = True

            session.add(scene)
            return scene

        return self._execute_db_operation(
            "create scene",
            _create_scene,
            game_id=game_id,
            title=title,
            description=description,
        )

    def list_scenes(self, game_id: str) -> List[Scene]:
        """List all scenes for the specified game.

        Args:
            game_id: ID of the game to list scenes for.

        Returns:
            List of Scene objects.

        Raises:
            SceneError: If there's an error listing the scenes.
        """
        logger.debug(f"Listing scenes for game {game_id}")

        def _list_scenes(session: Session, game_id: str) -> List[Scene]:
            return (
                session.query(Scene)
                .filter(Scene.game_id == game_id)
                .order_by(Scene.sequence)
                .all()
            )

        return self._execute_db_operation("list scenes", _list_scenes, game_id=game_id)

    def get_scene(self, game_id: str, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID.

        Args:
            game_id: ID of the game the scene belongs to.
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        logger.debug(f"Getting scene {scene_id} in game {game_id}")

        def _get_scene(
            session: Session, game_id: str, scene_id: str
        ) -> Optional[Scene]:
            return (
                session.query(Scene)
                .filter(and_(Scene.game_id == game_id, Scene.id == scene_id))
                .first()
            )

        return self._execute_db_operation(
            "get scene", _get_scene, game_id=game_id, scene_id=scene_id
        )

    def get_active_scene(self, game_id: str) -> Optional[Scene]:
        """Get the active scene for the specified game.

        Args:
            game_id: ID of the game to get the active scene for.

        Returns:
            Active Scene object if found, None otherwise.
        """
        logger.debug(f"Getting active scene for game {game_id}")

        def _get_active_scene(session: Session, game_id: str) -> Optional[Scene]:
            return (
                session.query(Scene)
                .filter(and_(Scene.game_id == game_id, Scene.is_active))
                .first()
            )

        return self._execute_db_operation(
            "get active scene", _get_active_scene, game_id=game_id
        )

    def complete_scene(self, game_id: str, scene_id: str) -> Scene:
        """Mark a scene as complete without changing which scene is current.

        Args:
            game_id: ID of the game the scene belongs to.
            scene_id: ID of the scene to complete.

        Returns:
            Updated Scene object.

        Raises:
            SceneError: If there's an error completing the scene.
        """
        logger.debug(f"Completing scene {scene_id} in game {game_id}")

        def _complete_scene(session: Session, game_id: str, scene_id: str) -> Scene:
            scene = (
                session.query(Scene)
                .filter(and_(Scene.game_id == game_id, Scene.id == scene_id))
                .first()
            )

            if not scene:
                raise SceneError(f"Scene {scene_id} not found in game {game_id}")

            if scene.status == SceneStatus.COMPLETED:
                raise SceneError(f"Scene {scene_id} is already completed")

            scene.status = SceneStatus.COMPLETED
            return scene

        return self._execute_db_operation(
            "complete scene", _complete_scene, game_id=game_id, scene_id=scene_id
        )

    def validate_active_context(self, game_manager: GameManager) -> Tuple[str, Scene]:
        """Validate active game and scene context.

        Args:
            game_manager: GameManager instance to check active game

        Returns:
            Tuple of (game_id, active_scene)

        Raises:
            SceneError: If no active game or scene
        """
        active_game = game_manager.get_active_game()
        if not active_game:
            raise SceneError("No active game. Use 'sologm game activate' to set one.")

        active_scene = self.get_active_scene(active_game.id)
        if not active_scene:
            raise SceneError("No active scene. Create one with 'sologm scene create'.")

        return active_game.id, active_scene

    def set_current_scene(self, game_id: str, scene_id: str) -> Scene:
        """Set which scene is currently being played without changing its status.

        Args:
            game_id: ID of the game the scene belongs to.
            scene_id: ID of the scene to make current.

        Returns:
            The Scene object that was made current.

        Raises:
            SceneError: If there's an error setting the current scene.
        """
        logger.debug(f"Setting scene {scene_id} as current in game {game_id}")

        def _set_current_scene(session: Session, game_id: str, scene_id: str) -> Scene:
            # Get the scene to make sure it exists
            scene = (
                session.query(Scene)
                .filter(and_(Scene.game_id == game_id, Scene.id == scene_id))
                .first()
            )

            if not scene:
                raise SceneError(f"Scene {scene_id} not found in game {game_id}")

            # Deactivate all scenes in this game
            session.query(Scene).filter(
                and_(Scene.game_id == game_id, Scene.is_active)
            ).update({"is_active": False})

            # Set this scene as active
            scene.is_active = True
            return scene

        return self._execute_db_operation(
            "set current scene", _set_current_scene, game_id=game_id, scene_id=scene_id
        )

    def get_previous_scene(self, game_id: str, current_scene: Scene) -> Optional[Scene]:
        """Get the scene that comes before the current scene in sequence.

        Args:
            game_id: ID of the game
            current_scene: Current scene to find the previous for

        Returns:
            Previous Scene object if found, None otherwise
        """
        logger.debug(f"Getting previous scene for {current_scene.id}")

        if current_scene.sequence <= 1:
            return None

        def _get_previous_scene(
            session: Session, game_id: str, sequence: int
        ) -> Optional[Scene]:
            return (
                session.query(Scene)
                .filter(and_(Scene.game_id == game_id, Scene.sequence == sequence - 1))
                .first()
            )

        return self._execute_db_operation(
            "get previous scene",
            _get_previous_scene,
            game_id=game_id,
            sequence=current_scene.sequence,
        )
