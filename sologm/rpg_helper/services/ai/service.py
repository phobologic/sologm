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
        """Synchronous text generation."""
        pass
    
    @abstractmethod
    async def generate_text_async(self, 
                          prompt: str, 
                          max_tokens: Optional[int] = None,
                          temperature: Optional[float] = None,
                          system_prompt: Optional[str] = None,
                          **kwargs) -> str:
        """Asynchronous text generation."""
        pass
    
    @abstractmethod
    def generate_chat(self, 
                     messages: List[Dict[str, str]], 
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     system_prompt: Optional[str] = None,
                     **kwargs) -> str:
        """Synchronous chat generation."""
        pass
    
    @abstractmethod
    async def generate_chat_async(self, 
                          messages: List[Dict[str, str]], 
                          max_tokens: Optional[int] = None,
                          temperature: Optional[float] = None,
                          system_prompt: Optional[str] = None,
                          **kwargs) -> str:
        """Asynchronous chat generation."""
        pass
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens
        """
        raise NotImplementedError("Token counting not implemented for this service")
    
    def get_context_window(self) -> int:
        """
        Get the maximum context window size for the current model.
        
        Returns:
            Maximum number of tokens that can be processed
        """
        raise NotImplementedError("Context window size not available for this service") 