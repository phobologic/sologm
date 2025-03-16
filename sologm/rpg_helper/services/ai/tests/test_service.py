"""
Tests for the AI service.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional

from sologm.rpg_helper.services.ai.service import AIService, AIServiceError, AIRequestError, AIResponseError


class MockAIService(AIService):
    """Mock implementation of AIService for testing."""
    
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.last_prompt = None
        self.last_messages = None
        self.last_kwargs = None
    
    def generate_text(self, 
                     prompt: str, 
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     system_prompt: Optional[str] = None,
                     **kwargs) -> str:
        """Mock text generation."""
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        
        if self.should_fail:
            raise AIRequestError("Mock error")
        
        return f"Response to: {prompt}"
    
    def generate_chat(self, 
                     messages: List[Dict[str, str]], 
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     system_prompt: Optional[str] = None,
                     **kwargs) -> str:
        """Mock chat generation."""
        self.last_messages = messages
        self.last_kwargs = kwargs
        
        if self.should_fail:
            raise AIRequestError("Mock error")
        
        return f"Response to chat with {len(messages)} messages"


def test_generate_text():
    """Test the generate_text interface."""
    service = MockAIService()
    
    response = service.generate_text(
        prompt="Test prompt",
        max_tokens=100,
        temperature=0.7,
        custom_param="test"
    )
    
    assert response == "Response to: Test prompt"
    assert service.last_prompt == "Test prompt"
    assert service.last_kwargs["custom_param"] == "test"


def test_generate_chat():
    """Test the generate_chat interface."""
    service = MockAIService()
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]
    
    response = service.generate_chat(
        messages=messages,
        max_tokens=100,
        temperature=0.7,
        custom_param="test"
    )
    
    assert response == "Response to chat with 2 messages"
    assert service.last_messages == messages
    assert service.last_kwargs["custom_param"] == "test"


def test_error_handling():
    """Test error handling in the service interface."""
    service = MockAIService(should_fail=True)
    
    with pytest.raises(AIRequestError) as excinfo:
        service.generate_text("Test prompt")
    
    assert "Mock error" in str(excinfo.value)


def test_error_hierarchy():
    """Test that error classes have the correct hierarchy."""
    assert issubclass(AIRequestError, AIServiceError)
    assert issubclass(AIResponseError, AIServiceError) 