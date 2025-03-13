"""
Tests for the MythicGameService class.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call

from sqlalchemy.orm import Session

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import (
    GameType, MythicChaosFactor, ChaosBoundaryError
)
from sologm.rpg_helper.services.game.mythic_game_service import MythicGameService


@pytest.fixture
def mock_game():
    """Create a mock game for testing."""
    game = MagicMock(spec=Game)
    game.id = "test-game-id"
    game.name = "Test Game"
    game.game_type = GameType.MYTHIC
    game.updated_at = datetime.now()
    
    # Setup get_setting to return default chaos factor
    game.get_setting.return_value = MythicChaosFactor.AVERAGE
    
    return game


@pytest.fixture
def mythic_service(mock_game):
    """Create a MythicGameService instance with a mock game."""
    return MythicGameService(mock_game)


class TestMythicGameService:
    """Tests for the MythicGameService class."""

    def test_init(self, mock_game):
        """Test initialization of MythicGameService."""
        service = MythicGameService(mock_game)
        assert service.game == mock_game

    def test_init_wrong_game_type(self):
        """Test initialization with wrong game type."""
        game = MagicMock(spec=Game)
        game.game_type = GameType.STANDARD
        game.id = "test-game-id"
        
        with pytest.raises(ValueError) as excinfo:
            MythicGameService(game)
        
        assert "not a Mythic game" in str(excinfo.value)

    def test_get_chaos_factor(self, mythic_service, mock_game):
        """Test getting the chaos factor."""
        # Setup
        mock_game.get_setting.return_value = MythicChaosFactor.AVERAGE
        
        # Execute
        result = mythic_service.get_chaos_factor()
        
        # Verify
        assert result == MythicChaosFactor.AVERAGE
        mock_game.get_setting.assert_called_with(
            mythic_service.SETTING_CHAOS_FACTOR, 
            MythicChaosFactor.AVERAGE
        )

    @patch('sologm.rpg_helper.services.game.mythic_game_service.object_session')
    def test_increase_chaos(self, mock_object_session, mythic_service, mock_game):
        """Test increasing the chaos factor."""
        # Setup
        mock_object_session.return_value = None
        current_chaos = MythicChaosFactor.AVERAGE
        mock_game.get_setting.return_value = current_chaos
        
        # Execute
        result = mythic_service.increase_chaos()
        
        # Verify
        assert result == current_chaos + 1
        mock_game.set_setting.assert_called_with(
            mythic_service.SETTING_CHAOS_FACTOR, 
            current_chaos + 1
        )

    def test_increase_chaos_at_max(self, mythic_service, mock_game):
        """Test increasing the chaos factor when already at max."""
        # Setup
        mock_game.get_setting.return_value = MythicChaosFactor.MAX
        
        # Execute & Verify
        with pytest.raises(ChaosBoundaryError) as excinfo:
            mythic_service.increase_chaos()
        
        assert "Cannot increase chaos factor above maximum" in str(excinfo.value)
        assert excinfo.value.current == MythicChaosFactor.MAX
        assert excinfo.value.attempted == MythicChaosFactor.MAX + 1

    @patch('sologm.rpg_helper.services.game.mythic_game_service.object_session')
    def test_decrease_chaos(self, mock_object_session, mythic_service, mock_game):
        """Test decreasing the chaos factor."""
        # Setup
        mock_object_session.return_value = None
        current_chaos = MythicChaosFactor.AVERAGE
        mock_game.get_setting.return_value = current_chaos
        
        # Execute
        result = mythic_service.decrease_chaos()
        
        # Verify
        assert result == current_chaos - 1
        mock_game.set_setting.assert_called_with(
            mythic_service.SETTING_CHAOS_FACTOR, 
            current_chaos - 1
        )

    def test_decrease_chaos_at_min(self, mythic_service, mock_game):
        """Test decreasing the chaos factor when already at min."""
        # Setup
        mock_game.get_setting.return_value = MythicChaosFactor.MIN
        
        # Execute & Verify
        with pytest.raises(ChaosBoundaryError) as excinfo:
            mythic_service.decrease_chaos()
        
        assert "Cannot decrease chaos factor below minimum" in str(excinfo.value)
        assert excinfo.value.current == MythicChaosFactor.MIN
        assert excinfo.value.attempted == MythicChaosFactor.MIN - 1

    @patch('sologm.rpg_helper.services.game.mythic_game_service.object_session')
    def test_set_chaos_factor(self, mock_object_session, mythic_service, mock_game):
        """Test setting the chaos factor."""
        # Setup
        mock_object_session.return_value = None
        current_chaos = MythicChaosFactor.AVERAGE
        new_chaos = MythicChaosFactor.HIGH
        mock_game.get_setting.return_value = current_chaos
        
        # Execute
        result = mythic_service.set_chaos_factor(new_chaos)
        
        # Verify
        assert result == new_chaos
        mock_game.set_setting.assert_called_with(
            mythic_service.SETTING_CHAOS_FACTOR, 
            new_chaos
        )

    @patch('sologm.rpg_helper.services.game.mythic_game_service.object_session')
    def test_set_chaos_factor_below_min(self, mock_object_session, mythic_service, mock_game):
        """Test setting the chaos factor below minimum."""
        # Setup
        mock_object_session.return_value = None
        current_chaos = MythicChaosFactor.AVERAGE
        new_chaos = MythicChaosFactor.MIN - 1
        mock_game.get_setting.return_value = current_chaos
        
        # Execute & Verify
        with pytest.raises(ChaosBoundaryError) as excinfo:
            mythic_service.set_chaos_factor(new_chaos)
        
        assert "Cannot decrease chaos factor below minimum" in str(excinfo.value)
        assert excinfo.value.current == current_chaos
        assert excinfo.value.attempted == new_chaos

    @patch('sologm.rpg_helper.services.game.mythic_game_service.object_session')
    def test_set_chaos_factor_above_max(self, mock_object_session, mythic_service, mock_game):
        """Test setting the chaos factor above maximum."""
        # Setup
        mock_object_session.return_value = None
        current_chaos = MythicChaosFactor.AVERAGE
        new_chaos = MythicChaosFactor.MAX + 1
        mock_game.get_setting.return_value = current_chaos
        
        # Execute & Verify
        with pytest.raises(ChaosBoundaryError) as excinfo:
            mythic_service.set_chaos_factor(new_chaos)
        
        assert "Cannot increase chaos factor above maximum" in str(excinfo.value)
        assert excinfo.value.current == current_chaos
        assert excinfo.value.attempted == new_chaos

    @patch('sologm.rpg_helper.services.game.mythic_game_service.object_session')
    def test_set_chaos_factor_commits_session(self, mock_object_session, mythic_service, mock_game):
        """Test that setting chaos factor commits the session if one exists."""
        # Setup
        mock_session = MagicMock(spec=Session)
        mock_object_session.return_value = mock_session
        
        # Execute
        mythic_service.set_chaos_factor(MythicChaosFactor.HIGH)
        
        # Verify
        mock_session.commit.assert_called_once()

    @patch('sologm.rpg_helper.services.game.mythic_game_service.object_session')
    def test_set_chaos_factor_no_session(self, mock_object_session, mythic_service, mock_game):
        """Test that setting chaos factor doesn't commit if no session exists."""
        # Setup
        mock_object_session.return_value = None
        
        # Execute
        mythic_service.set_chaos_factor(MythicChaosFactor.HIGH)
        
        # Verify - no exception should be raised
        assert True

    @patch('sologm.rpg_helper.services.game.mythic_game_service.object_session')
    def test_set_chaos_factor_updates_timestamp(self, mock_object_session, mythic_service, mock_game):
        """Test that setting chaos factor updates the game's timestamp."""
        # Setup
        mock_object_session.return_value = None
        old_timestamp = mock_game.updated_at
        
        # Execute
        mythic_service.set_chaos_factor(MythicChaosFactor.HIGH)
        
        # Verify
        assert mock_game.updated_at > old_timestamp 