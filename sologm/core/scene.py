"""Scene management functionality."""

import logging
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.core.game import GameManager
from sologm.core.act import ActManager
from sologm.models.scene import Scene, SceneStatus
from sologm.models.act import Act
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

    def get_active_context(
        self, game_manager: Optional[GameManager] = None, act_manager: Optional[ActManager] = None
    ) -> Dict[str, Any]:
        """Get the active game, act, and scene context.

        Args:
            game_manager: Optional GameManager instance. If not provided, a new one will be created.
            act_manager: Optional ActManager instance. If not provided, a new one will be created.

        Returns:
            Dictionary containing 'game', 'act', and 'scene' keys with their respective objects.

        Raises:
            SceneError: If no active game, act, or scene is found.
        """
        if game_manager is None:
            game_manager = GameManager(self._session)
        
        active_game = game_manager.get_active_game()
        if not active_game:
            raise SceneError("No active game. Use 'sologm game activate' to set one.")

        if act_manager is None:
            act_manager = ActManager(self._session)

        active_act = act_manager.get_active_act(active_game.id)
        if not active_act:
            raise SceneError("No active act. Create one with 'sologm act create'.")

        active_scene = self.get_active_scene(active_act.id)
        if not active_scene:
            raise SceneError("No active scene. Add one with 'sologm scene add'.")

        return {
            "game": active_game,
            "act": active_act,
            "scene": active_scene
        }

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID.

        Args:
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        logger.debug(f"Getting scene {scene_id}")

        def _get_scene(session: Session, scene_id: str) -> Optional[Scene]:
            return session.query(Scene).filter(Scene.id == scene_id).first()

        return self._execute_db_operation("get scene", _get_scene, scene_id=scene_id)

    def get_scene_in_act(self, act_id: str, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID within a specific act.

        Args:
            act_id: ID of the act the scene belongs to.
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        logger.debug(f"Getting scene {scene_id} in act {act_id}")

        def _get_scene_in_act(session: Session, act_id: str, scene_id: str) -> Optional[Scene]:
            return (
                session.query(Scene)
                .filter(and_(Scene.act_id == act_id, Scene.id == scene_id))
                .first()
            )

        return self._execute_db_operation(
            "get scene in act", _get_scene_in_act, act_id=act_id, scene_id=scene_id
        )

    def get_active_scene(self, act_id: str) -> Optional[Scene]:
        """Get the active scene for the specified act.

        Args:
            act_id: ID of the act to get the active scene for.

        Returns:
            Active Scene object if found, None otherwise.
        """
        logger.debug(f"Getting active scene for act {act_id}")

        def _get_active_scene(session: Session, act_id: str) -> Optional[Scene]:
            return (
                session.query(Scene)
                .filter(and_(Scene.act_id == act_id, Scene.is_active))
                .first()
            )

        return self._execute_db_operation(
            "get active scene", _get_active_scene, act_id=act_id
        )

    def create_scene(self, act_id: str, title: str, description: str) -> Scene:
        """Create a new scene in the specified act.

        Args:
            act_id: ID of the act to create the scene in.
            title: Title of the scene.
            description: Description of the scene.

        Returns:
            The created Scene object.

        Raises:
            SceneError: If there's an error creating the scene or if title is
                        not unique.
        """
        logger.debug(f"Creating new scene in act {act_id} with title '{title}'")

        def _create_scene(
            session: Session, act_id: str, title: str, description: str
        ) -> Scene:
            # Check if act exists
            act = session.query(Act).filter(Act.id == act_id).first()
            if not act:
                raise SceneError(f"Act with ID '{act_id}' does not exist")

            # Check for duplicate titles
            existing = (
                session.query(Scene)
                .filter(and_(Scene.act_id == act_id, Scene.title.ilike(title)))
                .first()
            )

            if existing:
                raise SceneError(
                    f"A scene with title '{title}' already exists in this act"
                )

            # Get the next sequence number
            max_sequence = (
                session.query(Scene.sequence)
                .filter(Scene.act_id == act_id)
                .order_by(desc(Scene.sequence))
                .first()
            )

            sequence = 1
            if max_sequence:
                sequence = max_sequence[0] + 1

            # Create new scene
            scene = Scene.create(
                act_id=act_id, title=title, description=description, sequence=sequence
            )

            # Deactivate all other scenes
            session.query(Scene).filter(
                and_(Scene.act_id == act_id, Scene.is_active)
            ).update({"is_active": False})

            # Set this scene as active
            scene.is_active = True

            session.add(scene)
            return scene

        return self._execute_db_operation(
            "create scene",
            _create_scene,
            act_id=act_id,
            title=title,
            description=description,
        )

    def list_scenes(self, act_id: str) -> List[Scene]:
        """List all scenes for the specified act.

        Args:
            act_id: ID of the act to list scenes for.

        Returns:
            List of Scene objects.

        Raises:
            SceneError: If there's an error listing the scenes.
        """
        logger.debug(f"Listing scenes for act {act_id}")

        def _list_scenes(session: Session, act_id: str) -> List[Scene]:
            return (
                session.query(Scene)
                .filter(Scene.act_id == act_id)
                .order_by(Scene.sequence)
                .all()
            )

        return self._execute_db_operation("list scenes", _list_scenes, act_id=act_id)

    def complete_scene(self, scene_id: str) -> Scene:
        """Mark a scene as complete without changing which scene is current.

        Args:
            scene_id: ID of the scene to complete.

        Returns:
            Updated Scene object.

        Raises:
            SceneError: If there's an error completing the scene.
        """
        logger.debug(f"Completing scene {scene_id}")

        def _complete_scene(session: Session, scene_id: str) -> Scene:
            scene = session.query(Scene).filter(Scene.id == scene_id).first()

            if not scene:
                raise SceneError(f"Scene {scene_id} not found")

            if scene.status == SceneStatus.COMPLETED:
                raise SceneError(f"Scene {scene_id} is already completed")

            scene.status = SceneStatus.COMPLETED
            return scene

        return self._execute_db_operation(
            "complete scene", _complete_scene, scene_id=scene_id
        )

    def set_current_scene(self, scene_id: str) -> Scene:
        """Set which scene is currently being played without changing its status.

        Args:
            scene_id: ID of the scene to make current.

        Returns:
            The Scene object that was made current.

        Raises:
            SceneError: If there's an error setting the current scene.
        """
        logger.debug(f"Setting scene {scene_id} as current")

        def _set_current_scene(session: Session, scene_id: str) -> Scene:
            # Get the scene to make sure it exists
            scene = session.query(Scene).filter(Scene.id == scene_id).first()

            if not scene:
                raise SceneError(f"Scene {scene_id} not found")

            # Deactivate all scenes in this act
            session.query(Scene).filter(
                and_(Scene.act_id == scene.act_id, Scene.is_active)
            ).update({"is_active": False})

            # Set this scene as active
            scene.is_active = True
            return scene

        return self._execute_db_operation(
            "set current scene", _set_current_scene, scene_id=scene_id
        )

    def update_scene(self, scene_id: str, title: str, description: str) -> Scene:
        """Update a scene's title and description.

        Args:
            scene_id: ID of the scene to update
            title: New title for the scene
            description: New description for the scene

        Returns:
            The updated Scene object

        Raises:
            SceneError: If there's an error updating the scene
        """
        logger.debug(f"Updating scene {scene_id}")

        def _update_scene(
            session: Session, scene_id: str, title: str, description: str
        ) -> Scene:
            # Get the scene to make sure it exists
            scene = session.query(Scene).filter(Scene.id == scene_id).first()

            if not scene:
                raise SceneError(f"Scene {scene_id} not found")

            act_id = scene.act_id

            # Check for duplicate titles (only if title is changing)
            if scene.title != title:
                existing = (
                    session.query(Scene)
                    .filter(
                        and_(
                            Scene.act_id == act_id,
                            Scene.title.ilike(title),
                            Scene.id != scene_id,
                        )
                    )
                    .first()
                )

                if existing:
                    raise SceneError(
                        f"A scene with title '{title}' already exists in this act"
                    )

            # Update the scene
            scene.title = title
            scene.description = description
            session.add(scene)
            return scene

        return self._execute_db_operation(
            "update scene",
            _update_scene,
            scene_id=scene_id,
            title=title,
            description=description,
        )

    def get_previous_scene(self, scene: Scene) -> Optional[Scene]:
        """Get the scene that comes before the current scene in sequence.

        Args:
            scene: Current scene to find the previous for

        Returns:
            Previous Scene object if found, None otherwise
        """
        logger.debug(f"Getting previous scene for {scene.id}")

        if scene.sequence <= 1:
            return None

        def _get_previous_scene(
            session: Session, act_id: str, sequence: int
        ) -> Optional[Scene]:
            return (
                session.query(Scene)
                .filter(and_(Scene.act_id == act_id, Scene.sequence == sequence - 1))
                .first()
            )

        return self._execute_db_operation(
            "get previous scene",
            _get_previous_scene,
            act_id=scene.act_id,
            sequence=scene.sequence,
        )

    def validate_active_context(
        self, game_manager: GameManager, act_manager: ActManager = None
    ) -> Tuple[str, Scene]:
        """Validate active game, act, and scene context.

        Args:
            game_manager: GameManager instance to check active game
            act_manager: Optional ActManager instance. If not provided, a new one will be created.

        Returns:
            Tuple of (act_id, active_scene)

        Raises:
            SceneError: If no active game, act, or scene
        """
        context = self.get_active_context(game_manager, act_manager)
        return context["act"].id, context["scene"]
