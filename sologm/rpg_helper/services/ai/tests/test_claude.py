"""
Tests for the Claude AI service.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
import anthropic

from sologm.rpg_helper.services.ai import ClaudeService, AIRequestError, AIResponseError, AIServiceError


def test_generate_text():
    """Test generating text with Claude."""
    # Skip if no API key is available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    
    service = ClaudeService()
    response = service.generate_text(
        prompt="Write a haiku about programming",
        max_tokens=100,
        temperature=0.7
    )
    
    assert response
    assert isinstance(response, str)
    assert len(response) > 0


def test_generate_chat():
    """Test generating chat responses with Claude."""
    # Skip if no API key is available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    
    service = ClaudeService()
    messages = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
        {"role": "user", "content": "Write a haiku about programming"}
    ]
    
    response = service.generate_chat(
        messages=messages,
        max_tokens=100,
        temperature=0.7
    )
    
    assert response
    assert isinstance(response, str)
    assert len(response) > 0


def test_api_error_handling():
    """Test handling of API errors."""
    # Create a custom exception that will be caught by our error handler
    class CustomError(Exception):
        def __str__(self):
            return "Invalid request"
    
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = CustomError()
    
    with patch('anthropic.Anthropic', return_value=mock_client):
        service = ClaudeService(api_key="fake_key")
        
        with pytest.raises(AIServiceError) as excinfo:
            service.generate_text("Test prompt")
        
        assert "Invalid request" in str(excinfo.value)


def test_network_error_handling():
    """Test handling of network errors."""
    # Create a custom exception that will be caught by our error handler
    class CustomNetworkError(Exception):
        def __str__(self):
            return "Network error"
    
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = CustomNetworkError()
    
    with patch('anthropic.Anthropic', return_value=mock_client):
        service = ClaudeService(api_key="fake_key")
        
        with pytest.raises(AIServiceError) as excinfo:
            service.generate_text("Test prompt")
        
        assert "Network error" in str(excinfo.value) 