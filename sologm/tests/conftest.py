"""Common test fixtures for all sologm tests."""

# Standard library imports
import logging
from typing import TYPE_CHECKING, Any, Callable, Generator, Optional
from unittest.mock import MagicMock

# Third-party imports
import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

# Local application/library imports
from sologm.core.factory import create_all_managers
from sologm.database.session import DatabaseManager, SessionContext
from sologm.integrations.anthropic import AnthropicClient
from sologm.models.base import Base
from sologm.models.event import Event
from sologm.models.event_source import EventSource
from sologm.models.game import Game
from sologm.models.scene import Scene
from sologm.utils.config import Config

# Conditional imports for type checking
if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.oracle import Interpretation, InterpretationSet


logger = logging.getLogger(__name__)


@pytest.fixture
def mock_config_no_api_key() -> MagicMock:
    """Create a mock Config object simulating a missing API key.

    This mock returns None when `get("anthropic_api_key")` is called.

    Returns:
        A configured MagicMock object simulating the Config class.
    """
    logger.debug("[Fixture mock_config_no_api_key] Creating mock Config object")
    mock_config = MagicMock(spec=Config)

    # Define the behavior for the mock's get method
    def mock_get(key: str, default: Any = None) -> Any:
        logger.debug(
            f"[Fixture mock_config_no_api_key] Mock config.get called with key: {key}"
        )
        if key == "anthropic_api_key":
            logger.debug(
                f"[Fixture mock_config_no_api_key] Mock config returning None "
                f"for key: {key}"
            )
            return None
        # For other keys, maybe return default or raise an error if unexpected
        logger.debug(
            f"[Fixture mock_config_no_api_key] Mock config returning default "
            f"for key: {key}"
        )
        return default

    mock_config.get.side_effect = mock_get
    logger.debug("[Fixture mock_config_no_api_key] Returning configured mock object")
    return mock_config


# --- Database Fixtures ---


@pytest.fixture
def db_engine() -> Generator[Engine, None, None]:
    """Create a new in-memory SQLite database engine for each test.

    Yields:
        An SQLAlchemy Engine connected to an in-memory SQLite database.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def database_manager(db_engine: Engine) -> Generator[DatabaseManager, None, None]:
    """Provide a test-specific DatabaseManager instance using an in-memory DB.

    Replaces the singleton DatabaseManager instance for the duration of a test,
    ensuring test isolation by using a dedicated in-memory SQLite database.
    The original instance is restored after the test.

    Args:
        db_engine: The in-memory SQLite engine fixture.

    Yields:
        A DatabaseManager instance configured for the test database.
    """
    # Import locally to avoid potential issues if this file is imported early
    from sologm.database.session import DatabaseManager

    # Save original instance to restore it after the test.
    # This prevents tests from affecting each other or the real application state.
    old_instance = DatabaseManager._instance

    # Create a new DatabaseManager instance using the test engine.
    db_manager = DatabaseManager(engine=db_engine)
    DatabaseManager._instance = db_manager

    yield db_manager

    # Restore the original singleton instance to prevent test pollution.
    DatabaseManager._instance = old_instance


# --- Mock Fixtures ---


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Create a mock Anthropic client.

    Returns:
        A MagicMock object simulating the AnthropicClient.
    """
    return MagicMock(spec=AnthropicClient)


@pytest.fixture
def cli_test() -> Callable[[Callable[[Session], Any]], Any]:
    """Provide a helper function to run test code within a DB session context.

    Mimics the pattern used by CLI commands where operations are wrapped
    in a database session context.

    Returns:
        A function that takes another function (the test logic) as input.
        The input function must accept a Session object as its argument.
        The helper executes the input function within a `get_db_context()` block.

    Example:
        def test_cli_pattern(cli_test):
            def _logic_using_session(session: Session):
                # ... use session ...
                return result

            result = cli_test(_logic_using_session)
            # ... assert result ...
    """

    def _run_with_context(test_func: Callable[[Session], Any]) -> Any:
        from sologm.database.session import get_db_context

        with get_db_context() as session:
            return test_func(session)

    return _run_with_context


# --- Session Context Fixture ---


@pytest.fixture
def session_context() -> SessionContext:
    """Provide a SessionContext instance for managing test database sessions.

    This allows tests to use the same `with session_context as session:` pattern
    as the application code.

    Returns:
        A SessionContext instance connected to the test database.
    """
    # Import locally to avoid potential issues if this file is imported early
    from sologm.database.session import SessionContext

    return SessionContext()


# --- Factory Fixtures ---


@pytest.fixture
def create_test_game(
    session_context: SessionContext,
) -> Callable[..., Game]:
    """Provide a factory function to create test Game instances.

    Args:
        session_context: Fixture to provide the database session context.

    Returns:
        A callable function `_create_game(name="...", description="...",
        is_active=True)` that creates and returns a persisted Game instance
        within the provided session.
    """

    def _create_game(
        name: str = "Test Game",
        description: str = "A test game",
        is_active: bool = True,
    ) -> Game:
        with session_context as session:
            managers = create_all_managers(session)
            game = managers.game.create_game(name, description, is_active=is_active)
            # No merge needed as the object is already session-bound via the manager.
            return game

    return _create_game


@pytest.fixture
def create_test_act(
    session_context: SessionContext,
) -> Callable[..., "Act"]:
    """Provide a factory function to create test Act instances.

    Args:
        session_context: Fixture to provide the database session context.

    Returns:
        A callable function `_create_act(game_id, title="...", ...)`
        that creates and returns a persisted Act instance.
    """
    # Import Act locally to avoid potential circular dependency issues at module level.
    from sologm.models.act import Act

    def _create_act(
        game_id: str,
        title: Optional[str] = "Test Act",
        summary: Optional[str] = "A test act",
        is_active: bool = True,
        sequence: Optional[int] = None,
    ) -> Act:
        with session_context as session:
            managers = create_all_managers(session)
            act = managers.act.create_act(
                game_id=game_id,
                title=title,
                summary=summary,
                make_active=is_active,
            )
            # If sequence was specified, update it directly using the correct session
            if sequence is not None:
                act.sequence = sequence
                session.add(act)
                session.flush()  # Keep flush here as sequence is manually
                # set outside manager.

            # No merge needed as the object is already session-bound via the manager.
            return act

    return _create_act


@pytest.fixture
def create_test_scene(
    session_context: SessionContext,
) -> Callable[..., Scene]:
    """Provide a factory function to create test Scene instances.

    Args:
        session_context: Fixture to provide the database session context.

    Returns:
        A callable function `_create_scene(act_id, title="...", ...)`
        that creates and returns a persisted Scene instance.
    """

    def _create_scene(
        act_id: str,
        title: str = "Test Scene",
        description: str = "A test scene",
        is_active: bool = True,
    ) -> Scene:
        with session_context as session:
            managers = create_all_managers(session)
            scene = managers.scene.create_scene(
                act_id=act_id,
                title=title,
                description=description,
                make_active=is_active,
            )

            # Refresh relationships to ensure they are loaded while the object is
            # known to be persistent within this session context.
            # Flushing ensures the object state is synchronized with the DB
            # before refresh.
            try:
                session.flush()  # Flush *before* refresh to ensure state is
                # synchronized.
                # Refresh common relationships typically needed immediately
                # after creation.
                session.refresh(scene, attribute_names=["act"])
            except Exception as e:
                logger.warning(
                    "Warning: Error refreshing relationships in "
                    "create_test_scene factory: %s",
                    e,
                )
                # Log and continue for now, but this might hide issues in tests.

            # No merge needed as the object is already session-bound via the manager.
            return scene

    return _create_scene


@pytest.fixture
def create_test_event(
    session_context: SessionContext,
) -> Callable[..., Event]:
    """Provide a factory function to create test Event instances.

    Args:
        session_context: Fixture to provide the database session context.

    Returns:
        A callable function `_create_event(scene_id, description="...", ...)`
        that creates and returns a persisted Event instance.
    """

    def _create_event(
        scene_id: str,
        description: str = "Test event",
        source: str = "manual",
        interpretation_id: Optional[str] = None,
    ) -> Event:
        with session_context as session:
            managers = create_all_managers(session)
            event = managers.event.add_event(
                description=description,
                scene_id=scene_id,
                source=source,
                interpretation_id=interpretation_id,
            )
            # No merge needed as the object is already session-bound via the manager.
            try:
                # Refresh relationships to ensure they are loaded.
                session.refresh(
                    event, attribute_names=["scene", "source", "interpretation"]
                )
            except Exception as e:
                logger.warning(
                    "Warning: Error refreshing relationships in "
                    "create_test_event factory: %s",
                    e,
                )
            return event

    return _create_event


@pytest.fixture
def create_test_interpretation_set(
    session_context: SessionContext,
) -> Callable[..., "InterpretationSet"]:
    """Provide a factory function to create test InterpretationSet instances.

    Args:
        session_context: Fixture to provide the database session context.

    Returns:
        A callable function `_create_interpretation_set(scene_id, context="...", ...)`
        that creates and returns a persisted InterpretationSet instance.
    """
    from sologm.models.oracle import InterpretationSet

    def _create_interpretation_set(
        scene_id: str,
        context: str = "Test Context",
        oracle_results: str = "Test Oracle Results",
        retry_attempt: int = 0,
        is_current: bool = False,
    ) -> InterpretationSet:
        with session_context as session:
            # TODO: Replace direct model creation with manager call when available.
            managers = create_all_managers(session)
            # Example: interp_set = managers.oracle.create_interpretation_set(...)
            interp_set = InterpretationSet.create(
                scene_id=scene_id,
                context=context,
                oracle_results=oracle_results,
                retry_attempt=retry_attempt,
                is_current=is_current,
            )
            session.add(interp_set)
            session.flush()
            try:
                session.refresh(
                    interp_set, attribute_names=["scene", "interpretations"]
                )
            except Exception as e:
                logger.warning(
                    "Warning: Error refreshing relationships in "
                    "create_test_interpretation_set factory: %s",
                    e,
                )
            logger.warning(
                "create_test_interpretation_set fixture is using placeholder "
                "implementation."
            )
            return interp_set

    return _create_interpretation_set


@pytest.fixture
def create_test_interpretation(
    session_context: SessionContext,
) -> Callable[..., "Interpretation"]:
    """Provide a factory function to create test Interpretation instances.

    Args:
        session_context: Fixture to provide the database session context.

    Returns:
        A callable function `_create_interpretation(set_id, title="...", ...)`
        that creates and returns a persisted Interpretation instance.
    """
    from sologm.models.oracle import Interpretation

    def _create_interpretation(
        set_id: str,
        title: str = "Test Interpretation",
        description: str = "A test interpretation.",
        is_selected: bool = False,
    ) -> Interpretation:
        with session_context as session:
            # TODO: Replace direct model creation with manager call when available.
            managers = create_all_managers(session)
            # Example: interp = managers.oracle.create_interpretation(...)
            interp = Interpretation.create(
                set_id=set_id,
                title=title,
                description=description,
                is_selected=is_selected,
            )
            session.add(interp)
            session.flush()
            try:
                session.refresh(interp, attribute_names=["interpretation_set", "event"])
            except Exception as e:
                logger.warning(
                    "Warning: Error refreshing relationships in "
                    "create_test_interpretation factory: %s",
                    e,
                )
            logger.warning(
                "create_test_interpretation fixture is using placeholder "
                "implementation."
            )
            return interp

    return _create_interpretation


# --- Helper Fixtures ---


@pytest.fixture(autouse=True)
def initialize_event_sources(session_context: SessionContext) -> None:
    """Initialize default event sources (manual, oracle, dice) for testing.

    Ensures these sources exist in the test database before tests run.

    Args:
        session_context: Fixture to provide the database session context.
    """
    sources = ["manual", "oracle", "dice"]
    with session_context as session:
        for source_name in sources:
            existing = (
                session.query(EventSource)
                .filter(EventSource.name == source_name)
                .first()
            )
            if not existing:
                source = EventSource.create(name=source_name)
                session.add(source)
        # Session is committed automatically by the SessionContext manager upon exit.
