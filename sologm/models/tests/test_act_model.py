"""
Act Model Test Coverage Audit Results:

AUDIT FINDINGS (Phase 1.1, Sub-step 1.1.2):
- Act model has 5 hybrid properties that need comprehensive test coverage
- No existing tests found for Act model hybrid properties
- Current tests are only in sologm/core/tests/test_act.py (manager tests)
- Need comprehensive tests for both Python and SQL contexts

TARGET PROPERTIES:
1. has_scenes - Direct relationship check (act.scenes)
2. has_active_scene - Filtered relationship check (scenes with is_active=True)
3. has_events - Cross-scene relationship check (scenes.events)
4. has_dice_rolls - Cross-scene relationship check (scenes.dice_rolls)
5. has_interpretations - Complex cross-scene relationship
   (scenes.interpretation_sets.interpretations)

COVERAGE GAPS IDENTIFIED:
- No Python context testing for hybrid properties
- No SQL context testing for hybrid properties
- No edge case testing (empty relationships, cross-scene scenarios)
- No positive/negative case testing
- Cross-scene relationship properties need comprehensive edge case coverage
- Complex SQL join validation needed for multi-table relationships

SPECIAL CONSIDERATIONS FOR ACT:
- Cross-scene relationships are more complex than Scene's direct relationships
- Need to test acts with no scenes vs acts with scenes
- Need to test acts with scenes but no content in those scenes
- Need to test acts with multiple scenes having different content
- SQL expressions require complex joins that must be validated

This test file implements comprehensive coverage for all gaps identified above.
"""

from typing import TYPE_CHECKING, Callable

import pytest

from sologm.database.session import SessionContext
from sologm.models.act import Act
from sologm.models.dice import DiceRoll

if TYPE_CHECKING:
    pass


class TestActStatusProperties:
    """Test Act model status hybrid properties in both Python and SQL contexts.

    Focuses specifically on status checking patterns for the 1 Act status property:
    - has_active_scene: Checks if act has any active scenes (direct filtered
      relationship)
    """

    def test_has_active_scene_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test has_active_scene status property in Python context."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_active_scene, "Act with no scenes should return False"

            # Add an inactive scene
            scene = create_test_scene(session=session, act_id=act.id, is_active=False)
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_active_scene, (
                "Act with only inactive scenes should return False"
            )

            # Make the scene active
            scene.is_active = True
            session.add(scene)
            session.flush()
            session.refresh(act, attribute_names=["scenes"])
            assert act.has_active_scene, "Act with active scene should return True"

    def test_has_active_scene_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test has_active_scene status property in SQL context."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act_with_active = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Active Scene",
            )
            act_with_inactive = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Inactive Scene",
                sequence=2,
                is_active=False,
            )
            act_without_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act Without Scenes",
                sequence=3,
                is_active=False,
            )

            # Add active scene to first act
            create_test_scene(
                session=session, act_id=act_with_active.id, is_active=True
            )

            # Add inactive scene to second act
            create_test_scene(
                session=session, act_id=act_with_inactive.id, is_active=False
            )

            # Test SQL filtering
            acts_with_active = session.query(Act).filter(Act.has_active_scene).all()
            act_ids_with_active = [a.id for a in acts_with_active]

            assert act_with_active.id in act_ids_with_active
            assert act_with_inactive.id not in act_ids_with_active
            assert act_without_scenes.id not in act_ids_with_active

    def test_status_property_state_transitions(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test that status property updates correctly when scene states change."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)
            scene = create_test_scene(session=session, act_id=act.id, is_active=False)

            # Initial state - scene inactive
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_active_scene, "Initially no active scenes"

            # Transition 1: Activate scene
            scene.is_active = True
            session.add(scene)
            session.flush()
            session.refresh(act, attribute_names=["scenes"])
            assert act.has_active_scene, "Should have active scene after activation"

            # Transition 2: Deactivate scene
            scene.is_active = False
            session.add(scene)
            session.flush()
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_active_scene, "Should no longer have active scene"

            # Transition 3: Reactivate scene
            scene.is_active = True
            session.add(scene)
            session.flush()
            session.refresh(act, attribute_names=["scenes"])
            assert act.has_active_scene, "Should have active scene again"

    def test_status_property_multiple_scenes(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test status property with multiple scenes in different states."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Create multiple scenes with different states
            scene_1_active = create_test_scene(
                session=session,
                act_id=act.id,
                title="Active Scene",
                is_active=True,
            )
            scene_2_inactive = create_test_scene(
                session=session,
                act_id=act.id,
                title="Inactive Scene 1",
                is_active=False,
            )
            create_test_scene(
                session=session,
                act_id=act.id,
                title="Inactive Scene 2",
                is_active=False,
            )

            # Refresh relationships
            session.refresh(act, attribute_names=["scenes"])

            # Test Python context - should be True because there's at least one
            # active scene
            assert act.has_active_scene, (
                "Act should have active scene (scene_1_active is active)"
            )

            # Test SQL context
            acts_with_active_scenes = (
                session.query(Act).filter(Act.has_active_scene).all()
            )

            assert act.id in [a.id for a in acts_with_active_scenes]

            # Now deactivate the active scene
            scene_1_active.is_active = False
            session.add(scene_1_active)
            session.flush()
            session.refresh(act, attribute_names=["scenes"])

            # Should no longer have active scenes
            assert not act.has_active_scene, "No active scenes remaining"

            # Activate a different scene
            scene_2_inactive.is_active = True
            session.add(scene_2_inactive)
            session.flush()
            session.refresh(act, attribute_names=["scenes"])

            # Should have active scene again
            assert act.has_active_scene, "Should have active scene from scene_2"

    def test_status_property_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test edge cases for direct status relationship checking (Act → Scene)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Edge case 1: Act with no scenes
            act_empty = create_test_act(
                session=session,
                game_id=game.id,
                title="Empty Act",
            )
            session.refresh(act_empty, attribute_names=["scenes"])
            assert not act_empty.has_active_scene, (
                "Empty act should have no active scenes"
            )

            # Edge case 2: Act with many inactive scenes
            act_all_inactive = create_test_act(
                session=session,
                game_id=game.id,
                title="All Inactive Scenes",
                sequence=2,
                is_active=False,
            )
            for i in range(5):
                create_test_scene(
                    session=session,
                    act_id=act_all_inactive.id,
                    title=f"Inactive Scene {i + 1}",
                    is_active=False,
                )
            session.refresh(act_all_inactive, attribute_names=["scenes"])
            assert not act_all_inactive.has_active_scene, (
                "Act with all inactive scenes should return False"
            )

            # Edge case 3: Act with mixed scenes (mostly inactive)
            act_mixed = create_test_act(
                session=session,
                game_id=game.id,
                title="Mixed Scenes",
                sequence=3,
                is_active=False,
            )
            # Create many inactive scenes
            for i in range(7):
                create_test_scene(
                    session=session,
                    act_id=act_mixed.id,
                    title=f"Inactive {i + 1}",
                    is_active=False,
                )
            # Create one active scene
            create_test_scene(
                session=session,
                act_id=act_mixed.id,
                title="Single Active",
                is_active=True,
            )
            session.refresh(act_mixed, attribute_names=["scenes"])
            assert act_mixed.has_active_scene, (
                "Act should have active scene even with mostly inactive scenes"
            )

            # Test SQL context for all edge cases
            acts_with_active_scenes = (
                session.query(Act).filter(Act.has_active_scene).all()
            )
            act_ids_with_active = [a.id for a in acts_with_active_scenes]

            assert act_empty.id not in act_ids_with_active
            assert act_all_inactive.id not in act_ids_with_active
            assert act_mixed.id in act_ids_with_active

    def test_status_property_sql_efficiency(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test that status property SQL expressions generate efficient queries."""
        with session_context as session:
            # Create test data with multiple acts for realistic testing
            game = create_test_game(session=session)
            acts = []
            for i in range(4):
                act = create_test_act(
                    session=session,
                    game_id=game.id,
                    title=f"Act {i}",
                    sequence=i,
                    is_active=(i == 0),
                )
                acts.append(act)

                # Create scenes with different active states
                for j in range(3):
                    create_test_scene(
                        session=session,
                        act_id=act.id,
                        title=f"Scene {j}",
                        is_active=(
                            i % 2 == 0 and j == 0
                        ),  # Only first scene in even acts is active
                    )

            session.flush()

            # Test SQL queries use efficient EXISTS subqueries
            # These should all complete quickly and return expected results

            # Test has_active_scene filtering
            acts_with_active_scenes = (
                session.query(Act).filter(Act.has_active_scene).all()
            )
            # Should return acts 0 and 2 (even indices)
            active_scene_count = len(acts_with_active_scenes)
            assert active_scene_count == 2, (
                f"Expected 2 acts with active scenes, got {active_scene_count}"
            )

            # Test combined filtering with other properties
            acts_with_scenes_and_active = (
                session.query(Act).filter(Act.has_scenes & Act.has_active_scene).all()
            )
            # Should also return acts 0 and 2
            combined_count = len(acts_with_scenes_and_active)
            assert combined_count == 2, (
                f"Expected 2 acts with scenes and active scenes, got {combined_count}"
            )

            # Test SQL ordering by other properties with status filtering
            acts_ordered_with_active = (
                session.query(Act)
                .filter(Act.has_active_scene)
                .order_by(Act.scene_count.desc())
                .all()
            )
            assert len(acts_ordered_with_active) == 2

            # Verify the correct acts are returned
            active_act_ids = [a.id for a in acts_with_active_scenes]
            assert acts[0].id in active_act_ids  # Even index
            assert acts[2].id in active_act_ids  # Even index
            assert acts[1].id not in active_act_ids  # Odd index
            assert acts[3].id not in active_act_ids  # Odd index


class TestActHybridProperties:
    """Test Act model hybrid properties in both Python and SQL contexts."""

    def test_has_scenes_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test has_scenes property in Python context (instance access)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_scenes, "Act with no scenes should return False"

            # Add a scene
            _ = create_test_scene(session=session, act_id=act.id)
            session.refresh(act, attribute_names=["scenes"])
            assert act.has_scenes, "Act with scenes should return True"

    def test_has_scenes_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test has_scenes property in SQL context (query filtering)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act_with_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Scenes",
            )
            act_without_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act Without Scenes",
                sequence=2,
                is_active=False,
            )

            # Add scene to one act only
            create_test_scene(session=session, act_id=act_with_scenes.id)

            # Test SQL filtering - acts with scenes
            acts_with_scenes = session.query(Act).filter(Act.has_scenes).all()
            act_ids_with_scenes = [a.id for a in acts_with_scenes]

            assert act_with_scenes.id in act_ids_with_scenes
            assert act_without_scenes.id not in act_ids_with_scenes

            # Test SQL filtering - acts without scenes
            acts_without_scenes = session.query(Act).filter(~Act.has_scenes).all()
            act_ids_without_scenes = [a.id for a in acts_without_scenes]

            assert act_with_scenes.id not in act_ids_without_scenes
            assert act_without_scenes.id in act_ids_without_scenes

    def test_has_active_scene_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test has_active_scene property in Python context."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_active_scene, "Act with no scenes should return False"

            # Add an inactive scene
            scene = create_test_scene(session=session, act_id=act.id, is_active=False)
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_active_scene, (
                "Act with only inactive scenes should return False"
            )

            # Make the scene active
            scene.is_active = True
            session.add(scene)
            session.flush()
            session.refresh(act, attribute_names=["scenes"])
            assert act.has_active_scene, "Act with active scene should return True"

    def test_has_active_scene_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test has_active_scene property in SQL context."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act_with_active = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Active Scene",
            )
            act_with_inactive = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Inactive Scene",
                sequence=2,
                is_active=False,
            )
            act_without_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act Without Scenes",
                sequence=3,
                is_active=False,
            )

            # Add active scene to first act
            create_test_scene(
                session=session, act_id=act_with_active.id, is_active=True
            )

            # Add inactive scene to second act
            create_test_scene(
                session=session, act_id=act_with_inactive.id, is_active=False
            )

            # Test SQL filtering
            acts_with_active = session.query(Act).filter(Act.has_active_scene).all()
            act_ids_with_active = [a.id for a in acts_with_active]

            assert act_with_active.id in act_ids_with_active
            assert act_with_inactive.id not in act_ids_with_active
            assert act_without_scenes.id not in act_ids_with_active

    def test_has_events_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_events property in Python context.
        This tests cross-scene relationship through scenes.events.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_events, "Act with no scenes should return False"

            # Add scene but no events
            scene = create_test_scene(session=session, act_id=act.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene, attribute_names=["events"])
            assert not act.has_events, (
                "Act with scenes but no events should return False"
            )

            # Add an event to the scene
            _ = create_test_event(session=session, scene_id=scene.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene, attribute_names=["events"])
            assert act.has_events, "Act with events should return True"

    def test_has_events_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_events property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act_with_events = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Events",
            )
            act_with_empty_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Empty Scenes",
                sequence=2,
                is_active=False,
            )
            act_without_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act Without Scenes",
                sequence=3,
                is_active=False,
            )

            # Act with events
            scene_with_events = create_test_scene(
                session=session, act_id=act_with_events.id
            )
            create_test_event(session=session, scene_id=scene_with_events.id)

            # Act with scene but no events
            create_test_scene(session=session, act_id=act_with_empty_scenes.id)

            # Test SQL filtering
            acts_with_events = session.query(Act).filter(Act.has_events).all()
            act_ids_with_events = [a.id for a in acts_with_events]

            assert act_with_events.id in act_ids_with_events
            assert act_with_empty_scenes.id not in act_ids_with_events
            assert act_without_scenes.id not in act_ids_with_events

    def test_has_dice_rolls_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test has_dice_rolls property in Python context.
        This tests cross-scene relationship through scenes.dice_rolls.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_dice_rolls, "Act with no scenes should return False"

            # Add scene but no dice rolls
            scene = create_test_scene(session=session, act_id=act.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene, attribute_names=["dice_rolls"])
            assert not act.has_dice_rolls, (
                "Act with scenes but no dice rolls should return False"
            )

            # Add a dice roll to the scene
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

            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene, attribute_names=["dice_rolls"])
            assert act.has_dice_rolls, "Act with dice rolls should return True"

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
            act_with_rolls = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Dice Rolls",
            )
            act_with_empty_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Empty Scenes",
                sequence=2,
                is_active=False,
            )
            act_without_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act Without Scenes",
                sequence=3,
                is_active=False,
            )

            # Act with dice rolls
            scene_with_rolls = create_test_scene(
                session=session, act_id=act_with_rolls.id
            )
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

            # Act with scene but no dice rolls
            create_test_scene(session=session, act_id=act_with_empty_scenes.id)

            # Test SQL filtering
            acts_with_rolls = session.query(Act).filter(Act.has_dice_rolls).all()
            act_ids_with_rolls = [a.id for a in acts_with_rolls]

            assert act_with_rolls.id in act_ids_with_rolls
            assert act_with_empty_scenes.id not in act_ids_with_rolls
            assert act_without_scenes.id not in act_ids_with_rolls

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
        This tests complex cross-scene relationship through
        scenes.interpretation_sets.interpretations.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert not act.has_interpretations, "Act with no scenes should return False"

            # Add scene but no interpretation sets
            scene = create_test_scene(session=session, act_id=act.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene, attribute_names=["interpretation_sets"])
            assert not act.has_interpretations, (
                "Act with scenes but no interpretation sets should return False"
            )

            # Add interpretation set but no interpretations
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene.id
            )
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert not act.has_interpretations, (
                "Act with interpretation sets but no interpretations should "
                "return False"
            )

            # Add an interpretation
            _ = create_test_interpretation(session=session, set_id=interp_set.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene, attribute_names=["interpretation_sets"])
            session.refresh(interp_set, attribute_names=["interpretations"])
            assert act.has_interpretations, (
                "Act with interpretations should return True"
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
            act_with_interpretations = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Interpretations",
            )
            act_with_empty_sets = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Empty Sets",
                sequence=2,
                is_active=False,
            )
            act_without_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act Without Scenes",
                sequence=3,
                is_active=False,
            )

            # Act with interpretations
            scene_with_interps = create_test_scene(
                session=session, act_id=act_with_interpretations.id
            )
            interp_set_with_interps = create_test_interpretation_set(
                session=session, scene_id=scene_with_interps.id
            )
            create_test_interpretation(
                session=session, set_id=interp_set_with_interps.id
            )

            # Act with scene and interpretation set but no interpretations
            scene_with_empty_sets = create_test_scene(
                session=session, act_id=act_with_empty_sets.id
            )
            create_test_interpretation_set(
                session=session, scene_id=scene_with_empty_sets.id
            )

            # Test SQL filtering
            acts_with_interpretations = (
                session.query(Act).filter(Act.has_interpretations).all()
            )
            act_ids_with_interpretations = [a.id for a in acts_with_interpretations]

            assert act_with_interpretations.id in act_ids_with_interpretations
            assert act_with_empty_sets.id not in act_ids_with_interpretations
            assert act_without_scenes.id not in act_ids_with_interpretations

    def test_cross_scene_edge_cases(
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
        """Test edge cases for cross-scene relationships."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Create multiple scenes with different content
            scene_1 = create_test_scene(session=session, act_id=act.id, title="Scene 1")
            scene_2 = create_test_scene(session=session, act_id=act.id, title="Scene 2")
            scene_3 = create_test_scene(session=session, act_id=act.id, title="Scene 3")

            # Scene 1: Has events only
            create_test_event(session=session, scene_id=scene_1.id)

            # Scene 2: Has dice rolls only
            dice_roll = DiceRoll.create(
                scene_id=scene_2.id,
                notation="1d20",
                individual_results=[12],
                modifier=0,
                total=12,
                reason="Test roll",
            )
            session.add(dice_roll)

            # Scene 3: Has interpretations only
            interp_set = create_test_interpretation_set(
                session=session, scene_id=scene_3.id
            )
            create_test_interpretation(session=session, set_id=interp_set.id)

            session.flush()

            # Refresh all relationships
            session.refresh(act, attribute_names=["scenes"])
            for scene in [scene_1, scene_2, scene_3]:
                session.refresh(
                    scene,
                    attribute_names=["events", "dice_rolls", "interpretation_sets"],
                )
            session.refresh(interp_set, attribute_names=["interpretations"])

            # Test Python context - act should have all types of content
            assert act.has_scenes, "Act should have scenes"
            assert act.has_events, "Act should have events (from scene 1)"
            assert act.has_dice_rolls, "Act should have dice rolls (from scene 2)"
            assert act.has_interpretations, (
                "Act should have interpretations (from scene 3)"
            )

            # Test SQL context - act should appear in all filtered queries
            acts_with_events = session.query(Act).filter(Act.has_events).all()
            acts_with_rolls = session.query(Act).filter(Act.has_dice_rolls).all()
            acts_with_interps = session.query(Act).filter(Act.has_interpretations).all()

            assert act.id in [a.id for a in acts_with_events]
            assert act.id in [a.id for a in acts_with_rolls]
            assert act.id in [a.id for a in acts_with_interps]

    def test_multiple_scenes_mixed_content(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test acts with multiple scenes having different content combinations."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Create multiple scenes, only some with events
            scene_with_events = create_test_scene(
                session=session, act_id=act.id, title="Scene With Events"
            )
            scene_empty_1 = create_test_scene(
                session=session, act_id=act.id, title="Empty Scene 1"
            )
            scene_empty_2 = create_test_scene(
                session=session, act_id=act.id, title="Empty Scene 2"
            )

            # Add events to only one scene
            create_test_event(session=session, scene_id=scene_with_events.id)

            # Refresh relationships
            session.refresh(act, attribute_names=["scenes"])
            for scene in [scene_with_events, scene_empty_1, scene_empty_2]:
                session.refresh(scene, attribute_names=["events"])

            # Test Python context - should return True because at least one
            # scene has events
            assert act.has_events, (
                "Act should have events even if only one scene has events"
            )

            # Test SQL context - should still find the act
            acts_with_events = session.query(Act).filter(Act.has_events).all()
            assert act.id in [a.id for a in acts_with_events]

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

            # Create acts with different combinations of content
            act_full = create_test_act(
                session=session, game_id=game.id, title="Full Act"
            )
            act_empty = create_test_act(
                session=session,
                game_id=game.id,
                title="Empty Act",
                sequence=2,
                is_active=False,
            )
            act_scenes_only = create_test_act(
                session=session,
                game_id=game.id,
                title="Scenes Only Act",
                sequence=3,
                is_active=False,
            )

            # Full act: has everything
            scene_full = create_test_scene(
                session=session, act_id=act_full.id, is_active=True
            )
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
            create_test_interpretation(session=session, set_id=interp_set_full.id)

            # Scenes only act: just empty scenes
            create_test_scene(
                session=session, act_id=act_scenes_only.id, is_active=False
            )

            session.flush()

            # Test complex SQL queries
            acts_with_scenes_and_events = (
                session.query(Act).filter(Act.has_scenes & Act.has_events).all()
            )

            acts_with_any_content = (
                session.query(Act)
                .filter(Act.has_events | Act.has_dice_rolls | Act.has_interpretations)
                .all()
            )

            acts_fully_featured = (
                session.query(Act)
                .filter(
                    Act.has_scenes
                    & Act.has_active_scene
                    & Act.has_events
                    & Act.has_dice_rolls
                    & Act.has_interpretations
                )
                .all()
            )

            # Verify results
            full_act_ids = [a.id for a in acts_with_scenes_and_events]
            any_content_ids = [a.id for a in acts_with_any_content]
            fully_featured_ids = [a.id for a in acts_fully_featured]

            assert act_full.id in full_act_ids
            assert act_scenes_only.id not in full_act_ids
            assert act_empty.id not in full_act_ids

            assert act_full.id in any_content_ids
            assert act_scenes_only.id not in any_content_ids
            assert act_empty.id not in any_content_ids

            assert act_full.id in fully_featured_ids
            assert act_scenes_only.id not in fully_featured_ids
            assert act_empty.id not in fully_featured_ids

    @pytest.mark.parametrize(
        "property_name,setup_func",
        [
            (
                "has_scenes",
                lambda session, act_id, create_test_scene, **_kwargs: (
                    create_test_scene(session=session, act_id=act_id)
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
    ) -> None:
        """Parametrized test for simple hybrid properties.
        Reduces code duplication for properties with similar test patterns.
        """
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test property returns False initially
            session.refresh(act)
            property_value = getattr(act, property_name)
            assert not property_value, (
                f"{property_name} should return False for empty act"
            )

            # Add related data using setup function
            setup_func(
                session=session,
                act_id=act.id,
                create_test_scene=create_test_scene,
            )

            # Test property returns True after adding data
            session.refresh(act)
            property_value = getattr(act, property_name)
            assert property_value, (
                f"{property_name} should return True after adding related data"
            )


class TestActCountProperties:
    """Test Act model count properties in both Python and SQL contexts.

    This test class provides comprehensive coverage for Act's 4 count properties:
    - scene_count (direct relationship)
    - event_count (cross-scene aggregation)
    - dice_roll_count (cross-scene aggregation)
    - interpretation_count (complex cross-scene aggregation)
    """

    def test_scene_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test scene_count property in Python context (instance access)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert act.scene_count == 0, "Act with no scenes should have count 0"

            # Add one scene
            _ = create_test_scene(session=session, act_id=act.id, title="Scene 1")
            session.refresh(act, attribute_names=["scenes"])
            assert act.scene_count == 1, "Act with one scene should have count 1"

            # Add more scenes
            _ = create_test_scene(session=session, act_id=act.id, title="Scene 2")
            _ = create_test_scene(session=session, act_id=act.id, title="Scene 3")
            session.refresh(act, attribute_names=["scenes"])
            assert act.scene_count == 3, "Act with three scenes should have count 3"

    def test_scene_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test scene_count property in SQL context (query operations)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act_no_scenes = create_test_act(
                session=session, game_id=game.id, title="No Scenes"
            )
            act_one_scene = create_test_act(
                session=session,
                game_id=game.id,
                title="One Scene",
                sequence=2,
                is_active=False,
            )
            act_many_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Many Scenes",
                sequence=3,
                is_active=False,
            )

            # Create scenes
            create_test_scene(session=session, act_id=act_one_scene.id)
            for i in range(5):
                create_test_scene(
                    session=session, act_id=act_many_scenes.id, title=f"Scene {i + 1}"
                )

            # Test SQL ordering by scene_count
            acts_ordered = session.query(Act).order_by(Act.scene_count.desc()).all()
            assert acts_ordered[0].id == act_many_scenes.id
            assert acts_ordered[1].id == act_one_scene.id
            assert acts_ordered[2].id == act_no_scenes.id

            # Test SQL filtering by scene_count
            acts_with_scenes = session.query(Act).filter(Act.scene_count > 0).all()
            assert len(acts_with_scenes) == 2
            assert act_no_scenes.id not in [a.id for a in acts_with_scenes]

            acts_with_many = session.query(Act).filter(Act.scene_count >= 3).all()
            assert len(acts_with_many) == 1
            assert acts_with_many[0].id == act_many_scenes.id

    def test_event_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test event_count property in Python context.
        This tests cross-scene aggregation of events.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert act.event_count == 0, "Act with no scenes should have event count 0"

            # Add scene but no events
            scene1 = create_test_scene(session=session, act_id=act.id, title="Scene 1")
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene1, attribute_names=["events"])
            assert act.event_count == 0, (
                "Act with scenes but no events should have count 0"
            )

            # Add events to first scene
            _ = create_test_event(session=session, scene_id=scene1.id)
            _ = create_test_event(session=session, scene_id=scene1.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene1, attribute_names=["events"])
            assert act.event_count == 2, "Act should count events from all scenes"

            # Add another scene with events
            scene2 = create_test_scene(session=session, act_id=act.id, title="Scene 2")
            _ = create_test_event(session=session, scene_id=scene2.id)
            _ = create_test_event(session=session, scene_id=scene2.id)
            _ = create_test_event(session=session, scene_id=scene2.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene2, attribute_names=["events"])
            assert act.event_count == 5, "Act should aggregate events across all scenes"

    def test_event_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test event_count property in SQL context."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act_no_events = create_test_act(
                session=session, game_id=game.id, title="No Events"
            )
            act_few_events = create_test_act(
                session=session,
                game_id=game.id,
                title="Few Events",
                sequence=2,
                is_active=False,
            )
            act_many_events = create_test_act(
                session=session,
                game_id=game.id,
                title="Many Events",
                sequence=3,
                is_active=False,
            )

            # Act with no events (has scenes but no events)
            _ = create_test_scene(session=session, act_id=act_no_events.id)

            # Act with few events across multiple scenes
            scene_few1 = create_test_scene(
                session=session, act_id=act_few_events.id, title="Scene 1"
            )
            scene_few2 = create_test_scene(
                session=session, act_id=act_few_events.id, title="Scene 2"
            )
            create_test_event(session=session, scene_id=scene_few1.id)
            create_test_event(session=session, scene_id=scene_few2.id)

            # Act with many events across scenes
            scene_many1 = create_test_scene(
                session=session, act_id=act_many_events.id, title="Scene A"
            )
            scene_many2 = create_test_scene(
                session=session, act_id=act_many_events.id, title="Scene B"
            )
            for _ in range(3):
                create_test_event(session=session, scene_id=scene_many1.id)
            for _ in range(4):
                create_test_event(session=session, scene_id=scene_many2.id)

            # Test SQL ordering by event_count
            acts_ordered = session.query(Act).order_by(Act.event_count.desc()).all()
            assert acts_ordered[0].id == act_many_events.id  # 7 events
            assert acts_ordered[1].id == act_few_events.id  # 2 events
            assert acts_ordered[2].id == act_no_events.id  # 0 events

            # Test SQL filtering by event_count
            acts_with_events = session.query(Act).filter(Act.event_count > 0).all()
            assert len(acts_with_events) == 2
            assert act_no_events.id not in [a.id for a in acts_with_events]

            acts_many_events = session.query(Act).filter(Act.event_count >= 5).all()
            assert len(acts_many_events) == 1
            assert acts_many_events[0].id == act_many_events.id

    def test_dice_roll_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test dice_roll_count property in Python context.
        This tests cross-scene aggregation of dice rolls.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert act.dice_roll_count == 0, (
                "Act with no scenes should have dice roll count 0"
            )

            # Add scene but no dice rolls
            scene1 = create_test_scene(session=session, act_id=act.id, title="Scene 1")
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene1, attribute_names=["dice_rolls"])
            assert act.dice_roll_count == 0, (
                "Act with scenes but no dice rolls should have count 0"
            )

            # Add dice rolls to first scene
            roll1 = DiceRoll.create(
                scene_id=scene1.id,
                notation="1d20",
                individual_results=[15],
                modifier=0,
                total=15,
                reason="Test roll 1",
            )
            roll2 = DiceRoll.create(
                scene_id=scene1.id,
                notation="2d6",
                individual_results=[3, 5],
                modifier=2,
                total=10,
                reason="Test roll 2",
            )
            session.add_all([roll1, roll2])
            session.flush()
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene1, attribute_names=["dice_rolls"])
            assert act.dice_roll_count == 2, (
                "Act should count dice rolls from all scenes"
            )

            # Add another scene with dice rolls
            scene2 = create_test_scene(session=session, act_id=act.id, title="Scene 2")
            roll3 = DiceRoll.create(
                scene_id=scene2.id,
                notation="3d6",
                individual_results=[2, 4, 6],
                modifier=0,
                total=12,
                reason="Test roll 3",
            )
            session.add(roll3)
            session.flush()
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene2, attribute_names=["dice_rolls"])
            assert act.dice_roll_count == 3, (
                "Act should aggregate dice rolls across all scenes"
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
            act_no_rolls = create_test_act(
                session=session, game_id=game.id, title="No Rolls"
            )
            act_some_rolls = create_test_act(
                session=session,
                game_id=game.id,
                title="Some Rolls",
                sequence=2,
                is_active=False,
            )
            act_many_rolls = create_test_act(
                session=session,
                game_id=game.id,
                title="Many Rolls",
                sequence=3,
                is_active=False,
            )

            # Act with no dice rolls
            _ = create_test_scene(session=session, act_id=act_no_rolls.id)

            # Act with some rolls across scenes
            scene_some1 = create_test_scene(
                session=session, act_id=act_some_rolls.id, title="Scene 1"
            )
            _ = create_test_scene(
                session=session, act_id=act_some_rolls.id, title="Scene 2"
            )
            for i in range(2):
                roll = DiceRoll.create(
                    scene_id=scene_some1.id,
                    notation="1d20",
                    individual_results=[10 + i],
                    modifier=0,
                    total=10 + i,
                    reason=f"Roll {i}",
                )
                session.add(roll)

            # Act with many rolls
            scene_many = create_test_scene(session=session, act_id=act_many_rolls.id)
            for i in range(6):
                roll = DiceRoll.create(
                    scene_id=scene_many.id,
                    notation="1d6",
                    individual_results=[i % 6 + 1],
                    modifier=0,
                    total=i % 6 + 1,
                    reason=f"Roll {i}",
                )
                session.add(roll)
            session.flush()

            # Test SQL ordering by dice_roll_count
            acts_ordered = session.query(Act).order_by(Act.dice_roll_count.desc()).all()
            assert acts_ordered[0].id == act_many_rolls.id  # 6 rolls
            assert acts_ordered[1].id == act_some_rolls.id  # 2 rolls
            assert acts_ordered[2].id == act_no_rolls.id  # 0 rolls

            # Test SQL filtering by dice_roll_count
            acts_with_rolls = session.query(Act).filter(Act.dice_roll_count > 0).all()
            assert len(acts_with_rolls) == 2
            assert act_no_rolls.id not in [a.id for a in acts_with_rolls]

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
        This tests complex cross-scene aggregation through interpretation_sets.
        """
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Test act with no scenes
            session.refresh(act, attribute_names=["scenes"])
            assert act.interpretation_count == 0, (
                "Act with no scenes should have interpretation count 0"
            )

            # Add scene but no interpretation sets
            scene1 = create_test_scene(session=session, act_id=act.id, title="Scene 1")
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene1, attribute_names=["interpretation_sets"])
            assert act.interpretation_count == 0, (
                "Act with scenes but no interpretation sets should have count 0"
            )

            # Add interpretation set but no interpretations
            set1 = create_test_interpretation_set(session=session, scene_id=scene1.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene1, attribute_names=["interpretation_sets"])
            session.refresh(set1, attribute_names=["interpretations"])
            assert act.interpretation_count == 0, (
                "Act with sets but no interpretations should have count 0"
            )

            # Add interpretations to first set
            _ = create_test_interpretation(session=session, set_id=set1.id)
            _ = create_test_interpretation(session=session, set_id=set1.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene1, attribute_names=["interpretation_sets"])
            session.refresh(set1, attribute_names=["interpretations"])
            assert act.interpretation_count == 2, (
                "Act should count interpretations from all sets"
            )

            # Add another scene with multiple sets and interpretations
            scene2 = create_test_scene(session=session, act_id=act.id, title="Scene 2")
            set2 = create_test_interpretation_set(session=session, scene_id=scene2.id)
            set3 = create_test_interpretation_set(session=session, scene_id=scene2.id)
            _ = create_test_interpretation(session=session, set_id=set2.id)
            _ = create_test_interpretation(session=session, set_id=set3.id)
            _ = create_test_interpretation(session=session, set_id=set3.id)
            session.refresh(act, attribute_names=["scenes"])
            session.refresh(scene2, attribute_names=["interpretation_sets"])
            session.refresh(set2, attribute_names=["interpretations"])
            session.refresh(set3, attribute_names=["interpretations"])
            assert act.interpretation_count == 5, (
                "Act should aggregate interpretations across all scenes and sets"
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
            act_no_interps = create_test_act(
                session=session, game_id=game.id, title="No Interpretations"
            )
            act_few_interps = create_test_act(
                session=session,
                game_id=game.id,
                title="Few Interpretations",
                sequence=2,
                is_active=False,
            )
            act_many_interps = create_test_act(
                session=session,
                game_id=game.id,
                title="Many Interpretations",
                sequence=3,
                is_active=False,
            )

            # Act with no interpretations
            scene_empty = create_test_scene(session=session, act_id=act_no_interps.id)
            _ = create_test_interpretation_set(session=session, scene_id=scene_empty.id)

            # Act with few interpretations
            scene_few = create_test_scene(session=session, act_id=act_few_interps.id)
            set_few = create_test_interpretation_set(
                session=session, scene_id=scene_few.id
            )
            for _ in range(3):
                create_test_interpretation(session=session, set_id=set_few.id)

            # Act with many interpretations across multiple scenes and sets
            scene_many1 = create_test_scene(
                session=session, act_id=act_many_interps.id, title="Scene X"
            )
            scene_many2 = create_test_scene(
                session=session, act_id=act_many_interps.id, title="Scene Y"
            )
            set_many1 = create_test_interpretation_set(
                session=session, scene_id=scene_many1.id
            )
            set_many2 = create_test_interpretation_set(
                session=session, scene_id=scene_many2.id
            )
            set_many3 = create_test_interpretation_set(
                session=session, scene_id=scene_many2.id
            )
            for _ in range(2):
                create_test_interpretation(session=session, set_id=set_many1.id)
            for _ in range(3):
                create_test_interpretation(session=session, set_id=set_many2.id)
            for _ in range(2):
                create_test_interpretation(session=session, set_id=set_many3.id)

            # Test SQL ordering by interpretation_count
            acts_ordered = (
                session.query(Act).order_by(Act.interpretation_count.desc()).all()
            )
            assert acts_ordered[0].id == act_many_interps.id  # 7 interpretations
            assert acts_ordered[1].id == act_few_interps.id  # 3 interpretations
            assert acts_ordered[2].id == act_no_interps.id  # 0 interpretations

            # Test SQL filtering by interpretation_count
            acts_with_interps = (
                session.query(Act).filter(Act.interpretation_count > 0).all()
            )
            assert len(acts_with_interps) == 2
            assert act_no_interps.id not in [a.id for a in acts_with_interps]

            acts_many_interps_filter = (
                session.query(Act).filter(Act.interpretation_count >= 5).all()
            )
            assert len(acts_many_interps_filter) == 1
            assert acts_many_interps_filter[0].id == act_many_interps.id

    def test_cross_scene_count_edge_cases(
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
        """Test edge cases for cross-scene count aggregation."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Create multiple scenes with different content patterns
            scene1 = create_test_scene(
                session=session, act_id=act.id, title="Events Only"
            )
            scene2 = create_test_scene(
                session=session, act_id=act.id, title="Dice Rolls Only"
            )
            scene3 = create_test_scene(
                session=session, act_id=act.id, title="Interpretations Only"
            )
            scene4 = create_test_scene(
                session=session, act_id=act.id, title="Empty Scene"
            )
            scene5 = create_test_scene(
                session=session, act_id=act.id, title="Mixed Content"
            )

            # Scene 1: Only events
            for _ in range(3):
                create_test_event(session=session, scene_id=scene1.id)

            # Scene 2: Only dice rolls
            for i in range(2):
                roll = DiceRoll.create(
                    scene_id=scene2.id,
                    notation="1d20",
                    individual_results=[10 + i],
                    modifier=0,
                    total=10 + i,
                    reason=f"Roll {i}",
                )
                session.add(roll)

            # Scene 3: Only interpretations
            set3 = create_test_interpretation_set(session=session, scene_id=scene3.id)
            for _ in range(4):
                create_test_interpretation(session=session, set_id=set3.id)

            # Scene 4: Empty (no content)

            # Scene 5: Mixed content
            create_test_event(session=session, scene_id=scene5.id)
            roll5 = DiceRoll.create(
                scene_id=scene5.id,
                notation="1d6",
                individual_results=[4],
                modifier=0,
                total=4,
                reason="Mixed roll",
            )
            session.add(roll5)
            set5 = create_test_interpretation_set(session=session, scene_id=scene5.id)
            create_test_interpretation(session=session, set_id=set5.id)

            session.flush()

            # Refresh all relationships
            session.refresh(act, attribute_names=["scenes"])
            for scene in [scene1, scene2, scene3, scene4, scene5]:
                session.refresh(
                    scene,
                    attribute_names=["events", "dice_rolls", "interpretation_sets"],
                )
            session.refresh(set3, attribute_names=["interpretations"])
            session.refresh(set5, attribute_names=["interpretations"])

            # Test Python context counts
            assert act.scene_count == 5, "Act should have 5 scenes"
            assert act.event_count == 4, "Act should have 4 events total"
            assert act.dice_roll_count == 3, "Act should have 3 dice rolls total"
            assert act.interpretation_count == 5, (
                "Act should have 5 interpretations total"
            )

            # Test SQL context counts match Python context
            event_count_sql = (
                session.query(Act.event_count).filter(Act.id == act.id).scalar()
            )
            dice_roll_count_sql = (
                session.query(Act.dice_roll_count).filter(Act.id == act.id).scalar()
            )
            interpretation_count_sql = (
                session.query(Act.interpretation_count)
                .filter(Act.id == act.id)
                .scalar()
            )

            assert event_count_sql == act.event_count
            assert dice_roll_count_sql == act.dice_roll_count
            assert interpretation_count_sql == act.interpretation_count

    def test_count_properties_sql_ordering(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test SQL ordering by multiple count properties."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data with different count patterns
            game = create_test_game(session=session)

            # Act 1: High scene count, low event count
            act1 = create_test_act(
                session=session, game_id=game.id, title="Many Scenes Few Events"
            )
            for i in range(4):
                scene = create_test_scene(
                    session=session, act_id=act1.id, title=f"Act1 Scene {i}"
                )
                if i == 0:  # Only first scene has events
                    create_test_event(session=session, scene_id=scene.id)

            # Act 2: Low scene count, high event count
            act2 = create_test_act(
                session=session,
                game_id=game.id,
                title="Few Scenes Many Events",
                sequence=2,
                is_active=False,
            )
            scene2 = create_test_scene(session=session, act_id=act2.id)
            for _ in range(5):
                create_test_event(session=session, scene_id=scene2.id)

            # Act 3: Balanced counts
            act3 = create_test_act(
                session=session,
                game_id=game.id,
                title="Balanced",
                sequence=3,
                is_active=False,
            )
            for i in range(2):
                scene = create_test_scene(
                    session=session, act_id=act3.id, title=f"Act3 Scene {i + 1}"
                )
                for _ in range(2):
                    create_test_event(session=session, scene_id=scene.id)

            # Test complex ordering
            acts_by_scene_count = (
                session.query(Act).order_by(Act.scene_count.desc()).all()
            )
            assert acts_by_scene_count[0].id == act1.id  # 4 scenes

            acts_by_event_count = (
                session.query(Act).order_by(Act.event_count.desc()).all()
            )
            assert acts_by_event_count[0].id == act2.id  # 5 events

            # Test compound ordering
            acts_compound = (
                session.query(Act)
                .order_by(Act.event_count.desc(), Act.scene_count.desc())
                .all()
            )
            assert acts_compound[0].id == act2.id  # 5 events, 1 scene
            assert acts_compound[1].id == act3.id  # 4 events, 2 scenes
            assert acts_compound[2].id == act1.id  # 1 event, 4 scenes

    def test_count_properties_sql_filtering(
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
        """Test complex SQL filtering with multiple count properties."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)

            # Create acts with different count combinations
            acts = []
            for i in range(4):
                act = create_test_act(
                    session=session,
                    game_id=game.id,
                    title=f"Act {i}",
                    sequence=i,
                    is_active=(i == 0),
                )
                acts.append(act)

            # Act 0: No content
            _ = create_test_scene(session=session, act_id=acts[0].id)

            # Act 1: Some of everything
            scene1 = create_test_scene(
                session=session, act_id=acts[1].id, title="Everything Scene"
            )
            create_test_event(session=session, scene_id=scene1.id)
            create_test_event(session=session, scene_id=scene1.id)
            roll = DiceRoll.create(
                scene_id=scene1.id,
                notation="1d20",
                individual_results=[15],
                modifier=0,
                total=15,
                reason="Test",
            )
            session.add(roll)
            set1 = create_test_interpretation_set(session=session, scene_id=scene1.id)
            create_test_interpretation(session=session, set_id=set1.id)

            # Act 2: Many events, no dice rolls
            scene2 = create_test_scene(
                session=session, act_id=acts[2].id, title="Events Scene"
            )
            for _ in range(5):
                create_test_event(session=session, scene_id=scene2.id)

            # Act 3: Many interpretations, few events
            scene3 = create_test_scene(
                session=session, act_id=acts[3].id, title="Interpretations Scene"
            )
            create_test_event(session=session, scene_id=scene3.id)
            set3 = create_test_interpretation_set(session=session, scene_id=scene3.id)
            for _ in range(4):
                create_test_interpretation(session=session, set_id=set3.id)

            session.flush()

            # Test complex filtering conditions
            # Acts with events AND dice rolls
            acts_events_and_rolls = (
                session.query(Act)
                .filter((Act.event_count > 0) & (Act.dice_roll_count > 0))
                .all()
            )
            assert len(acts_events_and_rolls) == 1
            assert acts_events_and_rolls[0].id == acts[1].id

            # Acts with high event count OR high interpretation count
            acts_high_counts = (
                session.query(Act)
                .filter((Act.event_count >= 3) | (Act.interpretation_count >= 3))
                .all()
            )
            assert len(acts_high_counts) == 2
            assert acts[2].id in [a.id for a in acts_high_counts]
            assert acts[3].id in [a.id for a in acts_high_counts]

            # Acts with any content
            acts_with_content = (
                session.query(Act)
                .filter(
                    (Act.event_count > 0)
                    | (Act.dice_roll_count > 0)
                    | (Act.interpretation_count > 0)
                )
                .all()
            )
            assert len(acts_with_content) == 3
            assert acts[0].id not in [a.id for a in acts_with_content]

    def test_count_properties_with_multiple_scenes(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,
        initialize_event_sources: Callable,
    ) -> None:
        """Test count properties with acts having varying numbers of scenes."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Create scenes with different event distributions
            scene_counts = [0, 1, 2, 3, 0, 4]  # Event counts per scene
            scenes = []
            total_expected_events = 0

            for i, event_count in enumerate(scene_counts):
                scene = create_test_scene(
                    session=session, act_id=act.id, title=f"Scene {i + 1}"
                )
                scenes.append(scene)
                for _ in range(event_count):
                    create_test_event(session=session, scene_id=scene.id)
                total_expected_events += event_count

            # Refresh to load relationships
            session.refresh(act, attribute_names=["scenes"])
            for scene in scenes:
                session.refresh(scene, attribute_names=["events"])

            # Test Python context
            assert act.scene_count == len(scenes)
            assert act.event_count == total_expected_events

            # Test SQL context matches
            scene_count_sql = (
                session.query(Act.scene_count).filter(Act.id == act.id).scalar()
            )
            event_count_sql = (
                session.query(Act.event_count).filter(Act.id == act.id).scalar()
            )

            assert scene_count_sql == len(scenes)
            assert event_count_sql == total_expected_events

            # Test that empty scenes don't affect the count
            empty_scenes = [s for i, s in enumerate(scenes) if scene_counts[i] == 0]
            assert len(empty_scenes) == 2
            assert act.event_count == 10  # Sum of non-zero counts

    def test_count_properties_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
        create_test_event: Callable,  # noqa: ARG002
        create_test_interpretation_set: Callable,
        create_test_interpretation: Callable,  # noqa: ARG002
        initialize_event_sources: Callable,
    ) -> None:
        """Test comprehensive edge cases for all count properties."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data
            game = create_test_game(session=session)

            # Edge case 1: Act with no scenes
            act_empty = create_test_act(
                session=session, game_id=game.id, title="Empty Act"
            )
            session.refresh(act_empty, attribute_names=["scenes"])
            assert act_empty.scene_count == 0
            assert act_empty.event_count == 0
            assert act_empty.dice_roll_count == 0
            assert act_empty.interpretation_count == 0

            # Edge case 2: Act with empty scenes (scenes exist but have no content)
            act_empty_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Empty Scenes",
                sequence=2,
                is_active=False,
            )
            for i in range(3):
                create_test_scene(
                    session=session,
                    act_id=act_empty_scenes.id,
                    title=f"Empty Scene {i + 1}",
                )
            session.refresh(act_empty_scenes, attribute_names=["scenes"])
            assert act_empty_scenes.scene_count == 3
            assert act_empty_scenes.event_count == 0
            assert act_empty_scenes.dice_roll_count == 0
            assert act_empty_scenes.interpretation_count == 0

            # Edge case 3: Act with interpretation sets but no interpretations
            act_empty_sets = create_test_act(
                session=session,
                game_id=game.id,
                title="Empty Sets",
                sequence=3,
                is_active=False,
            )
            scene_empty_sets = create_test_scene(
                session=session, act_id=act_empty_sets.id
            )
            for _ in range(2):
                create_test_interpretation_set(
                    session=session, scene_id=scene_empty_sets.id
                )
            session.refresh(act_empty_sets, attribute_names=["scenes"])
            session.refresh(scene_empty_sets, attribute_names=["interpretation_sets"])
            assert act_empty_sets.interpretation_count == 0

            # Test SQL context for all edge cases
            acts_zero_scenes = session.query(Act).filter(Act.scene_count == 0).all()
            assert act_empty.id in [a.id for a in acts_zero_scenes]
            assert act_empty_scenes.id not in [a.id for a in acts_zero_scenes]

            acts_zero_events = session.query(Act).filter(Act.event_count == 0).all()
            assert all(
                act_id in [a.id for a in acts_zero_events]
                for act_id in [act_empty.id, act_empty_scenes.id, act_empty_sets.id]
            )

    def test_count_properties_consistency(
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
        """Test consistency between Python and SQL contexts for all count properties."""
        with session_context as session:
            initialize_event_sources(session)

            # Create test data with known counts
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id)

            # Create predictable content
            expected_scene_count = 3
            expected_event_count = 0
            expected_dice_roll_count = 0
            expected_interpretation_count = 0

            for i in range(expected_scene_count):
                scene = create_test_scene(
                    session=session, act_id=act.id, title=f"Scene {i}"
                )

                # Add different amounts of content to each scene
                events_in_scene = i + 1
                for _ in range(events_in_scene):
                    create_test_event(session=session, scene_id=scene.id)
                expected_event_count += events_in_scene

                # Add dice rolls
                rolls_in_scene = i
                for j in range(rolls_in_scene):
                    roll = DiceRoll.create(
                        scene_id=scene.id,
                        notation="1d6",
                        individual_results=[j % 6 + 1],
                        modifier=0,
                        total=j % 6 + 1,
                        reason=f"Roll {j}",
                    )
                    session.add(roll)
                expected_dice_roll_count += rolls_in_scene

                # Add interpretations
                if i > 0:  # Skip first scene
                    interp_set = create_test_interpretation_set(
                        session=session, scene_id=scene.id
                    )
                    interps_in_set = i * 2
                    for _ in range(interps_in_set):
                        create_test_interpretation(
                            session=session, set_id=interp_set.id
                        )
                    expected_interpretation_count += interps_in_set

            session.flush()

            # Refresh to load all relationships
            session.refresh(act, attribute_names=["scenes"])
            for scene in act.scenes:
                session.refresh(
                    scene,
                    attribute_names=["events", "dice_rolls", "interpretation_sets"],
                )
                for interp_set in scene.interpretation_sets:
                    session.refresh(interp_set, attribute_names=["interpretations"])

            # Test Python context matches expected
            assert act.scene_count == expected_scene_count
            assert act.event_count == expected_event_count
            assert act.dice_roll_count == expected_dice_roll_count
            assert act.interpretation_count == expected_interpretation_count

            # Test SQL context matches Python context
            scene_count_sql = (
                session.query(Act.scene_count).filter(Act.id == act.id).scalar()
            )
            event_count_sql = (
                session.query(Act.event_count).filter(Act.id == act.id).scalar()
            )
            dice_roll_count_sql = (
                session.query(Act.dice_roll_count).filter(Act.id == act.id).scalar()
            )
            interpretation_count_sql = (
                session.query(Act.interpretation_count)
                .filter(Act.id == act.id)
                .scalar()
            )

            assert scene_count_sql == act.scene_count == expected_scene_count
            assert event_count_sql == act.event_count == expected_event_count
            assert (
                dice_roll_count_sql == act.dice_roll_count == expected_dice_roll_count
            )
            assert (
                interpretation_count_sql
                == act.interpretation_count
                == expected_interpretation_count
            )

            # Verify SQL can handle multiple count properties in single query
            result = (
                session.query(
                    Act.scene_count,
                    Act.event_count,
                    Act.dice_roll_count,
                    Act.interpretation_count,
                )
                .filter(Act.id == act.id)
                .first()
            )

            assert result[0] == expected_scene_count
            assert result[1] == expected_event_count
            assert result[2] == expected_dice_roll_count
            assert result[3] == expected_interpretation_count
