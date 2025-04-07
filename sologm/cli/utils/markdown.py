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
    content.append(game.description)
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
    content.append(scene.description)
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

    # Event entry
    content.append(f"- {source_indicator} {event.description}")

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
