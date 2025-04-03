"""Tests for the file manager module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from sologm.storage.file_manager import FileManager
from sologm.utils.errors import StorageError


class TestFileManager:
    """Tests for the FileManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.file_manager = FileManager(self.base_dir)

    def teardown_method(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_init_creates_directory_structure(self):
        """Test that initialization creates the directory structure."""
        assert (self.base_dir / "games").exists()
        assert (self.base_dir / "games").is_dir()

    def test_read_yaml_nonexistent_file(self):
        """Test reading a nonexistent YAML file."""
        path = self.base_dir / "nonexistent.yaml"
        assert self.file_manager.read_yaml(path) == {}

    def test_read_yaml_valid_file(self):
        """Test reading a valid YAML file."""
        path = self.base_dir / "test.yaml"
        data = {"key": "value", "nested": {"key": "value"}}
        with open(path, "w") as f:
            yaml.dump(data, f)

        assert self.file_manager.read_yaml(path) == data

    def test_read_yaml_invalid_file(self):
        """Test reading an invalid YAML file."""
        path = self.base_dir / "invalid.yaml"
        with open(path, "w") as f:
            f.write("invalid: yaml: content:")

        with pytest.raises(StorageError):
            self.file_manager.read_yaml(path)

    def test_write_yaml(self):
        """Test writing a YAML file."""
        path = self.base_dir / "test_write.yaml"
        data = {"key": "value", "nested": {"key": "value"}}
        self.file_manager.write_yaml(path, data)

        assert path.exists()
        with open(path, "r") as f:
            assert yaml.safe_load(f) == data

    def test_write_yaml_creates_parent_directories(self):
        """Test that writing a YAML file creates parent directories."""
        path = self.base_dir / "nested" / "dir" / "test.yaml"
        data = {"key": "value"}
        self.file_manager.write_yaml(path, data)

        assert path.exists()
        assert path.parent.exists()
        assert path.parent.is_dir()

    def test_write_yaml_creates_backup(self):
        """Test that writing a YAML file creates a backup of existing file."""
        path = self.base_dir / "test.yaml"

        # Write initial data
        initial_data = {"key": "initial"}
        self.file_manager.write_yaml(path, initial_data)

        # Write new data
        new_data = {"key": "new"}
        self.file_manager.write_yaml(path, new_data)

        # Check backup exists with initial data
        backup_path = path.with_suffix(".yaml.bak")
        assert backup_path.exists()
        with open(backup_path, "r") as f:
            assert yaml.safe_load(f) == initial_data

        # Check original file has new data
        with open(path, "r") as f:
            assert yaml.safe_load(f) == new_data

    def test_get_active_game_id_none(self):
        """Test getting the active game ID when none is set."""
        assert self.file_manager.get_active_game_id() is None

    def test_set_and_get_active_game_id(self):
        """Test setting and getting the active game ID."""
        game_id = "test-game"
        self.file_manager.set_active_game_id(game_id)
        assert self.file_manager.get_active_game_id() == game_id

    def test_get_active_scene_id_none(self):
        """Test getting the active scene ID when none is set."""
        game_id = "test-game"
        assert self.file_manager.get_active_scene_id(game_id) is None

    def test_set_and_get_active_scene_id(self):
        """Test setting and getting the active scene ID."""
        game_id = "test-game"
        scene_id = "test-scene"
        self.file_manager.set_active_scene_id(game_id, scene_id)
        assert self.file_manager.get_active_scene_id(game_id) == scene_id

    def test_get_game_path(self):
        """Test getting the path to a game's YAML file."""
        game_id = "test-game"
        expected_path = self.base_dir / "games" / game_id / "game.yaml"
        assert self.file_manager.get_game_path(game_id) == expected_path

    def test_get_scene_path(self):
        """Test getting the path to a scene's YAML file."""
        game_id = "test-game"
        scene_id = "test-scene"
        expected_path = (
            self.base_dir / "games" / game_id / "scenes" / scene_id / "scene.yaml"
        )
        assert self.file_manager.get_scene_path(game_id, scene_id) == expected_path

    def test_get_events_path(self):
        """Test getting the path to a scene's events YAML file."""
        game_id = "test-game"
        scene_id = "test-scene"
        expected_path = (
            self.base_dir / "games" / game_id / "scenes" / scene_id / "events.yaml"
        )
        assert self.file_manager.get_events_path(game_id, scene_id) == expected_path

    def test_get_interpretations_dir(self):
        """Test getting the path to a scene's interpretations directory."""
        game_id = "test-game"
        scene_id = "test-scene"
        expected_path = (
            self.base_dir / "games" / game_id / "scenes" / scene_id / "interpretations"
        )
        assert (
            self.file_manager.get_interpretations_dir(game_id, scene_id)
            == expected_path
        )

    def test_create_timestamp_filename(self):
        """Test creating a filename with a timestamp."""
        prefix = "test"
        suffix = ".yaml"
        filename = self.file_manager.create_timestamp_filename(prefix, suffix)
        assert filename.startswith(prefix)
        assert filename.endswith(suffix)
        assert "_" in filename  # Should contain timestamp separator
