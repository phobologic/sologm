"""
Game-related CLI commands.
"""
import os
import click
from typing import Optional

from sologm.interfaces.cli.main import command_bus
from sologm.commands.contexts import CLIContext
from sologm.commands.game.init import InitGameCommand
from sologm.commands.game.list import ListGamesCommand

@click.group()
def game():
    """Manage games."""
    pass

@game.command()
@click.argument('name')
@click.option('--system', '-s', default='standard', help='Game system to use (standard or mythic)')
@click.option('--description', '-d', help='Description of the game')
def init(name: str, system: str, description: Optional[str]):
    """Initialize a new game."""
    # Create CLI context
    context = CLIContext(
        working_directory=os.getcwd(),
        user=os.getenv('USER', 'unknown')
    )
    
    # Create command
    command = InitGameCommand(
        game_system=system,
        name=name,
        channel_id=os.getcwd(),  # Use current directory as channel ID
        workspace_id=f"cli:{os.getcwd()}",  # Use CLI workspace prefix
        description=description
    )
    
    # Set context on command
    command.context = context
    
    # Execute command
    result = command_bus.execute(command)
    
    # Display result
    if result.success:
        click.echo(click.style(result.message, fg='green'))
    else:
        click.echo(click.style(result.message, fg='red'))
        exit(1)

@game.command()
def list():
    """List games in the current directory."""
    # Create CLI context
    context = CLIContext(
        working_directory=os.getcwd(),
        user=os.getenv('USER', 'unknown')
    )
    
    # Create command
    command = ListGamesCommand(
        channel_id=os.getcwd(),  # Use current directory as channel ID
        workspace_id=f"cli:{os.getcwd()}"  # Use CLI workspace prefix
    )
    
    # Set context on command
    command.context = context
    
    # Execute command
    result = command_bus.execute(command)
    
    # Display result
    if not result.success:
        click.echo(click.style(result.message, fg='red'))
        exit(1)
    
    games = result.data.get('games', [])
    if not games:
        click.echo("No games found in current directory.")
        return
    
    # Display games
    click.echo("Games in current directory:")
    for game in games:
        status = click.style("Active", fg='green') if game['is_active'] else click.style("Inactive", fg='red')
        click.echo(f"\n🎲 {click.style(game['name'], bold=True)} ({status})")
        click.echo(f"    System: {game['game_type']}")
        if game['description']:
            click.echo(f"    Description: {game['description']}")
        click.echo(f"    Created: {game['created_at']}")
        if game['members']:
            click.echo(f"    Members: {', '.join(game['members'])}") 