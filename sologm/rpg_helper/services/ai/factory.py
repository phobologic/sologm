"""
Factory for creating AI service instances.
"""
from typing import Optional, Dict, Any

from .service import AIService
from .claude import ClaudeService


class AIServiceFactory:
    """Factory for creating AI service instances."""
    
    @staticmethod
    def create_service(service_type: str, **kwargs) -> AIService:
        """
        Create an AI service instance.
        
        Args:
            service_type: Type of service to create ("claude", etc.)
            **kwargs: Additional parameters to pass to the service constructor
            
        Returns:
            AIService instance
            
        Raises:
            ValueError: If an invalid service type is specified
        """
        if service_type.lower() == "claude":
            return ClaudeService(**kwargs)
        else:
            raise ValueError(f"Unknown AI service type: {service_type}") 