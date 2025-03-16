"""Tests for the Claude AI service."""
import os
import pytest
import asyncio
from unittest.mock import Mock, patch
from anthropic import Anthropic
from anthropic.types import Message

from sologm.rpg_helper.services.ai.claude import ClaudeService
from sologm.rpg_helper.services.ai.service import AIRequestError, AIServiceError


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client."""
    mock = Mock(spec=Anthropic)
    mock.messages = Mock()
    mock.messages.create = Mock()
    mock.count_tokens = Mock(return_value=10)
    return mock


@pytest.fixture
def service(mock_anthropic):
    """Create a Claude service with mocked client."""
    with patch("anthropic.Anthropic", return_value=mock_anthropic):
        service = ClaudeService(api_key="test-key")
    return service


def test_init_with_api_key():
    """Test initialization with API key."""
    service = ClaudeService(api_key="test-key")
    assert service.api_key == "test-key"
    assert service.model == "claude-3-opus-20240229"


def test_init_with_env_var():
    """Test initialization with environment variable."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
        service = ClaudeService()
        assert service.api_key == "env-key"


def test_init_no_api_key():
    """Test initialization with no API key raises error."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError):
            ClaudeService()


def test_count_tokens(service):
    """Test token counting."""
    text = "Hello world"
    service.client.count_tokens.return_value = 3
    assert service.count_tokens(text) == 3
    service.client.count_tokens.assert_called_once_with(text)


def test_get_context_window(service):
    """Test getting context window size."""
    assert service.get_context_window() == 200000  # Default model
    
    service.model = "unknown-model"
    assert service.get_context_window() == 100000  # Default fallback


def test_prepare_messages(service):
    """Test message preparation with token management."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "How are you?"}
    ]
    
    # Mock token counts - provide enough responses for both calls to _prepare_messages
    service.client.count_tokens.side_effect = [5, 8, 7,  # First call
                                             5, 8, 7]  # Second call
    
    prepared = service._prepare_messages(messages, max_tokens=1000)
    
    assert len(prepared) == 3
    assert prepared[0]["role"] == "user"
    assert prepared[0]["content"] == "Hello"
    
    # Verify system role conversion
    messages[1]["role"] = "system"
    prepared = service._prepare_messages(messages, max_tokens=1000)
    assert prepared[1]["role"] == "assistant"


def test_prepare_messages_truncation(service):
    """Test message truncation when exceeding context window."""
    messages = [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Second"},
        {"role": "user", "content": "Third"}
    ]
    
    # Mock large token counts
    service.client.count_tokens.side_effect = [50000, 150000, 50000]
    
    prepared = service._prepare_messages(messages, max_tokens=1000)
    
    # Should only include first message due to token limits
    assert len(prepared) == 1
    assert prepared[0]["content"] == "First"


def test_generate_text(service):
    """Test text generation."""
    mock_response = Mock()
    mock_response.content = [Mock(text="Generated text")]
    service.client.messages.create.return_value = mock_response
    
    result = service.generate_text("Hello")
    
    assert result == "Generated text"
    service.client.messages.create.assert_called_once()


def test_generate_chat(service):
    """Test chat generation."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]
    
    mock_response = Mock()
    mock_response.content = [Mock(text="Chat response")]
    service.client.messages.create.return_value = mock_response
    
    result = service.generate_chat(messages)
    
    assert result == "Chat response"
    service.client.messages.create.assert_called_once()


def test_api_error_handling(service):
    """Test API error handling."""
    service.client.messages.create.side_effect = Exception("API error")
    
    with pytest.raises(AIRequestError) as exc:
        service.generate_text("Hello")
    assert "API error" in str(exc.value)


def test_network_error_handling(service):
    """Test network error handling."""
    service.client.messages.create.side_effect = Exception("network timeout")
    
    with pytest.raises(AIRequestError) as exc:
        service.generate_text("Hello")
    assert "Network error" in str(exc.value)


def test_unexpected_error_handling(service):
    """Test unexpected error handling."""
    service.client.messages.create.side_effect = ValueError("Unexpected")
    
    with pytest.raises(AIServiceError) as exc:
        service.generate_text("Hello")
    assert "Unexpected error" in str(exc.value) 