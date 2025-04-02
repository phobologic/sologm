# Technical Design Document: Solo RPG Helper CLI

## 1. Introduction

### 1.1 Purpose and Scope
This Technical Design Document (TDD) outlines the detailed technical implementation for the Solo RPG Helper command-line application. It serves as the engineering blueprint for developing the application according to the specifications in the Product Requirements Document (PRD).

### 1.2 Relationship to PRD
This TDD is derived from the PRD document "Product Requirements Document: Solo RPG Helper Command-Line Application." The TDD translates the product requirements into technical specifications and architectural decisions.

### 1.3 Key Technical Goals
- Create a modular, maintainable CLI tool using Python 3.13
- Implement a YAML-based file storage system
- Integrate with Anthropic's Claude API for oracle interpretation
- Provide a seamless command-line experience for solo RPG gamers
- Ensure reliability and appropriate error handling

## 2. System Architecture

### 2.1 High-Level Design

The Solo RPG Helper will be implemented using a modular architecture with the following primary components:

```
sologm/
├── __init__.py
├── cli/              # Typer-based CLI interface
│   ├── __init__.py
│   ├── main.py       # Entry point
│   ├── game.py       # Game commands
│   ├── scene.py      # Scene commands
│   ├── event.py      # Event commands
│   ├── oracle.py     # Oracle interpretation commands
│   ├── dice.py       # Dice rolling commands
│   └── tests/        # CLI-related tests
├── core/             # Core business logic
│   ├── __init__.py
│   ├── game.py       # Game management
│   ├── scene.py      # Scene management
│   ├── event.py      # Event tracking
│   ├── oracle.py     # Oracle interpretation
│   ├── dice.py       # Dice system
│   └── tests/        # Core logic tests
├── storage/          # Data storage functionality
│   ├── __init__.py
│   ├── file_manager.py  # File I/O operations
│   ├── models.py     # Data models and schema
│   └── tests/        # Storage tests
├── integrations/     # External service integrations
│   ├── __init__.py
│   ├── anthropic.py  # Claude API integration
│   └── tests/        # Integration tests
└── utils/
    ├── __init__.py
    ├── config.py     # Configuration management
    ├── logger.py     # Logging utilities
    ├── errors.py     # Error handling
    └── tests/        # Utility tests
```

### 2.2 Component Interaction Diagram

```
[CLI Layer] <---> [Core Business Logic] <---> [Storage Layer]
                         ^
                         |
                  [External Integrations]
```

### 2.3 Design Patterns

The application will use the following design patterns:

1. **Command Pattern**: Implemented through Typer to handle CLI commands
2. **Repository Pattern**: For data access and management
3. **Factory Pattern**: For creating game, scene, and event objects
4. **Facade Pattern**: To simplify complex subsystems like the AI integration

## 3. Component Design

### 3.1 Command Line Interface

#### 3.1.1 Implementation Details
- Framework: Typer
- Structure: Command groups organized by domain (game, scene, event, oracle, dice)
- Error handling: Clear user messages with optional debug mode for verbose output

#### 3.1.2 Command Structure
```python
# Example implementation of CLI structure with Typer
import typer
from typing import Optional

app = typer.Typer()
game_app = typer.Typer()
scene_app = typer.Typer()
event_app = typer.Typer()
oracle_app = typer.Typer()
dice_app = typer.Typer()

app.add_typer(game_app, name="game", help="Game management commands")
app.add_typer(scene_app, name="scene", help="Scene management commands")
app.add_typer(event_app, name="event", help="Event tracking commands")
app.add_typer(oracle_app, name="oracle", help="Oracle interpretation commands")
app.add_typer(dice_app, name="dice", help="Dice rolling commands")

@game_app.command("create")
def create_game(
    name: str = typer.Option(..., "--name", help="Name of the game"),
    description: str = typer.Option(..., "--description", help="Game description")
):
    """Create a new game."""
    # Implementation will call core.game.create_game()
    pass

# Additional commands follow the same pattern
```

### 3.2 Game Management Module

#### 3.2.1 Core Functionality
- Game creation, listing, activation, and status retrieval
- State management for active game

#### 3.2.2 Key Methods
```python
def create_game(name: str, description: str) -> Game:
    """Create a new game with the given name and description."""
    
def list_games() -> list[Game]:
    """List all games in the system."""
    
def activate_game(game_id: str) -> Game:
    """Set the specified game as active."""
    
def get_active_game() -> Optional[Game]:
    """Get the currently active game, if one exists."""
```

### 3.3 Scene Management Module

#### 3.3.1 Core Functionality
- Scene creation, listing, and status retrieval
- Management of active scenes within a game

#### 3.3.2 Key Methods
```python
def create_scene(game_id: str, title: str, description: str) -> Scene:
    """Create a new scene in the specified game."""
    
def list_scenes(game_id: str) -> list[Scene]:
    """List all scenes for the specified game."""
    
def get_current_scene(game_id: str) -> Optional[Scene]:
    """Get the current scene for the specified game."""
    
def complete_scene(game_id: str, scene_id: str) -> Scene:
    """Mark a scene as complete without changing which scene is current."""

def set_current_scene(game_id: str, scene_id: str) -> Scene:
    """Set which scene is currently being played without changing its status."""
```

### 3.4 Event Tracking Module

#### 3.4.1 Core Functionality
- Event creation and retrieval
- Management of event history within a scene

#### 3.4.2 Key Methods
```python
def add_event(game_id: str, scene_id: str, text: str, source: str = "manual") -> Event:
    """Add a new event to the specified scene."""
    
def list_events(game_id: str, scene_id: str, limit: int = 5) -> list[Event]:
    """List recent events for the specified scene."""
```

### 3.5 Oracle Interpretation System

#### 3.5.1 Core Functionality
- Interpretation of oracle results using Claude API
- Generation of multiple interpretation options
- Selection and conversion of interpretations to events

#### 3.5.2 Key Methods
```python
def interpret_oracle(
    game_id: str,
    scene_id: str,
    context: str,
    oracle_results: str,
    count: int = 5
) -> list[Interpretation]:
    """Submit oracle results for AI interpretation."""
    
def select_interpretation(
    game_id: str,
    scene_id: str,
    interpretation_id: str
) -> Event:
    """Select an interpretation and add it as an event."""
```

#### 3.5.3 Oracle Interpretation Management
The system will track the current interpretation and handle retries:

```python
def set_current_interpretation(
    self,
    game_id: str,
    interpretation_set_id: str,
    context: str,
    oracle_results: str
) -> None:
    """Set the current interpretation for a game."""
    game_data = self.file_manager.read_yaml(
        self.file_manager.get_game_path(game_id)
    )
    game_data["current_interpretation"] = {
        "id": interpretation_set_id,
        "context": context,
        "results": oracle_results,
        "retry_count": 0
    }
    self.file_manager.write_yaml(
        self.file_manager.get_game_path(game_id),
        game_data
    )

def get_current_interpretation(
    self,
    game_id: str
) -> Optional[dict]:
    """Get the current interpretation data for a game."""
    game_data = self.file_manager.read_yaml(
        self.file_manager.get_game_path(game_id)
    )
    return game_data.get("current_interpretation")

def retry_interpretation(
    self,
    game_id: str,
    scene_id: str
) -> InterpretationSet:
    """Generate new interpretations for the current context/results."""
    current = self.get_current_interpretation(game_id)
    if not current:
        raise OracleError("No current interpretation to retry")
    
    # Increment retry count
    current["retry_count"] += 1
    game_data = self.file_manager.read_yaml(
        self.file_manager.get_game_path(game_id)
    )
    game_data["current_interpretation"] = current
    self.file_manager.write_yaml(
        self.file_manager.get_game_path(game_id),
        game_data
    )
    
    # Get new interpretations with retry context
    return self.get_interpretations(
        game_id,
        scene_id,
        current["context"],
        current["results"],
        retry_attempt=current["retry_count"]
    )
```

#### 3.5.4 Claude API Integration
The system will use Anthropic's Python SDK to interact with Claude:

```python
from anthropic import Anthropic

def generate_interpretations(
    game_description: str,
    scene_description: str,
    recent_events: list[str],
    context: str,
    oracle_results: str,
    count: int,
    retry_attempt: int = 0
) -> list[Interpretation]:
    """Generate interpretations using Claude API."""
    
    client = Anthropic(api_key=get_api_key())
    
    # Construct prompt with all relevant context
    retry_context = f"This is attempt #{retry_attempt + 1} for this context/results pair. Please provide different interpretations from previous attempts." if retry_attempt > 0 else ""
    
    prompt = f"""
    You are interpreting oracle results for a solo RPG player.
    
    Game: {game_description}
    Current Scene: {scene_description}
    Recent Events: {', '.join(recent_events)}
    
    Player's Question/Context: {context}
    Oracle Results: {oracle_results}
    {retry_context}
    
    Please provide {count} different interpretations of these oracle results.
    Format your response exactly as follows:
    
    === BEGIN INTERPRETATIONS ===
    
    --- INTERPRETATION 1 ---
    TITLE: Short title for the interpretation
    DESCRIPTION: Detailed description of interpretation idea
    --- END INTERPRETATION 1 ---
    
    [and so on for each interpretation]
    
    === END INTERPRETATIONS ===
    """
    
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0.7,
        system="You are a helpful assistant for solo roleplaying games.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response and extract interpretations
    return parse_interpretations(response.content[0].text)
```

### 3.6 Dice System

#### 3.6.1 Core Functionality
- Parsing of standard dice notation
- Dice rolling with modifiers
- Result formatting and display

#### 3.6.2 Implementation
```python
import re
import random
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DiceRoll:
    notation: str
    individual_results: List[int]
    modifier: int
    total: int
    reason: Optional[str]

def parse_dice_notation(notation: str) -> tuple[int, int, int]:
    """Parse XdY+Z notation into components."""
    pattern = r"(\d+)d(\d+)([+-]\d+)?"
    match = re.match(pattern, notation)
    
    if not match:
        raise ValueError(f"Invalid dice notation: {notation}")
    
    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3) or 0)
    
    return count, sides, modifier

def roll_dice(notation: str, reason: Optional[str] = None) -> DiceRoll:
    """Roll dice according to the specified notation."""
    count, sides, modifier = parse_dice_notation(notation)
    
    if count <= 0 or sides <= 1:
        raise ValueError("Invalid dice parameters")
    
    individual_results = [random.randint(1, sides) for _ in range(count)]
    total = sum(individual_results) + modifier
    
    return DiceRoll(
        notation=notation,
        individual_results=individual_results,
        modifier=modifier,
        total=total,
        reason=reason
    )
```

## 4. Data Models and Storage

### 4.1 YAML Schema Definitions

#### 4.1.1 Game Schema
```yaml
# game.yaml
id: "unique-game-id"
name: "Game Name"
description: "Game description"
created_at: "2025-04-01T12:00:00Z"
modified_at: "2025-04-01T14:30:00Z"
scenes:
  - "scene-id-1"
  - "scene-id-2"
```

#### 4.1.2 Scene Schema
```yaml
# scene.yaml
id: "unique-scene-id"
game_id: "parent-game-id"
title: "Scene Title"
description: "Scene description"
status: "active"  # Scene's completion status: active or completed
sequence: 1
created_at: "2025-04-01T12:30:00Z"
modified_at: "2025-04-01T14:45:00Z"

# current_scene file in game directory
scene_id: "unique-scene-id"  # ID of current scene being played
```

#### 4.1.3 Events Schema
```yaml
# events.yaml
- id: "event-id-1"
  scene_id: "parent-scene-id"
  description: "Event description"
  source: "manual"  # manual, oracle, dice
  created_at: "2025-04-01T13:00:00Z"
- id: "event-id-2"
  scene_id: "parent-scene-id"
  description: "Another event"
  source: "oracle"
  created_at: "2025-04-01T13:15:00Z"
```

#### 4.1.4 Interpretation Schema
```yaml
# interpretation_{timestamp}.yaml
id: "unique-interpretation-id"
scene_id: "parent-scene-id"
context: "User question/context"
oracle_results: "Original oracle results"
created_at: "2025-04-01T13:10:00Z"
selected_interpretation: 2  # Index of selected interpretation, if any
interpretations:
  - title: "Interpretation 1 Title"
    description: "Interpretation 1 Description"
  - title: "Interpretation 2 Title"
    description: "Interpretation 2 Description"
  # Additional interpretations...
```

### 4.2 File Storage Implementation

#### 4.2.1 File Manager Implementation
```python
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

class FileManager:
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the file manager with the base directory."""
        if base_dir is None:
            base_dir = Path.home() / ".sologm"
        self.base_dir = base_dir
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self) -> None:
        """Ensure the required directory structure exists."""
        (self.base_dir / "games").mkdir(parents=True, exist_ok=True)
    
    def read_yaml(self, path: Path) -> Dict[str, Any]:
        """Read YAML file and return its contents as a dictionary."""
        if not path.exists():
            return {}
        
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    
    def write_yaml(self, path: Path, data: Dict[str, Any]) -> None:
        """Write data to a YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def get_active_game_id(self) -> Optional[str]:
        """Get the ID of the active game, if any."""
        active_game_file = self.base_dir / "active_game"
        
        if not active_game_file.exists():
            return None
        
        with open(active_game_file, "r") as f:
            return f.read().strip() or None
    
    def set_active_game_id(self, game_id: str) -> None:
        """Set the ID of the active game."""
        active_game_file = self.base_dir / "active_game"
        
        with open(active_game_file, "w") as f:
            f.write(game_id)
    
    # Additional methods for game, scene, event, and interpretation management
```

## 5. External Integrations

### 5.1 Anthropic API Integration

#### 5.1.1 Client Setup
```python
from anthropic import Anthropic
from typing import Optional

class AnthropicClient:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Anthropic client."""
        self.api_key = api_key or self._get_api_key_from_env()
        self.client = Anthropic(api_key=self.api_key)
    
    def _get_api_key_from_env(self) -> str:
        """Get the Anthropic API key from environment variables."""
        import os
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Please set the ANTHROPIC_API_KEY "
                "environment variable or provide it in the configuration."
            )
        
        return api_key
```

#### 5.1.2 Oracle Interpretation Implementation
```python
def get_interpretations(
    self,
    game_description: str,
    scene_description: str,
    recent_events: list[str],
    context: str,
    oracle_results: str,
    count: int = 5
) -> list[dict]:
    """Get interpretations from Claude API."""
    prompt = self._build_prompt(
        game_description,
        scene_description,
        recent_events,
        context,
        oracle_results,
        count
    )
    
    response = self.client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=2000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return self._parse_interpretations(response.content[0].text)

def _build_prompt(
    self,
    game_description: str,
    scene_description: str,
    recent_events: list[str],
    context: str,
    oracle_results: str,
    count: int
) -> str:
    """Build the prompt for the Anthropic API."""
    events_text = "\n".join([f"- {event}" for event in recent_events]) if recent_events else "No recent events"
    
    return f"""
    You are interpreting oracle results for a solo RPG player.
    
    Game: {game_description}
    Current Scene: {scene_description}
    Recent Events:
    {events_text}
    
    Player's Question/Context: {context}
    Oracle Results: {oracle_results}
    
    Please provide {count} different interpretations of these oracle results.
    Each interpretation should make sense in the context of the game and scene.
    Be creative but consistent with the established narrative.
    
    Format your response exactly as follows:
    
    === BEGIN INTERPRETATIONS ===
    
    --- INTERPRETATION 1 ---
    TITLE: Short title for the interpretation
    DESCRIPTION: Detailed description of interpretation idea
    --- END INTERPRETATION 1 ---
    
    --- INTERPRETATION 2 ---
    TITLE: Short title for the interpretation
    DESCRIPTION: Detailed description of interpretation idea
    --- END INTERPRETATION 2 ---
    
    (and so on for each interpretation)
    
    === END INTERPRETATIONS ===
    """

def _parse_interpretations(self, response_text: str) -> list[dict]:
    """Parse the interpretations from the API response."""
    import re
    
    pattern = r"--- INTERPRETATION (\d+) ---\nTITLE: (.*?)\nDESCRIPTION: (.*?)\n--- END INTERPRETATION \1 ---"
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    interpretations = []
    for _, title, description in matches:
        interpretations.append({
            "title": title.strip(),
            "description": description.strip()
        })
    
    return interpretations
```

## 6. Error Handling and Logging

### 6.1 Error Handling Strategy

The application will use a two-tiered approach to error handling:

1. **User-facing errors**: Clear, concise error messages displayed in the terminal
2. **Debug mode**: Detailed logging and full exception traces when enabled

#### 6.1.1 Error Types
```python
class SoloGMError(Exception):
    """Base exception for all Solo GM errors."""
    pass

class GameError(SoloGMError):
    """Errors related to game management."""
    pass

class SceneError(SoloGMError):
    """Errors related to scene management."""
    pass

class EventError(SoloGMError):
    """Errors related to event tracking."""
    pass

class OracleError(SoloGMError):
    """Errors related to oracle interpretation."""
    pass

class DiceError(SoloGMError):
    """Errors related to dice rolling."""
    pass

class StorageError(SoloGMError):
    """Errors related to data storage."""
    pass

class APIError(SoloGMError):
    """Errors related to external API calls."""
    pass
```

#### 6.1.2 Error Handling in CLI
```python
import typer
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

def handle_errors(debug: bool = False) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to handle errors in CLI commands."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except SoloGMError as e:
                if debug:
                    typer.echo(f"Error: {str(e)}")
                    import traceback
                    typer.echo(traceback.format_exc())
                    raise typer.Exit(1)
                else:
                    typer.echo(f"Error: {str(e)}")
                    typer.echo("Run with --debug for more information.")
                    raise typer.Exit(1)
            except Exception as e:
                if debug:
                    typer.echo(f"Unexpected error: {str(e)}")
                    import traceback
                    typer.echo(traceback.format_exc())
                    raise typer.Exit(1)
                else:
                    typer.echo("An unexpected error occurred.")
                    typer.echo("Run with --debug for more information.")
                    raise typer.Exit(1)
        return wrapper
    return decorator
```

### 6.2 Logging Strategy

```python
import logging
import sys
from typing import Optional

def setup_logger(debug: bool = False) -> logging.Logger:
    """Set up the logger for the application.
    
    When debug mode is enabled, logs will be sent to stdout.
    Otherwise, only error logs will be displayed.
    """
    logger = logging.getLogger("sologm")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)  # Output to stdout
    
    if debug:
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        console_handler.setLevel(logging.ERROR)  # Only show errors in normal mode
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger
```

## 7. Development Environment and Tools

### 7.1 Development Setup with uv

```bash
# Create a new project with uv
uv venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate  # On Windows

# Install development dependencies
uv pip install typer pyyaml anthropic pytest pytest-cov black isort mypy
```

### 7.2 Development Tools Configuration

#### 7.2.1 pyproject.toml
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sologm"
version = "0.1.0"
description = "Solo RPG Helper command-line application"
readme = "README.md"
requires-python = ">=3.13"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Topic :: Games/Entertainment :: Role-Playing",
]
dependencies = [
    "typer>=0.9.0",
    "pyyaml>=6.0",
    "anthropic>=0.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.3.1",
    "pytest-cov>=4.1.0",
    "black>=23.3.0",
    "isort>=5.12.0",
    "mypy>=1.3.0",
]

[project.scripts]
sologm = "sologm.cli.main:app"

[tool.black]
line-length = 88
target-version = ["py313"]

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
python_files = "test_*.py"
testpaths = ["sologm"]
```

## 8. Testing Strategy

### 8.1 Unit Testing Framework

The application will use pytest for unit testing with tests located alongside the code they test:

```
sologm/
├── cli/
│   ├── main.py
│   ├── game.py
│   └── tests/
│       ├── conftest.py
│       ├── test_game.py
│       └── test_main.py
├── core/
│   ├── game.py
│   ├── dice.py
│   └── tests/
│       ├── test_game.py
│       └── test_dice.py
└── integrations/
    ├── anthropic.py
    └── tests/
        └── test_anthropic.py
```

We'll follow these testing principles:
1. Test each module independently
2. Mock external dependencies (file system, APIs)
3. Achieve high test coverage for critical components

### 8.2 Test Configuration

The `pyproject.toml` will need to be updated to reflect this test organization:

```toml
[tool.pytest.ini_options]
python_files = "test_*.py"
testpaths = ["sologm"]
```

### 8.3 Test Examples

#### 8.3.1 Dice System Tests (Located at sologm/core/tests/test_dice.py)
```python
import pytest
from ..dice import parse_dice_notation, roll_dice, DiceRoll

def test_parse_dice_notation_valid():
    """Test parsing valid dice notation."""
    assert parse_dice_notation("1d20") == (1, 20, 0)
    assert parse_dice_notation("3d6+2") == (3, 6, 2)
    assert parse_dice_notation("2d10-1") == (2, 10, -1)

def test_parse_dice_notation_invalid():
    """Test parsing invalid dice notation."""
    with pytest.raises(ValueError):
        parse_dice_notation("invalid")
    
    with pytest.raises(ValueError):
        parse_dice_notation("d20")
    
    with pytest.raises(ValueError):
        parse_dice_notation("20")

def test_roll_dice():
    """Test dice rolling functionality."""
    # Mocking random.randint for deterministic testing
    import random
    random.randint = lambda a, b: 4  # Always return 4
    
    result = roll_dice("3d6+2", "Test roll")
    
    assert result.notation == "3d6+2"
    assert result.individual_results == [4, 4, 4]
    assert result.modifier == 2
    assert result.total == 14
    assert result.reason == "Test roll"
```

#### 8.3.2 Oracle Interpretation Tests (Located at sologm/integrations/tests/test_anthropic.py)
```python
import pytest
from unittest.mock import MagicMock, patch
from ..anthropic import AnthropicClient

@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client for testing."""
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text="""
    === BEGIN INTERPRETATIONS ===
    
    --- INTERPRETATION 1 ---
    TITLE: Test Interpretation 1
    DESCRIPTION: Description for test interpretation 1
    --- END INTERPRETATION 1 ---
    
    --- INTERPRETATION 2 ---
    TITLE: Test Interpretation 2
    DESCRIPTION: Description for test interpretation 2
    --- END INTERPRETATION 2 ---
    
    === END INTERPRETATIONS ===
    """)]
    client.messages.create.return_value = response
    return client

@patch("anthropic.Anthropic")
def test_get_interpretations(mock_anthropic, mock_anthropic_client):
    """Test getting interpretations from the Anthropic API."""
    mock_anthropic.return_value = mock_anthropic_client
    
    client = AnthropicClient(api_key="test_key")
    interpretations = client.get_interpretations(
        game_description="Test Game",
        scene_description="Test Scene",
        recent_events=["Event 1", "Event 2"],
        context="Test Context",
        oracle_results="Test Oracle Results",
        count=2
    )
    
    assert len(interpretations) == 2
    assert interpretations[0]["title"] == "Test Interpretation 1"
    assert interpretations[0]["description"] == "Description for test interpretation 1"
    assert interpretations[1]["title"] == "Test Interpretation 2"
    assert interpretations[1]["description"] == "Description for test interpretation 2"
```

## 9. Deployment and Distribution

### 9.1 Package Structure
The final package will have the following structure for distribution:

```
sologm/
├── __init__.py
├── cli/
├── core/
├── storage/
├── integrations/
└── utils/
setup.py
pyproject.toml
LICENSE
README.md
```

### 9.2 Installation Process
```bash
# Install from PyPI
pip install sologm

# Install from GitHub
pip install git+https://github.com/username/sologm.git
```

### 9.3 Configuration During Installation
Upon first run, the application will:
1. Create the ~/.sologm directory structure
2. Create a default configuration file
3. Prompt for the Anthropic API key if not found in environment variables

## 10. Maintenance and Support

### 10.1 Logging Strategy
- All debug logs sent to stdout when debug mode is enabled 
- Error logs displayed regardless of debug mode
- No log files created - simplifies the application and reduces storage requirements
- Users can redirect output to files manually if needed using standard shell redirection
