"""
Tests for the AI service factory.
"""
import pytest
from unittest.mock import MagicMock, patch

from sologm.rpg_helper.services.ai import AIServiceFactory, AIService
from sologm.rpg_helper.services.ai.claude import ClaudeService  # Import directly from the module


def test_create_claude_service():
    """Test creating a Claude service."""
    service = AIServiceFactory.create_service("claude", api_key="test_key")
    
    assert isinstance(service, ClaudeService)
    assert service.api_key == "test_key"


def test_create_claude_service_case_insensitive():
    """Test that service type is case insensitive."""
    service = AIServiceFactory.create_service("CLAUDE", api_key="test_key")
    
    assert isinstance(service, ClaudeService)


def test_create_unknown_service():
    """Test creating an unknown service type."""
    with pytest.raises(ValueError) as excinfo:
        AIServiceFactory.create_service("unknown_service")
    
    assert "Unknown AI service type: unknown_service" in str(excinfo.value)


def test_create_service_passes_kwargs():
    """Test that kwargs are passed to the service constructor."""
    service = AIServiceFactory.create_service(
        "claude",
        api_key="test_key",
        model="custom-model"
    )
    
    assert service.api_key == "test_key"
    assert service.model == "custom-model" 