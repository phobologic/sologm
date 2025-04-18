"""Tests for Anthropic API client."""

from unittest.mock import MagicMock, patch

import pytest
from anthropic._types import NOT_GIVEN

from sologm.integrations.anthropic import AnthropicClient
from sologm.utils.errors import APIError


@pytest.fixture
def mock_anthropic():
    """Create a mock Anthropic client."""
    with patch("sologm.integrations.anthropic.Anthropic") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock, mock_instance


@pytest.fixture
def mock_response():
    """Create a mock response from Claude."""
    response = MagicMock()
    response.content = [MagicMock(text="Test response from Claude")]
    return response


def test_init_with_api_key(mock_anthropic):
    """Test initializing client with explicit API key."""
    mock_class, mock_instance = mock_anthropic
    client = AnthropicClient(api_key="test_key")
    mock_class.assert_called_once_with(api_key="test_key")


def test_init_with_env_var(mock_anthropic, monkeypatch):
    """Test initializing client with API key from environment."""
    mock_class, mock_instance = mock_anthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env_test_key")
    client = AnthropicClient()
    mock_class.assert_called_once_with(api_key="env_test_key")


def test_init_no_api_key(mock_anthropic, monkeypatch):
    """Test initialization fails without API key."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(APIError) as exc:
        client = AnthropicClient()
    assert "API key not found" in str(exc.value)


def test_init_anthropic_client_failure(mock_anthropic):
    """Test handling errors during Anthropic client instantiation."""
    mock_class, _ = mock_anthropic
    mock_class.side_effect = Exception("Initialization failed")  # Simulate failure

    with pytest.raises(APIError) as exc:
        AnthropicClient(api_key="test_key")
    assert "Failed to initialize Anthropic client: Initialization failed" in str(
        exc.value
    )


def test_send_message(mock_anthropic, mock_response):
    """Test sending a message to Claude."""
    mock_class, mock_instance = mock_anthropic
    mock_instance.messages.create.return_value = mock_response

    client = AnthropicClient(api_key="test_key")
    response = client.send_message("Test prompt")

    assert response == "Test response from Claude"
    mock_instance.messages.create.assert_called_once_with(
        model="claude-3-5-sonnet-latest",
        max_tokens=1000,
        temperature=0.7,
        system=NOT_GIVEN,
        messages=[{"role": "user", "content": "Test prompt"}],
    )


def test_send_message_with_options(mock_anthropic, mock_response):
    """Test sending a message with custom options."""
    mock_class, mock_instance = mock_anthropic
    mock_instance.messages.create.return_value = mock_response

    client = AnthropicClient(api_key="test_key")
    response = client.send_message(
        "Test prompt", max_tokens=500, temperature=0.5, system="Test system message"
    )

    assert response == "Test response from Claude"
    mock_instance.messages.create.assert_called_once_with(
        model="claude-3-5-sonnet-latest",
        max_tokens=500,
        temperature=0.5,
        system="Test system message",
        messages=[{"role": "user", "content": "Test prompt"}],
    )


def test_send_message_api_error(mock_anthropic):
    """Test handling API errors when sending messages."""
    mock_class, mock_instance = mock_anthropic
    mock_instance.messages.create.side_effect = Exception("API Error")

    client = AnthropicClient(api_key="test_key")
    with pytest.raises(APIError) as exc:
        client.send_message("Test prompt")
    assert "Failed to get response from Claude" in str(exc.value)


def test_send_message_invalid_response_format_empty(mock_anthropic):
    """Test handling empty content in response."""
    mock_class, mock_instance = mock_anthropic
    # Simulate response with empty content list
    empty_response = MagicMock()
    empty_response.content = []
    mock_instance.messages.create.return_value = empty_response

    client = AnthropicClient(api_key="test_key")
    with pytest.raises(APIError) as exc:
        client.send_message("Test prompt")
    assert "Unexpected response format from Claude" in str(exc.value)


def test_send_message_invalid_response_format_no_text(mock_anthropic):
    """Test handling response content without 'text' attribute."""
    mock_class, mock_instance = mock_anthropic
    # Simulate response where content item lacks 'text'
    malformed_response = MagicMock()
    malformed_content_item = MagicMock()
    # Ensure 'text' attribute is missing by removing it if present
    # or by ensuring it's not part of the spec if creating a new mock
    try:
        del malformed_content_item.text
    except AttributeError:
        pass  # Attribute didn't exist, which is the desired state
    malformed_response.content = [malformed_content_item]
    mock_instance.messages.create.return_value = malformed_response

    client = AnthropicClient(api_key="test_key")
    with pytest.raises(APIError) as exc:
        client.send_message("Test prompt")
    assert "Unexpected response format from Claude" in str(exc.value)
