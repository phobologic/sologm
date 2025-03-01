"""
Command handlers for Mythic GM Emulator fate checks.
"""
import logging
from slack_bolt import App

from rpg_helper.services.fate_service import fate_check
from rpg_helper.utils.formatting import format_fate_result

logger = logging.getLogger(__name__)


def register_fate_commands(app: App) -> None:
    """
    Register fate check command handlers with the Slack app.
    
    Args:
        app: Slack Bolt app instance
    """
    @app.command("/fate")
    def handle_fate_command(ack, command, say):
        """Handle the /fate command for Mythic GM fate checks."""
        ack()
        args = command["text"].strip().split()
        
        if len(args) < 2:
            say("Please provide a chaos factor (1-9) and likelihood (Impossible, Very Unlikely, Unlikely, 50/50, Likely, Very Likely, Near Certain)\nExample: `/fate 5 Likely`")
            return
        
        try:
            chaos_factor = args[0]
            likelihood = " ".join(args[1:])
            
            result = fate_check(chaos_factor, likelihood)
            response = format_fate_result(result)
            say(response)
        except Exception as e:
            logger.error(f"Error handling fate check: {e}")
            say(f"An error occurred while processing your fate check: {str(e)}")