"""Styled text helper for Rich console output."""

import logging
from typing import Any, Dict, Union

from rich.style import Style
from rich.text import Text

logger = logging.getLogger(__name__)

# Border style constants based on content type (Dracula-inspired)
BORDER_STYLES = {
    "game_info": "bright_blue",  # Game information (Dracula purple-blue)
    "current": "bright_cyan",  # Current/active content (Dracula cyan)
    "success": "bright_green",  # Success/completed content (Dracula green)
    "pending": "bright_yellow",  # Pending actions/decisions (Dracula yellow)
    "neutral": "bright_magenta",  # Neutral information (Dracula pink)
}


class StyledText:
    """Helper class for creating styled text using Rich's native style system."""

    # Define styles as class attributes
    STYLES = {
        "title": Style(bold=True),
        "title_blue": Style(bold=True, color="bright_blue"),
        "timestamp": Style(color="bright_cyan"),
        "subtitle": Style(color="magenta"),
        "success": Style(color="bright_green"),
        "warning": Style(color="bright_yellow"),
        "category": Style(color="bright_magenta"),
        # Combined styles
        "title_timestamp": Style(bold=True, color="bright_cyan"),
        "title_success": Style(bold=True, color="bright_green"),
    }

    @classmethod
    def create(cls, content: str, style_name: str) -> Text:
        """Create styled text using a named style.

        Args:
            content: The text content to style
            style_name: The name of the style to apply

        Returns:
            A Rich Text object with the specified style
        """
        if style_name not in cls.STYLES:
            logger.warning(f"Unknown style: {style_name}, using plain text")
            # Return Text with default Style() instead of no style
            return Text(str(content), style=Style())
        return Text(str(content), style=cls.STYLES[style_name])

    @classmethod
    def title(cls, content: Any) -> Text:
        """Apply title styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with title style
        """
        return cls.create(str(content), "title")

    @classmethod
    def title_blue(cls, content: Any) -> Text:
        """Apply blue title styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with blue title style
        """
        return cls.create(str(content), "title_blue")

    @classmethod
    def timestamp(cls, content: Any) -> Text:
        """Apply timestamp styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with timestamp style
        """
        return cls.create(str(content), "timestamp")

    @classmethod
    def subtitle(cls, content: Any) -> Text:
        """Apply subtitle styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with subtitle style
        """
        return cls.create(str(content), "subtitle")

    @classmethod
    def success(cls, content: Any) -> Text:
        """Apply success styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with success style
        """
        return cls.create(str(content), "success")

    @classmethod
    def warning(cls, content: Any) -> Text:
        """Apply warning styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with warning style
        """
        return cls.create(str(content), "warning")

    @classmethod
    def category(cls, content: Any) -> Text:
        """Apply category styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with category style
        """
        return cls.create(str(content), "category")

    @classmethod
    def title_timestamp(cls, content: Any) -> Text:
        """Apply title timestamp styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with title timestamp style
        """
        return cls.create(str(content), "title_timestamp")

    @classmethod
    def title_success(cls, content: Any) -> Text:
        """Apply title success styling.

        Args:
            content: The content to style

        Returns:
            A Rich Text object with title success style
        """
        return cls.create(str(content), "title_success")

    @classmethod
    def combine(cls, *elements: Union[Text, str, Any]) -> Text:
        """Combine multiple Text objects or strings into a single Text object.

        Args:
            *elements: Text objects, strings, or other objects to combine

        Returns:
            A combined Rich Text object
        """
        result = Text()
        for element in elements:
            if isinstance(element, Text):
                result.append(element)
            else:
                # Apply a default style to non-Text elements to ensure they
                # get their own span
                result.append(Text(str(element), style=Style()))
        return result

    @classmethod
    def format_metadata(cls, items: Dict[str, Any], separator: str = " • ") -> Text:
        """Format metadata items consistently.

        Args:
            items: Dictionary of metadata key-value pairs
            separator: Separator between metadata items

        Returns:
            Formatted metadata as a Rich Text object
        """
        result = Text()
        first = True

        for key, value in items.items():
            if value is not None:
                if not first:
                    result.append(separator)
                else:
                    first = False

                result.append(f"{key}: ")
                result.append(str(value))

        return result
