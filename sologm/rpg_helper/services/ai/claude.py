"""
Claude AI service implementation using Anthropic's API.
"""
import os
from typing import Dict, List, Optional, Any
import anthropic
from anthropic.types import Message
from anthropic.types.message import ContentBlock

from .service import AIService, AIRequestError, AIResponseError, AIServiceError
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

# Model context windows (in tokens)
MODEL_CONTEXT_WINDOWS = {
    "claude-3-opus-20240229": 200000,
    "claude-3-sonnet-20240229": 200000,
    "claude-3-haiku-20240229": 200000,
}

class ClaudeService(AIService):
    """Service for interacting with Anthropic's Claude API."""
    
    def __init__(self, 
                api_key: Optional[str] = None, 
                model: str = "claude-3-opus-20240229"):
        """Initialize the Claude service."""
        logger.debug("Initializing Claude service", model=model)
        
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.error("No API key provided and ANTHROPIC_API_KEY not set")
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key.")
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("Claude service initialized", model=model)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using Anthropic's tokenizer."""
        return self.client.count_tokens(text)
    
    def get_context_window(self) -> int:
        """Get the context window size for the current model."""
        return MODEL_CONTEXT_WINDOWS.get(self.model, 100000)  # Default to 100k
    
    def _prepare_messages(self, 
                       messages: List[Dict[str, str]], 
                       max_tokens: Optional[int] = None) -> List[Dict[str, str]]:
        """Prepare and validate messages, ensuring they fit within context window."""
        # Convert our generic message format to Anthropic's format
        anthropic_messages = []
        total_tokens = 0
        context_window = self.get_context_window()
        
        # Reserve tokens for the response
        available_tokens = context_window - (max_tokens or 1000)
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # Claude uses "assistant" instead of "system" for assistant messages
            if role == "system":
                role = "assistant"
            
            # Count tokens in this message
            message_tokens = self.count_tokens(content)
            if total_tokens + message_tokens > available_tokens:
                logger.warning(
                    "Message would exceed context window, truncating history",
                    total_tokens=total_tokens,
                    message_tokens=message_tokens,
                    available_tokens=available_tokens
                )
                break
            
            anthropic_messages.append({
                "role": role,
                "content": content
            })
            total_tokens += message_tokens
        
        logger.debug(
            "Prepared messages",
            message_count=len(anthropic_messages),
            total_tokens=total_tokens
        )
        return anthropic_messages
    
    def generate_text(self, 
                     prompt: str, 
                     max_tokens: Optional[int] = 1000,
                     temperature: Optional[float] = 0.7,
                     system_prompt: Optional[str] = None,
                     **kwargs) -> str:
        """Generate text from a prompt."""
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
        """Generate chat response."""
        logger.debug(
            "Generating chat response",
            message_count=len(messages),
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            **kwargs
        )
        
        try:
            # Prepare messages with token management
            anthropic_messages = self._prepare_messages(messages, max_tokens)
            
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