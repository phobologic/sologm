"""
Command handlers for interpretation generation and polls.
"""
import logging
from slack_bolt import App

from rpg_helper.models.user import user_preferences, UserPreferences
from rpg_helper.models.poll import active_polls
from rpg_helper.services.interpreter_service import generate_mythic_interpretations
from rpg_helper.services.poll_service import create_poll, end_poll, get_channel_polls
from rpg_helper.utils.formatting import create_poll_blocks

logger = logging.getLogger(__name__)


def register_interpret_commands(app: App) -> None:
    """
    Register interpretation command handlers with the Slack app.
    
    Args:
        app: Slack Bolt app instance
    """
    @app.command("/interpret")
    def handle_interpret_command(ack, command, say, client):
        """Handle the /interpret command to generate interpretation options for voting."""
        ack()
        
        context = command["text"].strip()
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        
        try:
            # Get user preferences (default to 5 options and 4 hour timeout)
            prefs = user_preferences.get(user_id, UserPreferences(user_id))
            num_options = prefs.num_options
            timeout_hours = prefs.timeout_hours
            
            # Generate interpretation options
            options = generate_mythic_interpretations(context, count=num_options)
            
            # Create a new poll
            question = f"How should we interpret this? {context}" if context else "How should we interpret this?"
            poll = create_poll(app, channel_id, user_id, options, question, timeout_hours)
            
            # Create options buttons for the poll
            blocks = create_poll_blocks(poll.id, question, options, user_id, timeout_hours)
            
            # Post the poll message
            try:
                result = client.chat_postMessage(
                    channel=channel_id,
                    blocks=blocks,
                    text=f"Poll: {question}"  # Fallback text
                )
                poll.message_ts = result["ts"]
            except Exception as e:
                logger.error(f"Error posting poll: {e}")
                say(f"Error creating poll: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error handling interpret command: {e}")
            say(f"An error occurred while processing your interpretation request: {str(e)}")

    @app.command("/endpoll")
    def handle_endpoll_command(ack, command, say):
        """Handle the /endpoll command to manually end a poll."""
        ack()
        
        channel_id = command["channel_id"]
        user_id = command["user_id"]
        
        try:
            # Find polls in this channel
            channel_polls = get_channel_polls(channel_id)
            
            if not channel_polls:
                say("There are no active polls in this channel.")
                return
            
            # If there's only one poll, end it
            if len(channel_polls) == 1:
                poll = channel_polls[0]
                
                # Check if user is the creator
                if poll.creator_id != user_id:
                    say("You can only end polls that you created.")
                    return
                
                end_poll(app, poll.id)
                say("Poll ended. Results will be posted shortly.")
            else:
                # If there are multiple polls, show the user's active polls
                user_polls = [p for p in channel_polls if p.creator_id == user_id]
                
                if not user_polls:
                    say("You don't have any active polls in this channel.")
                    return
                
                poll_list = []
                for i, poll in enumerate(user_polls):
                    created_time = poll.created_at.strftime("%H:%M:%S")
                    poll_list.append(f"{i+1}. Poll created at {created_time}: {poll.question[:50]}...")
                
                response = "You have multiple active polls. Use `/endpoll ID` with the number from this list:\n\n"
                response += "\n".join(poll_list)
                say(response)
                
        except Exception as e:
            logger.error(f"Error handling endpoll command: {e}")
            say(f"An error occurred while ending the poll: {str(e)}")