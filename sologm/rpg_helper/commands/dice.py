"""
Command handlers for dice rolling.
"""
import logging
from slack_bolt import App

from rpg_helper.services.dice_service import roll_dice, DiceRollError
from rpg_helper.utils.formatting import format_dice_result

logger = logging.getLogger(__name__)


def register_dice_commands(app: App) -> None:
    """
    Register dice rolling command handlers with the Slack app.
    
    Args:
        app: Slack Bolt app instance
    """
    @app.command("/roll")
    def handle_roll_command(ack, command, say):
        """Handle the /roll command for dice rolling."""
        ack()
        dice_str = command["text"].strip()
        
        # Handle empty command
        if not dice_str:
            say("Please specify dice to roll, e.g., `/roll 2d6+3`")
            return
        
        # Handle the roll
        try:
            result = roll_dice(dice_str)
            response = format_dice_result(result)
            say(response)
        except DiceRollError as e:
            say(f"Dice roll error: {str(e)}")
        except Exception as e:
            logger.error(f"Error handling dice roll: {e}")
            say(f"An error occurred while processing your dice roll: {str(e)}")