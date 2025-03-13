"""
Game-specific AI helper services.
"""
from typing import List, Optional, Dict, Any, Tuple
import re
import random

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import GameType, MythicChaosFactor
from sologm.rpg_helper.models.scene import Scene, SceneStatus
from sologm.rpg_helper.services.ai.factory import AIServiceFactory
from sologm.rpg_helper.services.game.service_factory import ServiceFactory
from sologm.rpg_helper.services.game.mythic_game_service import MythicGameService
from sologm.rpg_helper.utils.logging import get_logger
from .service import AIService, AIServiceError, AIResponseError

logger = get_logger()


class GameAIHelper:
    """Helper class for game-specific AI interactions."""
    
    def __init__(self, game: Game):
        """
        Initialize the game AI helper.
        
        Args:
            game: The game to use for generating content
        """
        logger.debug("Initializing game AI helper", service_type=type(game).__name__)
        self.game = game
        self.game_service = ServiceFactory.create_game_service(game)
        logger.info("Game AI helper initialized")
    
    def generate_outcome_ideas(self, 
                              game: Game,
                              scene: Optional[Scene] = None,
                              additional_context: Optional[str] = None,
                              focus_words: Optional[List[str]] = None,
                              num_ideas: int = 5) -> List[str]:
        """
        Generate potential outcome ideas for a game scene.
        
        Args:
            game: The game to generate ideas for
            scene: Optional current scene (defaults to game.current_scene)
            additional_context: Optional additional context to consider
            focus_words: Optional list of words to focus on (ideally 2)
            num_ideas: Number of ideas to generate (default: 5)
            
        Returns:
            List of outcome idea strings
            
        Raises:
            AIServiceError: If there's an error generating ideas
            ValueError: If no scene is provided and game has no current scene
        """
        logger.info(
            "Generating outcome ideas",
            game_id=game.id,
            scene_id=scene.id if scene else None,
            num_ideas=num_ideas
        )
        
        # Use provided scene or current scene
        if scene is None:
            scene = game.current_scene
            if scene is None:
                logger.error("No scene provided and game has no current scene", game_id=game.id)
                raise ValueError("No scene provided and game has no current scene")
        
        # Build the prompt
        prompt = self._build_outcome_prompt(
            game=game,
            scene=scene,
            additional_context=additional_context,
            focus_words=focus_words,
            num_ideas=num_ideas
        )
        
        logger.debug("Built prompt for outcome generation", prompt=prompt)
        
        # Generate ideas
        try:
            response = self.ai_service.generate_text(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.8,
                system_prompt="You are a creative game master assistant helping with tabletop RPG ideas."
            )
            
            # Parse the response into a list of ideas
            ideas = self._parse_outcome_ideas(response, num_ideas)
            
            logger.info("Generated outcome ideas", count=len(ideas))
            logger.debug("Generated ideas", ideas=ideas)
            
            return ideas
            
        except Exception as e:
            logger.error(
                "Error generating outcome ideas",
                error=str(e),
                error_type=type(e).__name__,
                game_id=game.id,
                scene_id=scene.id
            )
            raise
    
    def _build_outcome_prompt(self,
                             game: Game,
                             scene: Scene,
                             additional_context: Optional[str],
                             focus_words: Optional[List[str]],
                             num_ideas: int) -> str:
        """Build the prompt for generating outcome ideas."""
        logger.debug(
            "Building outcome prompt",
            game_id=game.id,
            scene_id=scene.id,
            focus_words=focus_words
        )
        
        # Start with basic information
        prompt_parts = [
            f"Generate {num_ideas} potential outcome ideas for a tabletop RPG scene.",
            "\nGame information:",
            f"- Game name: {game.name}",
        ]
        
        # Add setting if available
        if game.setting_info:
            prompt_parts.append(f"- Setting: {game.setting_info}")
        
        # Add scene information
        prompt_parts.append("\nCurrent scene:")
        if scene.title:
            prompt_parts.append(f"- Title: {scene.title}")
        if scene.description:
            prompt_parts.append(f"- Description: {scene.description}")
        
        # Add scene events if any
        if scene.events:
            prompt_parts.append("\nRecent events:")
            for event in scene.events[-3:]:  # Just use the last 3 events
                prompt_parts.append(f"- {event.description}")
        
        # Add additional context if provided
        if additional_context:
            prompt_parts.append(f"\nAdditional context: {additional_context}")
        
        # Add focus words if provided
        if focus_words and len(focus_words) > 0:
            words_str = ", ".join(focus_words)
            prompt_parts.append(f"\nFocus on these words/concepts: {words_str}")
        
        # Add specific instructions
        prompt_parts.append(
            f"\nPlease generate {num_ideas} creative and interesting outcome ideas "
            "that could happen next in this scene. Each idea should be a complete "
            "paragraph describing a potential development or twist.\n\n"
            "FORMAT: Respond with a JSON array of strings, where each string is "
            "one complete idea. Example format:\n"
            '["First complete idea here.", "Second complete idea here.", ...]\n\n'
            "Ensure the response is valid JSON. Start directly with the opening "
            "bracket and end with the closing bracket."
        )
        
        prompt = "\n".join(prompt_parts)
        logger.debug("Built prompt", prompt=prompt)
        return prompt
    
    def _parse_outcome_ideas(self, response: str, expected_count: int) -> List[str]:
        """Parse the AI response into a list of distinct ideas."""
        logger.debug("Parsing outcome ideas", response_length=len(response))
        
        try:
            import json
            ideas = json.loads(response)
            
            if not isinstance(ideas, list):
                logger.error("Response is not a JSON array", response=response[:100])
                raise AIResponseError("Expected JSON array in response")
                
            if len(ideas) < expected_count:
                logger.warning(
                    "Received fewer ideas than expected",
                    expected=expected_count,
                    received=len(ideas)
                )
            
            # Take up to the expected number of items
            result = ideas[:expected_count]
            logger.debug("Parsed ideas", count=len(result))
            return result
            
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON response",
                error=str(e),
                response=response[:100]
            )
            raise AIResponseError("Failed to parse JSON response") from e

    def get_game_context(self) -> Dict[str, Any]:
        """
        Get context information about the game for AI.
        
        Returns:
            Dict with game context information
        """
        context = {
            "game_id": self.game.id,
            "game_name": self.game.name,
            "game_type": self.game.game_type.value,
            "game_description": self.game.description or "",
        }
        
        # Add game type specific context
        if self.game.game_type == GameType.MYTHIC:
            mythic_service = self.game_service
            if not isinstance(mythic_service, MythicGameService):
                mythic_service = MythicGameService(self.game)
                
            context["chaos_factor"] = mythic_service.get_chaos_factor()
        
        # Add active scene if any
        active_scene = self.game_service.get_active_scene()
        if active_scene:
            context["active_scene"] = {
                "id": active_scene.id,
                "title": active_scene.title,
                "description": active_scene.description,
                "events": [
                    {"text": event.text, "created_at": event.created_at.isoformat()}
                    for event in active_scene.events
                ]
            }
        
        return context 