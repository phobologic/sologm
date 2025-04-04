"""Scene management functionality."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sologm.storage.file_manager import FileManager
from sologm.utils.errors import SceneError

logger = logging.getLogger(__name__)


class SceneStatus(Enum):
    """Enumeration of possible scene statuses."""

    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class Scene:
    """Represents a scene in a game."""

    id: str
    game_id: str
    title: str
    description: str
    status: SceneStatus
    sequence: int
    created_at: datetime
    modified_at: datetime


class SceneManager:
    """Manages scene operations."""

    def __init__(self, file_manager: Optional[FileManager] = None):
        """Initialize the scene manager.

        Args:
            file_manager: Optional FileManager instance. If not provided,
                a new one will be created.
        """
        self.file_manager = file_manager or FileManager()
        logger.debug(
            "Initialized SceneManager with file_manager: %s", self.file_manager
        )

    def _scene_to_dict(self, scene: Scene) -> dict:
        """Convert a Scene object to a dictionary for storage.

        Args:
            scene: Scene object to convert

        Returns:
            Dictionary representation of the scene
        """
        logger.debug("Converting scene to dict: %s", scene.id)
        return {
            "id": scene.id,
            "game_id": scene.game_id,
            "title": scene.title,
            "description": scene.description,
            "status": scene.status.value,  # Convert enum to string
            "sequence": scene.sequence,
            "created_at": scene.created_at.isoformat(),
            "modified_at": scene.modified_at.isoformat(),
        }

    def _dict_to_scene(self, data: dict) -> Scene:
        """Convert a dictionary to a Scene object.

        Args:
            data: Dictionary containing scene data

        Returns:
            Scene object
        """
        logger.debug("Converting dict to scene: %s", data["id"])
        return Scene(
            id=data["id"],
            game_id=data["game_id"],
            title=data["title"],
            description=data["description"],
            status=SceneStatus(data["status"]),  # Convert string to enum
            sequence=data["sequence"],
            created_at=datetime.fromisoformat(data["created_at"]).replace(
                tzinfo=timezone.utc if not datetime.fromisoformat(
                    data["created_at"]
                ).tzinfo else None
            ),
            modified_at=datetime.fromisoformat(data["modified_at"]).replace(
                tzinfo=timezone.utc if not datetime.fromisoformat(
                    data["modified_at"]
                ).tzinfo else None
            ),
        )

    def _get_game_data(self, game_id: str) -> dict:
        """Get game data from storage.

        Args:
            game_id: ID of the game

        Returns:
            Dictionary containing game data

        Raises:
            SceneError: If game not found
        """
        logger.debug("Getting game data for: %s", game_id)
        game_path = self.file_manager.get_game_path(game_id)
        game_data = self.file_manager.read_yaml(game_path)
        if not game_data:
            logger.error("Game not found: %s", game_id)
            raise SceneError(f"Game {game_id} not found")
        return game_data

    def _validate_scene_exists(self, game_id: str, scene_id: str) -> Scene:
        """Validate that a scene exists and return it.

        Args:
            game_id: ID of the game
            scene_id: ID of the scene

        Returns:
            Scene object if found

        Raises:
            SceneError: If scene not found
        """
        logger.debug("Validating scene exists: %s in game %s", scene_id, game_id)
        scene = self.get_scene(game_id, scene_id)
        if not scene:
            logger.error("Scene %s not found in game %s", scene_id, game_id)
            raise SceneError(f"Scene {scene_id} not found in game {game_id}")
        return scene

    def _validate_unique_title(self, game_id: str, title: str) -> None:
        """Validate that a scene title is unique within a game.

        Args:
            game_id: ID of the game
            title: Scene title to check

        Raises:
            SceneError: If title is not unique
        """
        logger.debug("Validating unique title: %s in game %s", title, game_id)
        existing_scenes = self.list_scenes(game_id)
        for scene in existing_scenes:
            if scene.title.lower() == title.lower():
                logger.error("Duplicate scene title found: %s", title)
                raise SceneError(
                    f"A scene with title '{title}' already exists in this game"
                )

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
        logger.debug(f"Creating new scene in game {game_id} with title " f"'{title}'")

        # Get the game's scenes to determine sequence number and check for
        # duplicate titles
        game_path = self.file_manager.get_game_path(game_id)
        game_data = self.file_manager.read_yaml(game_path)

        if not game_data:
            logger.error(f"Game {game_id} not found when creating scene")
            raise SceneError(f"Game {game_id} not found")

        # Check for duplicate titles
        logger.debug("Checking for duplicate scene titles")
        existing_scenes = self.list_scenes(game_id)
        for scene in existing_scenes:
            if scene.title.lower() == title.lower():
                logger.error(f"Duplicate scene title found: '{title}'")
                raise SceneError(
                    f"A scene with title '{title}' already " f"exists in this game"
                )

        scenes = game_data.get("scenes", [])
        sequence = len(scenes) + 1

        # Generate scene ID from title
        scene_id = f"scene-{sequence}-{title.lower().replace(' ', '-')}"

        # Create scene data
        now = datetime.now(UTC)
        scene = Scene(
            id=scene_id,
            game_id=game_id,
            title=title,
            description=description,
            status=SceneStatus.ACTIVE,
            sequence=sequence,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
        )

        # Save scene data
        scene_path = self.file_manager.get_scene_path(game_id, scene_id)
        scene_data = self._scene_to_dict(scene)
        self.file_manager.write_yaml(scene_path, scene_data)

        # Update game's scene list
        scenes.append(scene_id)
        game_data["scenes"] = scenes
        self.file_manager.write_yaml(game_path, game_data)

        # Set as active scene
        self.file_manager.set_active_scene_id(game_id, scene_id)

        logger.debug(f"Created scene {scene_id} in game {game_id}")
        return scene

    def list_scenes(self, game_id: str) -> List[Scene]:
        """List all scenes for the specified game.

        Args:
            game_id: ID of the game to list scenes for.

        Returns:
            List of Scene objects.

        Raises:
            SceneError: If there's an error listing the scenes.
        """
        game_path = self.file_manager.get_game_path(game_id)
        game_data = self.file_manager.read_yaml(game_path)
        logger.debug(f"Listing scenes for game {game_id}, " f"game_path: {game_path}")

        if not game_data:
            logger.error(f"Game {game_id} not found when listing scenes")
            raise SceneError(f"Game {game_id} not found")

        # Get list of scenes and filter out any that don't exist on disk
        scenes = []
        existing_scene_ids = []
        for scene_id in game_data.get("scenes", []):
            scene_path = self.file_manager.get_scene_path(game_id, scene_id)
            scene_data = self.file_manager.read_yaml(scene_path)

            if scene_data:
                scenes.append(self._dict_to_scene(scene_data))
                existing_scene_ids.append(scene_id)

        # Update game's scene list if any scenes were missing
        if len(existing_scene_ids) != len(game_data.get("scenes", [])):
            game_data["scenes"] = existing_scene_ids
            game_path = self.file_manager.get_game_path(game_id)
            self.file_manager.write_yaml(game_path, game_data)
            logger.debug(
                f"Updated game {game_id} scene list to remove " f"missing scenes"
            )

        return sorted(scenes, key=lambda s: s.sequence)

    def get_scene(self, game_id: str, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID.

        Args:
            game_id: ID of the game the scene belongs to.
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        scene_path = self.file_manager.get_scene_path(game_id, scene_id)
        scene_data = self.file_manager.read_yaml(scene_path)

        if scene_data:
            return self._dict_to_scene(scene_data)
        return None

    def get_active_scene(self, game_id: str) -> Optional[Scene]:
        """Get the active scene for the specified game.

        Args:
            game_id: ID of the game to get the active scene for.

        Returns:
            Active Scene object if found, None otherwise.
        """
        active_scene_id = self.file_manager.get_active_scene_id(game_id)
        if active_scene_id:
            return self.get_scene(game_id, active_scene_id)
        return None

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
        scene = self.get_scene(game_id, scene_id)
        if not scene:
            logger.error(
                f"Scene {scene_id} not found in game {game_id} when " f"completing"
            )
            raise SceneError(f"Scene {scene_id} not found in game {game_id}")

        if scene.status == SceneStatus.COMPLETED:
            logger.error(f"Scene {scene_id} is already completed")
            raise SceneError(f"Scene {scene_id} is already completed")

        # Update scene status
        scene.status = SceneStatus.COMPLETED
        scene.modified_at = datetime.now(UTC)

        # Save updated scene data
        scene_path = self.file_manager.get_scene_path(game_id, scene_id)
        scene_data = self._scene_to_dict(scene)
        self.file_manager.write_yaml(scene_path, scene_data)

        logger.debug(f"Completed scene {scene_id} in game {game_id}")
        return scene

    def set_current_scene(self, game_id: str, scene_id: str) -> Scene:
        """Set which scene is currently being played without changing its
           status.

        Args:
            game_id: ID of the game the scene belongs to.
            scene_id: ID of the scene to make current.

        Returns:
            The Scene object that was made current.

        Raises:
            SceneError: If there's an error setting the current scene.
        """
        logger.debug(f"Setting scene {scene_id} as current in game {game_id}")
        scene = self.get_scene(game_id, scene_id)
        if not scene:
            logger.error(
                f"Scene {scene_id} not found in game {game_id} " f"when setting current"
            )
            raise SceneError(f"Scene {scene_id} not found in game {game_id}")

        self.file_manager.set_active_scene_id(game_id, scene_id)
        logger.debug(f"Set scene {scene_id} as current in game {game_id}")
        return scene
