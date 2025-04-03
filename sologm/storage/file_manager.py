import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from sologm.utils.errors import StorageError

logger = logging.getLogger(__name__)


class FileManager:
    """File manager for Solo RPG Helper.

    Handles all file operations for the application, including reading and writing
    YAML files, managing the directory structure, and tracking active game/scene.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the file manager with the base directory.

        Args:
            base_dir: Base directory for storing application data.
                     Defaults to ~/.sologm if not specified.
        """
        if base_dir is None:
            base_dir = Path.home() / ".sologm"
        self.base_dir = base_dir
        logger.debug("Initializing FileManager with base_dir: %s", self.base_dir)
        self._ensure_directory_structure()

    def _ensure_directory_structure(self) -> None:
        """Ensure the required directory structure exists."""
        try:
            games_dir = self.base_dir / "games"
            logger.debug("Creating directory structure at: %s", games_dir)
            games_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create directory structure: %s", str(e))
            raise StorageError(f"Failed to create directory structure: {str(e)}") from e

    def read_yaml(self, path: Path) -> Dict[str, Any]:
        """Read YAML file and return its contents as a dictionary.

        Args:
            path: Path to the YAML file.

        Returns:
            Dictionary containing the YAML file contents.

        Raises:
            StorageError: If the file cannot be read or parsed.
        """
        logger.debug("Reading YAML file: %s", path)
        if not path.exists():
            logger.debug("File does not exist, returning empty dict: %s", path)
            return {}

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
                logger.debug("Read %d keys from %s", len(data), path)
                return data
        except Exception as e:
            logger.error("Failed to read YAML file %s: %s", path, str(e))
            raise StorageError(f"Failed to read YAML file {path}: {str(e)}") from e

    def _create_backup(self, path: Path) -> Optional[Path]:
        """Create a backup of a file if it exists.

        Args:
            path: Path to the file to backup.

        Returns:
            Path to the backup file, or None if no backup was created.

        Raises:
            StorageError: If the backup cannot be created.
        """
        if not path.exists():
            return None

        try:
            backup_path = path.with_suffix(f"{path.suffix}.bak")
            path.rename(backup_path)
            return backup_path
        except Exception as e:
            raise StorageError(f"Failed to create backup of {path}: {str(e)}") from e

    def write_yaml(self, path: Path, data: Dict[str, Any]) -> None:
        """Write data to a YAML file.

        Creates a backup of the existing file before writing if it exists.

        Args:
            path: Path to the YAML file.
            data: Dictionary to write to the file.

        Raises:
            StorageError: If the file cannot be written.
        """
        logger.debug("Writing YAML file: %s with %d keys", path, len(data))
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug("Created parent directory: %s", path.parent)

            # Create backup of existing file
            backup_path = self._create_backup(path)
            if backup_path:
                logger.debug("Created backup at: %s", backup_path)

            # Write new data
            with open(path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            logger.debug("Successfully wrote data to: %s", path)
        except Exception as e:
            logger.error("Failed to write YAML file %s: %s", path, str(e))
            raise StorageError(f"Failed to write YAML file {path}: {str(e)}") from e

    def get_active_game_id(self) -> Optional[str]:
        """Get the ID of the active game, if any.

        Returns:
            The ID of the active game, or None if no game is active.
        """
        active_game_file = self.base_dir / "active_game"
        logger.debug("Getting active game ID from: %s", active_game_file)

        if not active_game_file.exists():
            logger.debug("No active game file found")
            return None

        try:
            with open(active_game_file, "r") as f:
                game_id = f.read().strip() or None
                logger.debug("Active game ID: %s", game_id)
                return game_id
        except Exception as e:
            logger.error("Failed to read active game ID: %s", str(e))
            raise StorageError(f"Failed to read active game ID: {str(e)}") from e

    def set_active_game_id(self, game_id: str) -> None:
        """Set the ID of the active game.

        Args:
            game_id: ID of the game to set as active.

        Raises:
            StorageError: If the active game ID cannot be set.
        """
        active_game_file = self.base_dir / "active_game"
        logger.debug("Setting active game ID to %s in %s", game_id, active_game_file)

        try:
            with open(active_game_file, "w") as f:
                f.write(game_id)
            logger.debug("Successfully set active game ID")
        except Exception as e:
            logger.error("Failed to set active game ID: %s", str(e))
            raise StorageError(f"Failed to set active game ID: {str(e)}") from e

    def get_active_scene_id(self, game_id: str) -> Optional[str]:
        """Get the ID of the active scene for a game, if any.

        Args:
            game_id: ID of the game.

        Returns:
            The ID of the active scene, or None if no scene is active.

        Raises:
            StorageError: If the active scene ID cannot be read.
        """
        active_scene_file = self.base_dir / "games" / game_id / "active_scene"

        if not active_scene_file.exists():
            return None

        try:
            with open(active_scene_file, "r") as f:
                return f.read().strip() or None
        except Exception as e:
            raise StorageError(f"Failed to read active scene ID: {str(e)}") from e

    def set_active_scene_id(self, game_id: str, scene_id: str) -> None:
        """Set the ID of the active scene for a game.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene to set as active.

        Raises:
            StorageError: If the active scene ID cannot be set.
        """
        game_dir = self.base_dir / "games" / game_id
        active_scene_file = game_dir / "active_scene"

        try:
            game_dir.mkdir(parents=True, exist_ok=True)
            with open(active_scene_file, "w") as f:
                f.write(scene_id)
        except Exception as e:
            raise StorageError(f"Failed to set active scene ID: {str(e)}") from e

    def get_game_path(self, game_id: str) -> Path:
        """Get the path to a game's YAML file.

        Args:
            game_id: ID of the game.

        Returns:
            Path to the game's YAML file.
        """
        return self.base_dir / "games" / game_id / "game.yaml"

    def get_scene_path(self, game_id: str, scene_id: str) -> Path:
        """Get the path to a scene's YAML file.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene.

        Returns:
            Path to the scene's YAML file.
        """
        return self.base_dir / "games" / game_id / "scenes" / scene_id / "scene.yaml"

    def get_events_path(self, game_id: str, scene_id: str) -> Path:
        """Get the path to a scene's events YAML file.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene.

        Returns:
            Path to the scene's events YAML file.
        """
        return self.base_dir / "games" / game_id / "scenes" / scene_id / "events.yaml"

    def get_interpretations_dir(self, game_id: str, scene_id: str) -> Path:
        """Get the path to a scene's interpretations directory.

        Args:
            game_id: ID of the game.
            scene_id: ID of the scene.

        Returns:
            Path to the scene's interpretations directory.
        """
        return (
            self.base_dir / "games" / game_id / "scenes" / scene_id / "interpretations"
        )

    def create_timestamp_filename(self, prefix: str, suffix: str = ".yaml") -> str:
        """Create a filename with a timestamp.

        Args:
            prefix: Prefix for the filename.
            suffix: Suffix for the filename.

        Returns:
            Filename with timestamp.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}{suffix}"
