"""
Utilities for formatting Slack messages.
"""
from typing import Dict, List, Optional


def format_dice_result(result: Dict) -> str:
    """
    Format a dice roll result for display in Slack.
    
    Args:
        result: Dice roll result dictionary
        
    Returns:
        Formatted message string
    """
    if not result["success"]:
        return f"Error: {result['error']}"
    
    rolls_str = ", ".join(str(r) for r in result["rolls"])
    return (
        f"*Dice Roll:* {result['dice_str']}\n"
        f"*Rolls:* [{rolls_str}]\n"
        f"*Total:* {result['total']}"
    )


def format_fate_result(result: Dict) -> str:
    """
    Format a fate check result for display in Slack.
    
    Args:
        result: Fate check result dictionary
        
    Returns:
        Formatted message string
    """
    if not result["success"]:
        return f"Error: {result['error']}"
    
    return (
        f"*Fate Check*\n"
        f"*Chaos Factor:* {result['chaos_factor']}\n"
        f"*Likelihood:* {result['likelihood'].title()}\n"
        f"*Roll:* {result['roll']}\n"
        f"*Result:* {result['result']}\n"
        f"*Interpretation:* {result['description']}"
    )


def create_poll_blocks(poll_id: str, question: str, options: List[str], user_id: str, timeout_hours: int) -> List[Dict]:
    """
    Create Slack block kit blocks for a poll message.
    
    Args:
        poll_id: ID of the poll
        question: Poll question text
        options: List of interpretation options
        user_id: User ID of the poll creator
        timeout_hours: Hours until poll expiration
        
    Returns:
        List of Slack block kit blocks
    """
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{question}*\n\nVote for an interpretation:"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    for idx, option in enumerate(options):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Option {idx+1}:* {option}"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": f"Vote {idx+1}",
                    "emoji": True
                },
                "value": f"{poll_id}:{idx}",
                "action_id": f"vote_option_{idx}"
            }
        })
    
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Poll ends in {timeout_hours} hours. Created by <@{user_id}>"
            }
        ]
    })
    
    return blocks


def format_preferences_help() -> str:
    """
    Format the help message for the preferences command.
    
    Returns:
        Formatted help message string
    """
    return (
        "Usage:\n"
        "`/preferences options NUMBER` - Set number of interpretation options (default: 5)\n"
        "`/preferences timeout NUMBER` - Set poll timeout in hours (default: 4)\n"
        "`/preferences show` - Show current preferences"
    )


def format_user_preferences(num_options: int, timeout_hours: int) -> str:
    """
    Format the user preferences display message.
    
    Args:
        num_options: Number of options setting
        timeout_hours: Timeout hours setting
        
    Returns:
        Formatted message string
    """
    return f"Your current preferences:\nNumber of options: {num_options}\nTimeout hours: {timeout_hours}"