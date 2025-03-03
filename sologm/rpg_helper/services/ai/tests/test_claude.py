"""
Tests for the Claude AI service.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from sologm.rpg_helper.services.ai.claude import ClaudeService
from sologm.rpg_helper.services.ai import AIServiceError


@pytest.fixture
def mock_anthropic():
    """Mock the Anthropic client to avoid actual API calls."""
    with patch('anthropic.Anthropic') as mock_client_class:
        # Create a mock client instance
        mock_client = MagicMock()
        # Make the constructor return our mock instance
        mock_client_class.return_value = mock_client
        
        # Mock the messages.create method
        mock_messages_create = MagicMock()
        mock_client.messages.create = mock_messages_create
        
        # Set up a mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Mock response from Claude")]
        mock_messages_create.return_value = mock_response
        
        yield mock_client


@pytest.fixture
def claude_service(mock_anthropic):
    """Create a Claude service with a mocked client."""
    # Use a fake API key
    service = ClaudeService(api_key="fake_api_key")
    return service


def test_init():
    """Test initialization with API key."""
    # Patch the Anthropic client to avoid actual initialization
    with patch('anthropic.Anthropic'):
        service = ClaudeService(api_key="test_key")
        assert service.api_key == "test_key"
        assert service.model == "claude-3-opus-20240229"  # Update to match actual default


def test_init_with_env_var():
    """Test initialization with API key from environment variable."""
    # Patch the environment and Anthropic client
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env_test_key"}), \
         patch('anthropic.Anthropic'):
        service = ClaudeService()
        assert service.api_key == "env_test_key"


def test_init_no_api_key():
    """Test initialization with no API key."""
    # Patch the environment to ensure no API key is present
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True), \
         patch('anthropic.Anthropic'):
        with pytest.raises(ValueError) as excinfo:
            ClaudeService()
        assert "API key is required" in str(excinfo.value)


def test_generate_text(claude_service, mock_anthropic):
    """Test generating text."""
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is a test response")]
    mock_anthropic.messages.create.return_value = mock_response
    
    # Call the method
    result = claude_service.generate_text(
        prompt="Test prompt",
        max_tokens=100,
        temperature=0.7
    )
    
    # Check the result
    assert result == "This is a test response"
    
    # Verify the client was called correctly
    mock_anthropic.messages.create.assert_called_once()
    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-3-opus-20240229"  # Update to match actual default
    assert call_kwargs["max_tokens"] == 100
    assert call_kwargs["temperature"] == 0.7
    assert call_kwargs["messages"][0]["role"] == "user"
    assert call_kwargs["messages"][0]["content"] == "Test prompt"


def test_generate_text_with_system_prompt(claude_service, mock_anthropic):
    """Test generating text with a system prompt."""
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response with system prompt")]
    mock_anthropic.messages.create.return_value = mock_response
    
    # Call the method
    result = claude_service.generate_text(
        prompt="Test prompt",
        system_prompt="You are a helpful assistant",
        max_tokens=100
    )
    
    # Check the result
    assert result == "Response with system prompt"
    
    # Verify the client was called correctly
    mock_anthropic.messages.create.assert_called_once()
    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert call_kwargs["system"] == "You are a helpful assistant"


def test_generate_text_with_custom_model(claude_service, mock_anthropic):
    """Test generating text with a custom model."""
    # Set up the mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response from custom model")]
    mock_anthropic.messages.create.return_value = mock_response
    
    # Set a custom model
    claude_service.model = "claude-3-5-sonnet-20240620"  # Use a different model than default
    
    # Call the method
    result = claude_service.generate_text(prompt="Test prompt")
    
    # Check the result
    assert result == "Response from custom model"
    
    # Verify the client was called with the custom model
    mock_anthropic.messages.create.assert_called_once()
    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-3-5-sonnet-20240620"


def test_handle_api_error(claude_service, mock_anthropic):
    """Test handling API errors."""
    # Make the client raise an exception
    mock_anthropic.messages.create.side_effect = Exception("API error")
    
    # Call the method and check that it raises the expected exception
    with pytest.raises(AIServiceError) as excinfo:
        claude_service.generate_text(prompt="Test prompt")
    
    assert "API error" in str(excinfo.value) 