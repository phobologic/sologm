"""
Tests for command results.
"""
import pytest
from sologm.commands.results import CommandResult

def test_successful_result():
    """Test creating a successful result."""
    result = CommandResult(
        success=True,
        data={"key": "value"},
        message="Operation successful",
        metadata={"extra": "info"}
    )
    assert not result.is_error
    assert result.data == {"key": "value"}
    assert result.metadata == {"extra": "info"}

def test_error_result():
    """Test creating an error result."""
    error = ValueError("Something went wrong")
    result = CommandResult(
        success=False,
        data=None,
        message="Operation failed",
        error=error
    )
    assert result.is_error
    assert result.error == error

def test_cli_formatting_success():
    """Test formatting a successful result for CLI."""
    result = CommandResult(
        success=True,
        data=None,
        message="Operation completed"
    )
    formatted = result.format_for_cli()
    assert formatted == "Operation completed"

def test_cli_formatting_error():
    """Test formatting an error result for CLI."""
    result = CommandResult(
        success=False,
        data=None,
        message="Something went wrong"
    )
    formatted = result.format_for_cli()
    assert formatted == "Error: Something went wrong"

def test_slack_formatting_success():
    """Test formatting a successful result for Slack."""
    result = CommandResult(
        success=True,
        data=None,
        message="Operation completed"
    )
    formatted = result.format_for_slack()
    assert formatted["response_type"] == "in_channel"
    assert formatted["text"] == "Operation completed"

def test_slack_formatting_error():
    """Test formatting an error result for Slack."""
    result = CommandResult(
        success=False,
        data=None,
        message="Something went wrong"
    )
    formatted = result.format_for_slack()
    assert formatted["response_type"] == "ephemeral"
    assert formatted["text"] == "Error: Something went wrong"

def test_result_with_default_metadata():
    """Test that metadata defaults to an empty dict."""
    result = CommandResult(
        success=True,
        data=None,
        message="Test"
    )
    assert result.metadata == {} 