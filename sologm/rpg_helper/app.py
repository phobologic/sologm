"""
Slack app configuration and initialization.
"""
import os
import logging
import re
from slack_bolt import App

# Import command handlers
from rpg_helper.commands.dice import register_dice_commands
from rpg_helper.commands.fate import register_fate_commands
from rpg_helper.commands.interpret import register_interpret_commands
from rpg_helper.commands.preferences import register_preference_commands

# Import action handlers
from rpg_helper.handlers.actions import register_action_handlers

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Slack Bolt app."""
    # Initialize the Slack app
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    
    if not slack_bot_token or not slack_bot_token.startswith("xoxb-"):
        logger.error("SLACK_BOT_TOKEN not found or invalid")
        exit(1)
    
    app = App(token=slack_bot_token)
    
    # Register command handlers
    register_dice_commands(app)
    register_fate_commands(app)
    register_interpret_commands(app)
    register_preference_commands(app)
    
    # Register action handlers
    register_action_handlers(app)
    
    # Error handler
    @app.error
    def handle_errors(error, body, logger):
        logger.error(f"Error: {error}")
        logger.debug(f"Request body: {body}")
    
    return app