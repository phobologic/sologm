"""Tests for the structured_editor module."""

import pytest
from rich.console import Console

from sologm.cli.utils.structured_editor import (
    EditorConfig,
    FieldConfig,
    StructuredEditor,
    StructuredEditorConfig,
    TextFormatter,
    TextParser,
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
        assert wrapped[1].startswith("that should be")
        
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
        formatted_with_context = format_structured_text(data, config, context_info=context)
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


class MockEditorStrategy:
    """Mock editor strategy for testing."""
    
    def __init__(self, return_text=None, modified=True):
        """Initialize with predetermined return values."""
        self.return_text = return_text
        self.modified = modified
        self.called = False
        self.last_text = None
    
    def edit_text(
        self,
        text,
        console=None,
        message="",
        success_message="",
        cancel_message="",
        error_message="",
    ):
        """Mock implementation that returns predetermined values."""
        self.called = True
        self.last_text = text
        return self.return_text or text, self.modified


class TestStructuredEditor:
    """Tests for the StructuredEditor class."""
    
    def test_edit_data_success(self):
        """Test successful data editing."""
        config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="title",
                    display_name="Title",
                    required=True,
                ),
            ]
        )
        
        # Mock editor that returns valid data
        mock_editor = MockEditorStrategy(
            return_text="""--- TITLE ---
New Title
--- END TITLE ---
""",
            modified=True,
        )
        
        editor = StructuredEditor(
            config=config,
            editor_strategy=mock_editor,
        )
        
        data = {"title": "Original Title"}
        console = Console(width=80, file=None)
        
        result, modified = editor.edit_data(data, console)
        
        assert modified is True
        assert result["title"] == "New Title"
        assert mock_editor.called is True
    
    def test_edit_data_canceled(self):
        """Test canceled data editing."""
        config = StructuredEditorConfig(
            fields=[
                FieldConfig(
                    name="title",
                    display_name="Title",
                    required=True,
                ),
            ]
        )
        
        # Mock editor that simulates cancellation
        mock_editor = MockEditorStrategy(modified=False)
        
        editor = StructuredEditor(
            config=config,
            editor_strategy=mock_editor,
        )
        
        data = {"title": "Original Title"}
        console = Console(width=80, file=None)
        
        result, modified = editor.edit_data(data, console)
        
        assert modified is False
        assert result == data  # Original data returned unchanged
        assert mock_editor.called is True
