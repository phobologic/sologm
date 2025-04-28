import logging
import uuid
from typing import List, Optional, Tuple

import pytest
from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.orm.exc import DetachedInstanceError  # Or LazyInitializationError

# --- Basic Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Ensure logs are visible


# --- Models ---
class Base(DeclarativeBase):
    pass


class Parent(Base):
    __tablename__ = "parents"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str]
    children: Mapped[List["Child"]] = relationship(
        "Child", back_populates="parent", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Parent(id={self.id}, name='{self.name}', obj_id={id(self)})>"


class Child(Base):
    __tablename__ = "children"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str]
    parent_id: Mapped[str] = mapped_column(ForeignKey("parents.id"))
    parent: Mapped["Parent"] = relationship("Parent", back_populates="children")

    def __repr__(self):
        return f"<Child(id={self.id}, name='{self.name}', parent_id={self.parent_id}, obj_id={id(self)})>"


# --- Simplified Manager ---
class SimpleManager:
    def __init__(self, session: Optional[Session] = None):
        self._session = session
        self.logger = logging.getLogger(f"{__name__}.SimpleManager")
        self.logger.debug(
            f"Initialized SimpleManager with session ID: {id(self._session)}"
        )

    def _get_session(self) -> Tuple[Session, bool]:
        """Mimics BaseManager._get_session"""
        if self._session is not None:
            self.logger.debug(f"Using provided session ID: {id(self._session)}")
            return self._session, True  # was_provided = True
        else:
            # Simplified: In a real scenario, this would get from a global factory
            raise NotImplementedError(
                "Internal session creation not implemented for this example"
            )

    def _execute_db_operation_problematic(
        self, operation_name: str, operation, *args, **kwargs
    ):
        """Mimics the ORIGINAL BaseManager logic - ALWAYS COMMITS."""
        self.logger.debug(f"[Problematic] Executing: {operation_name}")
        session, was_provided = self._get_session()
        self.logger.debug(
            f"[Problematic] Got session ID: {id(session)}, was_provided={was_provided}"
        )
        try:
            result = operation(session, *args, **kwargs)
            self.logger.debug(
                f"[Problematic] Operation {operation_name} successful, calling commit() on session ID: {id(session)}"
            )
            session.commit()  # <-- The problematic commit
            self.logger.debug(
                f"[Problematic] Commit finished for session ID: {id(session)}"
            )
            return result
        except Exception:
            self.logger.error(
                f"[Problematic] Error in {operation_name}, rolling back session ID: {id(session)}",
                exc_info=True,
            )
            session.rollback()
            raise
        finally:
            # In real BaseManager, session closing is handled elsewhere
            self.logger.debug(f"[Problematic] Exiting execute for {operation_name}")

    def _execute_db_operation_fixed(
        self, operation_name: str, operation, *args, **kwargs
    ):
        """Mimics the FIXED BaseManager logic - FLUSHES provided sessions."""
        self.logger.debug(f"[Fixed] Executing: {operation_name}")
        session, was_provided = self._get_session()
        self.logger.debug(
            f"[Fixed] Got session ID: {id(session)}, was_provided={was_provided}"
        )
        try:
            result = operation(session, *args, **kwargs)
            self.logger.debug(f"[Fixed] Operation {operation_name} successful")
            if not was_provided:
                self.logger.debug(
                    f"[Fixed] Committing internally created session ID: {id(session)}"
                )
                session.commit()
                self.logger.debug(
                    f"[Fixed] Commit finished for session ID: {id(session)}"
                )
            else:
                self.logger.debug(
                    f"[Fixed] Flushing provided session ID: {id(session)}"
                )
                session.flush()  # <-- Flush instead of commit for provided sessions
                self.logger.debug(
                    f"[Fixed] Flush finished for session ID: {id(session)}"
                )
            return result
        except Exception:
            self.logger.error(
                f"[Fixed] Error in {operation_name}, rolling back session ID: {id(session)}",
                exc_info=True,
            )
            session.rollback()
            raise
        finally:
            self.logger.debug(f"[Fixed] Exiting execute for {operation_name}")

    # --- Operations using the problematic executor ---
    def create_parent_problematic(self, name: str) -> Parent:
        def _create(session: Session):
            parent = Parent(name=name)
            self.logger.debug(f"[Problematic] Creating Parent object: {parent}")
            session.add(parent)
            # Flush needed here within the operation to get the ID before returning
            # Note: The problematic commit happens *after* this returns in _execute_db_operation_problematic
            session.flush()
            self.logger.debug(
                f"[Problematic] Flushed session {id(session)}, Parent has ID: {parent.id}"
            )
            return parent

        return self._execute_db_operation_problematic("create_parent", _create)

    def add_child_problematic(self, parent: Parent, child_name: str) -> Child:
        def _add(session: Session):
            # Important: Use the parent object passed in, which might be from the test's session context
            self.logger.debug(
                f"[Problematic] Adding child '{child_name}' to Parent: {parent}"
            )
            # We might need to ensure the parent is in *this* session state if it came from elsewhere
            # For simplicity, assume parent is already associated or merge handles it (though merge is tricky)
            # parent_in_session = session.merge(parent) # Using merge can add its own complexities
            # self.logger.debug(f"[Problematic] Parent merged into session {id(session)}: {parent_in_session}")

            child = Child(name=child_name, parent=parent)  # Use original parent passed
            self.logger.debug(f"[Problematic] Creating Child object: {child}")
            session.add(child)
            session.flush()
            self.logger.debug(
                f"[Problematic] Flushed session {id(session)}, Child has ID: {child.id}"
            )
            return child

        return self._execute_db_operation_problematic(
            "add_child", _add, parent, child_name
        )

    # --- Operations using the fixed executor ---
    def create_parent_fixed(self, name: str) -> Parent:
        def _create(session: Session):
            parent = Parent(name=name)
            self.logger.debug(f"[Fixed] Creating Parent object: {parent}")
            session.add(parent)
            session.flush()  # Flush is fine within the operation
            self.logger.debug(
                f"[Fixed] Flushed session {id(session)}, Parent has ID: {parent.id}"
            )
            return parent

        return self._execute_db_operation_fixed("create_parent", _create)

    def add_child_fixed(self, parent: Parent, child_name: str) -> Child:
        def _add(session: Session):
            self.logger.debug(
                f"[Fixed] Adding child '{child_name}' to Parent: {parent}"
            )
            # parent_in_session = session.merge(parent) # Avoid merge if possible
            # self.logger.debug(f"[Fixed] Parent merged into session {id(session)}: {parent_in_session}")
            child = Child(name=child_name, parent=parent)  # Use original parent
            self.logger.debug(f"[Fixed] Creating Child object: {child}")
            session.add(child)
            session.flush()  # Flush is fine
            self.logger.debug(
                f"[Fixed] Flushed session {id(session)}, Child has ID: {child.id}"
            )
            return child

        return self._execute_db_operation_fixed("add_child", _add, parent, child_name)


# --- Pytest Fixtures ---


@pytest.fixture(scope="function")
def test_engine():
    """Creates an in-memory SQLite engine for each test function."""
    logger.debug("[Fixture test_engine] Creating in-memory SQLite engine")
    engine = create_engine("sqlite:///:memory:", echo=False)  # echo=True for SQL logs
    Base.metadata.create_all(engine)
    yield engine
    logger.debug("[Fixture test_engine] Disposing engine")
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Provides a single session bound to the test's engine."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    logger.debug(f"[Fixture test_session] Created session ID: {id(session)}")
    try:
        yield session
        logger.debug(
            f"[Fixture test_session] Test finished, committing session ID: {id(session)}"
        )
        session.commit()  # Commit everything at the end of the test
    except Exception:
        logger.error(
            f"[Fixture test_session] Exception during test, rolling back session ID: {id(session)}"
        )
        session.rollback()
        raise
    finally:
        logger.debug(f"[Fixture test_session] Closing session ID: {id(session)}")
        session.close()


@pytest.fixture
def problematic_manager(test_session):
    """Provides a SimpleManager configured with the problematic executor."""
    logger.debug(
        f"[Fixture problematic_manager] Creating manager with session ID: {id(test_session)}"
    )
    return SimpleManager(session=test_session)


@pytest.fixture
def fixed_manager(test_session):
    """Provides a SimpleManager configured with the fixed executor."""
    logger.debug(
        f"[Fixture fixed_manager] Creating manager with session ID: {id(test_session)}"
    )
    return SimpleManager(session=test_session)


# --- Test Functions ---


def test_failure_with_intermediate_commit(
    problematic_manager: SimpleManager, test_session: Session
):
    """
    Demonstrates failure when intermediate commits expire object state.
    """
    logger.info("--- Starting test_failure_with_intermediate_commit ---")
    logger.debug(
        f"Test using problematic_manager (obj_id={id(problematic_manager)}) with session ID: {id(test_session)}"
    )

    # 1. Create Parent (calls problematic executor -> commits)
    parent = problematic_manager.create_parent_problematic("Parent A")
    logger.debug(f"Test received Parent: {parent}")
    parent_id = parent.id  # Store ID before potential expiry

    # 2. Add Child (calls problematic executor -> commits again)
    child = problematic_manager.add_child_problematic(parent, "Child 1")
    logger.debug(f"Test received Child: {child}")

    # 3. Fetch Parent again using the *same test session*
    # This simulates accessing the object later in the test flow.
    logger.debug(
        f"Test fetching Parent with ID {parent_id} using session ID: {id(test_session)}"
    )
    # Use session.get for fetching by PK
    fetched_parent = test_session.get(Parent, parent_id)
    logger.debug(f"Test fetched Parent: {fetched_parent}")

    assert fetched_parent is not None, "Parent should exist in the database"
    logger.debug(f"Object ID of initial parent: {id(parent)}")
    logger.debug(f"Object ID of fetched parent: {id(fetched_parent)}")
    # Note: The object IDs might be the same or different depending on session state after commit/expiry

    # 4. Attempt to access the relationship (lazy load)
    logger.debug(
        f"Test attempting to access fetched_parent.children on session ID: {id(test_session)}"
    )
    # This is where the error occurs because the intermediate commits likely expired
    # the state, and the lazy load fails on the potentially detached instance.
    with pytest.raises(DetachedInstanceError) as exc_info:
        children_count = len(fetched_parent.children)
        logger.debug(
            f"Accessed fetched_parent.children, count = {children_count}"
        )  # This line likely won't be reached

    logger.error(
        f"Successfully caught expected error: {exc_info.type.__name__} - {exc_info.value}"
    )
    # Check if it's the specific error you expect
    assert isinstance(exc_info.value, DetachedInstanceError), (
        f"Expected DetachedInstanceError, but got {exc_info.type.__name__}"
    )

    logger.info(
        "--- Finished test_failure_with_intermediate_commit (Expected Failure Caught) ---"
    )


def test_success_with_flush(fixed_manager: SimpleManager, test_session: Session):
    """
    Demonstrates success when intermediate operations only flush.
    """
    logger.info("--- Starting test_success_with_flush ---")
    logger.debug(
        f"Test using fixed_manager (obj_id={id(fixed_manager)}) with session ID: {id(test_session)}"
    )

    # 1. Create Parent (calls fixed executor -> flushes)
    parent = fixed_manager.create_parent_fixed("Parent B")
    logger.debug(f"Test received Parent: {parent}")
    parent_id = parent.id

    # 2. Add Child (calls fixed executor -> flushes again)
    child = fixed_manager.add_child_fixed(parent, "Child 2")
    logger.debug(f"Test received Child: {child}")

    # 3. Fetch Parent again using the *same test session*
    logger.debug(
        f"Test fetching Parent with ID {parent_id} using session ID: {id(test_session)}"
    )
    fetched_parent = test_session.get(Parent, parent_id)
    logger.debug(f"Test fetched Parent: {fetched_parent}")

    assert fetched_parent is not None, "Parent should exist in the database"
    logger.debug(f"Object ID of initial parent: {id(parent)}")
    logger.debug(f"Object ID of fetched parent: {id(fetched_parent)}")

    # 4. Attempt to access the relationship (lazy load)
    logger.debug(
        f"Test attempting to access fetched_parent.children on session ID: {id(test_session)}"
    )
    # This should succeed because the flush operations kept the objects live
    # within the single transaction managed by test_session.
    try:
        children_count = len(fetched_parent.children)
        logger.debug(f"Accessed fetched_parent.children, count = {children_count}")
        assert children_count == 1
        assert fetched_parent.children[0].name == "Child 2"
        logger.debug("Child relationship accessed successfully.")
    except (DetachedInstanceError, Exception) as e:
        logger.error(
            f"Caught unexpected error: {type(e).__name__} - {e}", exc_info=True
        )
        pytest.fail(f"Relationship access failed unexpectedly: {e}")

    logger.info("--- Finished test_success_with_flush (Expected Success) ---")
