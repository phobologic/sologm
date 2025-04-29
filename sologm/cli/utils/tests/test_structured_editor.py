"""Tests for the structured_editor module."""

from typing import Optional # Add Optional here
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from sologm.cli.utils.structured_editor import (
    EditorAbortedError,
    EditorError,
    FieldConfig,
    StructuredEditor,
    StructuredEditorConfig,
    ValidationError,
    format_structured_text,
    parse_structured_text,
    wrap_text,
)


class TestTextFormatter:
    """Tests for the TextFormatter class."""

    def test_wrap_text(self):
        """Test wrapping text."""
        text = "This is a long line that should be wrapped at the specified width."
        wrapped = wrap_text(text, width=20)

        assert len(wrapped) > 1
        assert wrapped[0] == "This is a long line"
        assert wrapped[1].startswith(
            "  that should be"
        )  # Note the two spaces at the beginning

        # Test with indentation
        wrapped_indented = wrap_text(text, width=20, indent="    ")
        assert wrapped_indented[0] == "This is a long line"
        assert wrapped_indented[1].startswith("    that should be")

    def test_format_structured_text(self):
        """Test formatting structured text."""
        config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="title",
                    display_name="Title",
                    help_text="The title of the item",
                    required=True,
                ),
                FieldConfig(
                    name="description",
                    display_name="Description",
                    help_text="A detailed description",
                    multiline=True,
                ),
            ],
            wrap_width=40,
        )

        data = {
            "title": "Test Title",
            "description": "This is a test description.",
        }

        formatted = format_structured_text(data, config)

        # Check that the formatted text contains the expected elements
        assert "--- TITLE ---" in formatted
        assert "--- END TITLE ---" in formatted
        assert "Test Title" in formatted
        assert "--- DESCRIPTION ---" in formatted
        assert "--- END DESCRIPTION ---" in formatted
        assert "This is a test description." in formatted

        # Test with context info
        context = "This is context information."
        formatted_with_context = format_structured_text(
            data, config, context_info=context
        )
        assert "# This is context information." in formatted_with_context

        # Test with original data
        original_data = {
            "title": "Original Title",
            "description": "Original description.",
        }
        formatted_with_original = format_structured_text(
            data, config, original_data=original_data
        )
        assert "# Original value:" in formatted_with_original
        assert "# Original Title" in formatted_with_original


class TestTextParser:
    """Tests for the TextParser class."""

    def test_parse_structured_text(self):
        """Test parsing structured text."""
        config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="title",
                    display_name="Title",
                    required=True,
                ),
                FieldConfig(
                    name="description",
                    display_name="Description",
                ),
            ]
        )

        text = """--- TITLE ---
Test Title
--- END TITLE ---

--- DESCRIPTION ---
This is a test description.
--- END DESCRIPTION ---
"""

        parsed = parse_structured_text(text, config)

        assert parsed["title"] == "Test Title"
        assert parsed["description"] == "This is a test description."

    def test_parse_structured_text_with_missing_required_field(self):
        """Test parsing structured text with missing required field."""
        config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="title",
                    display_name="Title",
                    required=True,
                ),
                FieldConfig(
                    name="description",
                    display_name="Description",
                ),
            ]
        )

        text = """--- TITLE ---
--- END TITLE ---

--- DESCRIPTION ---
This is a test description.
--- END DESCRIPTION ---
"""

        with pytest.raises(ValidationError) as excinfo:
            parse_structured_text(text, config)

        assert "Required field(s) Title cannot be empty" in str(excinfo.value)

    def test_parse_structured_text_with_enum_validation(self):
        """Test parsing structured text with enum validation."""
        config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="status",
                    display_name="Status",
                    enum_values=["ACTIVE", "INACTIVE", "PENDING"],
                ),
            ]
        )

        # Valid enum value
        valid_text = """--- STATUS ---
ACTIVE
--- END STATUS ---
"""
        parsed = parse_structured_text(valid_text, config)
        assert parsed["status"] == "ACTIVE"

        # Invalid enum value
        invalid_text = """--- STATUS ---
UNKNOWN
--- END STATUS ---
"""
        with pytest.raises(ValidationError) as excinfo:
            parse_structured_text(invalid_text, config)

        assert "Invalid value for Status" in str(excinfo.value)
        assert "ACTIVE, INACTIVE, PENDING" in str(excinfo.value)


# Mock Editor Strategy for testing StructuredEditor behavior
class MockEditorStrategy:
    """Mock editor strategy for testing StructuredEditor."""

    def __init__(self, behavior="save_modified", return_text=None):
        """
        Initialize the mock editor strategy.

        Args:
            behavior: Controls the mock's behavior:
                - 'save_modified': Simulate saving with changes.
                - 'save_unchanged': Simulate saving without changes.
                - 'abort': Simulate aborting the editor (raises EditorAbortedError).
                - 'error': Simulate an editor launch error (raises EditorError).
            return_text: The text to return when behavior is 'save_modified' or 'save_unchanged'.
                         If None, returns the input text.
        """
        self.behavior = behavior
        self.return_text = return_text
        self.called_with_text = None
        self.call_count = 0

    def edit_text(
        self,
        text: str,
        console: Optional[Console] = None,
        message: str = "Edit the text below:",
        success_message: str = "Text updated.",
        cancel_message: str = "Text unchanged.",
        error_message: str = "Could not open editor.",
    ) -> tuple[str, bool]:
        """Mock the edit_text method."""
        self.call_count += 1
        self.called_with_text = text

        if self.behavior == "abort":
            raise EditorAbortedError("User aborted")
        elif self.behavior == "error":
            raise EditorError("Mock editor launch failed")
        elif self.behavior == "save_modified":
            # Return specific text if provided, otherwise modify input slightly
            edited_text = (
                self.return_text
                if self.return_text is not None
                else text + "\n# Modified"
            )
            return edited_text, True  # Indicate content was modified
        elif self.behavior == "save_unchanged":
            # Return specific text if provided, otherwise return original input
            edited_text = self.return_text if self.return_text is not None else text
            return edited_text, False  # Indicate content was NOT modified
        else:
            raise ValueError(f"Unknown mock behavior: {self.behavior}")


# Use parametrize for different scenarios
@pytest.mark.parametrize(
    "is_new, editor_behavior, initial_data, editor_return_text, expected_result, expected_succeeded, expected_mock_calls",
    [
        # --- SCENARIO: Create New Item ---
        # Save modified (new item) -> Success
        (
            True,
            "save_modified",
            {},
            "---\nTITLE\n---\nNew Title\n--- END TITLE ---",
            {"title": "New Title"},
            True,
            1,
        ),
        # Save empty (new item) -> Success (explicitly saving empty is allowed for new)
        (
            True,
            "save_unchanged",
            {},
            "---\nTITLE\n---\n\n--- END TITLE ---",
            {"title": ""},
            True,
            1,
        ),
        # Abort (new item) -> Cancelled
        (True, "abort", {}, None, {}, False, 1),
        # Editor error (new item) -> Cancelled
        (True, "error", {}, None, {}, False, 1),
        # --- SCENARIO: Edit Existing Item ---
        # Save modified (edit item) -> Success
        (
            False,
            "save_modified",
            {"title": "Old"},
            "---\nTITLE\n---\nNew Title\n--- END TITLE ---",
            {"title": "New Title"},
            True,
            1,
        ),
        # Save unchanged (edit item) -> Cancelled (no effective change)
        (
            False,
            "save_unchanged",
            {"title": "Old"},
            "---\nTITLE\n---\nOld\n--- END TITLE ---",
            {"title": "Old"},
            False,
            1,
        ),
        # Abort (edit item) -> Cancelled
        (False, "abort", {"title": "Old"}, None, {"title": "Old"}, False, 1),
        # Editor error (edit item) -> Cancelled
        (False, "error", {"title": "Old"}, None, {"title": "Old"}, False, 1),
    ],
)
def test_edit_data_scenarios(
    is_new,
    editor_behavior,
    initial_data,
    editor_return_text,
    expected_result,
    expected_succeeded,
    expected_mock_calls,
):
    """Test various scenarios for StructuredEditor.edit_data."""
    config = StructuredEditorConfig(
        fields=[
            FieldConfig(name="title", display_name="Title", required=False)
        ]  # Make not required for simplicity
    )
    mock_editor_strategy = MockEditorStrategy(
        behavior=editor_behavior, return_text=editor_return_text
    )
    editor = StructuredEditor(config=config, editor_strategy=mock_editor_strategy)
    console = Console(width=80, file=None)  # Mock console if needed for output checks

    # Use patch for UIManager if testing validation retries
    with patch("sologm.cli.utils.structured_editor.UIManager", MagicMock()):
        result, succeeded = editor.edit_data(
            data=initial_data,
            console=console,
            is_new=is_new,
            # Pass original data for comments if editing
            original_data_for_comments=initial_data if not is_new else None,
        )

    assert result == expected_result
    assert succeeded == expected_succeeded
    assert mock_editor_strategy.call_count == expected_mock_calls


def test_edit_data_validation_retry_and_fail():
    """Test validation failure, retry, and eventual failure."""
    config = StructuredEditorConfig(
        fields=[FieldConfig(name="title", display_name="Title", required=True)]
    )
    # Mock editor: first returns invalid (empty), second returns invalid again
    mock_editor_strategy = MagicMock(spec=MockEditorStrategy)
    mock_editor_strategy.edit_text.side_effect = [
        # First call (invalid)
        ("---\nTITLE\n---\n\n--- END TITLE ---", True),
        # Second call (retry, still invalid)
        ("---\nTITLE\n---\n\n--- END TITLE ---", True),
    ]

    editor_config = EditorConfig(max_retries=1)  # Allow one retry
    editor = StructuredEditor(
        config=config, editor_strategy=mock_editor_strategy, editor_config=editor_config
    )
    console = Console(width=80, file=None)
    initial_data = {"title": "Old"}

    with patch(
        "sologm.cli.utils.structured_editor.UIManager.display_validation_error"
    ) as mock_display_error:
        result, succeeded = editor.edit_data(
            data=initial_data, console=console, is_new=False
        )

    assert result == initial_data  # Returns original data on failure
    assert succeeded is False
    assert mock_editor_strategy.edit_text.call_count == 2  # Initial call + 1 retry
    assert mock_display_error.call_count == 1  # Validation error displayed once


def test_edit_data_validation_retry_and_succeed():
    """Test validation failure, retry, and eventual success."""
    config = StructuredEditorConfig(
        fields=[FieldConfig(name="title", display_name="Title", required=True)]
    )
    # Mock editor: first returns invalid (empty), second returns valid
    valid_text = "---\nTITLE\n---\nValid Title\n--- END TITLE ---"
    mock_editor_strategy = MagicMock(spec=MockEditorStrategy)
    mock_editor_strategy.edit_text.side_effect = [
        # First call (invalid)
        ("---\nTITLE\n---\n\n--- END TITLE ---", True),
        # Second call (retry, now valid)
        (valid_text, True),
    ]

    editor_config = EditorConfig(max_retries=1)  # Allow one retry
    editor = StructuredEditor(
        config=config, editor_strategy=mock_editor_strategy, editor_config=editor_config
    )
    console = Console(width=80, file=None)
    initial_data = {"title": "Old"}

    with patch(
        "sologm.cli.utils.structured_editor.UIManager.display_validation_error"
    ) as mock_display_error:
        result, succeeded = editor.edit_data(
            data=initial_data, console=console, is_new=False
        )

    assert result == {"title": "Valid Title"}  # Returns parsed valid data
    assert succeeded is True
    assert mock_editor_strategy.edit_text.call_count == 2  # Initial call + 1 retry
    assert mock_display_error.call_count == 1  # Validation error displayed once
