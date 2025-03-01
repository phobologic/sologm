"""
Service for interacting with the Anthropic Claude API.
"""
import os
import logging
import json
from typing import Dict, List, Optional, Any

import anthropic
from anthropic import Anthropic

from ..models.user import UserPreferences, user_preferences

logger = logging.getLogger(__name__)

# Default system prompt template for RPG interpretations
DEFAULT_SYSTEM_PROMPT = """
You are an assistant helping with a GM-less tabletop roleplaying game. 
Your role is to provide creative interpretations for game situations based on context provided.
You should provide 5 distinct, creative, and evocative possibilities for what might happen next in the story.
Keep your interpretations concise, interesting, and appropriate to the setting described.
Do not add any explanations or commentary - only provide the interpretations as a numbered list.
"""


class ClaudeClient:
    """Client for interacting with the Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Claude API client.
        
        Args:
            api_key: Anthropic API key (if not provided, will use ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = Anthropic(api_key=self.api_key)
    
    def generate_interpretations(
        self, 
        context: str, 
        keywords: List[str], 
        user_id: Optional[str] = None,
        num_options: int = 5,
        max_tokens: int = 1000
    ) -> List[str]:
        """
        Generate interpretation options for an RPG scenario using Claude.
        
        Args:
            context: Current game situation context
            keywords: List of keywords/themes to focus on
            user_id: Slack user ID (to retrieve setting preferences)
            num_options: Number of interpretation options to generate
            max_tokens: Maximum tokens in the response
            
        Returns:
            List of interpretation strings
        """
        # Get user setting preferences if available
        setting_context = ""
        if user_id and user_id in user_preferences:
            prefs = user_preferences[user_id]
            if hasattr(prefs, 'setting_description') and prefs.setting_description:
                setting_context = f"SETTING INFORMATION:\n{prefs.setting_description}\n\n"
        
        # Prepare the system prompt
        system_prompt = DEFAULT_SYSTEM_PROMPT
        if num_options != 5:
            system_prompt = system_prompt.replace(
                "provide 5 distinct", 
                f"provide {num_options} distinct"
            )
        
        # Format the keywords into a string
        keywords_str = ", ".join(keywords)
        
        # Construct the user message
        user_message = (
            f"GAME SETTING:\n{setting_context}\n\n"
            f"CURRENT SITUATION:\n{context}\n\n"
            f"Keywords: {keywords_str}"
        )
        
        try:
            # Call the Claude API
            response = self.client.messages.create(
                model="claude-3-opus-20240229",  # Use the best available model
                system=system_prompt,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Process the response
            response_text = response.content[0].text
            
            # Parse the numbered list
            interpretations = self._parse_numbered_list(response_text, num_options)
            
            return interpretations
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            # Return fallback interpretations if API call fails
            return [
                f"Error generating interpretations: {str(e)}",
                "The situation takes an unexpected turn...",
                "Something mysterious happens...",
                "A new character appears...",
                "The environment changes suddenly..."
            ][:num_options]
    
    def _parse_numbered_list(self, text: str, expected_count: int) -> List[str]:
        """
        Parse a numbered list from Claude's response.
        
        Args:
            text: Response text from Claude
            expected_count: Expected number of list items
            
        Returns:
            List of extracted interpretations
        """
        lines = text.strip().split("\n")
        interpretations = []
        current_item = ""
        
        for line in lines:
            line = line.strip()
            # Check for numbered list format (1., 2., etc.)
            if line and line[0].isdigit() and line[1:].startswith('. '):
                # If we were building a previous item, save it
                if current_item:
                    interpretations.append(current_item.strip())
                
                # Start new item, removing the number prefix
                current_item = line[line.find(' ')+1:]
            elif current_item:
                # Continue building the current item
                current_item += " " + line
        
        # Add the last item if it exists
        if current_item:
            interpretations.append(current_item.strip())
        
        # If we didn't get the expected number, try a different parsing method
        if len(interpretations) != expected_count:
            # Simple fallback - look for lines starting with numbers
            interpretations = []
            for line in lines:
                line = line.strip()
                if line and line[0].isdigit():
                    # Try to extract just the content part
                    parts = line.split(" ", 1)
                    if len(parts) > 1:
                        interpretations.append(parts[1].strip())
        
        # If we still don't have the right number, just return the whole text split
        if len(interpretations) != expected_count:
            # Last resort - split the text into roughly equal parts
            interpretations = []
            words = text.split()
            words_per_part = max(1, len(words) // expected_count)
            
            for i in range(0, min(expected_count, len(words)), words_per_part):
                end_idx = min(i + words_per_part, len(words))
                part = " ".join(words[i:end_idx])
                interpretations.append(part)
        
        # Ensure we return exactly the expected number
        return interpretations[:expected_count]


# Initialize a singleton instance
claude_client = None

def get_claude_client() -> ClaudeClient:
    """
    Get or create the Claude client singleton.
    
    Returns:
        ClaudeClient instance
    """
    global claude_client
    if claude_client is None:
        claude_client = ClaudeClient()
    return claude_client