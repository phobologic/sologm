"""Anthropic API client for Solo RPG Helper."""

import logging
import os
from typing import Optional, List, Dict, Any

from anthropic import Anthropic
from anthropic._types import NOT_GIVEN

from sologm.utils.errors import APIError

logger = logging.getLogger(__name__)

class AnthropicClient:
    """Client for interacting with Anthropic's Claude API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Anthropic client.
        
        Args:
            api_key: Optional API key. If not provided, will try to get from
                    environment variable ANTHROPIC_API_KEY.
        
        Raises:
            APIError: If no API key is found or if client initialization fails.
        """
        try:
            self.api_key = api_key or self._get_api_key_from_env()
            logger.debug("Initializing Anthropic client")
            self.client = Anthropic(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise APIError(f"Failed to initialize Anthropic client: {str(e)}")
    
    def _get_api_key_from_env(self) -> str:
        """Get the Anthropic API key from environment variables.
        
        Returns:
            str: The API key.
            
        Raises:
            APIError: If no API key is found in environment variables.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            logger.error("Anthropic API key not found in environment variables")
            raise APIError(
                "Anthropic API key not found. Please set the ANTHROPIC_API_KEY "
                "environment variable or provide it in the configuration."
            )
        
        return api_key
    
    def send_message(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system: str = NOT_GIVEN,
    ) -> str:
        """Send a message to Claude and get the response.
        
        Args:
            prompt: The message to send to Claude.
            max_tokens: Maximum number of tokens in the response.
            temperature: Controls randomness in the response (0.0 to 1.0).
            system: Optional system message to set context.
            
        Returns:
            str: Claude's response text.
            
        Raises:
            APIError: If the API call fails.
        """
        try:
            logger.debug(f"Sending message to Claude with {max_tokens} max tokens")
            
            logger.debug(f"Sending message to Claude with prompt length: {len(prompt)}")
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text
            logger.debug(f"Successfully received response from Claude (length: {len(response_text)})")
            return response_text
            
        except Exception as e:
            logger.error(f"Failed to get response from Claude: {e}")
            raise APIError(f"Failed to get response from Claude: {str(e)}")
