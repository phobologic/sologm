"""Markdown generation utilities."""

import logging
from typing import List

from sologm.core.event import EventManager
from sologm.core.scene import SceneManager
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.scene import Scene, SceneStatus
from sologm.utils.datetime_utils import format_datetime

logger = logging.getLogger(__name__)


def generate_game_markdown(
    game: Game,
    scene_manager: SceneManager,
    event_manager: EventManager,
    include_metadata: bool = False,
) -> str:
    """Generate a markdown document for a game with all scenes and events.

    Args:
        game: The game to export
        scene_manager: SceneManager instance
        event_manager: EventManager instance
        include_metadata: Whether to include technical metadata

    Returns:
        Markdown content as a string
    """
    content = []

    # Game header
    content.append(f"# {game.name}")
    content.append("")
    
    # Handle multi-line game description by ensuring each line is properly formatted
    for line in game.description.split("\n"):
        content.append(line)
    content.append("")

    if include_metadata:
        content.append(f"*Game ID: {game.id}*")
        content.append(f"*Created: {format_datetime(game.created_at)}*")
        content.append("")

    # Get all scenes in sequence order
    scenes = scene_manager.list_scenes(game.id)
    scenes.sort(key=lambda s: s.sequence)

    # Process each scene
    for scene in scenes:
        content.extend(generate_scene_markdown(scene, event_manager, include_metadata))

    return "\n".join(content)


def generate_scene_markdown(
    scene: Scene,
    event_manager: EventManager,
    include_metadata: bool = False,
) -> List[str]:
    """Generate markdown content for a scene with its events.

    Args:
        scene: The scene to export
        event_manager: EventManager instance
        include_metadata: Whether to include technical metadata

    Returns:
        List of markdown lines
    """
    content = []

    # Scene header
    status_indicator = " ✓" if scene.status == SceneStatus.COMPLETED else ""
    content.append(f"## Scene {scene.sequence}: {scene.title}{status_indicator}")
    content.append("")
    
    # Handle multi-line scene description
    for line in scene.description.split("\n"):
        content.append(line)
    content.append("")

    if include_metadata:
        content.append(f"*Scene ID: {scene.id}*")
        content.append(f"*Created: {format_datetime(scene.created_at)}*")
        if scene.completed_at:
            content.append(f"*Completed: {format_datetime(scene.completed_at)}*")
        content.append("")

    # Get all events for this scene
    events = event_manager.list_events(scene.game_id, scene.id)

    # Sort events chronologically
    events.sort(key=lambda e: e.created_at)

    if events:
        content.append("### Events")
        content.append("")

        # Process each event
        for event in events:
            content.extend(generate_event_markdown(event, include_metadata))

    return content


def generate_event_markdown(
    event: Event,
    include_metadata: bool = False,
) -> List[str]:
    """Generate markdown content for an event.

    Args:
        event: The event to export
        include_metadata: Whether to include technical metadata

    Returns:
        List of markdown lines
    """
    content = []

    # Format source indicator
    source_indicator = ""
    if event.source == "oracle":
        source_indicator = " 🔮:"
    elif event.source == "dice":
        source_indicator = " 🎲:"

    # Split the description into lines
    description_lines = event.description.split("\n")
    
    # First line with the bullet and source indicator
    if description_lines:
        content.append(f"- {source_indicator} {description_lines[0]}")
        
        # Additional lines need proper indentation to align with the first line content
        indent = "  " + " " * len(source_indicator)
        for line in description_lines[1:]:
            content.append(f"  {indent} {line}")

    if include_metadata and event.metadata:
        # Format any metadata as indented content
        metadata_lines = []
        for key, value in event.metadata.items():
            if key == "dice_results" and isinstance(value, dict):
                notation = value.get("notation", "")
                total = value.get("total", "")
                results = value.get("results", [])
                metadata_lines.append(f"  - Roll: {notation} = {total} {results}")
            elif key == "interpretation" and isinstance(value, dict):
                title = value.get("title", "")
                if title:
                    metadata_lines.append(f"  - Interpretation: {title}")
            else:
                metadata_lines.append(f"  - {key}: {value}")

        if metadata_lines:
            content.append("")
            content.extend(metadata_lines)
            content.append("")

    return content
