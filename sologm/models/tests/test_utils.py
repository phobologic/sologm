"""Tests for navigation utility functions.

This module provides comprehensive tests for all navigation utility functions
used to consolidate repetitive property patterns across SoloGM models.
"""

from datetime import datetime, timedelta

import pytest

from sologm.models.utils import (
    aggregate_cross_relationship_collection,
    get_active_entity,
    get_cross_relationship_entity,
    get_current_entity,
    get_filtered_collection,
    get_first_entity_by_sequence,
    get_latest_entity,
)


class TestGetActiveEntity:
    """Tests for get_active_entity utility function."""

    def test_empty_collection_returns_none(self):
        """Test that empty collection returns None."""
        result = get_active_entity([])
        assert result is None

    def test_single_active_entity_returns_it(self, create_mock_entity):
        """Test that single active entity is returned."""
        entity = create_mock_entity(is_active=True)
        result = get_active_entity([entity])
        assert result is entity

    def test_single_inactive_entity_returns_none(self, create_mock_entity):
        """Test that single inactive entity returns None."""
        entity = create_mock_entity(is_active=False)
        result = get_active_entity([entity])
        assert result is None

    def test_multiple_entities_one_active_returns_active(self, create_mock_entity):
        """Test that the active entity is found among multiple entities."""
        entities = [
            create_mock_entity(is_active=False),
            create_mock_entity(is_active=True),
            create_mock_entity(is_active=False),
        ]
        result = get_active_entity(entities)
        assert result is entities[1]
        assert result.is_active is True

    def test_multiple_active_entities_returns_first(self, create_mock_entity):
        """Test that first active entity is returned when multiple are active."""
        entities = [
            create_mock_entity(is_active=False),
            create_mock_entity(is_active=True, id="first_active"),
            create_mock_entity(is_active=True, id="second_active"),
        ]
        result = get_active_entity(entities)
        assert result is entities[1]
        assert result.id == "first_active"

    def test_no_active_entities_returns_none(self, create_mock_entity):
        """Test that None is returned when no entities are active."""
        entities = [
            create_mock_entity(is_active=False),
            create_mock_entity(is_active=False),
            create_mock_entity(is_active=False),
        ]
        result = get_active_entity(entities)
        assert result is None

    def test_entities_missing_is_active_treated_as_false(self, create_mock_entity):
        """Test that entities without is_active attribute are treated as inactive."""
        # Create entity without is_active
        entity1 = create_mock_entity()
        delattr(entity1, "is_active")

        entity2 = create_mock_entity(is_active=True)

        result = get_active_entity([entity1, entity2])
        assert result is entity2

    def test_none_in_collection_handled_gracefully(self, create_mock_entity):
        """Test that None values in collection are handled gracefully."""
        entities = [
            None,
            create_mock_entity(is_active=False),
            create_mock_entity(is_active=True),
            None,
        ]
        result = get_active_entity(entities)
        assert result is entities[2]


class TestGetLatestEntity:
    """Tests for get_latest_entity utility function."""

    def test_empty_collection_returns_none(self):
        """Test that empty collection returns None."""
        result = get_latest_entity([])
        assert result is None

    def test_single_entity_returns_it(self, create_mock_entity):
        """Test that single entity is returned."""
        entity = create_mock_entity()
        result = get_latest_entity([entity])
        assert result is entity

    def test_multiple_entities_returns_latest(self, create_mock_entity):
        """Test that entity with latest timestamp is returned."""
        now = datetime.now()
        entities = [
            create_mock_entity(created_at=now - timedelta(hours=2)),
            create_mock_entity(created_at=now - timedelta(hours=1)),
            create_mock_entity(created_at=now),  # Latest
            create_mock_entity(created_at=now - timedelta(hours=3)),
        ]
        result = get_latest_entity(entities)
        assert result is entities[2]

    def test_entities_with_same_timestamp_returns_any(self, create_mock_entity):
        """Test that any valid entity is returned when timestamps are equal."""
        same_time = datetime.now()
        entities = [
            create_mock_entity(created_at=same_time, id="1"),
            create_mock_entity(created_at=same_time, id="2"),
            create_mock_entity(created_at=same_time, id="3"),
        ]
        result = get_latest_entity(entities)
        assert result in entities

    def test_entities_missing_created_at_handled(self, create_mock_entity):
        """Test that entities without created_at are handled gracefully."""
        now = datetime.now()
        entity1 = create_mock_entity()
        delattr(entity1, "created_at")  # Remove created_at

        entity2 = create_mock_entity(created_at=now)

        result = get_latest_entity([entity1, entity2])
        assert result is entity2

    def test_all_entities_missing_created_at(self, create_mock_entity):
        """Test behavior when all entities lack created_at."""
        entities = []
        for _ in range(3):
            entity = create_mock_entity()
            delattr(entity, "created_at")
            entities.append(entity)

        result = get_latest_entity(entities)
        assert result in entities  # Should return one of them

    def test_none_created_at_treated_as_zero(self, create_mock_entity):
        """Test that None created_at values are treated as epoch zero."""
        now = datetime.now()

        # Create entities with explicit created_at values
        entity1 = create_mock_entity()
        entity1.created_at = None  # Explicitly set to None

        entity2 = create_mock_entity()
        entity2.created_at = now  # Set to now

        entity3 = create_mock_entity()
        entity3.created_at = None  # Explicitly set to None

        entities = [entity1, entity2, entity3]
        result = get_latest_entity(entities)

        # Should return the entity with actual timestamp (now)
        assert result is entity2

    @pytest.mark.parametrize("collection_size", [10, 100, 1000])
    def test_performance_with_large_collections(
        self, create_mock_entity, collection_size
    ):
        """Test performance with various collection sizes."""
        now = datetime.now()
        entities = []
        for i in range(collection_size):
            entities.append(create_mock_entity(created_at=now - timedelta(seconds=i)))

        # Latest should be the first one (i=0)
        result = get_latest_entity(entities)
        assert result is entities[0]


class TestGetFirstEntityBySequence:
    """Tests for get_first_entity_by_sequence utility function."""

    def test_empty_collection_returns_none(self):
        """Test that empty collection returns None."""
        result = get_first_entity_by_sequence([])
        assert result is None

    def test_single_entity_returns_it(self, create_mock_entity):
        """Test that single entity is returned."""
        entity = create_mock_entity(sequence=5)
        result = get_first_entity_by_sequence([entity])
        assert result is entity

    def test_ordered_sequences_returns_first(self, create_mock_entity):
        """Test that entity with lowest sequence is returned."""
        entities = [
            create_mock_entity(sequence=2),
            create_mock_entity(sequence=1),  # Lowest
            create_mock_entity(sequence=3),
        ]
        result = get_first_entity_by_sequence(entities)
        assert result is entities[1]
        assert result.sequence == 1

    def test_gaps_in_sequences_handled(self, create_mock_entity):
        """Test that gaps in sequence numbers are handled correctly."""
        entities = [
            create_mock_entity(sequence=10),
            create_mock_entity(sequence=1),  # Lowest
            create_mock_entity(sequence=100),
            create_mock_entity(sequence=5),
        ]
        result = get_first_entity_by_sequence(entities)
        assert result is entities[1]
        assert result.sequence == 1

    def test_negative_sequences_handled(self, create_mock_entity):
        """Test that negative sequence numbers are handled correctly."""
        entities = [
            create_mock_entity(sequence=0),
            create_mock_entity(sequence=-5),  # Lowest
            create_mock_entity(sequence=10),
            create_mock_entity(sequence=-1),
        ]
        result = get_first_entity_by_sequence(entities)
        assert result is entities[1]
        assert result.sequence == -5

    def test_entities_missing_sequence_treated_as_infinity(self, create_mock_entity):
        """Test that entities without sequence are treated as infinite sequence."""
        entity1 = create_mock_entity()
        delattr(entity1, "sequence")  # Remove sequence

        entity2 = create_mock_entity(sequence=1000)
        entity3 = create_mock_entity(sequence=1)  # Should be selected

        result = get_first_entity_by_sequence([entity1, entity2, entity3])
        assert result is entity3

    def test_all_entities_missing_sequence(self, create_mock_entity):
        """Test behavior when all entities lack sequence attribute."""
        entities = []
        for _ in range(3):
            entity = create_mock_entity()
            delattr(entity, "sequence")
            entities.append(entity)

        result = get_first_entity_by_sequence(entities)
        assert result in entities  # Should return one of them

    def test_equal_sequences_returns_any(self, create_mock_entity):
        """Test that any entity is returned when sequences are equal."""
        entities = [
            create_mock_entity(sequence=5, id="1"),
            create_mock_entity(sequence=5, id="2"),
            create_mock_entity(sequence=5, id="3"),
        ]
        result = get_first_entity_by_sequence(entities)
        assert result in entities
        assert result.sequence == 5


class TestGetCurrentEntity:
    """Tests for get_current_entity utility function."""

    def test_empty_collection_returns_none(self):
        """Test that empty collection returns None."""
        result = get_current_entity([])
        assert result is None

    def test_single_current_entity_returns_it(self, create_mock_entity):
        """Test that single current entity is returned."""
        entity = create_mock_entity(is_current=True)
        result = get_current_entity([entity])
        assert result is entity

    def test_single_non_current_entity_returns_none(self, create_mock_entity):
        """Test that single non-current entity returns None."""
        entity = create_mock_entity(is_current=False)
        result = get_current_entity([entity])
        assert result is None

    def test_multiple_entities_one_current_returns_current(self, create_mock_entity):
        """Test that the current entity is found among multiple entities."""
        entities = [
            create_mock_entity(is_current=False),
            create_mock_entity(is_current=True),
            create_mock_entity(is_current=False),
        ]
        result = get_current_entity(entities)
        assert result is entities[1]
        assert result.is_current is True

    def test_multiple_current_entities_returns_first(self, create_mock_entity):
        """Test that first current entity is returned when multiple are current."""
        entities = [
            create_mock_entity(is_current=False),
            create_mock_entity(is_current=True, id="first_current"),
            create_mock_entity(is_current=True, id="second_current"),
        ]
        result = get_current_entity(entities)
        assert result is entities[1]
        assert result.id == "first_current"

    def test_no_current_entities_returns_none(self, create_mock_entity):
        """Test that None is returned when no entities are current."""
        entities = [
            create_mock_entity(is_current=False),
            create_mock_entity(is_current=False),
            create_mock_entity(is_current=False),
        ]
        result = get_current_entity(entities)
        assert result is None

    def test_entities_missing_is_current_treated_as_false(self, create_mock_entity):
        """Test that entities without is_current are treated as not current."""
        # Create entity without is_current
        entity1 = create_mock_entity()
        delattr(entity1, "is_current")

        entity2 = create_mock_entity(is_current=True)

        result = get_current_entity([entity1, entity2])
        assert result is entity2


class TestGetFilteredCollection:
    """Tests for get_filtered_collection utility function."""

    def test_empty_collection_returns_empty_list(self):
        """Test that empty collection returns empty list."""
        result = get_filtered_collection([], "any_field", "any_value")
        assert result == []

    def test_filter_by_boolean_field(self, create_mock_entity):
        """Test filtering by boolean field."""
        entities = [
            create_mock_entity(is_selected=True),
            create_mock_entity(is_selected=False),
            create_mock_entity(is_selected=True),
            create_mock_entity(is_selected=False),
        ]
        result = get_filtered_collection(entities, "is_selected", True)
        assert len(result) == 2
        assert all(e.is_selected is True for e in result)

    def test_filter_by_string_field(self, create_mock_entity):
        """Test filtering by string field."""
        entities = [
            create_mock_entity(status="active"),
            create_mock_entity(status="inactive"),
            create_mock_entity(status="active"),
            create_mock_entity(status="pending"),
        ]
        result = get_filtered_collection(entities, "status", "active")
        assert len(result) == 2
        assert all(e.status == "active" for e in result)

    def test_filter_by_numeric_field(self, create_mock_entity):
        """Test filtering by numeric field."""
        entities = [
            create_mock_entity(priority=1),
            create_mock_entity(priority=2),
            create_mock_entity(priority=1),
            create_mock_entity(priority=3),
        ]
        result = get_filtered_collection(entities, "priority", 1)
        assert len(result) == 2
        assert all(e.priority == 1 for e in result)

    def test_no_matches_returns_empty_list(self, create_mock_entity):
        """Test that empty list is returned when no matches found."""
        entities = [
            create_mock_entity(status="active"),
            create_mock_entity(status="inactive"),
            create_mock_entity(status="pending"),
        ]
        result = get_filtered_collection(entities, "status", "nonexistent")
        assert result == []

    def test_all_match_returns_all(self, create_mock_entity):
        """Test that all entities are returned when all match."""
        entities = [
            create_mock_entity(is_active=True),
            create_mock_entity(is_active=True),
            create_mock_entity(is_active=True),
        ]
        result = get_filtered_collection(entities, "is_active", True)
        assert len(result) == 3
        assert result == entities

    def test_entities_missing_filter_field_excluded(self, create_mock_entity):
        """Test that entities without the filter field are excluded."""
        entity1 = create_mock_entity()
        entity2 = create_mock_entity(custom_field="value")
        entity3 = create_mock_entity(custom_field="value")

        entities = [entity1, entity2, entity3]
        result = get_filtered_collection(entities, "custom_field", "value")
        assert len(result) == 2
        assert entity1 not in result
        assert entity2 in result
        assert entity3 in result

    def test_filter_by_none_value(self, create_mock_entity):
        """Test filtering where the desired value is None."""
        entities = [
            create_mock_entity(optional_field=None),
            create_mock_entity(optional_field="value"),
            create_mock_entity(optional_field=None),
        ]
        result = get_filtered_collection(entities, "optional_field", None)
        assert len(result) == 2
        assert all(e.optional_field is None for e in result)

    @pytest.mark.parametrize("filter_value", [0, "", False, []])
    def test_filter_by_falsy_values(self, create_mock_entity, filter_value):
        """Test filtering by various falsy values."""
        entities = [
            create_mock_entity(field=filter_value),
            create_mock_entity(field="other"),
            create_mock_entity(field=filter_value),
        ]
        result = get_filtered_collection(entities, "field", filter_value)
        assert len(result) == 2
        assert all(e.field == filter_value for e in result)


class TestGetCrossRelationshipEntity:
    """Tests for get_cross_relationship_entity utility function."""

    def test_none_start_entity_returns_none(self):
        """Test that None start entity returns None."""
        result = get_cross_relationship_entity(None, ["any_path"], lambda _: True)
        assert result is None

    def test_empty_relationship_path_returns_none(self, create_mock_entity):
        """Test that empty relationship path returns None."""
        entity = create_mock_entity()
        result = get_cross_relationship_entity(entity, [], lambda _: True)
        assert result is None

    def test_single_level_navigation(self, create_mock_entity_with_relationships):
        """Test navigation through single relationship level."""
        # Create child entities
        child1 = create_mock_entity_with_relationships(is_active=False)
        child2 = create_mock_entity_with_relationships(is_active=True)
        child3 = create_mock_entity_with_relationships(is_active=False)

        # Create parent with children relationship
        parent = create_mock_entity_with_relationships(
            relationships={"children": [child1, child2, child3]}
        )

        result = get_cross_relationship_entity(
            parent, ["children"], lambda x: getattr(x, "is_active", False)
        )
        assert result is child2

    def test_multi_level_navigation(self, create_mock_entity_with_relationships):
        """Test navigation through multiple relationship levels."""
        # Create grandchildren
        grandchild1 = create_mock_entity_with_relationships(status="inactive")
        grandchild2 = create_mock_entity_with_relationships(status="active")
        grandchild3 = create_mock_entity_with_relationships(status="inactive")

        # Create children with grandchildren
        child1 = create_mock_entity_with_relationships(
            relationships={"items": [grandchild1]}
        )
        child2 = create_mock_entity_with_relationships(
            relationships={"items": [grandchild2, grandchild3]}
        )

        # Create parent
        parent = create_mock_entity_with_relationships(
            relationships={"children": [child1, child2]}
        )

        result = get_cross_relationship_entity(
            parent,
            ["children", "items"],
            lambda x: getattr(x, "status", "") == "active",
        )
        assert result is grandchild2

    def test_missing_intermediate_relationship_returns_none(
        self, create_mock_entity_with_relationships
    ):
        """Test that missing intermediate relationship returns None."""
        # Create entity without expected relationship
        entity = create_mock_entity_with_relationships()

        result = get_cross_relationship_entity(
            entity, ["nonexistent", "items"], lambda _: True
        )
        assert result is None

    def test_empty_intermediate_collection_returns_none(
        self, create_mock_entity_with_relationships
    ):
        """Test that empty intermediate collection returns None."""
        # Create parent with empty children
        parent = create_mock_entity_with_relationships(relationships={"children": []})

        result = get_cross_relationship_entity(parent, ["children"], lambda _: True)
        assert result is None

    def test_final_filter_no_matches_returns_none(
        self, create_mock_entity_with_relationships
    ):
        """Test that None is returned when filter matches nothing."""
        # Create children that won't match filter
        child1 = create_mock_entity_with_relationships(status="inactive")
        child2 = create_mock_entity_with_relationships(status="pending")

        parent = create_mock_entity_with_relationships(
            relationships={"children": [child1, child2]}
        )

        result = get_cross_relationship_entity(
            parent, ["children"], lambda x: getattr(x, "status", "") == "active"
        )
        assert result is None

    def test_mixed_single_and_collection_relationships(
        self, create_mock_entity_with_relationships
    ):
        """Test navigation through mix of single entity and collection relationships."""
        # Create final targets
        target1 = create_mock_entity_with_relationships(is_target=True)
        target2 = create_mock_entity_with_relationships(is_target=False)

        # Create intermediate with collection
        intermediate = create_mock_entity_with_relationships(
            relationships={"items": [target1, target2]}
        )

        # Create parent with single relationship
        parent = create_mock_entity_with_relationships(
            relationships={"current": intermediate}  # Single entity, not collection
        )

        result = get_cross_relationship_entity(
            parent, ["current", "items"], lambda x: getattr(x, "is_target", False)
        )
        assert result is target1

    def test_string_relationship_not_treated_as_collection(
        self, create_mock_entity_with_relationships
    ):
        """Test that string attributes are not treated as collections."""
        # Create entity with string attribute that could be mistaken for iterable
        entity = create_mock_entity_with_relationships(
            relationships={"name": "test_string"}
        )

        result = get_cross_relationship_entity(
            entity, ["name"], lambda x: x == "test_string"
        )
        # String should be treated as single entity, not collection
        assert result == "test_string"


class TestAggregateCrossRelationshipCollection:
    """Tests for aggregate_cross_relationship_collection utility function."""

    def test_none_start_entity_returns_empty_list(self):
        """Test that None start entity returns empty list."""
        result = aggregate_cross_relationship_collection(None, ["any_path"])
        assert result == []

    def test_empty_relationship_path_returns_empty_list(self, create_mock_entity):
        """Test that empty relationship path returns empty list."""
        entity = create_mock_entity()
        result = aggregate_cross_relationship_collection(entity, [])
        assert result == []

    def test_single_level_aggregation(self, create_mock_entity_with_relationships):
        """Test aggregation through single relationship level."""
        # Create items
        item1 = create_mock_entity_with_relationships(id="item1")
        item2 = create_mock_entity_with_relationships(id="item2")
        item3 = create_mock_entity_with_relationships(id="item3")

        # Create parent
        parent = create_mock_entity_with_relationships(
            relationships={"items": [item1, item2, item3]}
        )

        result = aggregate_cross_relationship_collection(parent, ["items"])
        assert len(result) == 3
        assert item1 in result
        assert item2 in result
        assert item3 in result

    def test_multi_level_aggregation(self, create_mock_entity_with_relationships):
        """Test aggregation through multiple relationship levels."""
        # Create events
        event1 = create_mock_entity_with_relationships(id="event1")
        event2 = create_mock_entity_with_relationships(id="event2")
        event3 = create_mock_entity_with_relationships(id="event3")
        event4 = create_mock_entity_with_relationships(id="event4")

        # Create scenes with events
        scene1 = create_mock_entity_with_relationships(
            relationships={"events": [event1, event2]}
        )
        scene2 = create_mock_entity_with_relationships(
            relationships={"events": [event3, event4]}
        )

        # Create act with scenes
        act = create_mock_entity_with_relationships(
            relationships={"scenes": [scene1, scene2]}
        )

        result = aggregate_cross_relationship_collection(act, ["scenes", "events"])
        assert len(result) == 4
        assert all(e in result for e in [event1, event2, event3, event4])

    def test_missing_intermediate_relationship_returns_empty_list(
        self, create_mock_entity_with_relationships
    ):
        """Test that missing intermediate relationship returns empty list."""
        entity = create_mock_entity_with_relationships()

        result = aggregate_cross_relationship_collection(
            entity, ["nonexistent", "items"]
        )
        assert result == []

    def test_empty_intermediate_collection_returns_empty_list(
        self, create_mock_entity_with_relationships
    ):
        """Test that empty intermediate collection returns empty list."""
        # Create scenes with no events
        scene1 = create_mock_entity_with_relationships(relationships={"events": []})
        scene2 = create_mock_entity_with_relationships(relationships={"events": []})

        act = create_mock_entity_with_relationships(
            relationships={"scenes": [scene1, scene2]}
        )

        result = aggregate_cross_relationship_collection(act, ["scenes", "events"])
        assert result == []

    def test_mixed_collection_sizes(self, create_mock_entity_with_relationships):
        """Test aggregation with varying collection sizes."""
        # Create items
        items_scene1 = [
            create_mock_entity_with_relationships(id=f"s1_item{i}") for i in range(5)
        ]
        items_scene2 = []  # Empty
        items_scene3 = [
            create_mock_entity_with_relationships(id=f"s3_item{i}") for i in range(3)
        ]

        # Create scenes
        scene1 = create_mock_entity_with_relationships(
            relationships={"items": items_scene1}
        )
        scene2 = create_mock_entity_with_relationships(
            relationships={"items": items_scene2}
        )
        scene3 = create_mock_entity_with_relationships(
            relationships={"items": items_scene3}
        )

        act = create_mock_entity_with_relationships(
            relationships={"scenes": [scene1, scene2, scene3]}
        )

        result = aggregate_cross_relationship_collection(act, ["scenes", "items"])
        assert len(result) == 8  # 5 + 0 + 3

        # Verify all items are included
        for item in items_scene1 + items_scene3:
            assert item in result

    def test_single_entity_relationships_handled(
        self, create_mock_entity_with_relationships
    ):
        """Test that single entity relationships are handled correctly."""
        # Create final items
        item1 = create_mock_entity_with_relationships(id="item1")
        item2 = create_mock_entity_with_relationships(id="item2")

        # Create intermediates with single item each (not collections)
        intermediate1 = create_mock_entity_with_relationships(
            relationships={"item": item1}  # Single entity
        )
        intermediate2 = create_mock_entity_with_relationships(
            relationships={"item": item2}  # Single entity
        )

        parent = create_mock_entity_with_relationships(
            relationships={"items": [intermediate1, intermediate2]}
        )

        result = aggregate_cross_relationship_collection(parent, ["items", "item"])
        assert len(result) == 2
        assert item1 in result
        assert item2 in result

    @pytest.mark.parametrize("depth", [1, 2, 3])
    def test_various_navigation_depths(
        self, create_mock_entity_with_relationships, depth
    ):
        """Test aggregation at various depths."""
        # Create simple nested structure for testing
        final_items = [
            create_mock_entity_with_relationships(id=f"final_{i}") for i in range(2)
        ]

        if depth == 1:
            # Simple single level: root -> items
            root = create_mock_entity_with_relationships(
                relationships={"items": final_items}
            )
            path = ["items"]
        elif depth == 2:
            # Two levels: root -> containers -> items
            container = create_mock_entity_with_relationships(
                relationships={"items": final_items}
            )
            root = create_mock_entity_with_relationships(
                relationships={"containers": [container]}
            )
            path = ["containers", "items"]
        else:  # depth == 3
            # Three levels: root -> groups -> containers -> items
            container = create_mock_entity_with_relationships(
                relationships={"items": final_items}
            )
            group = create_mock_entity_with_relationships(
                relationships={"containers": [container]}
            )
            root = create_mock_entity_with_relationships(
                relationships={"groups": [group]}
            )
            path = ["groups", "containers", "items"]

        # Aggregate through all levels
        result = aggregate_cross_relationship_collection(root, path)

        # Should get all final items regardless of depth
        assert len(result) == len(final_items)
        for item in final_items:
            assert item in result


class TestEdgeCasesAndIntegration:
    """Tests for edge cases and integration scenarios."""

    def test_none_values_in_collections_handled(self, create_mock_entity):
        """Test that None values in collections are handled gracefully by utilities."""
        entities = [None, create_mock_entity(is_active=True), None]

        # Test each utility handles None gracefully
        assert get_active_entity(entities).is_active is True
        assert get_latest_entity(entities) is not None
        assert get_first_entity_by_sequence(entities) is not None
        assert get_current_entity([None, None]) is None
        assert len(get_filtered_collection(entities, "is_active", True)) == 1

    def test_utility_combination_scenario(self, create_mock_entity_with_relationships):
        """Test realistic scenario combining multiple utilities."""
        # Create interpretations
        interp1 = create_mock_entity_with_relationships(
            is_selected=True, created_at=datetime.now() - timedelta(hours=2)
        )
        interp2 = create_mock_entity_with_relationships(
            is_selected=False, created_at=datetime.now() - timedelta(hours=1)
        )
        interp3 = create_mock_entity_with_relationships(
            is_selected=True,
            created_at=datetime.now(),  # Latest
        )

        # Create interpretation sets
        set1 = create_mock_entity_with_relationships(
            is_current=False, relationships={"interpretations": [interp1, interp2]}
        )
        set2 = create_mock_entity_with_relationships(
            is_current=True, relationships={"interpretations": [interp3]}
        )

        # Create scene
        scene = create_mock_entity_with_relationships(
            relationships={"interpretation_sets": [set1, set2]}
        )

        # Get current interpretation set
        current_set = get_current_entity(scene.interpretation_sets)
        assert current_set is set2

        # Get all interpretations across sets
        all_interps = aggregate_cross_relationship_collection(
            scene, ["interpretation_sets", "interpretations"]
        )
        assert len(all_interps) == 3

        # Get selected interpretations
        selected = get_filtered_collection(all_interps, "is_selected", True)
        assert len(selected) == 2

        # Get latest selected interpretation
        latest_selected = get_latest_entity(selected)
        assert latest_selected is interp3

    def test_performance_with_large_nested_structures(
        self, create_mock_entity_with_relationships
    ):
        """Test performance with large nested structures."""
        # Create a structure with many entities
        num_acts = 10
        num_scenes_per_act = 10
        num_events_per_scene = 10

        total_events = []
        acts = []

        for a in range(num_acts):
            scenes = []
            for s in range(num_scenes_per_act):
                events = []
                for e in range(num_events_per_scene):
                    event = create_mock_entity_with_relationships(
                        id=f"event_{a}_{s}_{e}",
                        created_at=datetime.now()
                        - timedelta(seconds=a * 1000 + s * 100 + e),
                    )
                    events.append(event)
                    total_events.append(event)

                scene = create_mock_entity_with_relationships(
                    relationships={"events": events}
                )
                scenes.append(scene)

            act = create_mock_entity_with_relationships(
                relationships={"scenes": scenes}
            )
            acts.append(act)

        game = create_mock_entity_with_relationships(relationships={"acts": acts})

        # Test aggregation performance
        all_events = aggregate_cross_relationship_collection(
            game, ["acts", "scenes", "events"]
        )
        assert len(all_events) == num_acts * num_scenes_per_act * num_events_per_scene

        # Test finding latest event
        latest = get_latest_entity(all_events)
        assert latest.id == "event_0_0_0"  # Should be the most recent

    def test_circular_reference_handling(self, create_mock_entity_with_relationships):
        """Test that circular references don't cause infinite loops."""
        # Create entities with circular references
        entity1 = create_mock_entity_with_relationships(id="entity1")
        entity2 = create_mock_entity_with_relationships(id="entity2")

        # Create circular reference
        entity1.next = entity2
        entity2.next = entity1

        # This should not hang - the path determines depth
        result = get_cross_relationship_entity(
            entity1,
            ["next"],  # Single level only
            lambda x: x.id == "entity2",
        )
        assert result is entity2

        # Even with multiple levels, it follows the path exactly
        result = get_cross_relationship_entity(
            entity1,
            ["next", "next"],  # Two levels - back to entity1
            lambda x: x.id == "entity1",
        )
        assert result is entity1
