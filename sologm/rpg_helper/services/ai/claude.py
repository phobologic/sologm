"""
Claude AI service implementation using Anthropic's API.
"""
import os
from typing import Dict, List, Optional, Any
import anthropic

from .service import AIService, AIRequestError, AIResponseError, AIServiceError
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()


class ClaudeService(AIService):
    """Service for interacting with Anthropic's Claude API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Claude service.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        logger.debug("Initializing Claude service", model=model)
        
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.error("No API key provided and ANTHROPIC_API_KEY not set")
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key.")
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("Claude service initialized", model=model)
    
    def generate_text(self, 
                     prompt: str, 
                     max_tokens: Optional[int] = 1000,
                     temperature: Optional[float] = 0.7,
                     system_prompt: Optional[str] = None,
                     **kwargs) -> str:
        """
        Generate text from a prompt using Claude.
        
        Args:
            prompt: The user prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system prompt to set context
            **kwargs: Additional Claude-specific parameters
            
        Returns:
            Generated text response
            
        Raises:
            AIRequestError: If there's an error making the request
            AIResponseError: If there's an error processing the response
        """
        logger.debug(
            "Generating text", 
            max_tokens=max_tokens, 
            temperature=temperature,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Convert single prompt to messages format
        messages = [{"role": "user", "content": prompt}]
        return self.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def generate_chat(self, 
                     messages: List[Dict[str, str]], 
                     max_tokens: Optional[int] = 1000,
                     temperature: Optional[float] = 0.7,
                     system_prompt: Optional[str] = None,
                     **kwargs) -> str:
        """
        Generate a response from a chat history using Claude.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system prompt to set context
            **kwargs: Additional Claude-specific parameters
            
        Returns:
            Generated text response
            
        Raises:
            AIRequestError: If there's an error making the request
            AIResponseError: If there's an error processing the response
        """
        logger.debug(
            "Generating chat response",
            message_count=len(messages),
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            **kwargs
        )
        
        try:
            # Convert our generic message format to Anthropic's format
            anthropic_messages = []
            for msg in messages:
                role = msg["role"]
                # Claude uses "assistant" instead of "system" for assistant messages
                if role == "system":
                    role = "assistant"
                anthropic_messages.append({
                    "role": role,
                    "content": msg["content"]
                })
            
            logger.debug("Converted messages to Anthropic format", messages=anthropic_messages)
            
            # Create the message
            response = self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else None,
                **kwargs
            )
            
            result = response.content[0].text
            logger.info("Generated response", length=len(result))
            logger.debug("Full response", response=result[:100] + "..." if len(result) > 100 else result)
            
            return result
            
        except Exception as e:
            error_message = str(e)
            logger.error(
                "Error generating response",
                error=error_message,
                error_type=type(e).__name__
            )
            
            if "API" in error_message or "request" in error_message.lower():
                raise AIRequestError(f"Claude API error: {error_message}")
            elif "network" in error_message.lower() or "connection" in error_message.lower():
                raise AIRequestError(f"Network error when calling Claude API: {error_message}")
            else:
                raise AIServiceError(f"Unexpected error: {error_message}") 