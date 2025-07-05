"""
Oracle Model Test Coverage Audit Results:

AUDIT FINDINGS (Phase 1.2, Sub-step 1.2.2):
- InterpretationSet model has 1 hybrid property: has_selection
- Interpretation model has 1 hybrid property: has_events
- No existing tests found for Oracle model hybrid properties
- Current tests are only in sologm/core/tests/test_oracle.py (manager tests)
- Need comprehensive tests for both Python and SQL contexts

TARGET PROPERTIES:
1. has_selection - Filtered relationship check (interpretations with is_selected=True)
2. has_events - Direct relationship check (interpretation.events)

COVERAGE GAPS IDENTIFIED:
- No Python context testing for hybrid properties
- No SQL context testing for hybrid properties
- No edge case testing (empty relationships, selection scenarios)
- No positive/negative case testing
- Complex filtered relationship properties need comprehensive edge case coverage

SPECIAL CONSIDERATIONS FOR ORACLE MODELS:
- InterpretationSet.has_selection checks for filtered interpretations (is_selected=True)
- Interpretation.has_events is a direct relationship check like Scene.has_events
- These are simpler cases compared to Game/Act cross-table relationships
- Selection state scenarios need comprehensive testing
- Event relationships need both presence and absence testing

This test file implements comprehensive coverage for all gaps identified above.
"""

from typing import TYPE_CHECKING, Callable

import pytest

from sologm.database.session import SessionContext
from sologm.models.oracle import Interpretation, InterpretationSet

if TYPE_CHECKING:
    pass


class TestInterpretationSetHybridProperties:
    """Test InterpretationSet model hybrid properties in both Python and SQL
    contexts."""

    def test_has_selection_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_selection property in Python context (instance access)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Test interpretation set with no interpretations
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert not interp_set.has_selection, (
                "InterpretationSet with no interpretations should return False"
            )

            # Add an unselected interpretation
            _ = create_test_interpretation(
                session=session, set_id=interp_set.id, is_selected=False
            )
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert not interp_set.has_selection, (
                "InterpretationSet with only unselected interpretations should "
                + "return False"
            )

            # Add a selected interpretation
            _ = create_test_interpretation(
                session=session, set_id=interp_set.id, is_selected=True
            )
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.has_selection, (
                "InterpretationSet with selected interpretation should return True"
            )

    def test_has_selection_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_selection property in SQL context (query filtering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            set_with_selection = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            set_without_selection = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            set_empty = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Add selected interpretation to first set
            create_test_interpretation(
                session=session, set_id=set_with_selection.id, is_selected=True
            )

            # Add unselected interpretation to second set
            create_test_interpretation(
                session=session, set_id=set_without_selection.id, is_selected=False
            )

            # Third set remains empty

            # Test SQL filtering - sets with selections
            sets_with_selection = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.has_selection)
                .all()
            )
            set_ids_with_selection = [s.id for s in sets_with_selection]

            assert set_with_selection.id in set_ids_with_selection
            assert set_without_selection.id not in set_ids_with_selection
            assert set_empty.id not in set_ids_with_selection

            # Test SQL filtering - sets without selections
            sets_without_selection = (
                session.query(InterpretationSet)
                .filter(~InterpretationSet.has_selection)
                .all()
            )
            set_ids_without_selection = [s.id for s in sets_without_selection]

            assert set_with_selection.id not in set_ids_without_selection
            assert set_without_selection.id in set_ids_without_selection
            assert set_empty.id in set_ids_without_selection

    def test_has_selection_mixed_states(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_selection with mixed interpretation selection states."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Add multiple interpretations with mixed selection states
            create_test_interpretation(
                session=session,
                set_id=interp_set.id,
                title="First Option",
                is_selected=False,
            )
            create_test_interpretation(
                session=session,
                set_id=interp_set.id,
                title="Second Option",
                is_selected=True,
            )
            create_test_interpretation(
                session=session,
                set_id=interp_set.id,
                title="Third Option",
                is_selected=False,
            )

            # Refresh relationships
            session.refresh(interp_set, attribute_names=["interpretations"])

            # Test Python context - should return True because at least one
            # interpretation is selected
            assert interp_set.has_selection, (
                "InterpretationSet should have selection even if only one "
                + "interpretation is selected"
            )

            # Test SQL context - should still find the set
            sets_with_selection = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.has_selection)
                .all()
            )
            assert interp_set.id in [s.id for s in sets_with_selection]

    def test_has_selection_multiple_selected(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_selection with multiple selected interpretations."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Add multiple selected interpretations
            create_test_interpretation(
                session=session,
                set_id=interp_set.id,
                title="First Selected",
                is_selected=True,
            )
            create_test_interpretation(
                session=session,
                set_id=interp_set.id,
                title="Second Selected",
                is_selected=True,
            )

            # Refresh relationships
            session.refresh(interp_set, attribute_names=["interpretations"])

            # Test Python context - should return True
            assert interp_set.has_selection, (
                "InterpretationSet with multiple selected interpretations should "
                + "return True"
            )

            # Test SQL context - should find the set
            sets_with_selection = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.has_selection)
                .all()
            )
            assert interp_set.id in [s.id for s in sets_with_selection]

    def test_has_selection_dynamic_changes(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_selection behavior when selection states change dynamically."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Add interpretation, initially unselected
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id, is_selected=False
            )

            # Test initially no selection
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert not interp_set.has_selection, (
                "InterpretationSet should not have selection initially"
            )

            # Select the interpretation
            interpretation.is_selected = True
            session.add(interpretation)
            session.flush()

            # Test after selection
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.has_selection, (
                "InterpretationSet should have selection after selecting "
                + "interpretation"
            )

            # Deselect the interpretation
            interpretation.is_selected = False
            session.add(interpretation)
            session.flush()

            # Test after deselection
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert not interp_set.has_selection, (
                "InterpretationSet should not have selection after deselecting "
                + "interpretation"
            )

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
        """Test interpretation_count property in Python context (instance access)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Test interpretation set with no interpretations
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.interpretation_count == 0, (
                "InterpretationSet with no interpretations should have count 0"
            )

            # Add one interpretation
            _ = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Interpretation 1"
            )
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.interpretation_count == 1, (
                "InterpretationSet with one interpretation should have count 1"
            )

            # Add second interpretation
            _ = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Interpretation 2"
            )
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.interpretation_count == 2, (
                "InterpretationSet with two interpretations should have count 2"
            )

            # Add third interpretation
            _ = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Interpretation 3"
            )
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.interpretation_count == 3, (
                "InterpretationSet with three interpretations should have count 3"
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
        """Test interpretation_count property in SQL context (query filtering and
        ordering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create interpretation sets with different counts
            set_0_interps = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            set_1_interp = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            set_3_interps = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Add interpretations
            create_test_interpretation(
                session=session, set_id=set_1_interp.id, title="Single Interpretation"
            )

            for i in range(3):
                create_test_interpretation(
                    session=session,
                    set_id=set_3_interps.id,
                    title=f"Interpretation {i + 1}",
                )

            # Test SQL ordering by interpretation_count
            sets_ordered = (
                session.query(InterpretationSet)
                .order_by(InterpretationSet.interpretation_count.desc())
                .all()
            )
            set_order = [s.id for s in sets_ordered]

            # Verify order - 3 interpretations should come first, then 1, then 0
            assert set_order.index(set_3_interps.id) < set_order.index(set_1_interp.id)
            assert set_order.index(set_1_interp.id) < set_order.index(set_0_interps.id)

            # Test SQL filtering with interpretation_count
            sets_with_interps = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.interpretation_count > 0)
                .all()
            )
            sets_with_multiple = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.interpretation_count > 1)
                .all()
            )
            sets_with_exact_one = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.interpretation_count == 1)
                .all()
            )

            # Verify filtering results
            set_ids_with_interps = [s.id for s in sets_with_interps]
            set_ids_with_multiple = [s.id for s in sets_with_multiple]
            set_ids_with_exact_one = [s.id for s in sets_with_exact_one]

            assert set_0_interps.id not in set_ids_with_interps
            assert set_1_interp.id in set_ids_with_interps
            assert set_3_interps.id in set_ids_with_interps

            assert set_0_interps.id not in set_ids_with_multiple
            assert set_1_interp.id not in set_ids_with_multiple
            assert set_3_interps.id in set_ids_with_multiple

            assert set_0_interps.id not in set_ids_with_exact_one
            assert set_1_interp.id in set_ids_with_exact_one
            assert set_3_interps.id not in set_ids_with_exact_one

    def test_interpretation_count_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test edge cases for interpretation_count property."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Test deleting interpretations affects count
            interp1 = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Interpretation 1"
            )
            interp2 = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Interpretation 2"
            )
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.interpretation_count == 2

            # Delete one interpretation
            session.delete(interp1)
            session.flush()
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.interpretation_count == 1, (
                "Count should decrease after deleting interpretation"
            )

            # Delete remaining interpretation
            session.delete(interp2)
            session.flush()
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert interp_set.interpretation_count == 0, (
                "Count should be 0 after deleting all interpretations"
            )

    def test_interpretation_count_consistency(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test that interpretation_count is consistent between Python and SQL
        contexts."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create interpretation sets with various counts
            sets = []
            expected_counts = [0, 1, 2, 5, 10]

            for _i, count in enumerate(expected_counts):
                interp_set = create_test_interpretation_set(
                    session=session, scene_id=scene.id
                )
                sets.append(interp_set)

                for j in range(count):
                    create_test_interpretation(
                        session=session,
                        set_id=interp_set.id,
                        title=f"Interpretation {j + 1}",
                    )

            # Test each interpretation set
            for interp_set, expected_count in zip(sets, expected_counts, strict=False):
                # Refresh to ensure relationships are loaded
                session.refresh(interp_set, attribute_names=["interpretations"])

                # Python context
                python_count = interp_set.interpretation_count

                # SQL context - get count via query
                sql_result = (
                    session.query(InterpretationSet.interpretation_count)
                    .filter(InterpretationSet.id == interp_set.id)
                    .scalar()
                )

                # Verify consistency
                assert python_count == expected_count, (
                    f"Python count {python_count} should match expected "
                    f"{expected_count}"
                )
                assert sql_result == expected_count, (
                    f"SQL count {sql_result} should match expected {expected_count}"
                )
                assert python_count == sql_result, (
                    "Python and SQL contexts should return same count"
                )


class TestInterpretationHybridProperties:
    """Test Interpretation model hybrid properties in both Python and SQL contexts."""

    def test_has_events_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
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
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id
            )

            # Test interpretation with no events
            session.refresh(interpretation, attribute_names=["events"])
            assert not interpretation.has_events, (
                "Interpretation with no events should return False"
            )

            # Add an event linked to this interpretation
            _ = create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
            )
            session.refresh(interpretation, attribute_names=["events"])
            assert interpretation.has_events, (
                "Interpretation with events should return True"
            )

    def test_has_events_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_events property in SQL context (query filtering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            interp_with_events = create_test_interpretation(
                session=session,
                set_id=interp_set.id,
                title="Interpretation With Events",
            )
            interp_without_events = create_test_interpretation(
                session=session,
                set_id=interp_set.id,
                title="Interpretation Without Events",
            )

            # Add event to one interpretation only
            create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interp_with_events.id,
            )

            # Test SQL filtering - interpretations with events
            interps_with_events = (
                session.query(Interpretation).filter(Interpretation.has_events).all()
            )
            interp_ids_with_events = [i.id for i in interps_with_events]

            assert interp_with_events.id in interp_ids_with_events
            assert interp_without_events.id not in interp_ids_with_events

            # Test SQL filtering - interpretations without events
            interps_without_events = (
                session.query(Interpretation).filter(~Interpretation.has_events).all()
            )
            interp_ids_without_events = [i.id for i in interps_without_events]

            assert interp_with_events.id not in interp_ids_without_events
            assert interp_without_events.id in interp_ids_without_events

    def test_has_events_multiple_events(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_events with multiple events per interpretation."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id
            )

            # Add multiple events linked to this interpretation
            create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
                description="First event",
            )
            create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
                description="Second event",
            )
            create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
                description="Third event",
            )

            # Refresh relationships
            session.refresh(interpretation, attribute_names=["events"])

            # Test Python context - should return True
            assert interpretation.has_events, (
                "Interpretation with multiple events should return True"
            )

            # Test SQL context - should find the interpretation
            interps_with_events = (
                session.query(Interpretation).filter(Interpretation.has_events).all()
            )
            assert interpretation.id in [i.id for i in interps_with_events]

    def test_has_events_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_events edge cases and complex scenarios."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data with multiple scenes
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene1 = create_test_scene(session=session, act_id=act.id, title="Scene 1")
            scene2 = create_test_scene(session=session, act_id=act.id, title="Scene 2")

            # Create interpretation sets in different scenes
            interp_set1 = create_test_interpretation_set(
                session=session, scene_id=scene1.id
            )
            interp_set2 = create_test_interpretation_set(
                session=session, scene_id=scene2.id
            )

            # Create interpretations
            interp1 = create_test_interpretation(
                session=session, set_id=interp_set1.id, title="Interpretation 1"
            )
            interp2 = create_test_interpretation(
                session=session, set_id=interp_set2.id, title="Interpretation 2"
            )

            # Add events to both scenes, but link only to interp1
            create_test_event(
                session=session,
                scene_id=scene1.id,
                interpretation_id=interp1.id,
                description="Event in scene 1",
            )
            create_test_event(
                session=session,
                scene_id=scene2.id,
                description="Event in scene 2 (no interpretation link)",
            )

            # Refresh relationships
            session.refresh(interp1, attribute_names=["events"])
            session.refresh(interp2, attribute_names=["events"])

            # Test Python context - only interp1 should have events
            assert interp1.has_events, (
                "Interpretation with linked events should return True"
            )
            assert not interp2.has_events, (
                "Interpretation without linked events should return False"
            )

            # Test SQL context - should find only interp1
            interps_with_events = (
                session.query(Interpretation).filter(Interpretation.has_events).all()
            )
            interp_ids_with_events = [i.id for i in interps_with_events]

            assert interp1.id in interp_ids_with_events
            assert interp2.id not in interp_ids_with_events

    def test_event_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
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
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id
            )

            # Test interpretation with no events
            session.refresh(interpretation, attribute_names=["events"])
            assert interpretation.event_count == 0, (
                "Interpretation with no events should have count 0"
            )

            # Add one event
            _ = create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
                description="Event 1",
            )
            session.refresh(interpretation, attribute_names=["events"])
            assert interpretation.event_count == 1, (
                "Interpretation with one event should have count 1"
            )

            # Add second event
            _ = create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
                description="Event 2",
            )
            session.refresh(interpretation, attribute_names=["events"])
            assert interpretation.event_count == 2, (
                "Interpretation with two events should have count 2"
            )

            # Add third event
            _ = create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
                description="Event 3",
            )
            session.refresh(interpretation, attribute_names=["events"])
            assert interpretation.event_count == 3, (
                "Interpretation with three events should have count 3"
            )

    def test_event_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test event_count property in SQL context (query filtering and ordering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Create interpretations with different event counts
            interp_0_events = create_test_interpretation(
                session=session, set_id=interp_set.id, title="0 Events"
            )
            interp_1_event = create_test_interpretation(
                session=session, set_id=interp_set.id, title="1 Event"
            )
            interp_3_events = create_test_interpretation(
                session=session, set_id=interp_set.id, title="3 Events"
            )

            # Add events
            create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interp_1_event.id,
                description="Single event",
            )

            for i in range(3):
                create_test_event(
                    session=session,
                    scene_id=scene.id,
                    interpretation_id=interp_3_events.id,
                    description=f"Event {i + 1}",
                )

            # Test SQL ordering by event_count
            interps_ordered = (
                session.query(Interpretation)
                .order_by(Interpretation.event_count.desc())
                .all()
            )
            interp_order = [i.id for i in interps_ordered]

            # Verify order - 3 events should come first, then 1, then 0
            assert interp_order.index(interp_3_events.id) < interp_order.index(
                interp_1_event.id
            )
            assert interp_order.index(interp_1_event.id) < interp_order.index(
                interp_0_events.id
            )

            # Test SQL filtering with event_count
            interps_with_events = (
                session.query(Interpretation)
                .filter(Interpretation.event_count > 0)
                .all()
            )
            interps_with_multiple = (
                session.query(Interpretation)
                .filter(Interpretation.event_count > 1)
                .all()
            )
            interps_with_exact_one = (
                session.query(Interpretation)
                .filter(Interpretation.event_count == 1)
                .all()
            )

            # Verify filtering results
            interp_ids_with_events = [i.id for i in interps_with_events]
            interp_ids_with_multiple = [i.id for i in interps_with_multiple]
            interp_ids_with_exact_one = [i.id for i in interps_with_exact_one]

            assert interp_0_events.id not in interp_ids_with_events
            assert interp_1_event.id in interp_ids_with_events
            assert interp_3_events.id in interp_ids_with_events

            assert interp_0_events.id not in interp_ids_with_multiple
            assert interp_1_event.id not in interp_ids_with_multiple
            assert interp_3_events.id in interp_ids_with_multiple

            assert interp_0_events.id not in interp_ids_with_exact_one
            assert interp_1_event.id in interp_ids_with_exact_one
            assert interp_3_events.id not in interp_ids_with_exact_one

    def test_event_count_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test edge cases for event_count property."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id
            )

            # Test deleting events affects count
            event1 = create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
                description="Event 1",
            )
            event2 = create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interpretation.id,
                description="Event 2",
            )
            session.refresh(interpretation, attribute_names=["events"])
            assert interpretation.event_count == 2

            # Delete one event
            session.delete(event1)
            session.flush()
            session.refresh(interpretation, attribute_names=["events"])
            assert interpretation.event_count == 1, (
                "Count should decrease after deleting event"
            )

            # Delete remaining event
            session.delete(event2)
            session.flush()
            session.refresh(interpretation, attribute_names=["events"])
            assert interpretation.event_count == 0, (
                "Count should be 0 after deleting all events"
            )

    def test_event_count_consistency(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test that event_count is consistent between Python and SQL contexts."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Create interpretations with various event counts
            interpretations = []
            expected_counts = [0, 1, 2, 5, 10]

            for i, count in enumerate(expected_counts):
                interpretation = create_test_interpretation(
                    session=session, set_id=interp_set.id, title=f"Interpretation {i}"
                )
                interpretations.append(interpretation)

                for j in range(count):
                    create_test_event(
                        session=session,
                        scene_id=scene.id,
                        interpretation_id=interpretation.id,
                        description=f"Event {j + 1}",
                    )

            # Test each interpretation
            for interpretation, expected_count in zip(
                interpretations, expected_counts, strict=False
            ):
                # Refresh to ensure relationships are loaded
                session.refresh(interpretation, attribute_names=["events"])

                # Python context
                python_count = interpretation.event_count

                # SQL context - get count via query
                sql_result = (
                    session.query(Interpretation.event_count)
                    .filter(Interpretation.id == interpretation.id)
                    .scalar()
                )

                # Verify consistency
                assert python_count == expected_count, (
                    f"Python count {python_count} should match expected "
                    f"{expected_count}"
                )
                assert sql_result == expected_count, (
                    f"SQL count {sql_result} should match expected {expected_count}"
                )
                assert python_count == sql_result, (
                    "Python and SQL contexts should return same count"
                )

    def test_combined_properties_sql_filtering(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test complex SQL queries combining Oracle model hybrid properties."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create interpretation sets with different combinations
            set_with_selected_and_events = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            set_with_selected_no_events = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            set_without_selection = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )

            # Set 1: Has selected interpretation with events
            interp_selected_with_events = create_test_interpretation(
                session=session,
                set_id=set_with_selected_and_events.id,
                title="Selected With Events",
                is_selected=True,
            )
            create_test_event(
                session=session,
                scene_id=scene.id,
                interpretation_id=interp_selected_with_events.id,
            )

            # Set 2: Has selected interpretation without events
            _ = create_test_interpretation(
                session=session,
                set_id=set_with_selected_no_events.id,
                title="Selected Without Events",
                is_selected=True,
            )

            # Set 3: Has unselected interpretation without events
            _ = create_test_interpretation(
                session=session,
                set_id=set_without_selection.id,
                title="Unselected Without Events",
                is_selected=False,
            )

            session.flush()

            # Test complex SQL queries
            sets_with_selection = (
                session.query(InterpretationSet)
                .filter(InterpretationSet.has_selection)
                .all()
            )

            interps_with_events = (
                session.query(Interpretation).filter(Interpretation.has_events).all()
            )

            # Test finding interpretations that are both selected and have events
            # Use separate queries to avoid auto-correlation issues with hybrid
            # properties
            selected_interps = (
                session.query(Interpretation).filter(Interpretation.is_selected).all()
            )
            # Refresh relationships for accurate has_events check
            for interp in selected_interps:
                session.refresh(interp, attribute_names=["events"])
            selected_interps_with_events = [
                interp for interp in selected_interps if interp.has_events
            ]

            # Verify results
            set_ids_with_selection = [s.id for s in sets_with_selection]
            interp_ids_with_events = [i.id for i in interps_with_events]
            selected_with_events_ids = [i.id for i in selected_interps_with_events]

            assert set_with_selected_and_events.id in set_ids_with_selection
            assert set_with_selected_no_events.id in set_ids_with_selection
            assert set_without_selection.id not in set_ids_with_selection

            assert interp_selected_with_events.id in interp_ids_with_events

            assert interp_selected_with_events.id in selected_with_events_ids

    @pytest.mark.parametrize(
        "property_name,setup_func",
        [
            (
                "has_events",
                lambda session,
                interpretation,
                create_test_event,
                scene_id,
                **_kwargs: (
                    create_test_event(
                        session=session,
                        scene_id=scene_id,
                        interpretation_id=interpretation.id,
                    )
                ),
            ),
        ],
    )
    def test_interpretation_property_parametrized(
        self,
        property_name: str,
        setup_func: Callable,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Parametrized test for Interpretation hybrid properties.
        Reduces code duplication for properties with similar test patterns.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id
            )

            # Test property returns False initially
            session.refresh(interpretation)
            property_value = getattr(interpretation, property_name)
            assert not property_value, (
                f"{property_name} should return False for empty interpretation"
            )

            # Add related data using setup function
            setup_func(
                session=session,
                interpretation=interpretation,
                scene_id=scene.id,
                create_test_event=create_test_event,
            )

            # Test property returns True after adding data
            session.refresh(interpretation)
            property_value = getattr(interpretation, property_name)
            assert property_value, (
                f"{property_name} should return True after adding related data"
            )
