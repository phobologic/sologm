"""Utility functions for SQLAlchemy models."""

import uuid
from typing import Any, Callable, List, Optional

# Navigation Property Utility Functions
# ====================================
#
# These utilities consolidate repetitive navigation property patterns across SoloGM
# models. They replace manual implementations of common patterns like active filtering,
# latest by timestamp, cross-relationship navigation, and collection aggregation.
#
# Identified Navigation Patterns:
# 1. Active filtering: Find entity where `is_active = True` (e.g., `active_act`)
# 2. Latest by timestamp: Find most recent entity by `created_at` (e.g., `latest_event`)
# 3. First by sequence: Find entity with lowest `sequence` (e.g., `first_scene`)
# 4. Current by flag: Find entity where `is_current = True` (e.g., `current_set`)
# 5. Cross-relationship navigation: Navigate through multiple relationships
# 6. Collection aggregation: Collect entities across relationships
# 7. Filtered collections: Filter collections by criteria (e.g., `selected_items`)


def get_active_entity(collection: List[Any]) -> Optional[Any]:
    """Get the first entity where is_active is True.

    Args:
        collection: List of entities to search through

    Returns:
        The first active entity, or None if no active entities found

    Example:
        # Replaces: next((act for act in self.acts if act.is_active), None)
        return get_active_entity(self.acts)
    """
    if not collection:
        return None
    return next(
        (entity for entity in collection if getattr(entity, "is_active", False)), None
    )


def get_latest_entity(collection: List[Any]) -> Optional[Any]:
    """Get the most recent entity by created_at timestamp.

    Args:
        collection: List of entities to search through

    Returns:
        The entity with the latest created_at timestamp, or None if collection is empty

    Example:
        # Replaces: max(self.events, key=lambda e: e.created_at, default=None)
        return get_latest_entity(self.events)
    """
    if not collection:
        return None

    # Filter out None values and get entities with valid timestamps
    valid_entities = [entity for entity in collection if entity is not None]
    if not valid_entities:
        return None

    def get_timestamp(entity):
        timestamp = getattr(entity, "created_at", None)
        if timestamp is None:
            # Use epoch time (1970-01-01) for entities without created_at
            from datetime import datetime

            return datetime.fromtimestamp(0)
        return timestamp

    return max(valid_entities, key=get_timestamp, default=None)


def get_first_entity_by_sequence(collection: List[Any]) -> Optional[Any]:
    """Get the entity with the lowest sequence number.

    Args:
        collection: List of entities to search through

    Returns:
        The entity with the lowest sequence number, or None if collection is empty

    Example:
        # Replaces: min(self.scenes, key=lambda s: s.sequence, default=None)
        return get_first_entity_by_sequence(self.scenes)
    """
    if not collection:
        return None

    # Filter out None values
    valid_entities = [entity for entity in collection if entity is not None]
    if not valid_entities:
        return None

    return min(
        valid_entities,
        key=lambda entity: getattr(entity, "sequence", float("inf")),
        default=None,
    )


def get_current_entity(collection: List[Any]) -> Optional[Any]:
    """Get the first entity where is_current is True.

    Args:
        collection: List of entities to search through

    Returns:
        The first current entity, or None if no current entities found

    Example:
        # Replaces: next((s for s in self.interpretation_sets if s.is_current), None)
        return get_current_entity(self.interpretation_sets)
    """
    if not collection:
        return None
    return next(
        (entity for entity in collection if getattr(entity, "is_current", False)), None
    )


def get_filtered_collection(
    collection: List[Any], filter_field: str, filter_value: Any
) -> List[Any]:
    """Get entities from collection where field matches value.

    Args:
        collection: List of entities to filter
        filter_field: Name of the field to filter by
        filter_value: Value to match against

    Returns:
        List of entities where field matches value

    Example:
        # Replaces: [i for i in interpretations if i.is_selected]
        return get_filtered_collection(interpretations, 'is_selected', True)
    """
    if not collection:
        return []
    return [
        entity
        for entity in collection
        if getattr(entity, filter_field, None) == filter_value
    ]


def get_cross_relationship_entity(
    start_entity: Any, relationship_path: List[str], final_filter: Callable[[Any], bool]
) -> Optional[Any]:
    """Navigate through multiple relationships to find an entity matching a filter.

    Args:
        start_entity: The starting entity to navigate from
        relationship_path: List of relationship names to traverse
        final_filter: Function to test entities at the end of the path

    Returns:
        The first entity matching the filter, or None if not found

    Example:
        # Replaces: Game.active_scene navigation through acts
        return get_cross_relationship_entity(
            self,
            ['acts'],
            lambda scene: getattr(scene, 'is_active', False)
        )
    """
    if not start_entity or not relationship_path:
        return None

    current_entities = [start_entity]

    # Navigate through the relationship path
    for relationship_name in relationship_path:
        next_entities = []
        for entity in current_entities:
            if entity is None:
                continue
            relationship = getattr(entity, relationship_name, None)
            if relationship is not None:
                if hasattr(relationship, "__iter__") and not isinstance(
                    relationship, (str, bytes)
                ):
                    # It's a collection - extend with non-None items
                    next_entities.extend(
                        [item for item in relationship if item is not None]
                    )
                else:
                    # It's a single entity
                    next_entities.append(relationship)
        current_entities = next_entities

        if not current_entities:
            return None

    # Apply final filter to find the target entity
    return next(
        (
            entity
            for entity in current_entities
            if entity is not None and final_filter(entity)
        ),
        None,
    )


def aggregate_cross_relationship_collection(
    start_entity: Any, relationship_path: List[str]
) -> List[Any]:
    """Collect all entities across multiple relationship levels.

    Args:
        start_entity: The starting entity to navigate from
        relationship_path: List of relationship names to traverse

    Returns:
        List of all entities found at the end of the relationship path

    Example:
        # Replaces: Act.all_events across scenes
        return aggregate_cross_relationship_collection(self, ['scenes', 'events'])
    """
    if not start_entity or not relationship_path:
        return []

    current_entities = [start_entity]

    # Navigate through the relationship path
    for relationship_name in relationship_path:
        next_entities = []
        for entity in current_entities:
            if entity is None:
                continue
            relationship = getattr(entity, relationship_name, None)
            if relationship is not None:
                if hasattr(relationship, "__iter__") and not isinstance(
                    relationship, (str, bytes)
                ):
                    # It's a collection - extend with non-None items
                    next_entities.extend(
                        [item for item in relationship if item is not None]
                    )
                else:
                    # It's a single entity
                    next_entities.append(relationship)
        current_entities = next_entities

        if not current_entities:
            return []

    return current_entities


def generate_unique_id(prefix: Optional[str] = None) -> str:
    """Generate a unique ID with an optional prefix.

    Args:
        prefix: Optional prefix for the ID.

    Returns:
        A unique ID string.
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}_{unique_id}" if prefix else unique_id


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: The text to convert.

    Returns:
        A URL-friendly version of the text.
    """
    return "-".join(text.lower().split())
