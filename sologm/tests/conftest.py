"""Common test fixtures for all sologm tests."""

# Standard library imports
import logging
from typing import TYPE_CHECKING, Any, Callable, Generator, Optional
from unittest.mock import MagicMock

# Third-party imports
import pytest
from sqlalchemy import Engine, create_engine, event  # Import event
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

    Enables foreign key support for SQLite.

    Yields:
        An SQLAlchemy Engine connected to an in-memory SQLite database.
    """
    logger.debug("Creating in-memory SQLite engine for test")
    engine = create_engine("sqlite:///:memory:")

    # --- Enable Foreign Key support for SQLite ---
    # This is crucial for cascade deletes to work correctly in tests
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_con, connection_record):
        logger.debug("Executing PRAGMA foreign_keys=ON for new SQLite connection")
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    # --- End Foreign Key support ---

    logger.debug("Creating all tables on the test engine")
    Base.metadata.create_all(engine)
    yield engine
    logger.debug("Disposing of the test engine")
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

    logger.debug("Saving original DatabaseManager instance")
    # Save original instance to restore it after the test.
    # This prevents tests from affecting each other or the real application state.
    old_instance = DatabaseManager._instance

    # Create a new DatabaseManager instance using the test engine.
    logger.debug("Creating new DatabaseManager instance for test")
    db_manager = DatabaseManager(engine=db_engine)
    DatabaseManager._instance = db_manager

    yield db_manager

    # Restore the original singleton instance to prevent test pollution.
    logger.debug("Restoring original DatabaseManager instance")
    DatabaseManager._instance = old_instance


# --- Mock Fixtures ---


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Create a mock Anthropic client.

    Returns:
        A MagicMock object simulating the AnthropicClient.
    """
    logger.debug("Creating mock AnthropicClient")
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
    logger.debug("[Fixture cli_test] Creating context runner function")

    def _run_with_context(test_func: Callable[[Session], Any]) -> Any:
        from sologm.database.session import get_db_context

        logger.debug(
            f"[Fixture cli_test] Running function {test_func.__name__} within DB context"
        )
        with get_db_context() as session:
            result = test_func(session)
        logger.debug(
            f"[Fixture cli_test] Finished running function {test_func.__name__}"
        )
        return result

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

    logger.debug("[Fixture session_context] Creating SessionContext instance")
    return SessionContext()


# --- Factory Fixtures ---


@pytest.fixture
def create_test_game() -> Callable[..., Game]:
    """Provide a factory function to create test Game instances.

    Args:
        session: The active SQLAlchemy session for the test.

    Returns:
        A callable function `_create_game(session, name="...", description="...",
        is_active=True)` that creates and returns a persisted Game instance
        within the provided session.
    """
    logger.debug("[Fixture create_test_game] Creating factory function")

    def _create_game(
        session: Session,
        name: str = "Test Game",
        description: str = "A test game",
        is_active: bool = True,
    ) -> Game:
        logger.debug(f"[Factory create_test_game] Creating game: name='{name}'")
        managers = create_all_managers(session)
        game = managers.game.create_game(name, description, is_active=is_active)
        # Object is already session-bound via the manager.
        logger.debug(f"[Factory create_test_game] Created game ID: {game.id}")
        return game

    return _create_game


@pytest.fixture
def create_test_act() -> Callable[..., "Act"]:
    """Provide a factory function to create test Act instances.

    Args:
        session: The active SQLAlchemy session for the test.
        game_id: The ID of the game this act belongs to.
        ... other args

    Returns:
        A callable function `_create_act(session, game_id, title="...", ...)`
        that creates and returns a persisted Act instance.
    """
    logger.debug("[Fixture create_test_act] Creating factory function")
    # Import Act locally to avoid potential circular dependency issues at module level.
    from sologm.models.act import Act

    def _create_act(
        session: Session,
        game_id: str,
        title: Optional[str] = "Test Act",
        summary: Optional[str] = "A test act",
        is_active: bool = True,
        sequence: Optional[int] = None,
    ) -> Act:
        logger.debug(
            f"[Factory create_test_act] Creating act: title='{title}', game_id='{game_id}'"
        )
        managers = create_all_managers(session)
        act = managers.act.create_act(
            game_id=game_id,
            title=title,
            summary=summary,
            make_active=is_active,
        )
        # If sequence was specified, update it directly.
        # No need for add/flush here as the object is already managed by the
        # session passed in, and the manager call above likely flushed.
        # If issues arise, a targeted flush might be needed, but start without.
        if sequence is not None:
            logger.debug(
                f"[Factory create_test_act] Setting sequence to {sequence} for act ID: {act.id}"
            )
            act.sequence = sequence
            # session.flush([act]) # Consider if needed later

        # Object is already session-bound via the manager.
        logger.debug(f"[Factory create_test_act] Created act ID: {act.id}")
        return act

    return _create_act


@pytest.fixture
def create_test_scene() -> Callable[..., Scene]:
    """Provide a factory function to create test Scene instances.

    Args:
        session: The active SQLAlchemy session for the test.
        act_id: The ID of the act this scene belongs to.
        ... other args

    Returns:
        A callable function `_create_scene(session, act_id, title="...", ...)`
        that creates and returns a persisted Scene instance.
    """
    logger.debug("[Fixture create_test_scene] Creating factory function")

    def _create_scene(
        session: Session,
        act_id: str,
        title: str = "Test Scene",
        description: str = "A test scene",
        is_active: bool = True,
    ) -> Scene:
        logger.debug(
            f"[Factory create_test_scene] Creating scene: title='{title}', act_id='{act_id}'"
        )
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
            logger.debug(
                f"[Factory create_test_scene] Flushing session before refresh for scene ID: {scene.id}"
            )
            session.flush()  # Flush *before* refresh to ensure state is synchronized.
            # Refresh common relationships typically needed immediately after creation.
            logger.debug(
                f"[Factory create_test_scene] Refreshing 'act' relationship for scene ID: {scene.id}"
            )
            session.refresh(scene, attribute_names=["act"])
        except Exception as e:
            # Use logger.warning for non-critical issues during test setup
            logger.warning(
                f"Warning: Error refreshing relationships in create_test_scene factory for scene ID {scene.id}: {e}",
                exc_info=True,  # Include traceback for warnings if helpful
            )
            # Log and continue for now, but this might hide issues in tests.

        # Object is already session-bound via the manager.
        logger.debug(f"[Factory create_test_scene] Created scene ID: {scene.id}")
        return scene

    return _create_scene


@pytest.fixture
def create_test_event() -> Callable[..., Event]:
    """Provide a factory function to create test Event instances.

    Args:
        session: The active SQLAlchemy session for the test.
        scene_id: The ID of the scene this event belongs to.
        ... other args

    Returns:
        A callable function `_create_event(session, scene_id, description="...", ...)`
        that creates and returns a persisted Event instance.
    """
    logger.debug("[Fixture create_test_event] Creating factory function")

    def _create_event(
        session: Session,
        scene_id: str,
        description: str = "Test event",
        source: str = "manual",
        interpretation_id: Optional[str] = None,
    ) -> Event:
        logger.debug(
            f"[Factory create_test_event] Creating event: description='{description[:20]}...', scene_id='{scene_id}'"
        )
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
            logger.debug(
                f"[Factory create_test_event] Refreshing relationships for event ID: {event.id}"
            )
            session.refresh(
                event, attribute_names=["scene", "source", "interpretation"]
            )
        except Exception as e:
            logger.warning(
                f"Warning: Error refreshing relationships in create_test_event factory for event ID {event.id}: {e}",
                exc_info=True,
            )
        # Object is already session-bound via the manager.
        logger.debug(f"[Factory create_test_event] Created event ID: {event.id}")
        return event

    return _create_event


@pytest.fixture
def create_test_interpretation_set() -> Callable[..., "InterpretationSet"]:
    """Provide a factory function to create test InterpretationSet instances.

    Args:
        session: The active SQLAlchemy session for the test.
        scene_id: The ID of the scene this set belongs to.
        ... other args

    Returns:
        A callable function `_create_interpretation_set(session, scene_id, context="...", ...)`
        that creates and returns a persisted InterpretationSet instance.
    """
    logger.debug("[Fixture create_test_interpretation_set] Creating factory function")
    from sologm.models.oracle import InterpretationSet

    def _create_interpretation_set(
        session: Session,
        scene_id: str,
        context: str = "Test Context",
        oracle_results: str = "Test Oracle Results",
        retry_attempt: int = 0,
        is_current: bool = False,
    ) -> InterpretationSet:
        logger.debug(
            f"[Factory create_test_interpretation_set] Creating set: scene_id='{scene_id}'"
        )
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
            logger.debug(
                f"[Factory create_test_interpretation_set] Refreshing relationships for set ID: {interp_set.id}"
            )
            session.refresh(interp_set, attribute_names=["scene", "interpretations"])
        except Exception as e:
            logger.warning(
                f"Warning: Error refreshing relationships in create_test_interpretation_set factory for set ID {interp_set.id}: {e}",
                exc_info=True,
            )
        logger.warning(
            "create_test_interpretation_set fixture is using placeholder implementation."
        )
        logger.debug(
            f"[Factory create_test_interpretation_set] Created set ID: {interp_set.id}"
        )
        return interp_set

    return _create_interpretation_set


@pytest.fixture
def create_test_interpretation() -> Callable[..., "Interpretation"]:
    """Provide a factory function to create test Interpretation instances.

    Args:
        session: The active SQLAlchemy session for the test.
        set_id: The ID of the InterpretationSet this interpretation belongs to.
        ... other args

    Returns:
        A callable function `_create_interpretation(session, set_id, title="...", ...)`
        that creates and returns a persisted Interpretation instance.
    """
    logger.debug("[Fixture create_test_interpretation] Creating factory function")
    from sologm.models.oracle import Interpretation

    def _create_interpretation(
        session: Session,
        set_id: str,
        title: str = "Test Interpretation",
        description: str = "A test interpretation.",
        is_selected: bool = False,
    ) -> Interpretation:
        logger.debug(
            f"[Factory create_test_interpretation] Creating interpretation: title='{title}', set_id='{set_id}'"
        )
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
            # Note: 'event' is likely incorrect here, should be 'events' (plural)
            # Also, Interpretation doesn't directly link to a single event, but a list.
            # Refreshing 'interpretation_set' is usually sufficient.
            logger.debug(
                f"[Factory create_test_interpretation] Refreshing relationships for interpretation ID: {interp.id}"
            )
            session.refresh(
                interp, attribute_names=["interpretation_set", "events"]
            )  # Corrected 'event' to 'events'
        except Exception as e:
            logger.warning(
                f"Warning: Error refreshing relationships in create_test_interpretation factory for interpretation ID {interp.id}: {e}",
                exc_info=True,
            )
        logger.warning(
            "create_test_interpretation fixture is using placeholder implementation."
        )
        logger.debug(
            f"[Factory create_test_interpretation] Created interpretation ID: {interp.id}"
        )
        return interp

    return _create_interpretation


# --- Helper Fixtures ---


# Note: This fixture now requires a session to be passed if used directly,
# but since it's autouse=True and depends on session_context, it might need
# adjustment if tests *don't* use session_context.
# Note: This fixture now requires a session to be passed if used directly.
# It should be called explicitly within a test's session block.
@pytest.fixture()
def initialize_event_sources() -> Callable[[Session], None]:
    """Provide a function to initialize default event sources (manual, oracle, dice).

    Ensures these sources exist in the test database. Needs to be called
    within an active session context by the test.

    Returns:
        A callable function `_initialize(session)` that adds the default
        event sources to the given session if they don't already exist.
    """
    sources = ["manual", "oracle", "dice"]
    logger.debug("[Fixture initialize_event_sources] Creating initializer function")

    def _initialize(session: Session) -> None:
        logger.debug(
            "[Initializer initialize_event_sources] Initializing event sources..."
        )
        added_count = 0
        for source_name in sources:
            # Use session.get for primary key lookup if ID were known,
            # but here we query by name.
            existing = session.query(EventSource).filter_by(name=source_name).first()
            if not existing:
                logger.debug(
                    f"[Initializer initialize_event_sources] Adding source: {source_name}"
                )
                source = EventSource.create(name=source_name)
                session.add(source)
                added_count += 1
            else:
                logger.debug(
                    f"[Initializer initialize_event_sources] Source '{source_name}' already exists."
                )
        if added_count > 0:
            # Flush here if immediate ID access or constraint checking is needed
            # before the test continues, otherwise rely on context manager's flush/commit.
            # session.flush()
            logger.debug(
                f"[Initializer initialize_event_sources] Added {added_count} new sources."
            )
        else:
            logger.debug(
                "[Initializer initialize_event_sources] All default sources already existed."
            )
        # Rely on the calling context (test's session_context) to commit/rollback.

    return _initialize
