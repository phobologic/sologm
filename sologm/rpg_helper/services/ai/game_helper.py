"""
Game-specific AI helper services.
"""
from typing import List, Optional, Dict, Any

from sologm.rpg_helper.models.game import Game
from sologm.rpg_helper.models.scene import Scene
from .service import AIService, AIServiceError


class GameAIHelper:
    """Helper class for game-specific AI interactions."""
    
    def __init__(self, ai_service: AIService):
        """
        Initialize the game AI helper.
        
        Args:
            ai_service: The AI service to use for generating content
        """
        self.ai_service = ai_service
    
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
        # Use provided scene or current scene
        if scene is None:
            scene = game.current_scene
            if scene is None:
                raise ValueError("No scene provided and game has no current scene")
        
        # Build the prompt
        prompt = self._build_outcome_prompt(
            game=game,
            scene=scene,
            additional_context=additional_context,
            focus_words=focus_words,
            num_ideas=num_ideas
        )
        
        # Generate ideas
        response = self.ai_service.generate_text(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.8,
            system_prompt="You are a creative game master assistant helping with tabletop RPG ideas."
        )
        
        # Parse the response into a list of ideas
        ideas = self._parse_outcome_ideas(response, num_ideas)
        return ideas
    
    def _build_outcome_prompt(self,
                             game: Game,
                             scene: Scene,
                             additional_context: Optional[str],
                             focus_words: Optional[List[str]],
                             num_ideas: int) -> str:
        """Build the prompt for generating outcome ideas."""
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
            "that could happen next in this scene. Each idea should be a paragraph "
            "describing a potential development or twist. Number each idea clearly. "
            "Provide ONLY the numbered list with no introduction or conclusion. "
            "Start directly with '1.' and end with the last numbered item."
        )
        
        return "\n".join(prompt_parts)
    
    def _parse_outcome_ideas(self, response: str, expected_count: int) -> List[str]:
        """Parse the AI response into a list of distinct ideas."""
        # Simple parsing: split by numbered items and clean up
        ideas = []
        
        # Try to find numbered items (1., 2., etc.)
        import re
        numbered_items = re.split(r'\n\s*\d+[\.\)]\s*', response)
        
        # Remove any empty items and the text before the first number
        items = [item.strip() for item in numbered_items if item.strip()]
        if items and not response.strip().startswith("1"):
            items = items[1:]  # Remove text before first numbered item
        
        # If we couldn't find numbered items or found too few, just split by newlines
        if len(items) < expected_count:
            # Fallback: just split the text into roughly equal parts
            paragraphs = [p for p in response.split('\n\n') if p.strip()]
            if len(paragraphs) >= expected_count:
                items = paragraphs[:expected_count]
        
        # Take up to the expected number of items
        return items[:expected_count] 