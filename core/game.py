"""Game management functionality."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sologm.storage.file_manager import FileManager
from sologm.utils.errors import GameError

@dataclass
class Game:
    """Represents a game in the system."""
    
    id: str
    name: str
    description: str
    status: str  # active, inactive, completed, abandoned
    created_at: datetime
    modified_at: datetime
    scenes: List[str]

class GameManager:
    """Manages game operations."""
    
    def __init__(self, file_manager: Optional[FileManager] = None):
        """Initialize the game manager.
        
        Args:
            file_manager: FileManager instance to use.
                         If None, creates a new instance.
        """
        self.file_manager = file_manager or FileManager()
    
    def create_game(self, name: str, description: str) -> Game:
        """Create a new game.
        
        Args:
            name: Name of the game.
            description: Description of the game.
            
        Returns:
            The created Game instance.
            
        Raises:
            GameError: If the game cannot be created.
        """
        # Generate a URL-friendly ID from the name
        game_id = "-".join(name.lower().split())
        
        # Ensure uniqueness by adding a UUID suffix if needed
        base_id = game_id
        counter = 1
        while Path(self.file_manager.get_game_path(game_id)).exists():
            suffix = str(uuid.uuid4())[:8]
            game_id = f"{base_id}-{suffix}"
            counter += 1
            if counter > 10:  # Prevent infinite loops
                raise GameError(f"Failed to generate unique ID for game: {name}")
        
        # Create the game instance
        now = datetime.now()
        game = Game(
            id=game_id,
            name=name,
            description=description,
            status="active",
            created_at=now,
            modified_at=now,
            scenes=[]
        )
        
        # Save the game data
        try:
            self.file_manager.write_yaml(
                self.file_manager.get_game_path(game_id),
                {
                    "id": game.id,
                    "name": game.name,
                    "description": game.description,
                    "status": game.status,
                    "created_at": game.created_at.isoformat(),
                    "modified_at": game.modified_at.isoformat(),
                    "scenes": game.scenes
                }
            )
            
            # Set as active game
            self.file_manager.set_active_game_id(game_id)
            
            return game
            
        except Exception as e:
            raise GameError(f"Failed to create game: {str(e)}")
    
    def list_games(self) -> List[Game]:
        """List all games in the system.
        
        Returns:
            List of Game instances.
            
        Raises:
            GameError: If games cannot be listed.
        """
        try:
            games_dir = self.file_manager.base_dir / "games"
            games = []
            
            if not games_dir.exists():
                return games
            
            for game_dir in games_dir.iterdir():
                if game_dir.is_dir():
                    game_path = game_dir / "game.yaml"
                    if game_path.exists():
                        game_data = self.file_manager.read_yaml(game_path)
                        games.append(Game(
                            id=game_data["id"],
                            name=game_data["name"],
                            description=game_data["description"],
                            status=game_data["status"],
                            created_at=datetime.fromisoformat(game_data["created_at"]),
                            modified_at=datetime.fromisoformat(game_data["modified_at"]),
                            scenes=game_data["scenes"]
                        ))
            
            return sorted(games, key=lambda g: g.created_at)
            
        except Exception as e:
            raise GameError(f"Failed to list games: {str(e)}")
    
    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a specific game by ID.
        
        Args:
            game_id: ID of the game to get.
            
        Returns:
            Game instance if found, None otherwise.
            
        Raises:
            GameError: If the game cannot be retrieved.
        """
        try:
            game_path = self.file_manager.get_game_path(game_id)
            if not game_path.exists():
                return None
                
            game_data = self.file_manager.read_yaml(game_path)
            return Game(
                id=game_data["id"],
                name=game_data["name"],
                description=game_data["description"],
                status=game_data["status"],
                created_at=datetime.fromisoformat(game_data["created_at"]),
                modified_at=datetime.fromisoformat(game_data["modified_at"]),
                scenes=game_data["scenes"]
            )
            
        except Exception as e:
            raise GameError(f"Failed to get game {game_id}: {str(e)}")
    
    def get_active_game(self) -> Optional[Game]:
        """Get the currently active game.
        
        Returns:
            Active Game instance if one exists, None otherwise.
            
        Raises:
            GameError: If the active game cannot be retrieved.
        """
        try:
            game_id = self.file_manager.get_active_game_id()
            if not game_id:
                return None
            return self.get_game(game_id)
            
        except Exception as e:
            raise GameError(f"Failed to get active game: {str(e)}")
    
    def activate_game(self, game_id: str) -> Game:
        """Set a game as active.
        
        Args:
            game_id: ID of the game to activate.
            
        Returns:
            The activated Game instance.
            
        Raises:
            GameError: If the game cannot be activated.
        """
        try:
            game = self.get_game(game_id)
            if not game:
                raise GameError(f"Game not found: {game_id}")
            
            self.file_manager.set_active_game_id(game_id)
            return game
            
        except Exception as e:
            raise GameError(f"Failed to activate game {game_id}: {str(e)}")
