"""
Unit tests for Claude service.
"""
import pytest
from unittest.mock import patch, MagicMock, ANY

from ..claude_service import (
    ClaudeClient, 
    get_claude_client,
    DEFAULT_SYSTEM_PROMPT
)
from ...models.user import UserPreferences


class TestClaudeClient:
    
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        client = ClaudeClient()
        assert client.api_key == 'test_key'
    
    def test_init_with_provided_key(self):
        """Test initialization with provided API key."""
        client = ClaudeClient(api_key='provided_key')
        assert client.api_key == 'provided_key'
    
    @patch.dict('os.environ', clear=True)
    def test_init_without_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError) as excinfo:
            ClaudeClient()
        assert "Anthropic API key is required" in str(excinfo.value)
    
    @patch('sologm.rpg_helper.services.claude_service.Anthropic')
    def test_generate_interpretations_basic(self, mock_anthropic):
        """Test basic interpretation generation."""
        # Setup mock response
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "1. First interpretation\n2. Second interpretation\n3. Third interpretation\n4. Fourth interpretation\n5. Fifth interpretation"
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client
        
        # Create client and call method
        client = ClaudeClient(api_key='test_key')
        result = client.generate_interpretations(
            context="A dark forest",
            keywords=["spooky", "mysterious"]
        )
        
        # Verify results
        assert len(result) == 5
        assert result[0] == "First interpretation"
        assert result[4] == "Fifth interpretation"
        
        # Verify API was called correctly
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs['model'] == "claude-3-opus-20240229"
        assert call_kwargs['system'] == DEFAULT_SYSTEM_PROMPT
        assert "spooky, mysterious" in call_kwargs['messages'][0]['content']
        assert "A dark forest" in call_kwargs['messages'][0]['content']
    
    @patch('sologm.rpg_helper.services.claude_service.Anthropic')
    def test_generate_interpretations_with_user_preferences(self, mock_anthropic):
        """Test interpretation generation with user preferences."""
        # Setup mock response
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "1. First interpretation\n2. Second interpretation\n3. Third interpretation"
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client
        
        # Setup mock user preferences
        test_user_id = "U12345"
        test_prefs = UserPreferences(setting_description="A cyberpunk future")
        
        with patch('sologm.rpg_helper.services.claude_service.user_preferences', {test_user_id: test_prefs}):
            # Create client and call method
            client = ClaudeClient(api_key='test_key')
            result = client.generate_interpretations(
                context="A neon-lit street",
                keywords=["hacker", "corporation"],
                user_id=test_user_id,
                num_options=3
            )
            
            # Verify results
            assert len(result) == 3
            
            # Verify API was called with setting information
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert "A cyberpunk future" in call_kwargs['messages'][0]['content']
            assert "provide 3 distinct" in call_kwargs['system']
    
    @patch('sologm.rpg_helper.services.claude_service.Anthropic')
    def test_generate_interpretations_api_error(self, mock_anthropic):
        """Test handling of API errors."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client
        
        # Create client and call method
        client = ClaudeClient(api_key='test_key')
        result = client.generate_interpretations(
            context="A mountain pass",
            keywords=["danger", "avalanche"]
        )
        
        # Verify fallback results
        assert len(result) == 5
        assert "Error generating interpretations" in result[0]
        
        # Verify the mock was called
        mock_anthropic.assert_called_once_with(api_key='test_key')
    
    def test_parse_numbered_list_standard(self):
        """Test parsing a standard numbered list."""
        client = ClaudeClient(api_key='test_key')
        text = "1. First item\n2. Second item\n3. Third item"
        result = client._parse_numbered_list(text, 3)
        
        assert len(result) == 3
        assert result[0] == "First item"
        assert result[1] == "Second item"
        assert result[2] == "Third item"
    
    def test_parse_numbered_list_with_multiline_items(self):
        """Test parsing a numbered list with multi-line items."""
        client = ClaudeClient(api_key='test_key')
        text = "1. First item\n   with continuation\n2. Second item\n   also with continuation\n3. Third item"
        result = client._parse_numbered_list(text, 3)
        
        assert len(result) == 3
        assert "with continuation" in result[0]
        assert "also with continuation" in result[1]
    
    def test_parse_numbered_list_fallback(self):
        """Test fallback parsing when standard parsing fails."""
        client = ClaudeClient(api_key='test_key')
        # Text without proper numbered list format
        text = "Item one\nItem two\nItem three"
        result = client._parse_numbered_list(text, 3)
        
        assert len(result) == 3
    
    def test_parse_numbered_list_wrong_count(self):
        """Test handling when the number of items doesn't match expected count."""
        client = ClaudeClient(api_key='test_key')
        text = "1. First item\n2. Second item"  # Only 2 items when 3 expected
        result = client._parse_numbered_list(text, 3)
        
        assert len(result) == 3  # Should still return 3 items
    
    @patch('sologm.rpg_helper.services.claude_service.claude_client', None)
    @patch('sologm.rpg_helper.services.claude_service.ClaudeClient')
    def test_get_claude_client_creates_new(self, mock_client_class):
        """Test that get_claude_client creates a new client when none exists."""
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        
        result = get_claude_client()
        
        mock_client_class.assert_called_once()
        assert result == mock_instance
    
    @patch('sologm.rpg_helper.services.claude_service.claude_client')
    def test_get_claude_client_returns_existing(self, mock_client):
        """Test that get_claude_client returns existing client."""
        result = get_claude_client()
        
        assert result == mock_client 