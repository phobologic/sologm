"""Tests for game CLI commands."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sologm.cli.main import app
from sologm.storage.file_manager import FileManager

runner = CliRunner()

@pytest.fixture
def temp_base_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

def test_create_game(temp_base_dir, monkeypatch):
    """Test creating a game via CLI."""
    monkeypatch.setattr("sologm.core.game.FileManager", 
                       lambda: FileManager(temp_base_dir))
    monkeypatch.setattr("sologm.cli.game.GameManager",
                       lambda: GameManager(FileManager(temp_base_dir)))
    
    result = runner.invoke(
        app, 
        ["game", "create", "--name", "Test Game", "--description", "A test game"]
    )
    assert result.exit_code == 0
    assert "Created game: Test Game" in result.stdout
    assert "Description: A test game" in result.stdout
    assert "Status: active" in result.stdout

def test_list_games_empty(temp_base_dir, monkeypatch):
    """Test listing games when none exist."""
    monkeypatch.setattr("sologm.core.game.FileManager", 
                       lambda: FileManager(temp_base_dir))
    
    result = runner.invoke(app, ["game", "list"])
    assert result.exit_code == 0
    assert "No games found." in result.stdout

def test_list_games(temp_base_dir, monkeypatch):
    """Test listing multiple games."""
    monkeypatch.setattr("sologm.core.game.FileManager", 
                       lambda: FileManager(temp_base_dir))
    
    # Create some games first
    runner.invoke(
        app, 
        ["game", "create", "--name", "Game 1", "--description", "First game"]
    )
    runner.invoke(
        app, 
        ["game", "create", "--name", "Game 2", "--description", "Second game"]
    )
    
    result = runner.invoke(app, ["game", "list"])
    assert result.exit_code == 0
    assert "Game 1" in result.stdout
    assert "First game" in result.stdout
    assert "Game 2" in result.stdout
    assert "Second game" in result.stdout

def test_activate_game(temp_base_dir, monkeypatch):
    """Test activating a game."""
    monkeypatch.setattr("sologm.core.game.FileManager", 
                       lambda: FileManager(temp_base_dir))
    
    # Create a game first
    create_result = runner.invoke(
        app, 
        ["game", "create", "--name", "Test Game", "--description", "A test game"]
    )
    game_id = create_result.stdout.split("(")[1].split(")")[0]
    
    result = runner.invoke(app, ["game", "activate", "--id", game_id])
    assert result.exit_code == 0
    assert f"Activated game: Test Game ({game_id})" in result.stdout

def test_game_info_no_active(temp_base_dir, monkeypatch):
    """Test getting game info when no game is active."""
    monkeypatch.setattr("sologm.core.game.FileManager", 
                       lambda: FileManager(temp_base_dir))
    
    result = runner.invoke(app, ["game", "info"])
    assert result.exit_code == 0
    assert "No active game." in result.stdout

def test_game_info(temp_base_dir, monkeypatch):
    """Test getting info for the active game."""
    monkeypatch.setattr("sologm.core.game.FileManager", 
                       lambda: FileManager(temp_base_dir))
    
    # Create and activate a game
    runner.invoke(
        app, 
        ["game", "create", "--name", "Test Game", "--description", "A test game"]
    )
    
    result = runner.invoke(app, ["game", "info"])
    assert result.exit_code == 0
    assert "Test Game" in result.stdout
    assert "A test game" in result.stdout
    assert "Status: active" in result.stdout
