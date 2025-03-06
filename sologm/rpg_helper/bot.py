"""
Main bot application.
"""
# Update imports to use new models directly
from sologm.rpg_helper.models.init_db import init_db

# Initialize the database at startup
def startup():
    """Initialize the bot."""
    # Initialize the database
    init_db()
    # Rest of startup code...

# Rest of the file remains the same 