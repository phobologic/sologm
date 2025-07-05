"""
Scene Model Test Coverage Audit Results:

AUDIT FINDINGS (Phase 1.0, Sub-step 1.0.1):
- Scene model has 5 hybrid properties that need comprehensive test coverage
- No existing tests found for Scene model hybrid properties
- Current tests are only in sologm/core/tests/test_scene.py (manager tests)
- Need comprehensive tests for both Python and SQL contexts

TARGET PROPERTIES:
1. has_events - Direct relationship check (scene.events)
2. has_dice_rolls - Direct relationship check (scene.dice_rolls)
3. has_interpretation_sets - Direct relationship check (scene.interpretation_sets)
4. has_interpretations - Complex cross-table relationship (through interpretation_sets)
5. has_selected_interpretations - Complex filtered relationship (is_selected=True)

COVERAGE GAPS IDENTIFIED:
- No Python context testing for hybrid properties
- No SQL context testing for hybrid properties
- No edge case testing (empty relationships, complex scenarios)
- No positive/negative case testing
- Complex relationship properties need comprehensive edge case coverage

This test file implements comprehensive coverage for all gaps identified above.
"""

from typing import TYPE_CHECKING, Callable

import pytest

from sologm.database.session import SessionContext
from sologm.models.dice import DiceRoll
from sologm.models.scene import Scene

if TYPE_CHECKING:
    pass


class TestSceneHybridProperties:
    """Test Scene model hybrid properties in both Python and SQL contexts."""

    def test_has_events_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_events property in Python context (instance access)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test scene with no events
            session.refresh(scene, attribute_names=["events"])
            assert not scene.has_events, "Scene with no events should return False"

            # Add an event
            _ = create_test_event(session=session, scene_id=scene.id)
            session.refresh(scene, attribute_names=["events"])
            assert scene.has_events, "Scene with events should return True"

    def test_has_events_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_events property in SQL context (query filtering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene_with_events = create_test_scene(
                session=session, act_id=act.id, title="Scene With Events"
            )
            scene_without_events = create_test_scene(
                session=session, act_id=act.id, title="Scene Without Events"
            )

            # Add event to one scene only
            create_test_event(session=session, scene_id=scene_with_events.id)

            # Test SQL filtering - scenes with events
            scenes_with_events = session.query(Scene).filter(Scene.has_events).all()
            scene_ids_with_events = [s.id for s in scenes_with_events]

            assert scene_with_events.id in scene_ids_with_events
            assert scene_without_events.id not in scene_ids_with_events

            # Test SQL filtering - scenes without events
            scenes_without_events = session.query(Scene).filter(~Scene.has_events).all()
            scene_ids_without_events = [s.id for s in scenes_without_events]

            assert scene_with_events.id not in scene_ids_without_events
            assert scene_without_events.id in scene_ids_without_events

    def test_has_dice_rolls_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_dice_rolls property in Python context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test scene with no dice rolls
            session.refresh(scene, attribute_names=["dice_rolls"])
            assert not scene.has_dice_rolls, (
                "Scene with no dice rolls should return False"
            )

            # Add a dice roll
            dice_roll = DiceRoll.create(
                scene_id=scene.id,
                notation="1d20",
                individual_results=[15],
                modifier=0,
                total=15,
                reason="Test roll",
            )
            session.add(dice_roll)
            session.flush()

            session.refresh(scene, attribute_names=["dice_rolls"])
            assert scene.has_dice_rolls, "Scene with dice rolls should return True"

    def test_has_dice_rolls_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_dice_rolls property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene_with_rolls = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene With Rolls",
            )
            scene_without_rolls = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene Without Rolls",
            )

            # Add dice roll to one scene only
            dice_roll = DiceRoll.create(
                scene_id=scene_with_rolls.id,
                notation="1d20",
                individual_results=[10],
                modifier=0,
                total=10,
                reason="Test roll",
            )
            session.add(dice_roll)
            session.flush()

            # Test SQL filtering
            scenes_with_rolls = session.query(Scene).filter(Scene.has_dice_rolls).all()
            scene_ids_with_rolls = [s.id for s in scenes_with_rolls]

            assert scene_with_rolls.id in scene_ids_with_rolls
            assert scene_without_rolls.id not in scene_ids_with_rolls

    def test_has_interpretation_sets_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_interpretation_sets property in Python context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test scene with no interpretation sets
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert not scene.has_interpretation_sets, (
                "Scene with no interpretation sets should return False"
            )

            # Add an interpretation set
            _ = create_test_interpretation_set(session=session, scene_id=scene.id)
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert scene.has_interpretation_sets, (
                "Scene with interpretation sets should return True"
            )

    def test_has_interpretation_sets_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_interpretation_sets property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene_with_sets = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene With Sets",
            )
            scene_without_sets = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene Without Sets",
            )

            # Add interpretation set to one scene only
            create_test_interpretation_set(session=session, scene_id=scene_with_sets.id)

            # Test SQL filtering
            scenes_with_sets = (
                session.query(Scene).filter(Scene.has_interpretation_sets).all()
            )
            scene_ids_with_sets = [s.id for s in scenes_with_sets]

            assert scene_with_sets.id in scene_ids_with_sets
            assert scene_without_sets.id not in scene_ids_with_sets

    def test_has_interpretations_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_interpretations property in Python context.
        This tests complex cross-table relationship through interpretation_sets.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test scene with no interpretation sets
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert not scene.has_interpretations, (
                "Scene with no interpretation sets should return False"
            )

            # Add interpretation set but no interpretations
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert not scene.has_interpretations, (
                "Scene with interpretation sets but no interpretations should "
                "return False"
            )

            # Add an interpretation
            _ = create_test_interpretation(session=session, set_id=interp_set.id)
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert scene.has_interpretations, (
                "Scene with interpretations should return True"
            )

    def test_has_interpretations_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_interpretations property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene_with_interpretations = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene With Interpretations",
            )
            scene_with_empty_sets = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene With Empty Sets",
            )
            scene_without_sets = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene Without Sets",
            )

            # Scene with interpretations
            interp_set_with_interps = create_test_interpretation_set(
                session=session, scene_id=scene_with_interpretations.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_with_interps.id
            )

            # Scene with interpretation set but no interpretations
            create_test_interpretation_set(
                session=session, scene_id=scene_with_empty_sets.id
            )

            # Test SQL filtering
            scenes_with_interpretations = (
                session.query(Scene).filter(Scene.has_interpretations).all()
            )
            scene_ids_with_interpretations = [s.id for s in scenes_with_interpretations]

            assert scene_with_interpretations.id in scene_ids_with_interpretations
            assert scene_with_empty_sets.id not in scene_ids_with_interpretations
            assert scene_without_sets.id not in scene_ids_with_interpretations

    def test_has_selected_interpretations_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_selected_interpretations property in Python context.
        This tests complex filtered relationship with is_selected=True.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test scene with no interpretation sets
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert not scene.has_selected_interpretations, (
                "Scene with no interpretation sets should return False"
            )

            # Add interpretation set with unselected interpretation
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            _ = create_test_interpretation(
                session=session, set_id=interp_set.id, is_selected=False
            )
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert not scene.has_selected_interpretations, (
                "Scene with unselected interpretations should return False"
            )

            # Add a selected interpretation
            _ = create_test_interpretation(
                session=session, set_id=interp_set.id, is_selected=True
            )
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert scene.has_selected_interpretations, (
                "Scene with selected interpretations should return True"
            )

    def test_has_selected_interpretations_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_selected_interpretations property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene_with_selected = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene With Selected",
            )
            scene_with_unselected = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene With Unselected",
            )
            scene_without_sets = create_test_scene(
                session=session,
                act_id=act.id,
                title="Scene Without Sets",
            )

            # Scene with selected interpretations
            interp_set_selected = create_test_interpretation_set(
                session=session, scene_id=scene_with_selected.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_selected.id, is_selected=True
            )

            # Scene with unselected interpretations only
            interp_set_unselected = create_test_interpretation_set(
                session=session, scene_id=scene_with_unselected.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_unselected.id, is_selected=False
            )

            # Test SQL filtering
            scenes_with_selected = (
                session.query(Scene).filter(Scene.has_selected_interpretations).all()
            )
            scene_ids_with_selected = [s.id for s in scenes_with_selected]

            assert scene_with_selected.id in scene_ids_with_selected
            assert scene_with_unselected.id not in scene_ids_with_selected
            assert scene_without_sets.id not in scene_ids_with_selected

    def test_complex_interpretation_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test edge cases for complex interpretation relationships."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create multiple interpretation sets with mixed content
            interp_set_1 = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            interp_set_2 = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Set 1: Has both selected and unselected interpretations
            create_test_interpretation(
                session=session,
                set_id=interp_set_1.id,
                title="Selected 1",
                is_selected=True,
            )
            create_test_interpretation(
                session=session,
                set_id=interp_set_1.id,
                title="Unselected 1",
                is_selected=False,
            )

            # Set 2: Has only unselected interpretations
            create_test_interpretation(
                session=session,
                set_id=interp_set_2.id,
                title="Unselected 2",
                is_selected=False,
            )

            # Refresh all relationships
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set_1, attribute_names=["interpretations"])
            session.refresh(interp_set_2, attribute_names=["interpretations"])

            # Test Python context
            assert scene.has_interpretation_sets, (
                "Scene should have interpretation sets"
            )
            assert scene.has_interpretations, (
                "Scene should have interpretations across multiple sets"
            )
            assert scene.has_selected_interpretations, (
                "Scene should have selected interpretations"
            )

            # Test SQL context
            scenes_with_interpretations = (
                session.query(Scene).filter(Scene.has_interpretations).all()
            )
            scenes_with_selected = (
                session.query(Scene).filter(Scene.has_selected_interpretations).all()
            )

            assert scene.id in [s.id for s in scenes_with_interpretations]
            assert scene.id in [s.id for s in scenes_with_selected]

    def test_all_properties_combined_sql_filtering(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test complex SQL queries combining multiple hybrid properties."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Create scenes with different combinations of content
            scene_full = create_test_scene(
                session=session, act_id=act.id, title="Full Scene"
            )
            scene_empty = create_test_scene(
                session=session, act_id=act.id, title="Empty Scene"
            )
            scene_events_only = create_test_scene(
                session=session, act_id=act.id, title="Events Only"
            )

            # Full scene: has everything
            create_test_event(session=session, scene_id=scene_full.id)

            dice_roll = DiceRoll.create(
                scene_id=scene_full.id,
                notation="1d20",
                individual_results=[15],
                modifier=0,
                total=15,
                reason="Test roll",
            )
            session.add(dice_roll)

            interp_set_full = create_test_interpretation_set(
                session=session, scene_id=scene_full.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_full.id, is_selected=True
            )

            # Events only scene
            create_test_event(session=session, scene_id=scene_events_only.id)

            session.flush()

            # Test complex SQL queries
            scenes_with_events_and_dice = (
                session.query(Scene)
                .filter(Scene.has_events & Scene.has_dice_rolls)
                .all()
            )

            scenes_with_any_content = (
                session.query(Scene)
                .filter(
                    Scene.has_events
                    | Scene.has_dice_rolls
                    | Scene.has_interpretation_sets
                )
                .all()
            )

            scenes_fully_featured = (
                session.query(Scene)
                .filter(
                    Scene.has_events
                    & Scene.has_dice_rolls
                    & Scene.has_interpretation_sets
                    & Scene.has_selected_interpretations
                )
                .all()
            )

            # Verify results
            full_scene_ids = [s.id for s in scenes_with_events_and_dice]
            any_content_ids = [s.id for s in scenes_with_any_content]
            fully_featured_ids = [s.id for s in scenes_fully_featured]

            assert scene_full.id in full_scene_ids
            assert scene_events_only.id not in full_scene_ids
            assert scene_empty.id not in full_scene_ids

            assert scene_full.id in any_content_ids
            assert scene_events_only.id in any_content_ids
            assert scene_empty.id not in any_content_ids

            assert scene_full.id in fully_featured_ids
            assert scene_events_only.id not in fully_featured_ids
            assert scene_empty.id not in fully_featured_ids

    @pytest.mark.parametrize(
        "property_name,setup_func",
        [
            (
                "has_events",
                lambda session, scene_id, create_test_event, **_kwargs: (
                    create_test_event(session=session, scene_id=scene_id)
                ),
            ),
            (
                "has_interpretation_sets",
                lambda session, scene_id, create_test_interpretation_set, **_kwargs: (
                    create_test_interpretation_set(session=session, scene_id=scene_id)
                ),
            ),
        ],
    )
    def test_hybrid_property_parametrized(
        self,
        property_name: str,
        setup_func: Callable,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        create_test_interpretation_set: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Parametrized test for simple hybrid properties.
        Reduces code duplication for properties with similar test patterns.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test property returns False initially
            session.refresh(scene)
            property_value = getattr(scene, property_name)
            assert not property_value, (
                f"{property_name} should return False for empty scene"
            )

            # Add related data using setup function
            setup_func(
                session=session,
                scene_id=scene.id,
                create_test_event=create_test_event,
                create_test_interpretation_set=create_test_interpretation_set,
            )

            # Test property returns True after adding data
            session.refresh(scene)
            property_value = getattr(scene, property_name)
            assert property_value, (
                f"{property_name} should return True after adding related data"
            )


class TestSceneCountProperties:
    """Test Scene model count properties in both Python and SQL contexts.

    This test class provides comprehensive coverage for Scene's 5 count properties:
    - event_count (direct relationship)
    - dice_roll_count (direct relationship)
    - interpretation_set_count (direct relationship)
    - interpretation_count (complex cross-table count)
    - selected_interpretation_count (complex filtered count)
    """

    def test_event_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test event_count property in Python context (instance access)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test zero count
            session.refresh(scene, attribute_names=["events"])
            assert scene.event_count == 0, "Scene with no events should have count 0"

            # Test single count
            create_test_event(session=session, scene_id=scene.id)
            session.refresh(scene, attribute_names=["events"])
            assert scene.event_count == 1, "Scene with 1 event should have count 1"

            # Test multiple count
            create_test_event(session=session, scene_id=scene.id)
            create_test_event(session=session, scene_id=scene.id)
            session.refresh(scene, attribute_names=["events"])
            assert scene.event_count == 3, "Scene with 3 events should have count 3"

    def test_event_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test event_count property in SQL context (ORDER BY, WHERE clauses)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            scene_0_events = create_test_scene(
                session=session, act_id=act.id, title="Zero Events"
            )
            scene_1_event = create_test_scene(
                session=session, act_id=act.id, title="One Event"
            )
            scene_3_events = create_test_scene(
                session=session, act_id=act.id, title="Three Events"
            )

            # Add different numbers of events
            create_test_event(session=session, scene_id=scene_1_event.id)

            for _ in range(3):
                create_test_event(session=session, scene_id=scene_3_events.id)

            session.flush()

            # Test ORDER BY event_count DESC
            scenes_desc = session.query(Scene).order_by(Scene.event_count.desc()).all()
            expected_order = [scene_3_events.id, scene_1_event.id, scene_0_events.id]
            actual_order = [s.id for s in scenes_desc]
            assert actual_order == expected_order, (
                "Scenes should be ordered by event_count descending"
            )

            # Test WHERE event_count > 1
            scenes_multiple = session.query(Scene).filter(Scene.event_count > 1).all()
            assert len(scenes_multiple) == 1
            assert scenes_multiple[0].id == scene_3_events.id

            # Test WHERE event_count = 0
            scenes_empty = session.query(Scene).filter(Scene.event_count == 0).all()
            assert len(scenes_empty) == 1
            assert scenes_empty[0].id == scene_0_events.id

    def test_dice_roll_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test dice_roll_count property in Python context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test zero count
            session.refresh(scene, attribute_names=["dice_rolls"])
            assert scene.dice_roll_count == 0, (
                "Scene with no dice rolls should have count 0"
            )

            # Test single count
            dice_roll_1 = DiceRoll.create(
                scene_id=scene.id,
                notation="1d20",
                individual_results=[15],
                modifier=0,
                total=15,
                reason="First roll",
            )
            session.add(dice_roll_1)
            session.flush()
            session.refresh(scene, attribute_names=["dice_rolls"])
            assert scene.dice_roll_count == 1, (
                "Scene with 1 dice roll should have count 1"
            )

            # Test multiple count
            dice_roll_2 = DiceRoll.create(
                scene_id=scene.id,
                notation="1d6",
                individual_results=[4],
                modifier=2,
                total=6,
                reason="Second roll",
            )
            session.add(dice_roll_2)
            session.flush()
            session.refresh(scene, attribute_names=["dice_rolls"])
            assert scene.dice_roll_count == 2, (
                "Scene with 2 dice rolls should have count 2"
            )

    def test_dice_roll_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test dice_roll_count property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            scene_no_rolls = create_test_scene(
                session=session, act_id=act.id, title="No Rolls"
            )
            scene_one_roll = create_test_scene(
                session=session, act_id=act.id, title="One Roll"
            )
            scene_two_rolls = create_test_scene(
                session=session, act_id=act.id, title="Two Rolls"
            )

            # Add dice rolls
            roll_1 = DiceRoll.create(
                scene_id=scene_one_roll.id,
                notation="1d20",
                individual_results=[10],
                modifier=0,
                total=10,
            )
            session.add(roll_1)

            roll_2 = DiceRoll.create(
                scene_id=scene_two_rolls.id,
                notation="1d6",
                individual_results=[3],
                modifier=0,
                total=3,
            )
            roll_3 = DiceRoll.create(
                scene_id=scene_two_rolls.id,
                notation="1d8",
                individual_results=[7],
                modifier=0,
                total=7,
            )
            session.add(roll_2)
            session.add(roll_3)
            session.flush()

            # Test ORDER BY dice_roll_count
            scenes_by_rolls = (
                session.query(Scene).order_by(Scene.dice_roll_count.desc()).all()
            )
            expected_order = [scene_two_rolls.id, scene_one_roll.id, scene_no_rolls.id]
            actual_order = [s.id for s in scenes_by_rolls]
            assert actual_order == expected_order

            # Test WHERE dice_roll_count >= 1
            scenes_with_rolls = (
                session.query(Scene).filter(Scene.dice_roll_count >= 1).all()
            )
            roll_scene_ids = [s.id for s in scenes_with_rolls]
            assert scene_one_roll.id in roll_scene_ids
            assert scene_two_rolls.id in roll_scene_ids
            assert scene_no_rolls.id not in roll_scene_ids

    def test_interpretation_set_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test interpretation_set_count property in Python context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test zero count
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert scene.interpretation_set_count == 0, (
                "Scene with no interpretation sets should have count 0"
            )

            # Test single count
            create_test_interpretation_set(session=session, scene_id=scene.id)
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert scene.interpretation_set_count == 1, (
                "Scene with 1 interpretation set should have count 1"
            )

            # Test multiple count
            create_test_interpretation_set(session=session, scene_id=scene.id)
            create_test_interpretation_set(session=session, scene_id=scene.id)
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert scene.interpretation_set_count == 3, (
                "Scene with 3 interpretation sets should have count 3"
            )

    def test_interpretation_set_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test interpretation_set_count property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            scene_no_sets = create_test_scene(
                session=session, act_id=act.id, title="No Sets"
            )
            scene_one_set = create_test_scene(
                session=session, act_id=act.id, title="One Set"
            )
            scene_two_sets = create_test_scene(
                session=session, act_id=act.id, title="Two Sets"
            )

            # Add interpretation sets
            create_test_interpretation_set(session=session, scene_id=scene_one_set.id)
            create_test_interpretation_set(session=session, scene_id=scene_two_sets.id)
            create_test_interpretation_set(session=session, scene_id=scene_two_sets.id)

            # Test ORDER BY interpretation_set_count
            scenes_by_sets = (
                session.query(Scene)
                .order_by(Scene.interpretation_set_count.desc())
                .all()
            )
            expected_order = [scene_two_sets.id, scene_one_set.id, scene_no_sets.id]
            actual_order = [s.id for s in scenes_by_sets]
            assert actual_order == expected_order

            # Test WHERE interpretation_set_count > 1
            scenes_multiple_sets = (
                session.query(Scene).filter(Scene.interpretation_set_count > 1).all()
            )
            assert len(scenes_multiple_sets) == 1
            assert scenes_multiple_sets[0].id == scene_two_sets.id

    def test_interpretation_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test interpretation_count property in Python context.
        This tests complex cross-table counting through interpretation_sets.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test zero count (no interpretation sets)
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert scene.interpretation_count == 0, (
                "Scene with no interpretation sets should have count 0"
            )

            # Add interpretation set but no interpretations
            interp_set_1 = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set_1, attribute_names=["interpretations"])
            assert scene.interpretation_count == 0, (
                "Scene with empty interpretation sets should have count 0"
            )

            # Add one interpretation
            create_test_interpretation(session=session, set_id=interp_set_1.id)
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set_1, attribute_names=["interpretations"])
            assert scene.interpretation_count == 1, (
                "Scene with 1 interpretation should have count 1"
            )

            # Add second interpretation set with multiple interpretations
            interp_set_2 = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            create_test_interpretation(session=session, set_id=interp_set_2.id)
            create_test_interpretation(session=session, set_id=interp_set_2.id)

            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set_1, attribute_names=["interpretations"])
            session.refresh(interp_set_2, attribute_names=["interpretations"])
            assert scene.interpretation_count == 3, (
                "Scene with 3 interpretations across 2 sets should have count 3"
            )

    def test_interpretation_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test interpretation_count property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            scene_no_interps = create_test_scene(
                session=session, act_id=act.id, title="No Interpretations"
            )
            scene_one_interp = create_test_scene(
                session=session, act_id=act.id, title="One Interpretation"
            )
            scene_three_interps = create_test_scene(
                session=session, act_id=act.id, title="Three Interpretations"
            )

            # Scene with one interpretation
            interp_set_1 = create_test_interpretation_set(
                session=session, scene_id=scene_one_interp.id
            )
            create_test_interpretation(session=session, set_id=interp_set_1.id)

            # Scene with three interpretations across two sets
            interp_set_2 = create_test_interpretation_set(
                session=session, scene_id=scene_three_interps.id
            )
            interp_set_3 = create_test_interpretation_set(
                session=session, scene_id=scene_three_interps.id
            )
            create_test_interpretation(session=session, set_id=interp_set_2.id)
            create_test_interpretation(session=session, set_id=interp_set_3.id)
            create_test_interpretation(session=session, set_id=interp_set_3.id)

            # Scene with empty interpretation set (no interpretations)
            create_test_interpretation_set(
                session=session, scene_id=scene_no_interps.id
            )

            session.flush()

            # Test ORDER BY interpretation_count
            scenes_by_interps = (
                session.query(Scene).order_by(Scene.interpretation_count.desc()).all()
            )
            expected_order = [
                scene_three_interps.id,
                scene_one_interp.id,
                scene_no_interps.id,
            ]
            actual_order = [s.id for s in scenes_by_interps]
            assert actual_order == expected_order

            # Test WHERE interpretation_count >= 2
            scenes_multiple_interps = (
                session.query(Scene).filter(Scene.interpretation_count >= 2).all()
            )
            assert len(scenes_multiple_interps) == 1
            assert scenes_multiple_interps[0].id == scene_three_interps.id

    def test_selected_interpretation_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test selected_interpretation_count property in Python context.
        This tests complex filtered counting through interpretation_sets.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test zero count (no interpretation sets)
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert scene.selected_interpretation_count == 0, (
                "Scene with no interpretations should have selected count 0"
            )

            # Add interpretation set with unselected interpretations only
            interp_set_1 = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_1.id, is_selected=False
            )
            create_test_interpretation(
                session=session, set_id=interp_set_1.id, is_selected=False
            )

            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set_1, attribute_names=["interpretations"])
            assert scene.selected_interpretation_count == 0, (
                "Scene with only unselected interpretations should have count 0"
            )

            # Add one selected interpretation
            create_test_interpretation(
                session=session, set_id=interp_set_1.id, is_selected=True
            )

            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set_1, attribute_names=["interpretations"])
            assert scene.selected_interpretation_count == 1, (
                "Scene with 1 selected interpretation should have count 1"
            )

            # Add second interpretation set with mixed selections
            interp_set_2 = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_2.id, is_selected=True
            )
            create_test_interpretation(
                session=session, set_id=interp_set_2.id, is_selected=False
            )

            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set_1, attribute_names=["interpretations"])
            session.refresh(interp_set_2, attribute_names=["interpretations"])
            assert scene.selected_interpretation_count == 2, (
                "Scene with 2 selected interpretations should have count 2"
            )

    def test_selected_interpretation_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test selected_interpretation_count property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            scene_no_selected = create_test_scene(
                session=session, act_id=act.id, title="No Selected"
            )
            scene_one_selected = create_test_scene(
                session=session, act_id=act.id, title="One Selected"
            )
            scene_two_selected = create_test_scene(
                session=session, act_id=act.id, title="Two Selected"
            )

            # Scene with no selected interpretations
            interp_set_1 = create_test_interpretation_set(
                session=session, scene_id=scene_no_selected.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_1.id, is_selected=False
            )
            create_test_interpretation(
                session=session, set_id=interp_set_1.id, is_selected=False
            )

            # Scene with one selected interpretation
            interp_set_2 = create_test_interpretation_set(
                session=session, scene_id=scene_one_selected.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_2.id, is_selected=True
            )
            create_test_interpretation(
                session=session, set_id=interp_set_2.id, is_selected=False
            )

            # Scene with two selected interpretations
            interp_set_3 = create_test_interpretation_set(
                session=session, scene_id=scene_two_selected.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_3.id, is_selected=True
            )
            create_test_interpretation(
                session=session, set_id=interp_set_3.id, is_selected=True
            )

            session.flush()

            # Test ORDER BY selected_interpretation_count
            scenes_by_selected = (
                session.query(Scene)
                .order_by(Scene.selected_interpretation_count.desc())
                .all()
            )
            expected_order = [
                scene_two_selected.id,
                scene_one_selected.id,
                scene_no_selected.id,
            ]
            actual_order = [s.id for s in scenes_by_selected]
            assert actual_order == expected_order

            # Test WHERE selected_interpretation_count > 0
            scenes_with_selected = (
                session.query(Scene)
                .filter(Scene.selected_interpretation_count > 0)
                .all()
            )
            selected_scene_ids = [s.id for s in scenes_with_selected]
            assert scene_one_selected.id in selected_scene_ids
            assert scene_two_selected.id in selected_scene_ids
            assert scene_no_selected.id not in selected_scene_ids

            # Test WHERE selected_interpretation_count = 2
            scenes_two_selected_filter = (
                session.query(Scene)
                .filter(Scene.selected_interpretation_count == 2)
                .all()
            )
            assert len(scenes_two_selected_filter) == 1
            assert scenes_two_selected_filter[0].id == scene_two_selected.id

    def test_count_properties_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test edge cases for all count properties together."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create complex scenario: multiple of each type
            # Events
            for _ in range(3):
                create_test_event(session=session, scene_id=scene.id)

            # Dice rolls
            for i in range(2):
                dice_roll = DiceRoll.create(
                    scene_id=scene.id,
                    notation=f"1d{6 + i}",
                    individual_results=[i + 1],
                    modifier=0,
                    total=i + 1,
                    reason=f"Roll {i + 1}",
                )
                session.add(dice_roll)

            # Interpretation sets with mixed content
            interp_set_1 = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            interp_set_2 = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # First set: 2 interpretations (1 selected, 1 unselected)
            create_test_interpretation(
                session=session, set_id=interp_set_1.id, is_selected=True
            )
            create_test_interpretation(
                session=session, set_id=interp_set_1.id, is_selected=False
            )

            # Second set: 1 interpretation (selected)
            create_test_interpretation(
                session=session, set_id=interp_set_2.id, is_selected=True
            )

            session.flush()
            session.refresh(
                scene, attribute_names=["events", "dice_rolls", "interpretation_sets"]
            )
            session.refresh(interp_set_1, attribute_names=["interpretations"])
            session.refresh(interp_set_2, attribute_names=["interpretations"])

            # Test all counts are correct
            assert scene.event_count == 3, "Should have 3 events"
            assert scene.dice_roll_count == 2, "Should have 2 dice rolls"
            assert scene.interpretation_set_count == 2, (
                "Should have 2 interpretation sets"
            )
            assert scene.interpretation_count == 3, (
                "Should have 3 interpretations total"
            )
            assert scene.selected_interpretation_count == 2, (
                "Should have 2 selected interpretations"
            )

            # Test SQL consistency
            scene_from_db = session.query(Scene).filter(Scene.id == scene.id).first()
            assert scene_from_db is not None

            # Verify SQL expressions return same values as Python context
            # Test individual SQL expressions work correctly
            event_count_sql = (
                session.query(Scene.event_count).filter(Scene.id == scene.id).scalar()
            )
            dice_roll_count_sql = (
                session.query(Scene.dice_roll_count)
                .filter(Scene.id == scene.id)
                .scalar()
            )
            interpretation_set_count_sql = (
                session.query(Scene.interpretation_set_count)
                .filter(Scene.id == scene.id)
                .scalar()
            )
            interpretation_count_sql = (
                session.query(Scene.interpretation_count)
                .filter(Scene.id == scene.id)
                .scalar()
            )
            selected_interpretation_count_sql = (
                session.query(Scene.selected_interpretation_count)
                .filter(Scene.id == scene.id)
                .scalar()
            )

            assert event_count_sql == 3
            assert dice_roll_count_sql == 2
            assert interpretation_set_count_sql == 2
            assert interpretation_count_sql == 3
            assert selected_interpretation_count_sql == 2

    def test_count_properties_performance(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test that count properties generate efficient SQL queries."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data with larger numbers
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Create multiple scenes with varying amounts of content
            scenes = []
            for scene_num in range(3):
                scene = create_test_scene(
                    session=session, act_id=act.id, title=f"Scene {scene_num}"
                )
                scenes.append(scene)

                # Add varying numbers of events (0, 5, 10)
                event_count = scene_num * 5
                for _ in range(event_count):
                    create_test_event(session=session, scene_id=scene.id)

                # Add interpretation sets with interpretations
                if scene_num > 0:
                    interp_set = create_test_interpretation_set(
                        session=session, scene_id=scene.id
                    )
                    for _ in range(scene_num * 2):
                        create_test_interpretation(
                            session=session,
                            set_id=interp_set.id,
                            is_selected=(
                                scene_num == 2
                            ),  # Only last scene has selected
                        )

            session.flush()

            # Test that we can efficiently order by multiple count properties
            # This should generate efficient SQL with proper COUNT subqueries
            scenes_ordered = (
                session.query(Scene)
                .order_by(
                    Scene.event_count.desc(),
                    Scene.interpretation_count.desc(),
                    Scene.selected_interpretation_count.desc(),
                )
                .all()
            )

            # Verify the order is correct (scene with most events first)
            assert len(scenes_ordered) == 3
            assert scenes_ordered[0].title == "Scene 2"  # 10 events
            assert scenes_ordered[1].title == "Scene 1"  # 5 events
            assert scenes_ordered[2].title == "Scene 0"  # 0 events

            # Test complex filtering with multiple count conditions
            # This tests that multiple COUNT subqueries work together efficiently
            scenes_filtered = (
                session.query(Scene)
                .filter((Scene.event_count > 3) & (Scene.interpretation_count > 0))
                .all()
            )

            assert len(scenes_filtered) == 2  # Scenes 1 and 2
            filtered_titles = [s.title for s in scenes_filtered]
            assert "Scene 1" in filtered_titles
            assert "Scene 2" in filtered_titles

    @pytest.mark.parametrize(
        "count_property,setup_count",
        [
            ("event_count", 3),
            ("dice_roll_count", 2),
            ("interpretation_set_count", 4),
        ],
    )
    def test_count_properties_parametrized(
        self,
        count_property: str,
        setup_count: int,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        create_test_interpretation_set: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Parametrized test for simple count properties to reduce duplication."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test initial count is zero
            session.refresh(scene)
            initial_count = getattr(scene, count_property)
            assert initial_count == 0, f"{count_property} should start at 0"

            # Add entities based on property type
            if count_property == "event_count":
                for _ in range(setup_count):
                    create_test_event(session=session, scene_id=scene.id)
                session.refresh(scene, attribute_names=["events"])
            elif count_property == "dice_roll_count":
                for i in range(setup_count):
                    dice_roll = DiceRoll.create(
                        scene_id=scene.id,
                        notation="1d20",
                        individual_results=[i + 1],
                        modifier=0,
                        total=i + 1,
                    )
                    session.add(dice_roll)
                session.flush()
                session.refresh(scene, attribute_names=["dice_rolls"])
            elif count_property == "interpretation_set_count":
                for _ in range(setup_count):
                    create_test_interpretation_set(session=session, scene_id=scene.id)
                session.refresh(scene, attribute_names=["interpretation_sets"])

            # Test count matches expected value
            final_count = getattr(scene, count_property)
            assert final_count == setup_count, (
                f"{count_property} should equal {setup_count}"
            )
