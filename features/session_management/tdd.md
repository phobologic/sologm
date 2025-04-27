# Technical Design Document: Session Management Refactoring

**Version:** 1.0
**Date:** 2025-04-27
**Author:** AI Assistant

## 1. Introduction

This document outlines the design for refactoring the database session management within the SoloGM application. The current approach has led to complexities and inconsistencies, particularly in the testing environment, resulting in errors like `DetachedInstanceError` and unexpected state mismatches. The goal is to establish a single, clear, and robust pattern for handling database sessions and transactions throughout the application and its tests.

## 2. Problem Statement

The existing session management suffers from several issues:

*   **Multiple Session Sources:** Sessions can originate from different places:
    *   The `db_session` pytest fixture.
    *   The `session_context` pytest fixture (using `get_db_context`).
    *   The `BaseManager._get_session` method attempting to use an injected session or fetch from a singleton `scoped_session`.
*   **Inconsistent Lifecycles:** The lifecycle (creation, commit/rollback, close) of sessions obtained through these different sources is managed differently, leading to confusion and errors.
*   **Testing Complexity:** Test fixtures often inject sessions (`db_session`) or use `session.merge()`, bypassing manager logic and making it hard to ensure managers and test assertions operate on the same session state. This causes tests to fail unexpectedly (e.g., not finding an "active" entity that was just created).
*   **`scoped_session` Overhead:** The use of `scoped_session` adds complexity (thread-local management, `.remove()` requirement) that isn't strictly necessary for a single-threaded CLI application where the scope is typically the entire command execution.

## 3. Goals

*   Establish a single, unambiguous source and lifecycle management pattern for database sessions.
*   Ensure managers are always provided with an active session and do not manage session creation or transaction boundaries themselves.
*   Simplify the `BaseManager` by removing session fetching and transaction logic.
*   Make the test environment accurately reflect the application's session handling pattern.
*   Eliminate session-related errors like `DetachedInstanceError` and state inconsistencies in tests.
*   Improve the overall clarity, maintainability, and testability of database interactions.

## 4. Proposed Solution

The core idea is to centralize session lifecycle and transaction control within the `SessionContext` context manager and make all other components (managers, test helpers) dependent on receiving an active session from this context.

**Key Components:**

1.  **`SessionContext` (via `get_db_context`)**:
    *   Becomes the **sole entry point** for obtaining and managing a session for a unit of work (CLI command, test function).
    *   Uses a standard `sessionmaker` (configured by `DatabaseManager`) to create a *new* session upon entering the `with` block (`__enter__`).
    *   Handles the final `commit()` or `rollback()` upon exiting the block (`__exit__`).
    *   Ensures the session is always closed (`session.close()`) upon exit, regardless of success or failure.

2.  **`DatabaseManager`**:
    *   Simplified role: Holds the engine configuration and the `sessionmaker` factory.
    *   No longer uses `scoped_session`.
    *   No longer provides `get_session` or `close_session` methods.

3.  **`BaseManager`**:
    *   Requires an active `Session` instance passed to its `__init__` method.
    *   Removes the `_get_session` method.
    *   `_execute_db_operation` method is simplified: it executes the given operation function using the manager's `self._session` but **does not** handle commit/rollback.

4.  **Manager Factory (`sologm/core/factory.py`)**:
    *   A new helper function `create_all_managers(session: Session)` will be introduced.
    *   This function takes an active session, imports all core manager classes, instantiates them (passing the session and resolving dependencies), and returns them bundled (e.g., in a `SimpleNamespace`).
    *   This primarily serves to reduce boilerplate in test setup but could potentially be used in complex application logic if needed.

5.  **Test Environment**:
    *   Tests will exclusively use `with session_context as session:` (obtained via the `session_context` fixture).
    *   Inside the `with` block, tests will call `managers = create_all_managers(session)` to get manager instances.
    *   Test data setup will use refactored factory fixtures (`create_test_*`) which accept the `session` argument and operate within that session.
    *   The `db_session` fixture and individual manager fixtures in `conftest.py` will be removed.

## 5. Implementation Details

*   **`sologm/database/session.py`**: Refactor `DatabaseManager` and `SessionContext` as described above. Remove `get_session()`.
*   **`sologm/core/base_manager.py`**: Refactor `__init__` and `_execute_db_operation`. Remove `_get_session`.
*   **`sologm/core/factory.py`**: Create the new file and implement `create_all_managers(session)`.
*   **`sologm/tests/conftest.py`**: Remove `db_session` and manager fixtures. Update `database_manager`. Refactor factory fixtures (`create_test_*`) to accept and use the `session`.
*   **`sologm/**/*.py` (CLI Commands)**: No changes expected, as they should already follow the `with get_db_context() as session: manager = Manager(session=session)` pattern.
*   **`sologm/**/tests/*.py`**: Refactor all tests to use the `session_context` fixture, call `create_all_managers(session)`, and use the refactored factory fixtures, passing the `session`.

## 6. Benefits

*   **Consistency:** Uniform session handling across the application and tests.
*   **Simplicity:** Easier-to-understand session lifecycle and transaction management. Reduced complexity in `BaseManager` and test fixtures.
*   **Reliability:** Eliminates a class of common ORM errors related to detached instances and session state.
*   **Testability:** Tests become more robust, easier to write, and more accurately reflect application behavior.
*   **Maintainability:** Code involving database interactions becomes cleaner and less prone to session-related bugs.

## 7. Risks and Mitigation

*   **Refactoring Effort:** Significant changes required, especially in test setup (`conftest.py` and individual test files). Mitigation: Perform changes incrementally, ensuring tests pass after each major step.
*   **Potential Performance Impact (Negligible):** Eagerly creating all managers via `create_all_managers` in tests might seem less efficient than lazy loading, but the overhead is expected to be minimal in a test context and outweighed by the gains in correctness and simplicity.

## 8. Alternatives Considered

*   **Keeping `scoped_session`:** Rejected due to unnecessary complexity for the CLI use case and being a source of confusion.
*   **Manager Fixtures with Session Injection:** Attempted previously, but led to complex fixture dependencies and did not fully resolve session mismatch issues.
*   **Test Helper Fixture vs. Plain Function:** A plain function (`create_all_managers`) was chosen over a fixture factory for simplicity and explicitness, placed in `core/factory.py` for potential reuse.
