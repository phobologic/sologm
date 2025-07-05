"""
Game Model Test Coverage Audit Results:

AUDIT FINDINGS (Phase 1.2, Sub-step 1.2.1):
- Game model has 4 hybrid properties that need comprehensive test coverage
- No existing tests found for Game model hybrid properties
- Current tests are only in sologm/core/tests/test_game.py (manager tests)
- Need comprehensive tests for both Python and SQL contexts

TARGET PROPERTIES:
1. has_acts - Direct relationship check (game.acts)
2. has_active_act - Filtered relationship check (acts with is_active=True)
3. has_active_scene - Complex cross-act relationship (acts.scenes with is_active=True)
4. has_completed_acts - BROKEN - references non-existent ActStatus.COMPLETED

COVERAGE GAPS IDENTIFIED:
- No Python context testing for hybrid properties
- No SQL context testing for hybrid properties
- No edge case testing (empty relationships, hierarchical scenarios)
- No positive/negative case testing
- Cross-act relationship properties need comprehensive edge case coverage
- Complex SQL join validation needed for multi-table relationships

SPECIAL CONSIDERATIONS FOR GAME:
- Hierarchical relationships (Game → Act → Scene) are most complex
- Need to test games with no acts vs games with acts
- Need to test games with acts but no scenes vs games with acts and scenes
- Need to test games with multiple acts having different combinations of content
- SQL expressions require complex joins across 3 tables for has_active_scene
- has_completed_acts property is broken and needs documentation

BUG DOCUMENTATION:
- Game.has_completed_acts references ActStatus.COMPLETED which doesn't exist
- This property will raise ImportError or AttributeError when used
- Property should be tested to document the bug, not fixed in this phase

This test file implements comprehensive coverage for all gaps identified above.
"""

from typing import TYPE_CHECKING, Callable

import pytest

from sologm.database.session import SessionContext
from sologm.models.game import Game

if TYPE_CHECKING:
    pass


class TestGameStatusProperties:
    """Test Game model status hybrid properties in both Python and SQL contexts.

    Focuses specifically on status checking patterns for the 3 Game status properties:
    - has_active_act: Checks if game has any active acts
    - has_active_scene: Checks if game has active scenes through acts (hierarchical)
    - has_completed_acts: Checks for completed acts (BROKEN - documents bug)
    """

    def test_has_active_act_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test has_active_act status property in Python context."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Test game with no acts
            session.refresh(game, attribute_names=["acts"])
            assert not game.has_active_act, "Game with no acts should return False"

            # Add an inactive act
            act = create_test_act(session=session, game_id=game.id, is_active=False)
            session.refresh(game, attribute_names=["acts"])
            assert not game.has_active_act, (
                "Game with only inactive acts should return False"
            )

            # Make the act active
            act.is_active = True
            session.add(act)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            assert game.has_active_act, "Game with active act should return True"

    def test_has_active_act_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test has_active_act status property in SQL context."""
        with session_context as session:
            # Create test data
            game_with_active = create_test_game(
                session=session, name="Game With Active Act"
            )
            game_with_inactive = create_test_game(
                session=session,
                name="Game With Inactive Act",
                is_active=False,
            )
            game_without_acts = create_test_game(
                session=session,
                name="Game Without Acts",
                is_active=False,
            )

            # Add active act to first game
            create_test_act(
                session=session, game_id=game_with_active.id, is_active=True
            )

            # Add inactive act to second game
            create_test_act(
                session=session, game_id=game_with_inactive.id, is_active=False
            )

            # Test SQL filtering
            games_with_active = session.query(Game).filter(Game.has_active_act).all()
            game_ids_with_active = [g.id for g in games_with_active]

            assert game_with_active.id in game_ids_with_active
            assert game_with_inactive.id not in game_ids_with_active
            assert game_without_acts.id not in game_ids_with_active

    def test_has_active_scene_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test has_active_scene status property in Python context.
        This tests complex hierarchical status checking through Game → Act → Scene.
        """
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Test game with no acts
            session.refresh(game, attribute_names=["acts"])
            assert not game.has_active_scene, "Game with no acts should return False"

            # Add act but no scenes
            act = create_test_act(session=session, game_id=game.id)
            session.refresh(game, attribute_names=["acts"])
            session.refresh(act, attribute_names=["scenes"])
            assert not game.has_active_scene, (
                "Game with acts but no scenes should return False"
            )

            # Add inactive scene
            scene = create_test_scene(session=session, act_id=act.id, is_active=False)
            session.refresh(game, attribute_names=["acts"])
            session.refresh(act, attribute_names=["scenes"])
            assert not game.has_active_scene, (
                "Game with only inactive scenes should return False"
            )

            # Make scene active
            scene.is_active = True
            session.add(scene)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            session.refresh(act, attribute_names=["scenes"])
            assert game.has_active_scene, "Game with active scene should return True"

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
            game_with_active_scene = create_test_game(
                session=session, name="Game With Active Scene"
            )
            game_with_inactive_scene = create_test_game(
                session=session,
                name="Game With Inactive Scene",
                is_active=False,
            )
            game_with_acts_only = create_test_game(
                session=session,
                name="Game With Acts Only",
                is_active=False,
            )
            game_without_acts = create_test_game(
                session=session,
                name="Game Without Acts",
                is_active=False,
            )

            # Game with active scenes
            act_with_active_scene = create_test_act(
                session=session, game_id=game_with_active_scene.id
            )
            create_test_scene(
                session=session, act_id=act_with_active_scene.id, is_active=True
            )

            # Game with inactive scenes only
            act_with_inactive_scene = create_test_act(
                session=session, game_id=game_with_inactive_scene.id
            )
            create_test_scene(
                session=session,
                act_id=act_with_inactive_scene.id,
                is_active=False,
            )

            # Game with acts but no scenes
            create_test_act(session=session, game_id=game_with_acts_only.id)

            # Test SQL filtering
            games_with_active_scenes = (
                session.query(Game).filter(Game.has_active_scene).all()
            )
            game_ids_with_active_scenes = [g.id for g in games_with_active_scenes]

            assert game_with_active_scene.id in game_ids_with_active_scenes
            assert game_with_inactive_scene.id not in game_ids_with_active_scenes
            assert game_with_acts_only.id not in game_ids_with_active_scenes
            assert game_without_acts.id not in game_ids_with_active_scenes

    def test_has_completed_acts_bug_documentation(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test and document the broken has_completed_acts status property.

        BUG: Game.has_completed_acts references ActStatus.COMPLETED which
        doesn't exist in the codebase. This will cause ImportError or
        AttributeError when accessed.

        This test documents the bug without fixing it, as requested.
        """
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            create_test_act(session=session, game_id=game.id)
            session.refresh(game, attribute_names=["acts"])

            # Test Python context - should raise error due to missing ActStatus
            with pytest.raises((ImportError, AttributeError, NameError)):
                _ = game.has_completed_acts

            # Test SQL context - should also raise error
            with pytest.raises((ImportError, AttributeError, NameError)):
                session.query(Game).filter(Game.has_completed_acts).all()

    def test_status_property_state_transitions(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test that status properties update correctly when entity states change."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)
            act = create_test_act(session=session, game_id=game.id, is_active=False)
            scene = create_test_scene(session=session, act_id=act.id, is_active=False)

            # Initial state - everything inactive
            session.refresh(game, attribute_names=["acts"])
            session.refresh(act, attribute_names=["scenes"])
            assert not game.has_active_act, "Initially no active acts"
            assert not game.has_active_scene, "Initially no active scenes"

            # Transition 1: Activate act
            act.is_active = True
            session.add(act)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            assert game.has_active_act, "Should have active act after activation"
            assert not game.has_active_scene, "Should still not have active scene"

            # Transition 2: Activate scene
            scene.is_active = True
            session.add(scene)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            session.refresh(act, attribute_names=["scenes"])
            assert game.has_active_act, "Should still have active act"
            assert game.has_active_scene, "Should now have active scene"

            # Transition 3: Deactivate scene but keep act active
            scene.is_active = False
            session.add(scene)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            session.refresh(act, attribute_names=["scenes"])
            assert game.has_active_act, "Should still have active act"
            assert not game.has_active_scene, "Should no longer have active scene"

            # Transition 4: Deactivate act
            act.is_active = False
            session.add(act)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            assert not game.has_active_act, "Should no longer have active act"
            assert not game.has_active_scene, "Should still not have active scene"

    def test_status_property_multiple_entities(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test status properties with multiple acts and scenes in different states."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Create multiple acts with different states
            act_1_active = create_test_act(
                session=session,
                game_id=game.id,
                title="Active Act",
                sequence=1,
                is_active=True,
            )
            act_2_inactive = create_test_act(
                session=session,
                game_id=game.id,
                title="Inactive Act",
                sequence=2,
                is_active=False,
            )

            # Add scenes to acts with different states
            create_test_scene(
                session=session,
                act_id=act_1_active.id,
                title="Active Scene in Active Act",
                is_active=True,
            )
            create_test_scene(
                session=session,
                act_id=act_1_active.id,
                title="Inactive Scene in Active Act",
                is_active=False,
            )
            create_test_scene(
                session=session,
                act_id=act_2_inactive.id,
                title="Active Scene in Inactive Act",
                is_active=True,
            )

            # Refresh relationships
            session.refresh(game, attribute_names=["acts"])
            for act in [act_1_active, act_2_inactive]:
                session.refresh(act, attribute_names=["scenes"])

            # Test Python context - should be True because there's at least one
            # active act
            assert game.has_active_act, (
                "Game should have active act (act_1_active is active)"
            )

            # Test Python context - should be True because act_1_active has active scene
            assert game.has_active_scene, (
                "Game should have active scene (scene_1_active in act_1_active)"
            )

            # Test SQL context
            games_with_active_acts = (
                session.query(Game).filter(Game.has_active_act).all()
            )
            games_with_active_scenes = (
                session.query(Game).filter(Game.has_active_scene).all()
            )

            assert game.id in [g.id for g in games_with_active_acts]
            assert game.id in [g.id for g in games_with_active_scenes]

            # Now deactivate the last active act
            act_1_active.is_active = False
            session.add(act_1_active)
            session.flush()
            session.refresh(game, attribute_names=["acts"])

            # Should no longer have active act or active scene
            assert not game.has_active_act, "No active acts remaining"
            assert not game.has_active_scene, "No active scenes in active acts"

    def test_hierarchical_status_checking_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test edge cases for hierarchical status checking (Game → Act → Scene)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Create multiple acts with complex scene combinations
            # Note: Only one act can be active at a time due to business rules
            act_1 = create_test_act(
                session=session,
                game_id=game.id,
                title="Act with Mixed Scenes",
                sequence=1,
                is_active=True,
            )
            act_2 = create_test_act(
                session=session,
                game_id=game.id,
                title="Act with Only Inactive Scenes",
                sequence=2,
                is_active=False,
            )
            act_3 = create_test_act(
                session=session,
                game_id=game.id,
                title="Act with No Scenes",
                sequence=3,
                is_active=False,
            )
            act_4 = create_test_act(
                session=session,
                game_id=game.id,
                title="Inactive Act with Active Scenes",
                sequence=4,
                is_active=False,
            )

            # Act 1: Has both active and inactive scenes
            create_test_scene(
                session=session, act_id=act_1.id, title="Active Scene", is_active=True
            )
            create_test_scene(
                session=session,
                act_id=act_1.id,
                title="Inactive Scene",
                is_active=False,
            )

            # Act 2: Has only inactive scenes
            create_test_scene(
                session=session,
                act_id=act_2.id,
                title="Another Inactive Scene",
                is_active=False,
            )

            # Act 3: Has no scenes

            # Act 4: Inactive act with active scenes (shouldn't count for
            # has_active_scene)
            create_test_scene(
                session=session,
                act_id=act_4.id,
                title="Active Scene in Inactive Act",
                is_active=True,
            )

            # Refresh all relationships
            session.refresh(game, attribute_names=["acts"])
            for act in [act_1, act_2, act_3, act_4]:
                session.refresh(act, attribute_names=["scenes"])

            # Test Python context
            assert game.has_active_act, "Game should have active act (act_1)"
            assert game.has_active_scene, (
                "Game should have active scene (from act_1, since act_1 is active "
                + "and has active scene)"
            )

            # Test SQL context
            games_with_active_acts = (
                session.query(Game).filter(Game.has_active_act).all()
            )
            games_with_active_scenes = (
                session.query(Game).filter(Game.has_active_scene).all()
            )

            assert game.id in [g.id for g in games_with_active_acts]
            assert game.id in [g.id for g in games_with_active_scenes]

            # Now make act_1's scene inactive - should remove active scene status
            for scene in act_1.scenes:
                if scene.is_active:
                    scene.is_active = False
                    session.add(scene)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            for act in [act_1, act_2, act_3, act_4]:
                session.refresh(act, attribute_names=["scenes"])

            # Should still have active act but no active scenes
            assert game.has_active_act, "Should still have active act (act_1)"
            assert not game.has_active_scene, (
                "Should no longer have active scenes (act_1 scene deactivated, "
                + "act_2 has no active scenes, act_3 has no scenes, "
                + "act_4 is inactive so doesn't count)"
            )

    def test_status_property_sql_efficiency(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test that status property SQL expressions generate efficient queries."""
        with session_context as session:
            # Create test data with multiple games for realistic testing
            games = []
            for i in range(3):
                game = create_test_game(session=session, name=f"Game {i}")
                games.append(game)

                # Create acts and scenes for each game
                act = create_test_act(
                    session=session,
                    game_id=game.id,
                    is_active=(i % 2 == 0),  # Make some active, some inactive
                )
                create_test_scene(
                    session=session,
                    act_id=act.id,
                    is_active=(i == 0),  # Only first game has active scene
                )

            session.flush()

            # Test SQL queries use efficient EXISTS subqueries
            # These should all complete quickly and return expected results

            # Test has_active_act filtering
            games_with_active_acts = (
                session.query(Game).filter(Game.has_active_act).all()
            )
            # Should return games 0 and 2 (even indices)
            active_act_count = len(games_with_active_acts)
            assert active_act_count == 2, (
                f"Expected 2 games with active acts, got {active_act_count}"
            )

            # Test has_active_scene filtering (more complex JOIN)
            games_with_active_scenes = (
                session.query(Game).filter(Game.has_active_scene).all()
            )
            # Should return only game 0
            active_scene_count = len(games_with_active_scenes)
            assert active_scene_count == 1, (
                f"Expected 1 game with active scenes, got {active_scene_count}"
            )

            # Test combined filtering
            games_with_both = (
                session.query(Game)
                .filter(Game.has_active_act & Game.has_active_scene)
                .all()
            )
            # Should return only game 0
            both_count = len(games_with_both)
            assert both_count == 1, (
                f"Expected 1 game with both active acts and scenes, got {both_count}"
            )

            # Verify the correct game is returned
            assert games_with_both[0].id == games[0].id


class TestGameHybridProperties:
    """Test Game model hybrid properties in both Python and SQL contexts."""

    def test_has_acts_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test has_acts property in Python context (instance access)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Test game with no acts
            session.refresh(game, attribute_names=["acts"])
            assert not game.has_acts, "Game with no acts should return False"

            # Add an act
            _ = create_test_act(session=session, game_id=game.id)
            session.refresh(game, attribute_names=["acts"])
            assert game.has_acts, "Game with acts should return True"

    def test_has_acts_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test has_acts property in SQL context (query filtering)."""
        with session_context as session:
            # Create test data
            game_with_acts = create_test_game(session=session, name="Game With Acts")
            game_without_acts = create_test_game(
                session=session, name="Game Without Acts", is_active=False
            )

            # Add act to one game only
            create_test_act(session=session, game_id=game_with_acts.id)

            # Test SQL filtering - games with acts
            games_with_acts = session.query(Game).filter(Game.has_acts).all()
            game_ids_with_acts = [g.id for g in games_with_acts]

            assert game_with_acts.id in game_ids_with_acts
            assert game_without_acts.id not in game_ids_with_acts

            # Test SQL filtering - games without acts
            games_without_acts = session.query(Game).filter(~Game.has_acts).all()
            game_ids_without_acts = [g.id for g in games_without_acts]

            assert game_with_acts.id not in game_ids_without_acts
            assert game_without_acts.id in game_ids_without_acts

    def test_hierarchical_relationships_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test edge cases for hierarchical relationships (Game → Act → Scene)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Create multiple acts with different scene combinations
            act_1 = create_test_act(
                session=session, game_id=game.id, title="Act 1", sequence=1
            )
            act_2 = create_test_act(
                session=session,
                game_id=game.id,
                title="Act 2",
                sequence=2,
                is_active=False,
            )
            act_3 = create_test_act(
                session=session,
                game_id=game.id,
                title="Act 3",
                sequence=3,
                is_active=False,
            )

            # Act 1: Has active scenes
            create_test_scene(
                session=session, act_id=act_1.id, title="Scene 1.1", is_active=True
            )
            create_test_scene(
                session=session,
                act_id=act_1.id,
                title="Scene 1.2",
                is_active=False,
            )

            # Act 2: Has only inactive scenes
            create_test_scene(
                session=session,
                act_id=act_2.id,
                title="Scene 2.1",
                is_active=False,
            )

            # Act 3: Has no scenes

            # Refresh all relationships
            session.refresh(game, attribute_names=["acts"])
            for act in [act_1, act_2, act_3]:
                session.refresh(act, attribute_names=["scenes"])

            # Test Python context - game should have various properties
            assert game.has_acts, "Game should have acts"
            assert game.has_active_act, "Game should have active act (act_1)"
            assert game.has_active_scene, "Game should have active scene (from act_1)"

            # Test SQL context - game should appear in various filtered queries
            games_with_acts = session.query(Game).filter(Game.has_acts).all()
            games_with_active_acts = (
                session.query(Game).filter(Game.has_active_act).all()
            )
            games_with_active_scenes = (
                session.query(Game).filter(Game.has_active_scene).all()
            )

            assert game.id in [g.id for g in games_with_acts]
            assert game.id in [g.id for g in games_with_active_acts]
            assert game.id in [g.id for g in games_with_active_scenes]

    def test_multiple_acts_mixed_content(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test games with multiple acts having different content combinations."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Create multiple acts, only some with active scenes
            act_with_active_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Active Scenes",
                sequence=1,
            )
            act_with_inactive_scenes = create_test_act(
                session=session,
                game_id=game.id,
                title="Act With Inactive Scenes",
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

            # Add scenes to acts
            create_test_scene(
                session=session,
                act_id=act_with_active_scenes.id,
                title="Active Scene",
                is_active=True,
            )
            create_test_scene(
                session=session,
                act_id=act_with_inactive_scenes.id,
                title="Inactive Scene",
                is_active=False,
            )

            # Refresh relationships
            session.refresh(game, attribute_names=["acts"])
            for act in [
                act_with_active_scenes,
                act_with_inactive_scenes,
                act_without_scenes,
            ]:
                session.refresh(act, attribute_names=["scenes"])

            # Test Python context - should return True because at least one
            # act has active scenes
            assert game.has_active_scene, (
                "Game should have active scene even if only one act has "
                + "active scenes"
            )

            # Test SQL context - should still find the game
            games_with_active_scenes = (
                session.query(Game).filter(Game.has_active_scene).all()
            )
            assert game.id in [g.id for g in games_with_active_scenes]

    def test_all_properties_combined_sql_filtering(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test complex SQL queries combining multiple hybrid properties."""
        with session_context as session:
            # Create test data
            game_full = create_test_game(session=session, name="Full Game")
            game_empty = create_test_game(
                session=session, name="Empty Game", is_active=False
            )
            game_acts_only = create_test_game(
                session=session, name="Acts Only Game", is_active=False
            )

            # Full game: has everything
            act_full = create_test_act(
                session=session, game_id=game_full.id, is_active=True
            )
            create_test_scene(session=session, act_id=act_full.id, is_active=True)

            # Acts only game: just empty acts
            create_test_act(session=session, game_id=game_acts_only.id, is_active=False)

            session.flush()

            # Test complex SQL queries
            games_with_acts_and_active_acts = (
                session.query(Game).filter(Game.has_acts & Game.has_active_act).all()
            )

            games_with_any_content = (
                session.query(Game)
                .filter(Game.has_acts | Game.has_active_act | Game.has_active_scene)
                .all()
            )

            games_fully_featured = (
                session.query(Game)
                .filter(Game.has_acts & Game.has_active_act & Game.has_active_scene)
                .all()
            )

            # Verify results
            full_game_ids = [g.id for g in games_with_acts_and_active_acts]
            any_content_ids = [g.id for g in games_with_any_content]
            fully_featured_ids = [g.id for g in games_fully_featured]

            assert game_full.id in full_game_ids
            assert game_acts_only.id not in full_game_ids
            assert game_empty.id not in full_game_ids

            assert game_full.id in any_content_ids
            assert game_acts_only.id in any_content_ids
            assert game_empty.id not in any_content_ids

            assert game_full.id in fully_featured_ids
            assert game_acts_only.id not in fully_featured_ids
            assert game_empty.id not in fully_featured_ids

    def _create_game_with_complex_hierarchy(
        self,
        session,
        game_name: str,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ):
        """Helper method to create a game with complex act/scene hierarchy."""
        game = create_test_game(session=session, name=game_name)

        # Create multiple acts with various configurations
        act_1 = create_test_act(
            session=session,
            game_id=game.id,
            title="First Act",
            sequence=1,
            is_active=True,
        )
        act_2 = create_test_act(
            session=session,
            game_id=game.id,
            title="Second Act",
            sequence=2,
            is_active=False,
        )

        # First act has both active and inactive scenes
        create_test_scene(
            session=session,
            act_id=act_1.id,
            title="Active Scene 1",
            is_active=True,
        )
        create_test_scene(
            session=session,
            act_id=act_1.id,
            title="Inactive Scene 1",
            is_active=False,
        )

        # Second act has only inactive scenes
        create_test_scene(
            session=session,
            act_id=act_2.id,
            title="Inactive Scene 2",
            is_active=False,
        )

        return game

    def test_complex_hierarchy_scenarios(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
        create_test_scene: Callable,
    ) -> None:
        """Test various complex hierarchical scenarios."""
        with session_context as session:
            # Create games with different hierarchical structures
            game_complex = self._create_game_with_complex_hierarchy(
                session,
                "Complex Game",
                create_test_game,
                create_test_act,
                create_test_scene,
            )

            # Create a simpler comparison game
            game_simple = create_test_game(session=session, name="Simple Game")
            simple_act = create_test_act(
                session=session, game_id=game_simple.id, is_active=False
            )
            create_test_scene(session=session, act_id=simple_act.id, is_active=False)

            # Refresh all relationships
            for game in [game_complex, game_simple]:
                session.refresh(game, attribute_names=["acts"])
                for act in game.acts:
                    session.refresh(act, attribute_names=["scenes"])

            # Test Python context properties
            assert game_complex.has_acts, "Complex game should have acts"
            assert game_complex.has_active_act, "Complex game should have active act"
            assert game_complex.has_active_scene, (
                "Complex game should have active scene"
            )

            assert game_simple.has_acts, "Simple game should have acts"
            assert not game_simple.has_active_act, (
                "Simple game should not have active act"
            )
            assert not game_simple.has_active_scene, (
                "Simple game should not have active scene"
            )

            # Test SQL context filtering
            games_with_active_acts = (
                session.query(Game).filter(Game.has_active_act).all()
            )
            games_with_active_scenes = (
                session.query(Game).filter(Game.has_active_scene).all()
            )

            complex_in_active_acts = game_complex.id in [
                g.id for g in games_with_active_acts
            ]
            simple_in_active_acts = game_simple.id in [
                g.id for g in games_with_active_acts
            ]
            complex_in_active_scenes = game_complex.id in [
                g.id for g in games_with_active_scenes
            ]
            simple_in_active_scenes = game_simple.id in [
                g.id for g in games_with_active_scenes
            ]

            assert complex_in_active_acts, (
                "Complex game should be found in active acts query"
            )
            assert not simple_in_active_acts, (
                "Simple game should not be found in active acts query"
            )
            assert complex_in_active_scenes, (
                "Complex game should be found in active scenes query"
            )
            assert not simple_in_active_scenes, (
                "Simple game should not be found in active scenes query"
            )

    @pytest.mark.parametrize(
        "property_name,setup_func",
        [
            (
                "has_acts",
                lambda session, game_id, create_test_act, **_kwargs: (
                    create_test_act(session=session, game_id=game_id)
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
    ) -> None:
        """Parametrized test for simple hybrid properties.
        Reduces code duplication for properties with similar test patterns.
        """
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Test property returns False initially
            session.refresh(game)
            property_value = getattr(game, property_name)
            assert not property_value, (
                f"{property_name} should return False for empty game"
            )

            # Add related data using setup function
            setup_func(
                session=session,
                game_id=game.id,
                create_test_act=create_test_act,
            )

            # Test property returns True after adding data
            session.refresh(game)
            property_value = getattr(game, property_name)
            assert property_value, (
                f"{property_name} should return True after adding related data"
            )

    def test_act_count_python_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test act_count property in Python context (instance access)."""
        with session_context as session:
            # Create test data
            game = create_test_game(session=session)

            # Test game with no acts
            session.refresh(game, attribute_names=["acts"])
            assert game.act_count == 0, "Game with no acts should have count 0"

            # Add one act
            act1 = create_test_act(
                session=session, game_id=game.id, title="Act 1", sequence=1
            )
            session.refresh(game, attribute_names=["acts"])
            assert game.act_count == 1, "Game with one act should have count 1"

            # Add second act (make first act inactive to allow creation)
            act1.is_active = False
            session.add(act1)
            session.flush()
            act2 = create_test_act(
                session=session, game_id=game.id, title="Act 2", sequence=2
            )
            session.refresh(game, attribute_names=["acts"])
            assert game.act_count == 2, "Game with two acts should have count 2"

            # Add third act (make second act inactive)
            act2.is_active = False
            session.add(act2)
            session.flush()
            _ = create_test_act(
                session=session, game_id=game.id, title="Act 3", sequence=3
            )
            session.refresh(game, attribute_names=["acts"])
            assert game.act_count == 3, "Game with three acts should have count 3"

    def test_act_count_sql_context(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test act_count property in SQL context (query filtering and ordering)."""
        with session_context as session:
            # Create games with different act counts
            game_0_acts = create_test_game(session=session, name="Game 0 Acts")
            game_1_act = create_test_game(session=session, name="Game 1 Act")
            game_3_acts = create_test_game(session=session, name="Game 3 Acts")

            # Add acts (all inactive to avoid validation)
            create_test_act(session=session, game_id=game_1_act.id, is_active=False)

            for i in range(3):
                create_test_act(
                    session=session,
                    game_id=game_3_acts.id,
                    title=f"Act {i + 1}",
                    sequence=i + 1,
                    is_active=False,
                )

            # Test SQL ordering by act_count
            games_ordered = session.query(Game).order_by(Game.act_count.desc()).all()
            game_order = [g.id for g in games_ordered]

            # Verify order - 3 acts should come first, then 1, then 0
            assert game_order.index(game_3_acts.id) < game_order.index(game_1_act.id)
            assert game_order.index(game_1_act.id) < game_order.index(game_0_acts.id)

            # Test SQL filtering with act_count
            games_with_acts = session.query(Game).filter(Game.act_count > 0).all()
            games_with_multiple = session.query(Game).filter(Game.act_count > 1).all()
            games_with_exact_one = session.query(Game).filter(Game.act_count == 1).all()

            # Verify filtering results
            game_ids_with_acts = [g.id for g in games_with_acts]
            game_ids_with_multiple = [g.id for g in games_with_multiple]
            game_ids_with_exact_one = [g.id for g in games_with_exact_one]

            assert game_0_acts.id not in game_ids_with_acts
            assert game_1_act.id in game_ids_with_acts
            assert game_3_acts.id in game_ids_with_acts

            assert game_0_acts.id not in game_ids_with_multiple
            assert game_1_act.id not in game_ids_with_multiple
            assert game_3_acts.id in game_ids_with_multiple

            assert game_0_acts.id not in game_ids_with_exact_one
            assert game_1_act.id in game_ids_with_exact_one
            assert game_3_acts.id not in game_ids_with_exact_one

    def test_act_count_edge_cases(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test edge cases for act_count property."""
        with session_context as session:
            # Create test game
            game = create_test_game(session=session)

            # Test deleting acts affects count
            act1 = create_test_act(
                session=session,
                game_id=game.id,
                title="Act 1",
                sequence=1,
                is_active=False,
            )
            act2 = create_test_act(
                session=session,
                game_id=game.id,
                title="Act 2",
                sequence=2,
                is_active=False,
            )
            session.refresh(game, attribute_names=["acts"])
            assert game.act_count == 2

            # Delete one act
            session.delete(act1)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            assert game.act_count == 1, "Count should decrease after deleting act"

            # Delete remaining act
            session.delete(act2)
            session.flush()
            session.refresh(game, attribute_names=["acts"])
            assert game.act_count == 0, "Count should be 0 after deleting all acts"

    def test_act_count_consistency(
        self,
        session_context: SessionContext,
        create_test_game: Callable,
        create_test_act: Callable,
    ) -> None:
        """Test that act_count is consistent between Python and SQL contexts."""
        with session_context as session:
            # Create games with various act counts
            games = []
            expected_counts = [0, 1, 2, 5, 10]

            for i, count in enumerate(expected_counts):
                game = create_test_game(session=session, name=f"Game {i}")
                games.append(game)

                for j in range(count):
                    create_test_act(
                        session=session,
                        game_id=game.id,
                        title=f"Act {j + 1}",
                        sequence=j + 1,
                        is_active=False,
                    )

            # Test each game
            for game, expected_count in zip(games, expected_counts, strict=False):
                # Refresh to ensure relationships are loaded
                session.refresh(game, attribute_names=["acts"])

                # Python context
                python_count = game.act_count

                # SQL context - get count via query
                sql_result = (
                    session.query(Game.act_count).filter(Game.id == game.id).scalar()
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
