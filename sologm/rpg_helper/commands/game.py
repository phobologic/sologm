"""
Command handlers for managing games.
"""
import logging
from typing import List, Dict, Any
from slack_bolt import App

from rpg_helper.models.game import (
    Game, create_game, get_games_in_channel, 
    get_active_game_for_user, delete_game, games_by_id
)
from rpg_helper.models.user import get_user_preferences

logger = logging.getLogger(__name__)


def register_game_commands(app: App) -> None:
    """
    Register game management command handlers with the Slack app.
    
    Args:
        app: Slack Bolt app instance
    """
    @app.command("/create-game")
    def handle_create_game_command(ack, command, say, client):
        """Handle the /create-game command to create a new RPG game."""
        ack()
        
        game_name = command["text"].strip()
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        
        if not game_name:
            say("Please provide a name for the game. Usage: `/create-game Game Name`")
            return
        
        try:
            # Create the game
            game = create_game(game_name, user_id, channel_id)
            
            # Update the user's active game
            prefs = get_user_preferences(user_id)
            prefs.active_game_id = game.id
            
            # Build the response blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"New Game: {game_name}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}> has created a new GM-less RPG game! Use `/join-game` to join."
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Created by:* <@{user_id}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Game ID:* {game.id}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Setting:* No setting description yet. Use `/game-setting` to add one."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "This is now your active game. All RPG Helper commands will use this game's context."
                        }
                    ]
                }
            ]
            
            # Send the message
            say(blocks=blocks)
            
            # Open the setting modal to encourage setting a description
            client.views_open(
                trigger_id=command["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "game_setting_modal",
                    "private_metadata": game.id,  # Store game ID
                    "title": {"type": "plain_text", "text": "Game Setting"},
                    "submit": {"type": "plain_text", "text": "Save"},
                    "close": {"type": "plain_text", "text": "Skip for Now"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Describe the setting for \"{game_name}\"*"
                            }
                        },
                        {
                            "type": "input",
                            "block_id": "setting_block",
                            "label": {"type": "plain_text", "text": "Setting Description"},
                            "hint": {"type": "plain_text", "text": "This will be used by Claude AI to generate consistent interpretations."},
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "setting_input",
                                "multiline": True,
                                "placeholder": {"type": "plain_text", "text": "E.g., A post-apocalyptic world where nature has reclaimed cities and technology is rare..."}
                            }
                        }
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating game: {e}")
            say(f"Error creating game: {str(e)}")
    
    @app.command("/join-game")
    def handle_join_game_command(ack, command, say):
        """Handle the /join-game command to join an existing game."""
        ack()
        
        game_id = command["text"].strip()
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        
        try:
            # Find games in the channel
            channel_games = get_games_in_channel(channel_id)
            
            if not channel_games:
                say("There are no games in this channel. Use `/create-game` to create one.")
                return
            
            # If no game ID provided, show list of available games
            if not game_id:
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Available games in this channel:"
                        }
                    }
                ]
                
                for game in channel_games:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{game.name}*\nCreated by <@{game.creator_id}> • {len(game.members)} members"
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Join",
                                "emoji": True
                            },
                            "value": game.id,
                            "action_id": "join_game_button"
                        }
                    })
                
                say(blocks=blocks)
                return
            
            # If game ID provided, try to join that game
            if game_id not in games_by_id:
                say(f"Game with ID {game_id} not found. Use `/join-game` without parameters to see available games.")
                return
            
            game = games_by_id[game_id]
            
            # Check if the game is in this channel
            if game.channel_id != channel_id:
                say("This game is not available in this channel.")
                return
            
            # Add user to the game
            game.add_member(user_id)
            
            # Set as active game for the user
            prefs = get_user_preferences(user_id)
            prefs.active_game_id = game.id
            
            # Confirm joining
            say(f"You have joined *{game.name}*! This is now your active game in this channel.")
            
        except Exception as e:
            logger.error(f"Error joining game: {e}")
            say(f"Error joining game: {str(e)}")
    
    @app.command("/leave-game")
    def handle_leave_game_command(ack, command, say):
        """Handle the /leave-game command to leave a game."""
        ack()
        
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        
        try:
            # Get user's active game
            active_game = get_active_game_for_user(user_id, channel_id)
            
            if not active_game:
                say("You are not currently in any game in this channel.")
                return
            
            # Leave the game
            if active_game.is_creator(user_id):
                say(f"You are the creator of *{active_game.name}*. If you want to end the game, use `/end-game` instead.")
                return
            
            active_game.remove_member(user_id)
            
            # Update user preferences
            prefs = get_user_preferences(user_id)
            if prefs.active_game_id == active_game.id:
                prefs.active_game_id = None
            
            say(f"You have left *{active_game.name}*.")
            
        except Exception as e:
            logger.error(f"Error leaving game: {e}")
            say(f"Error leaving game: {str(e)}")
    
    @app.command("/end-game")
    def handle_end_game_command(ack, command, say):
        """Handle the /end-game command to completely end a game."""
        ack()
        
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        
        try:
            # Get user's active game
            active_game = get_active_game_for_user(user_id, channel_id)
            
            if not active_game:
                say("You are not currently in any game in this channel.")
                return
            
            # Check if user is the creator
            if not active_game.is_creator(user_id):
                say("Only the game creator can end the game.")
                return
            
            # Confirm and delete
            game_name = active_game.name
            game_id = active_game.id
            
            # Get all members to update their preferences
            members = list(active_game.members)
            
            # Delete the game
            delete_game(game_id)
            
            # Update all members' preferences
            for member_id in members:
                prefs = get_user_preferences(member_id)
                if prefs.active_game_id == game_id:
                    prefs.active_game_id = None
            
            say(f"The game *{game_name}* has been ended and deleted.")
            
        except Exception as e:
            logger.error(f"Error ending game: {e}")
            say(f"Error ending game: {str(e)}")
    
    @app.command("/game-setting")
    def handle_game_setting_command(ack, command, client):
        """Handle the /game-setting command to update a game's setting description."""
        ack()
        
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        
        try:
            # Get user's active game
            active_game = get_active_game_for_user(user_id, channel_id)
            
            if not active_game:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="You are not currently in any game in this channel. Join or create a game first."
                )
                return
            
            # Open the setting modal
            client.views_open(
                trigger_id=command["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "game_setting_modal",
                    "private_metadata": active_game.id,  # Store game ID
                    "title": {"type": "plain_text", "text": "Game Setting"},
                    "submit": {"type": "plain_text", "text": "Save"},
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Edit the setting for \"{active_game.name}\"*"
                            }
                        },
                        {
                            "type": "input",
                            "block_id": "setting_block",
                            "label": {"type": "plain_text", "text": "Setting Description"},
                            "hint": {"type": "plain_text", "text": "This will be used by Claude AI to generate consistent interpretations."},
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "setting_input",
                                "multiline": True,
                                "initial_value": active_game.setting_description or "",
                                "placeholder": {"type": "plain_text", "text": "E.g., A post-apocalyptic world where nature has reclaimed cities and technology is rare..."}
                            }
                        }
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"Error opening game setting modal: {e}")
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Error updating game setting: {str(e)}"
            )
    
    @app.command("/switch-game")
    def handle_switch_game_command(ack, command, say):
        """Handle the /switch-game command to switch between games in a channel."""
        ack()
        
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        
        try:
            # Find all games the user is a member of in this channel
            channel_games = get_games_in_channel(channel_id)
            user_games = [game for game in channel_games if game.is_member(user_id)]
            
            if not user_games:
                say("You are not a member of any game in this channel. Use `/join-game` to join one.")
                return
            
            if len(user_games) == 1:
                active_game = user_games[0]
                prefs = get_user_preferences(user_id)
                prefs.active_game_id = active_game.id
                say(f"Switched to *{active_game.name}* as your active game.")
                return
            
            # Show list of games to switch to
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Select a game to switch to:"
                    }
                }
            ]
            
            for game in user_games:
                # Mark the currently active one
                prefs = get_user_preferences(user_id)
                is_active = prefs.active_game_id == game.id
                active_text = " (Active)" if is_active else ""
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{game.name}*{active_text}\nCreated by <@{game.creator_id}> • {len(game.members)} members"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Select",
                            "emoji": True
                        },
                        "value": game.id,
                        "action_id": "switch_game_button"
                    }
                })
            
            say(blocks=blocks)
            
        except Exception as e:
            logger.error(f"Error switching game: {e}")
            say(f"Error switching game: {str(e)}")
    
    @app.command("/game-info")
    def handle_game_info_command(ack, command, say):
        """Handle the /game-info command to display information about the current game."""
        ack()
        
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        
        try:
            # Get user's active game
            active_game = get_active_game_for_user(user_id, channel_id)
            
            if not active_game:
                say("You are not currently in any game in this channel.")
                return
            
            # Format member list
            member_count = len(active_game.members)
            member_list = ", ".join([f"<@{member_id}>" for member_id in list(active_game.members)[:5]])
            if member_count > 5:
                member_list += f" and {member_count - 5} more"
            
            # Build the response blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": active_game.name
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Created by:* <@{active_game.creator_id}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Members:* {member_count}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Current Chaos Factor:* {active_game.chaos_factor}/9"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Game ID:* {active_game.id}"
                        }
                    ]
                }
            ]
            
            # Add setting description if available
            if active_game.setting_description:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Setting:*\n{active_game.setting_description}"
                    }
                })
            else:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Setting:* No setting description yet. Use `/game-setting` to add one."
                    }
                })
            
            # Add members list
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Members:* {member_list}"
                }
            })
            
            # Add available commands
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Available Commands:*\n• `/roll` - Roll dice\n• `/fate` - Mythic GM fate check\n• `/ask-claude` - Get interpretations from Claude AI\n• `/interpret` - Generate random interpretations"
                }
            })
            
            # Send the message
            say(blocks=blocks)
            
        except Exception as e:
            logger.error(f"Error getting game info: {e}")
            say(f"Error getting game info: {str(e)}")
    
    @app.command("/chaos")
    def handle_chaos_command(ack, command, say):
        """Handle the /chaos command to view or update the game's chaos factor."""
        ack()
        
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        chaos_value = command["text"].strip()
        
        try:
            # Get user's active game
            active_game = get_active_game_for_user(user_id, channel_id)
            
            if not active_game:
                say("You are not currently in any game in this channel.")
                return
            
            # If no value provided, show current chaos factor
            if not chaos_value:
                say(f"The current chaos factor for *{active_game.name}* is *{active_game.chaos_factor}/9*.")
                return
            
            # Try to update the chaos factor
            try:
                new_chaos = int(chaos_value)
                if not 1 <= new_chaos <= 9:
                    say("Chaos factor must be between 1 and 9.")
                    return
                
                # Update the chaos factor
                old_chaos = active_game.chaos_factor
                active_game.update_chaos_factor(new_chaos)
                
                # Notify about the change
                if new_chaos > old_chaos:
                    direction = "increased"
                elif new_chaos < old_chaos:
                    direction = "decreased"
                else:
                    direction = "remained at"
                
                say(f"The chaos factor has {direction} to *{new_chaos}/9* for *{active_game.name}*.")
                
            except ValueError:
                say("Chaos factor must be a number between 1 and 9.")
                
        except Exception as e:
            logger.error(f"Error handling chaos command: {e}")
            say(f"Error updating chaos factor: {str(e)}")
    
    # Handle the game setting modal submission
    @app.view("game_setting_modal")
    def handle_game_setting_modal_submission(ack, body, view, client):
        """Handle submission of the game setting modal."""
        ack()
        
        user_id = body["user"]["id"]
        game_id = view["private_metadata"]
        setting_value = view["state"]["values"]["setting_block"]["setting_input"]["value"]
        
        try:
            # Check if the game exists
            if game_id not in games_by_id:
                client.chat_postEphemeral(
                    channel=body["user"]["id"],
                    user=body["user"]["id"],
                    text="The game no longer exists."
                )
                return
            
            game = games_by_id[game_id]
            
            # Update the game's setting
            game.update_setting(setting_value)
            
            # Send a confirmation message
            client.chat_postEphemeral(
                channel=game.channel_id,
                user=user_id,
                text=f"The setting for *{game.name}* has been updated."
            )
            
        except Exception as e:
            logger.error(f"Error saving game setting: {e}")
            client.chat_postEphemeral(
                channel=body["user"]["id"],
                user=body["user"]["id"],
                text=f"Error saving setting description: {str(e)}"
            )
    
    # Button action handler for joining a game
    @app.action("join_game_button")
    def handle_join_game_button(ack, body, client):
        """Handle the join game button click."""
        ack()
        
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        game_id = body["actions"][0]["value"]
        
        try:
            # Check if the game exists
            if game_id not in games_by_id:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="This game no longer exists."
                )
                return
            
            game = games_by_id[game_id]
            
            # Check if the game is in this channel
            if game.channel_id != channel_id:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="This game is not available in this channel."
                )
                return
            
            # Add user to the game
            game.add_member(user_id)
            
            # Set as active game for the user
            prefs = get_user_preferences(user_id)
            prefs.active_game_id = game.id
            
            # Confirm joining
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"You have joined *{game.name}*! This is now your active game in this channel."
            )
            
        except Exception as e:
            logger.error(f"Error handling join game button: {e}")
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Error joining game: {str(e)}"
            )
    
    # Button action handler for switching games
    @app.action("switch_game_button")
    def handle_switch_game_button(ack, body, client):
        """Handle the switch game button click."""
        ack()
        
        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        game_id = body["actions"][0]["value"]
        
        try:
            # Check if the game exists
            if game_id not in games_by_id:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="This game no longer exists."
                )
                return
            
            game = games_by_id[game_id]
            
            # Check if the game is in this channel
            if game.channel_id != channel_id:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="This game is not available in this channel."
                )
                return
            
            # Check if user is a member
            if not game.is_member(user_id):
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text=f"You are not a member of *{game.name}*. Use `/join-game` to join."
                )
                return
            
            # Set as active game for the user
            prefs = get_user_preferences(user_id)
            prefs.active_game_id = game.id
            
            # Confirm switching
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Switched to *{game.name}* as your active game."
            )
            
        except Exception as e:
            logger.error(f"Error handling switch game button: {e}")
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Error switching game: {str(e)}"
            )