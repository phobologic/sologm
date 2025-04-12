"""Scene management functionality."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from sologm.core.act import ActManager
from sologm.core.base_manager import BaseManager
from sologm.core.game import GameManager
from sologm.models.act import Act
from sologm.models.scene import Scene, SceneStatus
from sologm.utils.errors import SceneError

if TYPE_CHECKING:
    from sologm.core.dice import DiceManager
    from sologm.core.event import EventManager
    from sologm.core.oracle import OracleManager


logger = logging.getLogger(__name__)


class SceneManager(BaseManager[Scene, Scene]):
    """Manages scene operations."""

    def __init__(
        self,
        act_manager: Optional[ActManager] = None,
        session: Optional[Session] = None,
    ):
        """Initialize the scene manager.

        Args:
            act_manager: Optional ActManager instance. If not provided,
                a new one will be lazy-initialized when needed.
            session: Optional SQLAlchemy session. If not provided,
                a new one will be created for each operation.
        """
        super().__init__(session)
        self._act_manager: Optional["ActManager"] = act_manager
        self._dice_manager: Optional["DiceManager"] = None
        self._event_manager: Optional["EventManager"] = None
        self._oracle_manager: Optional["OracleManager"] = None
        logger.debug("Initialized SceneManager")

    @property
    def act_manager(self) -> ActManager:
        """Lazy-initialize act manager if not provided."""
        return self._lazy_init_manager("_act_manager", "sologm.core.act.ActManager")

    @property
    def game_manager(self) -> GameManager:
        """Access game manager through act manager."""
        return self.act_manager.game_manager

    @property
    def oracle_manager(self) -> "OracleManager":
        """Lazy-initialize oracle manager."""
        return self._lazy_init_manager(
            "_oracle_manager", "sologm.core.oracle.OracleManager", scene_manager=self
        )

    @property
    def event_manager(self) -> "EventManager":
        """Lazy-initialize event manager."""
        return self._lazy_init_manager(
            "_event_manager", "sologm.core.event.EventManager"
        )

    @property
    def dice_manager(self) -> "DiceManager":
        """Lazy-initialize dice manager."""
        return self._lazy_init_manager("_dice_manager", "sologm.core.dice.DiceManager")

    def _check_title_uniqueness(
        self,
        session: Session,
        act_id: str,
        title: str,
        exclude_scene_id: Optional[str] = None,
    ) -> None:
        """Check if a scene title is unique within an act.

        Args:
            session: Database session
            act_id: ID of the act to check in
            title: Title to check for uniqueness
            exclude_scene_id: Optional scene ID to exclude from the check (for updates)

        Raises:
            SceneError: If a scene with the same title already exists
        """
        query = session.query(Scene).filter(
            and_(Scene.act_id == act_id, Scene.title.ilike(title))
        )

        if exclude_scene_id:
            query = query.filter(Scene.id != exclude_scene_id)

        existing = query.first()
        if existing:
            raise SceneError(f"A scene with title '{title}' already exists in this act")

    def get_active_context(self) -> Dict[str, Any]:
        """Get the active game, act, and scene context.

        Returns:
            Dictionary containing 'game', 'act', and 'scene' keys with their
            respective objects.

        Raises:
            SceneError: If no active game, act, or scene is found.
        """
        logger.debug("Getting active context")
        try:
            # First get the active game
            active_game = self.game_manager.get_active_game()
            if not active_game:
                msg = "No active game. Use 'sologm game activate' to set one."
                logger.warning(msg)
                raise SceneError(msg)
            logger.debug(f"Active game: {active_game.id} ({active_game.name})")

            # Get the active act for this game
            active_act = self.act_manager.get_active_act(active_game.id)
            if not active_act:
                msg = "No active act. Create one with 'sologm act create'."
                logger.warning(msg)
                raise SceneError(msg)
            logger.debug(f"Active act: {active_act.id} ({active_act.title})")

            # Get the active scene for this act
            active_scene = self.get_active_scene(active_act.id)
            if not active_scene:
                msg = "No active scene. Add one with 'sologm scene add'."
                logger.warning(msg)
                raise SceneError(msg)
            logger.debug(f"Active scene: {active_scene.id} ({active_scene.title})")

            logger.debug("Active context retrieved successfully")
            return {"game": active_game, "act": active_act, "scene": active_scene}
        except Exception as e:
            if not isinstance(e, SceneError):
                logger.error(f"Error getting active context: {str(e)}", exc_info=True)
                self._handle_operation_error("get active context", e, SceneError)
            logger.warning(f"Failed to get active context: {str(e)}")
            raise

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID.

        Args:
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        logger.debug(f"Getting scene with ID {scene_id}")

        try:
            scenes = self.list_entities(Scene, filters={"id": scene_id}, limit=1)
            result = scenes[0] if scenes else None
            logger.debug(f"Found scene: {result.id if result else 'None'}")
            return result
        except Exception as e:
            logger.error(f"Error getting scene {scene_id}: {str(e)}", exc_info=True)
            self._handle_operation_error(f"get scene {scene_id}", e, SceneError)
            return None  # This will never be reached as _handle_operation_error raises

    def get_scene_in_act(self, act_id: str, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID within a specific act.

        Args:
            act_id: ID of the act the scene belongs to.
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        logger.debug(f"Getting scene {scene_id} in act {act_id}")

        try:
            scenes = self.list_entities(
                Scene, filters={"act_id": act_id, "id": scene_id}, limit=1
            )
            result = scenes[0] if scenes else None
            logger.debug(
                f"Found scene in act {act_id}: {result.id if result else 'None'}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Error getting scene {scene_id} in act {act_id}: {str(e)}", 
                exc_info=True
            )
            self._handle_operation_error(
                f"get scene {scene_id} in act {act_id}", e, SceneError
            )
            return None

    def get_active_scene(self, act_id: Optional[str] = None) -> Optional[Scene]:
        """Get the active scene for the specified act.

        Args:
            act_id: ID of the act to get the active scene for.
                   If not provided, uses the active act.

        Returns:
            Active Scene object if found, None otherwise.

        Raises:
            SceneError: If act_id is not provided and no active act is found.
        """
        logger.debug(f"Getting active scene for act_id={act_id or 'from active context'}")

        try:
            if not act_id:
                active_game = self.game_manager.get_active_game()
                if not active_game:
                    msg = "No active game. Use 'sologm game activate' to set one."
                    logger.warning(msg)
                    raise SceneError(msg)

                active_act = self.act_manager.get_active_act(active_game.id)
                if not active_act:
                    msg = "No active act. Create one with 'sologm act create'."
                    logger.warning(msg)
                    raise SceneError(msg)

                act_id = active_act.id
                logger.debug(f"Using active act with ID {act_id}")

            scenes = self.list_entities(
                Scene, filters={"act_id": act_id, "is_active": True}, limit=1
            )

            result = scenes[0] if scenes else None
            logger.debug(
                f"Active scene for act {act_id}: {result.id if result else 'None'}"
            )
            return result
        except Exception as e:
            if not isinstance(e, SceneError):
                logger.error(f"Error getting active scene: {str(e)}", exc_info=True)
                self._handle_operation_error(
                    f"get active scene for act {act_id}", e, SceneError
                )
            raise

    def create_scene(
        self,
        title: str,
        description: str,
        act_id: Optional[str] = None,
        make_active: bool = True
    ) -> Scene:
        """Create a new scene.
    
        Args:
            title: Title of the scene.
            description: Description of the scene.
            act_id: Optional ID of the act to create the scene in.
                   If not provided, uses the active act.
            make_active: Whether to make this scene the active scene in its act.
                
        Returns:
            The created Scene object.

        Raises:
            SceneError: If there's an error creating the scene or if title is
                        not unique.
        """
        logger.debug(
            f"Creating new scene: title='{title}', "
            f"description='{description[:20]}...', "
            f"act_id={act_id or 'from active context'}, "
            f"make_active={make_active}"
        )

        # Get act_id from active context if not provided
        if not act_id:
            try:
                context = self.get_active_context()
                act_id = context["act"].id
                logger.debug(f"Using active act with ID {act_id}")
            except SceneError as e:
                logger.error(f"Failed to get active context: {str(e)}")
                self._handle_operation_error(
                    f"create scene '{title}' in active act", e, SceneError
                )

        def _create_scene(session: Session) -> Scene:
            try:
                # Check if act exists
                act = self.act_manager.get_entity_or_error(
                    session,
                    Act,
                    act_id,
                    SceneError,
                    f"Act with ID '{act_id}' does not exist",
                )
                logger.debug(f"Found act: {act.title}")

                # Check for duplicate titles
                self._check_title_uniqueness(session, act_id, title)
                logger.debug(f"Title '{title}' is unique in act {act_id}")

                # Get the next sequence number
                scenes = self.list_entities(
                    Scene,
                    filters={"act_id": act_id},
                    order_by="sequence",
                    order_direction="desc",
                    limit=1,
                )

                sequence = 1
                if scenes:
                    sequence = scenes[0].sequence + 1
                logger.debug(f"Using sequence number {sequence}")

                # Create new scene
                scene = Scene.create(
                    act_id=act_id,
                    title=title,
                    description=description,
                    sequence=sequence,
                )
                logger.debug(f"Created scene with ID {scene.id}")

                if make_active:
                    # Deactivate all other scenes
                    session.query(Scene).filter(
                        and_(Scene.act_id == act_id, Scene.is_active)
                    ).update({"is_active": False})
                    logger.debug(f"Deactivated all other scenes in act {act_id}")

                    # Set this scene as active
                    scene.is_active = True
                    logger.debug(f"Set scene {scene.id} as active")

                session.add(scene)
                logger.info(
                    f"Created scene '{title}' with ID {scene.id} in act {act_id}"
                )
                return scene
            except Exception as e:
                logger.error(
                    f"Error creating scene '{title}' in act {act_id}: {str(e)}",
                    exc_info=True
                )
                self._handle_operation_error(f"create scene '{title}'", e, SceneError)

        return self._execute_db_operation("create scene", _create_scene)

    def list_scenes(self, act_id: Optional[str] = None) -> List[Scene]:
        """List all scenes for an act.

        Args:
            act_id: Optional ID of the act to list scenes for.
                   If not provided, uses the active act.

        Returns:
            List of Scene objects.

        Raises:
            SceneError: If act_id is not provided and no active act is found.
        """
        logger.debug(f"Listing scenes for act_id={act_id or 'from active context'}")

        if not act_id:
            try:
                context = self.get_active_context()
                act_id = context["act"].id
                logger.debug(f"Using active act with ID {act_id}")
            except SceneError as e:
                logger.error(f"Failed to get active context: {str(e)}")
                self._handle_operation_error("list scenes in active act", e, SceneError)

        try:
            scenes = self.list_entities(
                Scene, filters={"act_id": act_id}, order_by="sequence"
            )
            logger.debug(f"Found {len(scenes)} scenes in act {act_id}")
            return scenes
        except Exception as e:
            logger.error(f"Error listing scenes for act {act_id}: {str(e)}", exc_info=True)
            self._handle_operation_error(f"list scenes for act {act_id}", e, SceneError)
            return []  # This will never be reached as _handle_operation_error raises

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

        def _complete_scene(session: Session) -> Scene:
            try:
                scene = self.get_entity_or_error(
                    session, Scene, scene_id, SceneError, f"Scene {scene_id} not found"
                )
                logger.debug(f"Found scene: {scene.title}")

                if scene.status == SceneStatus.COMPLETED:
                    msg = f"Scene {scene_id} is already completed"
                    logger.warning(msg)
                    raise SceneError(msg)

                scene.status = SceneStatus.COMPLETED
                logger.info(f"Marked scene {scene_id} as completed")
                return scene
            except Exception as e:
                logger.error(f"Error completing scene {scene_id}: {str(e)}", exc_info=True)
                self._handle_operation_error(
                    f"complete scene {scene_id}", e, SceneError
                )

        return self._execute_db_operation("complete scene", _complete_scene)

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

        def _set_current_scene(session: Session) -> Scene:
            try:
                # Get the scene and raise error if not found
                scene = self.get_entity_or_error(
                    session, Scene, scene_id, SceneError, f"Scene {scene_id} not found"
                )
                logger.debug(f"Found scene: {scene.title}")

                # Deactivate all scenes in this act
                session.query(Scene).filter(
                    and_(Scene.act_id == scene.act_id, Scene.is_active)
                ).update({"is_active": False})
                logger.debug(f"Deactivated all scenes in act {scene.act_id}")

                # Set this scene as active
                scene.is_active = True
                logger.info(f"Set scene {scene_id} as current")
                return scene
            except Exception as e:
                logger.error(f"Error setting current scene {scene_id}: {str(e)}", exc_info=True)
                self._handle_operation_error(
                    f"set current scene {scene_id}", e, SceneError
                )

        return self._execute_db_operation("set current scene", _set_current_scene)

    def update_scene(
        self,
        scene_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Scene:
        """Update a scene's attributes.
    
        Only updates the attributes that are provided.
    
        Args:
            scene_id: ID of the scene to update
            title: Optional new title for the scene
            description: Optional new description for the scene
        
        Returns:
            The updated Scene object
        
        Raises:
            SceneError: If there's an error updating the scene
        """
        logger.debug(
            f"Updating scene {scene_id}: "
            f"title={title or '(unchanged)'}, "
            f"description={description[:20] + '...' if description else '(unchanged)'}"
        )

        def _update_scene(session: Session) -> Scene:
            try:
                # Get the scene and raise error if not found
                scene = self.get_entity_or_error(
                    session, Scene, scene_id, SceneError, f"Scene {scene_id} not found"
                )
                logger.debug(f"Found scene: {scene.title}")

                # Only update attributes that are provided
                if title is not None:
                    if scene.title != title:
                        logger.debug(f"Checking uniqueness for new title: {title}")
                        self._check_title_uniqueness(session, scene.act_id, title, scene_id)
                        logger.debug(f"Title '{title}' is unique in act {scene.act_id}")
                        scene.title = title

                if description is not None:
                    scene.description = description

                session.add(scene)
                logger.info(f"Updated scene {scene_id}")
                return scene
            except Exception as e:
                logger.error(f"Error updating scene {scene_id}: {str(e)}", exc_info=True)
                self._handle_operation_error(f"update scene {scene_id}", e, SceneError)

        return self._execute_db_operation("update scene", _update_scene)

    def get_previous_scene(
        self, scene: Optional[Scene] = None, scene_id: Optional[str] = None
    ) -> Optional[Scene]:
        """Get the scene that comes before the specified scene in sequence.
    
        Args:
            scene: Scene object to find the previous for
            scene_id: ID of the scene to find the previous for (alternative to scene)
        
        Returns:
            Previous Scene object if found, None otherwise
        
        Raises:
            SceneError: If neither scene nor scene_id is provided
        """
        if not scene and not scene_id:
            msg = "Either scene or scene_id must be provided"
            logger.error(msg)
            raise SceneError(msg)

        if not scene and scene_id:
            logger.debug(f"Getting scene with ID {scene_id} to find previous")
            scene = self.get_scene(scene_id)
            if not scene:
                logger.warning(f"Scene with ID {scene_id} not found")
                return None

        logger.debug(f"Getting previous scene for {scene.id} (sequence {scene.sequence})")

        if scene.sequence <= 1:
            logger.debug(f"Scene {scene.id} is the first scene (sequence {scene.sequence})")
            return None

        try:
            scenes = self.list_entities(
                Scene,
                filters={"act_id": scene.act_id, "sequence": scene.sequence - 1},
                limit=1,
            )
            result = scenes[0] if scenes else None
            logger.debug(
                f"Previous scene for {scene.id}: {result.id if result else 'None'}"
            )
            return result
        except Exception as e:
            logger.error(f"Error getting previous scene: {str(e)}", exc_info=True)
            self._handle_operation_error(
                f"get previous scene for {scene.id}", e, SceneError
            )
            return None

    def validate_active_context(self) -> Tuple[str, Scene]:
        """Validate active game, act, and scene context.

        Returns:
            Tuple of (act_id, active_scene)

        Raises:
            SceneError: If no active game, act, or scene
        """
        logger.debug("Validating active context")
        try:
            context = self.get_active_context()
            logger.debug(
                f"Active context validated: game={context['game'].id}, "
                f"act={context['act'].id}, scene={context['scene'].id}"
            )
            return context["act"].id, context["scene"]
        except Exception as e:
            if not isinstance(e, SceneError):
                logger.error(f"Error validating active context: {str(e)}", exc_info=True)
                self._handle_operation_error("validate active context", e, SceneError)
            logger.warning(f"Active context validation failed: {str(e)}")
            raise

    def create_scene_in_active_act(self, title: str, description: str) -> Scene:
        """Create a new scene in the active act.

        This is a convenience method that uses the active act.

        Args:
            title: Title of the scene
            description: Description of the scene

        Returns:
            The created Scene object

        Raises:
            SceneError: If there's an error creating the scene or no active act
        """
        return self.create_scene(title, description)

    def list_scenes_in_active_act(self) -> List[Scene]:
        """List all scenes in the active act.

        This is a convenience method that uses the active act.

        Returns:
            List of Scene objects

        Raises:
            SceneError: If there's an error listing the scenes or no active act
        """
        return self.list_scenes()
