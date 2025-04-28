"""Tests for Anthropic API client."""

import logging  # Make sure logger is available if not already imported/configured
from unittest.mock import MagicMock, patch

import pytest
from anthropic._types import NOT_GIVEN

# Import Config for type hinting if needed elsewhere, but not strictly required for this change
# from sologm.utils.config import Config
from sologm.integrations.anthropic import AnthropicClient
from sologm.utils.errors import APIError

logger = logging.getLogger(__name__)


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


# Use the new fixture name and apply patch within the test
def test_init_no_api_key(
    mock_anthropic, monkeypatch, mock_config_no_api_key
):  # Use new fixture
    """Test initialization fails without API key from env or config."""
    logger.debug("--- Starting test_init_no_api_key ---")
    # Ensure environment variables are clear
    env_var1 = "ANTHROPIC_API_KEY"
    env_var2 = "SOLOGM_ANTHROPIC_API_KEY"
    logger.debug(f"Clearing environment variable: {env_var1}")
    monkeypatch.delenv(env_var1, raising=False)
    logger.debug(f"Clearing environment variable: {env_var2}")
    monkeypatch.delenv(env_var2, raising=False)

    # Define the target to patch - WHERE get_config IS LOOKED UP/USED
    patch_target = "sologm.integrations.anthropic.get_config"  # <--- CORRECT TARGET
    logger.debug(
        f"Attempting to patch '{patch_target}' to return mock config: {mock_config_no_api_key}"
    )

    # Apply the patch using a context manager JUST around the code that needs it
    with patch(
        patch_target, return_value=mock_config_no_api_key, autospec=True
    ) as mock_get_config:
        logger.debug(
            f"Patch active for '{patch_target}'. Mock object: {mock_get_config}"
        )
        logger.debug(
            "Expecting APIError during AnthropicClient initialization inside patch block..."
        )
        with pytest.raises(APIError) as exc:
            # Instantiation happens HERE, while the patch is active
            client = AnthropicClient()
            # This should not be reached
            logger.error(
                "AnthropicClient initialized unexpectedly without raising APIError!"
            )

    # Log the caught exception after the 'with' blocks
    logger.debug(f"Patch for '{patch_target}' finished.")
    logger.debug(f"Caught expected exception: {exc.type.__name__}('{exc.value}')")
    # Check the specific error message
    assert "Anthropic API key not found" in str(exc.value)
    logger.debug("--- Finished test_init_no_api_key successfully ---")


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
