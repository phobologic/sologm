"""Scene management functionality."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from sologm.core.base_manager import BaseManager
from sologm.models.act import Act
from sologm.models.scene import Scene
from sologm.utils.errors import ActError, SceneError

if TYPE_CHECKING:
    from sologm.core.act import ActManager
    from sologm.core.dice import DiceManager
    from sologm.core.event import EventManager
    from sologm.core.game import GameManager
    from sologm.core.oracle import OracleManager


logger = logging.getLogger(__name__)


class SceneManager(BaseManager[Scene, Scene]):
    """Manages scene operations."""

    def __init__(
        self,
        session: Optional[Session] = None,
        act_manager: Optional["ActManager"] = None,
    ):
        """Initialize the scene manager.

        Args:
            session: Optional session for testing or CLI command injection.
            act_manager: Optional ActManager instance. If not provided,
                a new one will be lazy-initialized when needed.
        """
        super().__init__(session=session)
        self._act_manager: Optional["ActManager"] = act_manager
        self._dice_manager: Optional["DiceManager"] = None
        self._event_manager: Optional["EventManager"] = None
        self._oracle_manager: Optional["OracleManager"] = None
        logger.debug("Initialized SceneManager")

    @property
    def act_manager(self) -> "ActManager":
        """Lazy-initialize act manager if not provided."""
        if self._act_manager is None:
            from sologm.core.act import ActManager

            self._act_manager = ActManager(session=self._session)
        return self._act_manager

    @property
    def game_manager(self) -> "GameManager":
        """Access game manager through act manager."""
        return self.act_manager.game_manager

    @property
    def oracle_manager(self) -> "OracleManager":
        """Lazy-initialize oracle manager."""
        return self._lazy_init_manager(
            attr_name="_oracle_manager",
            manager_class_path="sologm.core.oracle.OracleManager",
            scene_manager=self,
            session=self._session,
        )

    @property
    def event_manager(self) -> "EventManager":
        """Lazy-initialize event manager."""
        return self._lazy_init_manager(
            attr_name="_event_manager",
            manager_class_path="sologm.core.event.EventManager",
            session=self._session,
        )

    @property
    def dice_manager(self) -> "DiceManager":
        """Lazy-initialize dice manager."""
        return self._lazy_init_manager(
            attr_name="_dice_manager",
            manager_class_path="sologm.core.dice.DiceManager",
            session=self._session,
        )

    def _get_act_id_or_active(self, act_id: Optional[str] = None) -> str:
        """Get the provided act_id or retrieve the active act's ID.

        Args:
            act_id: Optional act ID to use

        Returns:
            The act ID to use

        Raises:
            SceneError: If no act_id provided and no active act found
        """
        if act_id:
            logger.debug(f"Using provided act ID: {act_id}")
            return act_id

        logger.debug("No act_id provided, retrieving active act")
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

        logger.debug(f"Using active act with ID {active_act.id}")
        return active_act.id

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
            GameError: If there's an issue retrieving the active game.
            ActError: If there's an issue retrieving the active act.
        """
        logger.debug("Getting active context")

        # Get the active game
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

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID.

        Args:
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        logger.debug(f"Getting scene with ID {scene_id}")

        scenes = self.list_entities(Scene, filters={"id": scene_id}, limit=1)
        result = scenes[0] if scenes else None
        logger.debug(f"Found scene: {result.id if result else 'None'}")
        return result

    def get_scene_by_identifier(self, identifier: str) -> Optional[Scene]:
        """Get a specific scene by its ID (UUID) or slug.

        Args:
            identifier: ID or slug of the scene to get.

        Returns:
            Scene instance if found, None otherwise.
        """
        logger.debug(f"Getting scene by identifier: {identifier}")

        def _get_scene(session: Session) -> Optional[Scene]:
            return self.get_entity_by_identifier(session, Scene, identifier)

        scene = self._execute_db_operation(
            f"get scene by identifier {identifier}", _get_scene
        )
        logger.debug(
            f"Retrieved scene by identifier: {scene.id if scene else 'None'} "
            f"(Input: '{identifier}')",
        )
        return scene

    def get_scene_by_identifier_or_error(self, identifier: str) -> Scene:
        """Get a specific scene by its ID (UUID) or slug, raising SceneError
           if not found.

        Args:
            identifier: ID or slug of the scene to get.

        Returns:
            The Scene instance.

        Raises:
            SceneError: If the scene is not found.
        """
        logger.debug(f"Getting scene by identifier or error: {identifier}")

        def _get_scene(session: Session) -> Scene:
            # Call the base manager method correctly
            return self.get_entity_by_identifier_or_error(
                session=session,
                model_class=Scene,
                identifier=identifier,
                error_class=SceneError,
                error_message=f"Scene not found with identifier '{identifier}'",
            )

        scene = self._execute_db_operation(
            f"get scene by identifier or error {identifier}", _get_scene
        )
        logger.debug(
            f"Retrieved scene by identifier: {scene.id} (Input: '{identifier}')",
        )
        return scene

    def get_scene_in_act(self, act_id: str, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID within a specific act.

        Args:
            act_id: ID of the act the scene belongs to.
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        logger.debug(f"Getting scene {scene_id} in act {act_id}")

        scenes = self.list_entities(
            Scene, filters={"act_id": act_id, "id": scene_id}, limit=1
        )
        result = scenes[0] if scenes else None
        logger.debug(f"Found scene in act {act_id}: {result.id if result else 'None'}")
        return result

    def get_active_scene(self, act_id: Optional[str] = None) -> Optional[Scene]:
        """Get the active scene for the specified act.

        Args:
            act_id: ID of the act to get the active scene for.
                   If not provided, uses the active act.

        Returns:
            Active Scene object if found, None otherwise.

        Raises:
            SceneError: If act_id is not provided and no active act is found,
                        or if the underlying act/game retrieval fails.
        """
        logger.debug(
            f"Getting active scene for act_id={act_id or 'from active context'}",
        )

        act_id = self._get_act_id_or_active(act_id)

        scenes = self.list_entities(
            Scene, filters={"act_id": act_id, "is_active": True}, limit=1
        )

        result = scenes[0] if scenes else None
        logger.debug(
            f"Active scene for act {act_id}: {result.id if result else 'None'}"
        )
        return result

    def create_scene(  # noqa: PLR0913
        self,
        title: str,
        description: Optional[str],  # Changed from str
        act_id: Optional[str] = None,
        make_active: bool = True,
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
            SceneError: If there's an error creating the scene (e.g., title not
                        unique, underlying act/game retrieval fails).
            ActError: If the specified act doesn't exist or no active act is found.
        """
        logger.debug(
            "Creating new scene: title='%s', description='%s...', act_id=%s, "
            "make_active=%s",
            title,
            description[:20] if description else "None",
            act_id or "from active context",
            make_active,
        )

        # Get act_id from active context if not provided
        act_id = self._get_act_id_or_active(act_id)

        def _create_scene(session: Session) -> Scene:
            # Check if act exists using the ActManager
            act = self.act_manager.get_entity_or_error(
                session=session,
                model_class=Act,
                entity_id=act_id,
                error_class=ActError,
                error_message=f"Act with ID '{act_id}' does not exist",
            )
            logger.debug(f"Found act: {act.id} ('{act.title}')")

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
            logger.debug(f"Added scene {scene.title} to session")

            # --- MODIFICATION START ---
            # Flush to send the INSERT to the DB and generate timestamps/ID
            logger.debug("Flushing session to persist scene and generate timestamps")
            session.flush()
            logger.debug(f"Scene flushed. DB ID should now be: {scene.id}")

            # Refresh to load DB-generated values (ID, timestamps) and relationships
            try:
                logger.debug(
                    "Refreshing scene %s to load attributes: %s",
                    scene.id,
                    ["id", "created_at", "modified_at", "act"],
                )
                # Explicitly refresh the necessary attributes
                session.refresh(
                    scene,
                    attribute_names=["id", "created_at", "modified_at", "act"],
                )
                logger.debug(
                    "Scene %s refreshed. Created_at: %s, Act loaded: %s",
                    scene.id,
                    scene.created_at,
                    scene.act is not None,
                )
            except Exception as e:
                # Log a warning if refresh fails, but proceed cautiously
                logger.warning(
                    f"Warning: Failed to refresh scene {scene.id} after creation: {e}"
                )
                # The scene object might have stale data, but the DB record exists.
            # --- MODIFICATION END ---

            logger.info(f"Created scene '{title}' with ID {scene.id} in act {act_id}")
            return scene

        return self._execute_db_operation("create scene", _create_scene)

    def list_scenes(self, act_id: Optional[str] = None) -> List[Scene]:
        """List all scenes for an act.

        Args:
            act_id: Optional ID of the act to list scenes for.
                   If not provided, uses the active act.

        Returns:
            List of Scene objects.

        Raises:
            SceneError: If act_id is not provided and no active act is found,
                        or if the underlying act/game retrieval fails.
            ActError: If the specified act doesn't exist.
        """
        logger.debug(f"Listing scenes for act_id={act_id or 'from active context'}")

        act_id = self._get_act_id_or_active(act_id)

        scenes = self.list_entities(
            Scene, filters={"act_id": act_id}, order_by="sequence"
        )
        logger.debug(f"Found {len(scenes)} scenes in act {act_id}")
        return scenes

    def set_current_scene(self, scene_id: str) -> Scene:
        """Set which scene is currently being played.

        Args:
            scene_id: ID of the scene to make current.

        Returns:
            The Scene object that was made current.

        Raises:
            SceneError: If the scene doesn't exist
        """
        logger.debug(f"Setting scene {scene_id} as current")

        def _set_current_scene(session: Session) -> Scene:
            # Get the scene and raise error if not found
            scene = self.get_entity_or_error(
                session=session,
                model_class=Scene,
                entity_id=scene_id,
                error_class=SceneError,
                error_message=f"Scene {scene_id} not found",
            )
            logger.debug(f"Found scene: {scene.id} ('{scene.title}')")

            # Deactivate all scenes in this act
            session.query(Scene).filter(
                and_(Scene.act_id == scene.act_id, Scene.is_active)
            ).update({"is_active": False})
            logger.debug(f"Deactivated all scenes in act {scene.act_id}")

            # Set this scene as active
            scene.is_active = True
            session.add(scene)  # Ensure change is tracked
            logger.debug(f"Marked scene {scene_id} as active in session")

            # Flush to send UPDATEs (for deactivated scenes and the new active one)
            logger.debug("Flushing session to persist active status changes")
            session.flush()

            # Refresh the newly activated scene to get updated modified_at
            try:
                logger.debug(
                    "Refreshing scene %s to load attributes: %s",
                    scene.id,
                    ["modified_at", "is_active"],
                )
                session.refresh(scene, attribute_names=["modified_at", "is_active"])
                logger.debug(
                    "Scene %s refreshed. Modified_at: %s, Is Active: %s",
                    scene.id,
                    scene.modified_at,
                    scene.is_active,
                )
            except Exception as e:
                logger.warning(
                    f"Warning: Failed to refresh scene {scene.id} "
                    f"after setting current: {e}"
                )

            logger.info(f"Set scene {scene_id} as current")
            return scene

        return self._execute_db_operation("set current scene", _set_current_scene)

    def update_scene(  # noqa: PLR0913
        self,
        scene_id: str,
        title: Optional[str] = None,  # Corrected type hint
        description: Optional[str] = None,  # Corrected type hint
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
            SceneError: If the scene doesn't exist or title isn't unique.
            ValueError: If neither title nor description is provided.
        """
        logger.debug(
            "Updating scene %s: title=%s, description=%s...",
            scene_id,
            title or "(unchanged)",
            description[:20] if description else "(unchanged)",
        )

        # Validate input
        if title is None and description is None:
            raise ValueError("At least one of title or description must be provided")

        def _update_scene(session: Session) -> Scene:
            # Get the scene and raise error if not found
            scene = self.get_entity_or_error(
                session=session,
                model_class=Scene,
                entity_id=scene_id,
                error_class=SceneError,
                error_message=f"Scene {scene_id} not found",
            )
            logger.debug(f"Found scene: {scene.id} ('{scene.title}')")

            # Only update attributes that are provided
            if title and scene.title != title:
                logger.debug(f"Checking uniqueness for new title: {title}")
                self._check_title_uniqueness(session, scene.act_id, title, scene_id)
                logger.debug(f"Title '{title}' is unique in act {scene.act_id}")
                scene.title = title

            if description is not None:
                scene.description = description

            session.add(scene)  # Ensure changes are tracked
            logger.debug(f"Marked scene {scene_id} for update in session")

            # Flush to send UPDATE and update modified_at in DB
            logger.debug("Flushing session to persist scene updates")
            session.flush()

            # Refresh to load updated modified_at
            try:
                logger.debug(
                    "Refreshing scene %s to load attributes: %s",
                    scene.id,
                    ["modified_at", "title", "description"],
                )
                session.refresh(
                    scene,
                    attribute_names=["modified_at", "title", "description"],
                )
                logger.debug(
                    "Scene %s refreshed. Modified_at: %s",
                    scene.id,
                    scene.modified_at,
                )
            except Exception as e:
                logger.warning(
                    "Warning: Failed to refresh scene %s after update: %s",
                    scene.id,
                    e,
                )

            logger.info(f"Updated scene {scene_id}")
            return scene

        return self._execute_db_operation("update scene", _update_scene)

    def get_previous_scene(self, scene_id: str) -> Optional[Scene]:
        """Get the scene that comes before the specified scene in sequence.

        Args:
            scene_id: ID of the scene to find the previous for

        Returns:
            Previous Scene object if found, None otherwise.

        Raises:
            SceneError: If the specified scene is not found.
        """
        logger.debug(f"Getting previous scene for scene_id={scene_id}")

        scene = self.get_scene(scene_id)
        if not scene:
            logger.warning(f"Scene with ID {scene_id} not found")
            return None

        logger.debug(f"Found scene {scene_id}, sequence={scene.sequence}")

        if scene.sequence <= 1:
            logger.debug(
                f"Scene {scene_id} is the first scene (sequence {scene.sequence})"
            )
            return None

        scenes = self.list_entities(
            Scene,
            filters={"act_id": scene.act_id, "sequence": scene.sequence - 1},
            limit=1,
        )

        result = scenes[0] if scenes else None
        logger.debug(
            f"Previous scene for {scene_id}: {result.id if result else 'None'}"
        )
        return result

    def get_most_recent_scene(self, act_id: str) -> Optional[Scene]:
        """Get the most recent scene based on sequence number for a specific act.

        Args:
            act_id: ID of the act to search within.

        Returns:
            The most recent Scene instance in the act or None if no scenes exist.
        """
        self.logger.debug(f"Getting most recent scene for act_id='{act_id}'")

        def _operation(session: Session, act_id: str) -> Optional[Scene]:
            # Ensure correct model is used and order_by is applied
            return (
                session.query(Scene)
                .filter(Scene.act_id == act_id)
                .order_by(Scene.sequence.desc())
                .first()
            )

        # Ensure correct arguments are passed to _execute_db_operation
        return self._execute_db_operation(
            operation_name="get most recent scene",
            operation=_operation,
            act_id=act_id,
        )

    def validate_active_context(self) -> Tuple[str, Scene]:
        """Validate active game, act, and scene context.

        Returns:
            Tuple of (act_id, active_scene).

        Raises:
            SceneError: If no active game, act, or scene is found.
            GameError: If there's an issue retrieving the active game.
            ActError: If there's an issue retrieving the active act.
        """
        logger.debug("Validating active context")
        context = self.get_active_context()
        logger.debug(
            "Active context validated: game=%s, act=%s, scene=%s",
            context["game"].id,
            context["act"].id,
            context["scene"].id,
        )
        return context["act"].id, context["scene"]
