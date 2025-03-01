"""
Handlers for Slack interactive actions.
"""
import re
import logging
from slack_bolt import App

from rpg_helper.services.poll_service import record_vote

logger = logging.getLogger(__name__)


def register_action_handlers(app: App) -> None:
    """
    Register action handlers with the Slack app.
    
    Args:
        app: Slack Bolt app instance
    """
    # Handler for vote button clicks
    @app.action(re.compile(r"vote_option_(\d+)"))
    def handle_vote(ack, body, client, logger):
        """Handle vote button clicks."""
        ack()
        
        try:
            user_id = body["user"]["id"]
            channel_id = body["channel"]["id"]
            value = body["actions"][0]["value"]
            poll_id, option_idx = value.split(":")
            option_idx = int(option_idx)
            
            # Record the vote
            success, message = record_vote(poll_id, user_id, option_idx)
            
            # Send ephemeral message to confirm vote
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=message
            )
            
        except Exception as e:
            logger.error(f"Error handling vote: {e}")
            # Notify user of error
            try:
                client.chat_postEphemeral(
                    channel=body["channel"]["id"],
                    user=body["user"]["id"],
                    text=f"Error processing your vote: {str(e)}"
                )
            except Exception:
                logger.error("Could not send error message to user")