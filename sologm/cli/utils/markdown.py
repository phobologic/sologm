"""Markdown generation utilities for exporting game content.

This module provides functions to convert game data into formatted markdown text,
allowing users to export their game content for documentation or sharing purposes.
"""

import logging
from typing import List

from sologm.core.event import EventManager
from sologm.core.scene import SceneManager
from sologm.models.act import Act
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.scene import Scene
from sologm.utils.datetime_utils import format_datetime

logger = logging.getLogger(__name__)


def generate_concepts_header() -> List[str]:
    """Generate a header explaining the game structure concepts.

    Creates a markdown section that explains the key concepts of the game structure
    (Game, Acts, Scenes, Events) to help readers understand the document organization.

    Returns:
        List[str]: Markdown lines explaining the game structure concepts
    """
    return [
        "# Game Structure Guide",
        "",
        "This document follows a specific structure to organize your solo roleplaying game:",
        "",
        "## Game",
        "The overall container for your adventure, with a name and description.",
        "",
        "## Acts",
        "Major divisions of your game, similar to acts in a play or chapters in a book. Each act has:",
        "- A sequence number (Act 1, Act 2, etc.)",
        "- A title",
        "- An optional summary describing the overall events or themes",
        "",
        "## Scenes",
        "Specific moments or locations within an act. Each scene has:",
        "- A sequence number within its act",
        "- A title",
        "- A description",
        # Scene status field removed
        "",
        "## Events",
        "Individual moments, actions, or occurrences within a scene. Events can come from:",
        "- 🔮 Oracle interpretations (AI-assisted random events)",
        "- 🎲 Dice rolls (random outcomes)",
        "- Manual entries (player-created events)",
        "",
        "Events form the core narrative of your game, showing what happened in each scene.",
        # Scene completion indicator removed
        "",
        "---",
        "",
    ]


def generate_game_markdown(
    game: Game,
    scene_manager: SceneManager,
    event_manager: EventManager,
    include_metadata: bool = False,
    include_concepts: bool = False,
) -> str:
    """Generate a markdown document for a game with all scenes and events.

    Creates a complete markdown document representing the entire game, including
    all acts, scenes, and events in a hierarchical structure. The document follows
    a consistent format with proper headers and indentation.

    Args:
        game: The game to export
        scene_manager: SceneManager instance for retrieving scene data
        event_manager: EventManager instance for retrieving event data
        include_metadata: Whether to include technical metadata (IDs, timestamps)
        include_concepts: Whether to include a header explaining game concepts

    Returns:
        str: Complete markdown content as a single string with line breaks
    """
    content = []

    if include_concepts:
        content.extend(generate_concepts_header())

    content.append(f"# {game.name}")
    content.append("")

    for line in game.description.split("\n"):
        content.append(line)
    content.append("")

    if include_metadata:
        content.append(f"*Game ID: {game.id}*")
        content.append(f"*Created: {format_datetime(game.created_at)}*")
        content.append("")

    # Process acts if they exist and are loaded.
    if hasattr(game, "acts") and game.acts:
        acts = sorted(game.acts, key=lambda a: a.sequence)

        for act in acts:
            act_content = generate_act_markdown(
                act, scene_manager, event_manager, include_metadata
            )
            content.extend(act_content)
            content.append("")  # Ensure separation between acts.

    return "\n".join(content)


def generate_act_markdown(
    act: Act,
    scene_manager: SceneManager,
    event_manager: EventManager,
    include_metadata: bool = False,
) -> List[str]:
    """Generate markdown content for an act with its scenes.

    Creates a markdown section for a single act, including its title, summary,
    and all scenes contained within it. Scenes are sorted by sequence number.

    Args:
        act: The act to export
        scene_manager: SceneManager instance for retrieving scenes in this act
        event_manager: EventManager instance for retrieving events in scenes
        include_metadata: Whether to include technical metadata (IDs, timestamps)

    Returns:
        List[str]: List of markdown lines representing the act and its scenes
    """
    content = []

    act_title = act.title or "Untitled Act"
    content.append(f"## Act {act.sequence}: {act_title}")
    content.append("")

    if act.summary:
        for line in act.summary.split("\n"):
            content.append(line)
        content.append("")

    if include_metadata:
        content.append(f"*Act ID: {act.id}*")
        content.append(f"*Created: {format_datetime(act.created_at)}*")
        content.append("")

    # Retrieve and sort scenes for the act.
    scenes = scene_manager.list_scenes(act_id=act.id)
    scenes.sort(key=lambda s: s.sequence)

    for scene in scenes:
        scene_content = generate_scene_markdown(scene, event_manager, include_metadata)
        content.extend(scene_content)
        content.append("")  # Ensure separation between scenes.

    return content


def generate_scene_markdown(
    scene: Scene,
    event_manager: EventManager,
    include_metadata: bool = False,
) -> List[str]:
    """Generate markdown content for a scene with its events.

    Creates a markdown section for a single scene, including its title, description,
    and all events that occurred within it. Events are sorted chronologically by
    creation date.

    Args:
        scene: The scene to export
        event_manager: EventManager instance for retrieving events in this scene
        include_metadata: Whether to include technical metadata (IDs, timestamps)

    Returns:
        List[str]: List of markdown lines representing the scene and its events
    """
    content = []

    content.append(f"### Scene {scene.sequence}: {scene.title}")
    content.append("")

    for line in scene.description.split("\n"):
        content.append(line)
    content.append("")

    if include_metadata:
        content.append(f"*Scene ID: {scene.id}*")
        content.append(f"*Created: {format_datetime(scene.created_at)}*")
        content.append(f"*Modified: {format_datetime(scene.modified_at)}*")
        content.append("")

    # Retrieve and sort events for the scene.
    events = event_manager.list_events(scene_id=scene.id)
    events.sort(key=lambda e: e.created_at)

    if events:
        content.append("### Events")
        content.append("")

        for event in events:
            content.extend(generate_event_markdown(event, include_metadata))

    return content


def generate_event_markdown(
    event: Event,
    include_metadata: bool = False,
) -> List[str]:
    """Generate markdown content for an event.

    Creates markdown content for a single event, formatting it as a list item with
    appropriate source indicators (🔮 for oracle events, 🎲 for dice events).
    Multi-line event descriptions are properly indented to maintain list formatting.

    Args:
        event: The event to export
        include_metadata: Whether to include technical metadata (source information)

    Returns:
        List[str]: List of markdown lines representing the event
    """
    content = []

    source_indicator = ""
    if event.source == "oracle":
        source_indicator = " 🔮:"
    elif event.source == "dice":
        source_indicator = " 🎲:"

    description_lines = event.description.split("\n")

    if description_lines:
        content.append(f"-{source_indicator} {description_lines[0]}")

        # Indent subsequent lines to align under the first line's content for list formatting.
        indent = "  " + " " * len(source_indicator)
        for line in description_lines[1:]:
            content.append(f"  {indent} {line}")

    if include_metadata:
        metadata_lines = []
        metadata_lines.append(f"  - Source: {event.source_name}")

        if metadata_lines:
            content.append("")  # Ensure separation before metadata.
            content.extend(metadata_lines)

    return content
