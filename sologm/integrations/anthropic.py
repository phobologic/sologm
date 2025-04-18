"""Anthropic API client for Solo RPG Helper."""

import logging
from typing import Optional

from anthropic import Anthropic
from anthropic._types import NOT_GIVEN

from sologm.utils.config import get_config
from sologm.utils.errors import APIError

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for interacting with Anthropic's Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Anthropic client.

        Args:
            api_key: Optional API key. If not provided, will try to get from
                    config (which checks environment variables and config file).

        Raises:
            APIError: If no API key is found or if client initialization fails.
        """
        logger.debug("[AnthropicClient.__init__] Initializing...")
        try:
            if api_key is None:
                logger.debug(
                    "[AnthropicClient.__init__] API key not provided, "
                    "attempting to load from config."
                )

                logger.debug("[AnthropicClient.__init__] Calling get_config()")
                config = get_config()
                # Log details about the config object received
                logger.debug(
                    "[AnthropicClient.__init__] get_config() returned "
                    f"object: {config} (type: {type(config)})"
                )
                # Check if it's the mock object we expect in tests

                logger.debug(
                    "[AnthropicClient.__init__] Calling config.get('anthropic_api_key')"
                )
                api_key = config.get("anthropic_api_key")
                # Log the exact value returned by config.get
                logger.debug(
                    f"[AnthropicClient.__init__] "
                    f"config.get('anthropic_api_key') returned: {api_key!r}"
                )

                if not api_key:
                    logger.error(
                        "[AnthropicClient.__init__] API key is missing or "
                        "empty after config lookup."
                    )
                    raise APIError(
                        "Anthropic API key not found. Please set the "
                        "ANTHROPIC_API_KEY environment variable or add "
                        "'anthropic_api_key' "
                        "to your configuration file."
                    )
                else:
                    logger.debug("[AnthropicClient.__init__] API key found via config.")
            else:
                logger.debug(
                    "[AnthropicClient.__init__] API key was provided directly."
                )

            self.api_key = api_key
            logger.debug(
                "[AnthropicClient.__init__] Initializing actual Anthropic "
                "library client"
            )
            self.client = Anthropic(api_key=self.api_key)
            logger.debug(
                "[AnthropicClient.__init__] Anthropic library client "
                "initialized successfully."
            )
        except Exception as e:
            logger.error(
                f"[AnthropicClient.__init__] Failed during initialization: {e}",
                exc_info=True,
            )  # Add exc_info for traceback
            # Avoid shadowing the original error type if it's already APIError
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to initialize Anthropic client: {str(e)}") from e

    def send_message(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system: Optional[str] = None,
    ) -> str:
        """Send a message to Claude and get the response.

        Args:
            prompt: The message to send to Claude.
            max_tokens: Maximum number of tokens in the response.
            temperature: Controls randomness in the response (0.0 to 1.0).
            system: Optional system message to set context.

        Returns:
            str: Claude's response text.

        Raises:
            APIError: If the API call fails.
        """
        try:
            logger.debug(f"Sending message to Claude with {max_tokens} max tokens")

            logger.debug(f"Sending message to Claude with prompt length: {len(prompt)}")
            logger.debug(f"Prompt: {prompt}")
            # Handle system message
            system_param = system if system is not None else NOT_GIVEN

            response = self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_param,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from the first content block
            if not response.content or not hasattr(response.content[0], "text"):
                raise APIError("Unexpected response format from Claude")
            response_text = response.content[0].text
            logger.debug(
                f"Successfully received response from Claude "
                f"(length: {len(response_text)})"
            )
            logger.debug(f"Response Text: {response_text}")
            return response_text

        except Exception as e:
            logger.error(f"Failed to get response from Claude: {e}")
            raise APIError(f"Failed to get response from Claude: {str(e)}") from e
