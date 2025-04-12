"""Tests for styled text helper."""

from rich.style import Style
from rich.text import Text

from sologm.cli.utils.styled_text import BORDER_STYLES, StyledText


def test_styled_text_create():
    """Test creating styled text with a named style."""
    # Test with a valid style
    text = StyledText.create("Test", "title")
    assert isinstance(text, Text)
    assert text.plain == "Test"
    assert text.style == StyledText.STYLES["title"]

    # Test with an invalid style
    text = StyledText.create("Test", "nonexistent_style")
    assert isinstance(text, Text)
    assert text.plain == "Test"
    assert text.style == Style()  # Default style


def test_styled_text_methods():
    """Test the various styled text methods."""
    # Test title
    text = StyledText.title("Title")
    assert text.plain == "Title"
    assert text.style == StyledText.STYLES["title"]

    # Test timestamp
    text = StyledText.timestamp("2023-01-01")
    assert text.plain == "2023-01-01"
    assert text.style == StyledText.STYLES["timestamp"]

    # Test subtitle
    text = StyledText.subtitle("Subtitle")
    assert text.plain == "Subtitle"
    assert text.style == StyledText.STYLES["subtitle"]

    # Test success
    text = StyledText.success("Success")
    assert text.plain == "Success"
    assert text.style == StyledText.STYLES["success"]

    # Test warning
    text = StyledText.warning("Warning")
    assert text.plain == "Warning"
    assert text.style == StyledText.STYLES["warning"]

    # Test category
    text = StyledText.category("Category")
    assert text.plain == "Category"
    assert text.style == StyledText.STYLES["category"]

    # Test title_timestamp
    text = StyledText.title_timestamp("Title Timestamp")
    assert text.plain == "Title Timestamp"
    assert text.style == StyledText.STYLES["title_timestamp"]

    # Test title_success
    text = StyledText.title_success("Title Success")
    assert text.plain == "Title Success"
    assert text.style == StyledText.STYLES["title_success"]


def test_styled_text_combine():
    """Test combining multiple text elements."""
    # Test combining Text objects
    text1 = StyledText.title("Title")
    text2 = StyledText.timestamp("2023-01-01")
    combined = StyledText.combine(text1, " - ", text2)
    assert combined.plain == "Title - 2023-01-01"
    # Only expect spans for the styled portions (not the plain " - " string)
    assert len(combined.spans) == 2

    # Test combining strings and other objects
    combined = StyledText.combine("Plain", " ", 123, " ", True)
    assert combined.plain == "Plain 123 True"
    # No styles applied to any of these elements, so no spans expected
    assert len(combined.spans) == 0


def test_styled_text_format_metadata():
    """Test formatting metadata."""
    # Test with multiple items
    metadata = {"Created": "2023-01-01", "Modified": "2023-01-02", "Items": 5}
    result = StyledText.format_metadata(metadata)
    assert result.plain == "Created: 2023-01-01 • Modified: 2023-01-02 • Items: 5"

    # Test with single item
    metadata = {"Created": "2023-01-01"}
    result = StyledText.format_metadata(metadata)
    assert result.plain == "Created: 2023-01-01"

    # Test with None values
    metadata = {"Created": "2023-01-01", "Modified": None}
    result = StyledText.format_metadata(metadata)
    assert result.plain == "Created: 2023-01-01"

    # Test with empty dict
    metadata = {}
    result = StyledText.format_metadata(metadata)
    assert result.plain == ""

    # Test with custom separator
    metadata = {"Created": "2023-01-01", "Modified": "2023-01-02"}
    result = StyledText.format_metadata(metadata, separator=" | ")
    assert result.plain == "Created: 2023-01-01 | Modified: 2023-01-02"


def test_border_styles():
    """Test that border styles are defined correctly."""
    assert "game_info" in BORDER_STYLES
    assert "current" in BORDER_STYLES
    assert "success" in BORDER_STYLES
    assert "pending" in BORDER_STYLES
    assert "neutral" in BORDER_STYLES
