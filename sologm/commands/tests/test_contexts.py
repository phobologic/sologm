"""
Tests for command contexts.
"""
import pytest
from sologm.commands.contexts import CLIContext, SlackContext

def test_cli_context_creation():
    """Test creating a CLI context."""
    context = CLIContext(
        working_directory="/test/dir",
        user="testuser",
        extra_args={"flag": True}
    )
    assert context.workspace_id == "cli:/test/dir"
    assert context.formatted_user_id == "cli:testuser"
    assert context.metadata == {"flag": True}

def test_cli_context_default_metadata():
    """Test CLI context with default metadata."""
    context = CLIContext(
        working_directory="/test/dir",
        user="testuser"
    )
    assert context.metadata == {}

def test_slack_context_creation():
    """Test creating a Slack context."""
    context = SlackContext(
        channel_id="C123",
        user_id="U456",
        team_id="T789",
        response_url="https://slack.com/response",
        extra_data={"thread_ts": "1234.5678"}
    )
    assert context.workspace_id == "slack:T789:C123"
    assert context.formatted_user_id == "slack:U456"
    assert "response_url" in context.metadata
    assert "thread_ts" in context.metadata

def test_slack_context_without_response_url():
    """Test Slack context without response URL."""
    context = SlackContext(
        channel_id="C123",
        user_id="U456",
        team_id="T789"
    )
    assert "response_url" not in context.metadata

def test_slack_context_metadata_isolation():
    """Test that Slack context metadata modifications don't affect original data."""
    extra_data = {"original": "data"}
    context = SlackContext(
        channel_id="C123",
        user_id="U456",
        team_id="T789",
        extra_data=extra_data
    )
    
    # Modify the metadata
    metadata = context.metadata
    metadata["new"] = "value"
    
    # Check that original extra_data is unchanged
    assert "new" not in context.extra_data
    assert context.extra_data == {"original": "data"} 