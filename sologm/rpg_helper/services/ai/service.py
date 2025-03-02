"""
Generic interface for AI services.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AIRequestError(AIServiceError):
    """Exception raised when there's an error making a request to the AI service."""
    pass


class AIResponseError(AIServiceError):
    """Exception raised when there's an error processing the AI service response."""
    pass


class AIService(ABC):
    """Abstract base class for AI services."""
    
    @abstractmethod
    def generate_text(self, 
                     prompt: str, 
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     system_prompt: Optional[str] = None,
                     **kwargs) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The user prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system prompt to set context
            **kwargs: Additional service-specific parameters
            
        Returns:
            Generated text response
            
        Raises:
            AIRequestError: If there's an error making the request
            AIResponseError: If there's an error processing the response
        """
        pass
    
    @abstractmethod
    def generate_chat(self, 
                     messages: List[Dict[str, str]], 
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     system_prompt: Optional[str] = None,
                     **kwargs) -> str:
        """
        Generate a response from a chat history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system prompt to set context
            **kwargs: Additional service-specific parameters
            
        Returns:
            Generated text response
            
        Raises:
            AIRequestError: If there's an error making the request
            AIResponseError: If there's an error processing the response
        """
        pass 