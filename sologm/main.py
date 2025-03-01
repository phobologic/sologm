#!/usr/bin/env python3
"""
Main entry point for the RPG Helper Slack bot application.
"""
import os
import logging
from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode import SocketModeHandler

from rpg_helper.app import create_app

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Initialize and start the Slack bot application."""
    # Create the Slack Bolt app
    app = create_app()

    # Get tokens from environment
    slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    
    if not slack_app_token or not slack_app_token.startswith("xapp-"):
        logger.error("SLACK_APP_TOKEN not found or invalid")
        exit(1)
    
    # Start the Socket Mode handler
    handler = SocketModeHandler(app, slack_app_token)
    logger.info("Starting RPG Helper Bot...")
    handler.start()


if __name__ == "__main__":
    main()