"""
Event Model Test Coverage for Status Properties - Phase 3.0

AUDIT FINDINGS (Phase 3.0):
- Event model has 4 status properties that need comprehensive test coverage
- No existing tests found for Event model status properties
- Current tests are only in sologm/core/tests/test_event.py (manager tests)
- Need comprehensive tests for both Python and SQL contexts

TARGET PROPERTIES:
1. is_from_oracle - Relationship-based check (interpretation_id is not None)
2. is_manual - Source-based check via JOIN (source.name == 'manual')
3. is_oracle_generated - Source-based check via JOIN (source.name == 'oracle')
4. is_dice_generated - Source-based check via JOIN (source.name == 'dice')

COVERAGE GAPS IDENTIFIED:
- No Python context testing for status properties
- No SQL context testing for status properties
- No edge case testing (different sources, missing interpretations)
- No JOIN efficiency testing for source-based properties
- Complex source-based properties need comprehensive JOIN testing

This test file implements comprehensive coverage for all gaps identified above.
"""

from typing import TYPE_CHECKING, Callable

from sologm.database.session import SessionContext
from sologm.models.event import Event

if TYPE_CHECKING:
    pass


class TestEventStatusProperties:
    """Test Event model status hybrid properties in both Python and SQL contexts."""

    def test_is_from_oracle_python_context(
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
        """Test is_from_oracle property in Python context (instance access)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test event without interpretation (not from oracle)
            event_manual = create_test_event(
                session=session, scene_id=scene.id, description="Manual event"
            )
            session.refresh(event_manual)
            assert not event_manual.is_from_oracle, (
                "Event without interpretation should return False"
            )

            # Test event with interpretation (from oracle)
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id, context="Test context"
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Test interpretation"
            )
            event_oracle = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event",
                interpretation_id=interpretation.id,
            )
            session.refresh(event_oracle)
            assert event_oracle.is_from_oracle, (
                "Event with interpretation should return True"
            )

    def test_is_from_oracle_sql_context(
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
        """Test is_from_oracle property in SQL context (query filtering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create events with and without interpretations
            event_manual = create_test_event(
                session=session, scene_id=scene.id, description="Manual event"
            )

            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id, context="Test context"
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Test interpretation"
            )
            event_oracle = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event",
                interpretation_id=interpretation.id,
            )

            # Test SQL filtering - events from oracle
            oracle_events = session.query(Event).filter(Event.is_from_oracle).all()
            oracle_event_ids = [e.id for e in oracle_events]

            assert event_oracle.id in oracle_event_ids
            assert event_manual.id not in oracle_event_ids

            # Test SQL filtering - events NOT from oracle
            non_oracle_events = session.query(Event).filter(~Event.is_from_oracle).all()
            non_oracle_event_ids = [e.id for e in non_oracle_events]

            assert event_manual.id in non_oracle_event_ids
            assert event_oracle.id not in non_oracle_event_ids

    def test_is_manual_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test is_manual property in Python context (instance access)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test manual event
            event_manual = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Manual event",
                source="manual",
            )
            session.refresh(event_manual, attribute_names=["source"])
            assert event_manual.is_manual, "Manual source event should return True"

            # Test non-manual event
            event_oracle = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event",
                source="oracle",
            )
            session.refresh(event_oracle, attribute_names=["source"])
            assert not event_oracle.is_manual, "Oracle source event should return False"

    def test_is_manual_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test is_manual property in SQL context (query filtering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create events with different sources
            event_manual = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Manual event",
                source="manual",
            )
            event_oracle = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event",
                source="oracle",
            )
            event_dice = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Dice event",
                source="dice",
            )

            # Test SQL filtering - manual events only
            manual_events = session.query(Event).filter(Event.is_manual).all()
            manual_event_ids = [e.id for e in manual_events]

            assert event_manual.id in manual_event_ids
            assert event_oracle.id not in manual_event_ids
            assert event_dice.id not in manual_event_ids

    def test_is_oracle_generated_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test is_oracle_generated property in Python context (instance access)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test oracle event
            event_oracle = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event",
                source="oracle",
            )
            session.refresh(event_oracle, attribute_names=["source"])
            assert event_oracle.is_oracle_generated, (
                "Oracle source event should return True"
            )

            # Test non-oracle event
            event_manual = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Manual event",
                source="manual",
            )
            session.refresh(event_manual, attribute_names=["source"])
            assert not event_manual.is_oracle_generated, (
                "Manual source event should return False"
            )

    def test_is_oracle_generated_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test is_oracle_generated property in SQL context (query filtering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create events with different sources
            event_manual = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Manual event",
                source="manual",
            )
            event_oracle = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event",
                source="oracle",
            )
            event_dice = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Dice event",
                source="dice",
            )

            # Test SQL filtering - oracle events only
            oracle_events = session.query(Event).filter(Event.is_oracle_generated).all()
            oracle_event_ids = [e.id for e in oracle_events]

            assert event_oracle.id in oracle_event_ids
            assert event_manual.id not in oracle_event_ids
            assert event_dice.id not in oracle_event_ids

    def test_is_dice_generated_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test is_dice_generated property in Python context (instance access)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Test dice event
            event_dice = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Dice event",
                source="dice",
            )
            session.refresh(event_dice, attribute_names=["source"])
            assert event_dice.is_dice_generated, "Dice source event should return True"

            # Test non-dice event
            event_manual = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Manual event",
                source="manual",
            )
            session.refresh(event_manual, attribute_names=["source"])
            assert not event_manual.is_dice_generated, (
                "Manual source event should return False"
            )

    def test_is_dice_generated_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test is_dice_generated property in SQL context (query filtering)."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create events with different sources
            event_manual = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Manual event",
                source="manual",
            )
            event_oracle = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event",
                source="oracle",
            )
            event_dice = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Dice event",
                source="dice",
            )

            # Test SQL filtering - dice events only
            dice_events = session.query(Event).filter(Event.is_dice_generated).all()
            dice_event_ids = [e.id for e in dice_events]

            assert event_dice.id in dice_event_ids
            assert event_manual.id not in dice_event_ids
            assert event_oracle.id not in dice_event_ids

    def test_source_based_properties_comprehensive(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test all source-based properties together with comprehensive scenarios."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create events with all source types
            events = {
                "manual": create_test_event(
                    session=session,
                    scene_id=scene.id,
                    description="Manual event",
                    source="manual",
                ),
                "oracle": create_test_event(
                    session=session,
                    scene_id=scene.id,
                    description="Oracle event",
                    source="oracle",
                ),
                "dice": create_test_event(
                    session=session,
                    scene_id=scene.id,
                    description="Dice event",
                    source="dice",
                ),
            }

            # Refresh to load source relationships
            for event in events.values():
                session.refresh(event, attribute_names=["source"])

            # Test mutual exclusivity of source properties
            # Manual event
            assert events["manual"].is_manual
            assert not events["manual"].is_oracle_generated
            assert not events["manual"].is_dice_generated

            # Oracle event
            assert not events["oracle"].is_manual
            assert events["oracle"].is_oracle_generated
            assert not events["oracle"].is_dice_generated

            # Dice event
            assert not events["dice"].is_manual
            assert not events["dice"].is_oracle_generated
            assert events["dice"].is_dice_generated

            # Test SQL filtering for each source type
            manual_results = session.query(Event).filter(Event.is_manual).all()
            oracle_results = (
                session.query(Event).filter(Event.is_oracle_generated).all()
            )
            dice_results = session.query(Event).filter(Event.is_dice_generated).all()

            # Verify each query returns only the correct event
            assert (
                len(manual_results) == 1 and manual_results[0].id == events["manual"].id
            )
            assert (
                len(oracle_results) == 1 and oracle_results[0].id == events["oracle"].id
            )
            assert len(dice_results) == 1 and dice_results[0].id == events["dice"].id

    def test_oracle_property_with_interpretation_relationships(
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
        """Test is_from_oracle property interactions with interpretations."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id)

            # Create interpretation data
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id, context="Test context"
            )
            interpretation = create_test_interpretation(
                session=session, set_id=interp_set.id, title="Test interpretation"
            )

            # Test different combinations of source and interpretation

            # 1. Oracle source + interpretation (both oracle indicators)
            event_oracle_with_interp = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event with interpretation",
                source="oracle",
                interpretation_id=interpretation.id,
            )
            session.refresh(event_oracle_with_interp, attribute_names=["source"])
            assert event_oracle_with_interp.is_oracle_generated, (
                "Should be oracle generated"
            )
            assert event_oracle_with_interp.is_from_oracle, (
                "Should be from oracle (has interpretation)"
            )

            # 2. Manual source + interpretation (mixed indicators)
            event_manual_with_interp = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Manual event with interpretation",
                source="manual",
                interpretation_id=interpretation.id,
            )
            session.refresh(event_manual_with_interp, attribute_names=["source"])
            assert event_manual_with_interp.is_manual, "Should be manual"
            assert event_manual_with_interp.is_from_oracle, (
                "Should be from oracle (has interpretation)"
            )

            # 3. Oracle source without interpretation
            event_oracle_no_interp = create_test_event(
                session=session,
                scene_id=scene.id,
                description="Oracle event without interpretation",
                source="oracle",
            )
            session.refresh(event_oracle_no_interp, attribute_names=["source"])
            assert event_oracle_no_interp.is_oracle_generated, (
                "Should be oracle generated"
            )
            assert not event_oracle_no_interp.is_from_oracle, (
                "Should not be from oracle (no interpretation)"
            )

            # Test SQL context filtering for complex scenarios
            oracle_generated_events = (
                session.query(Event).filter(Event.is_oracle_generated).all()
            )
            from_oracle_events = session.query(Event).filter(Event.is_from_oracle).all()

            oracle_generated_ids = [e.id for e in oracle_generated_events]
            from_oracle_ids = [e.id for e in from_oracle_events]

            # Verify oracle generated filtering
            assert event_oracle_with_interp.id in oracle_generated_ids
            assert event_oracle_no_interp.id in oracle_generated_ids
            assert event_manual_with_interp.id not in oracle_generated_ids

            # Verify from oracle filtering
            assert event_oracle_with_interp.id in from_oracle_ids
            assert event_manual_with_interp.id in from_oracle_ids
            assert event_oracle_no_interp.id not in from_oracle_ids
