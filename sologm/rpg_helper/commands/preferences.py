"""
Command handlers for user preferences.
"""
import logging
from slack_bolt import App

from rpg_helper.models.user import user_preferences, UserPreferences
from rpg_helper.utils.formatting import format_preferences_help, format_user_preferences

logger = logging.getLogger(__name__)


def register_preference_commands(app: App) -> None:
    """
    Register preference command handlers with the Slack app.
    
    Args:
        app: Slack Bolt app instance
    """
    @app.command("/preferences")
    def handle_preferences_command(ack, command, say):
        """Handle the /preferences command to set user preferences."""
        ack()
        args = command["text"].strip().split()
        user_id = command["user_id"]
        
        try:
            if not args or args[0] == "help":
                say(format_preferences_help())
                return
            
            if args[0] == "show":
                prefs = user_preferences.get(user_id, UserPreferences(user_id))
                say(format_user_preferences(prefs.num_options, prefs.timeout_hours))
                return
            
            if len(args) < 2:
                say("Please provide a value for the preference.")
                return
            
            try:
                value = int(args[1])
                if value <= 0:
                    say("Value must be a positive number.")
                    return
                
                if user_id not in user_preferences:
                    user_preferences[user_id] = UserPreferences(user_id)
                
                if args[0] == "options":
                    if value > 10:
                        say("Maximum number of options is 10.")
                        return
                    user_preferences[user_id].num_options = value
                    say(f"Number of interpretation options set to {value}.")
                
                elif args[0] == "timeout":
                    if value > 24:
                        say("Maximum timeout is 24 hours.")
                        return
                    user_preferences[user_id].timeout_hours = value
                    say(f"Poll timeout set to {value} hours.")
                
                else:
                    say(f"Unknown preference: {args[0]}")
            
            except ValueError:
                say("Value must be a number.")
                
        except Exception as e:
            logger.error(f"Error handling preferences command: {e}")
            say(f"An error occurred while updating your preferences: {str(e)}")