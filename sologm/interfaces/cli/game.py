"""
Game-related CLI commands.
"""
import os
import click
import getpass
from typing import Optional
from datetime import datetime

from sologm.commands.game.init import InitGameCommand
from sologm.commands.game.list import ListGamesCommand
from sologm.commands.contexts import CLIContext
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger(__name__)

@click.group()
def game():
    """Game management commands."""
    pass

@game.command()
@click.argument("name")
@click.option("--system", "-s", default="standard", help="Game system to use")
@click.option("--description", "-d", default="", help="Game description")
def init(name: str, system: str, description: str):
    """Initialize a new game."""
    from sologm.interfaces.cli.main import get_command_bus, get_workspace_info
    
    workspace_id, channel_id = get_workspace_info()
    bus = get_command_bus()
    
    # Create context with current directory and user
    context = CLIContext(
        working_directory=channel_id,
        user=getpass.getuser()
    )
    
    command = InitGameCommand(
        name=name,
        game_type=system,
        description=description,
        channel_id=channel_id,
        workspace_id=workspace_id,
        context=context
    )
    
    result = bus.execute(command)
    
    if result.success:
        click.echo(click.style("✨ Game initialized successfully!", fg="green"))
        click.echo(result.message)
    else:
        click.echo(click.style(f"Error: {result.message}", fg="red"), err=True)

@game.command()
def list():
    """List games in current directory."""
    from sologm.interfaces.cli.main import get_command_bus, get_workspace_info
    
    workspace_id, channel_id = get_workspace_info()
    bus = get_command_bus()
    
    # Create context with current directory and user
    context = CLIContext(
        working_directory=channel_id,
        user=getpass.getuser()
    )
    
    command = ListGamesCommand(
        channel_id=channel_id,
        workspace_id=workspace_id,
        context=context
    )
    
    result = bus.execute(command)
    
    if not result.success:
        click.echo(click.style(f"Error: {result.message}", fg="red"), err=True)
        return
        
    games = result.data["games"]
    if not games:
        click.echo("No games found in current directory.")
        return
        
    for game in games:
        status = click.style("active", fg="green") if game["is_active"] else click.style("inactive", fg="yellow")
        
        # Print game header with name and status
        click.echo(f"🎲 {click.style(game['name'], bold=True)} ({status})")
        
        # Print game details
        click.echo(f"    System: {game['game_type']}")
        if game["description"]:
            click.echo(f"    Description: {game['description']}")
            
        created_at = datetime.fromisoformat(game["created_at"])
        click.echo(f"    Created: {created_at.isoformat()}")
        
        if game["members"]:
            click.echo(f"    Members: {', '.join(game['members'])}")
            
        logger.debug("Displayed game details",
            game_name=game["name"],
            is_active=game["is_active"],
            member_count=len(game["members"])
        ) 