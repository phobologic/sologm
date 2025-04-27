# Implementation Plan: Session Management Refactoring

**Version:** 1.0
**Date:** 2025-04-27
**Related TDD:** features/session_management/tdd.md

## Overview

This plan details the steps to refactor the database session management according to the design outlined in the TDD. The goal is to move to a consistent session handling pattern using `SessionContext` and ensure managers always operate with an explicitly provided session. This plan is structured incrementally to allow for verification at each stage.

**Note:** Expect tests to fail significantly after Phase 2 and Phase 4. The goal is to get them passing again incrementally during Phase 5. Commit frequently after completing each step successfully.

---

## Phase 1: Core Session Management Refactoring (One-time)

**Goal:** Modify the central `DatabaseManager` and `SessionContext` to use `sessionmaker` directly and handle the session lifecycle correctly. This phase involves changes to a single file (`sologm/database/session.py`).

*   **Step 1.1: Modify `DatabaseManager`**
    *   **File:** `sologm/database/session.py`
    *   **Action:**
        *   Change the `session` attribute from `scoped_session` to `sessionmaker`. Store the result of `sessionmaker(...)` here.
        *   Update the `__init__` method to create and store a `sessionmaker` instance instead of `scoped_session`.
        *   Remove the `get_session` method.
        *   Remove the `close_session` method.
    *   **Rationale:** Centralizes session creation configuration but removes the complexity of `scoped_session`.

*   **Step 1.2: Modify `SessionContext`**
    *   **File:** `sologm/database/session.py`
    *   **Action:**
        *   Update `__enter__`: Instead of `self._db.get_session()`, call `self._db.session()` (assuming `session` is now the `sessionmaker` instance) to create a new session.
        *   Update `__exit__`: Remove the call to `self._db.close_session()`. Ensure `self.session.close()` is called within a `finally` block *after* commit/rollback logic.
    *   **Rationale:** Makes `SessionContext` responsible for creating and closing the session it manages.

*   **Step 1.3: Remove Standalone `get_session()`**
    *   **File:** `sologm/database/session.py`
    *   **Action:** Delete the `get_session()` function entirely.
    *   **Rationale:** Enforces that sessions are only obtained via the `SessionContext`.

*   **Verification (Phase 1):**
    *   Run basic application commands that initialize the database (e.g., `sologm game list` on an empty DB). It should initialize without errors.
    *   Run `uv run pytest -v --log-cli-level=DEBUG`. Many tests will likely fail, especially those using the removed `get_session` or relying on the old `db_session` fixture behavior. Check that failures relate to session handling or manager instantiation.

---

## Phase 2: Adapt Base Manager (One-time)

**Goal:** Modify `BaseManager` to require a session upon initialization and remove its internal session/transaction handling logic. This phase involves changes to a single file (`sologm/core/base_manager.py`).

*   **Step 2.1: Change `BaseManager.__init__`**
    *   **File:** `sologm/core/base_manager.py`
    *   **Action:** Change the `session` parameter in `__init__` from `Optional[Session] = None` to `session: Session`. Update the docstring accordingly.
    *   **Rationale:** Enforces that all managers receive an active session when created.

*   **Step 2.2: Remove `BaseManager._get_session`**
    *   **File:** `sologm/core/base_manager.py`
    *   **Action:** Delete the `_get_session` method entirely.
    *   **Rationale:** Managers no longer fetch their own sessions.

*   **Step 2.3: Simplify `BaseManager._execute_db_operation`**
    *   **File:** `sologm/core/base_manager.py`
    *   **Action:**
        *   Remove the lines `session, should_close = self._get_session()`.
        *   Use `self._session` directly where `session` was used.
        *   Remove the `session.commit()` call.
        *   Remove the `session.rollback()` call. The method should now only contain the `try...except...raise` block around the `operation(self._session, ...)` call. Update logging messages.
    *   **Rationale:** Shifts transaction responsibility entirely to the `SessionContext`.

*   **Step 2.4: Update `BaseManager._lazy_init_manager`**
    *   **File:** `sologm/core/base_manager.py`
    *   **Action:** Ensure the line `kwargs["session"] = self._session` correctly passes the manager's session to the newly initialized manager. Verify the logging confirms the session ID propagation.
    *   **Rationale:** Ensures lazily loaded managers use the same session as their parent.

*   **Verification (Phase 2):**
    *   Run `uv run pytest -v --log-cli-level=DEBUG`. Expect widespread failures, particularly `TypeError`s where managers are instantiated without the required `session` argument (especially in `conftest.py` fixtures). This is expected.

---

## Phase 3: Introduce Manager Factory (One-time)

**Goal:** Create a helper function to simplify manager instantiation in tests. This phase involves creating one new file (`sologm/core/factory.py`).

*   **Step 3.1: Create `factory.py`**
    *   **File:** `sologm/core/factory.py`
    *   **Action:** Create this new file.
    *   **Rationale:** Provides a dedicated location for factory/helper functions within the core package.

*   **Step 3.2: Implement `create_all_managers`**
    *   **File:** `sologm/core/factory.py`
    *   **Action:**
        *   Add necessary imports (`Session`, `SimpleNamespace`, all manager classes).
        *   Define the function `create_all_managers(session: Session) -> SimpleNamespace`.
        *   Inside the function, instantiate each manager class in dependency order, passing the `session` and any required manager dependencies (e.g., `game_manager = GameManager(session=session)`, `act_manager = ActManager(session=session, game_manager=game_manager)`).
        *   Return a `SimpleNamespace` containing all created managers (e.g., `managers.game`, `managers.act`).
    *   **Rationale:** Creates the reusable helper function defined in the TDD.

*   **Verification (Phase 3):**
    *   Ensure `sologm/core/factory.py` has no syntax errors.
    *   You can add a temporary simple test (or use an interactive Python session) to import and call `create_all_managers` with a mock session to verify it runs without errors.

---

## Phase 4: Refactor Test Infrastructure (`conftest.py`) (One-time)

**Goal:** Update test fixtures to align with the new session management and manager instantiation patterns. This phase involves changes primarily to a single file (`sologm/tests/conftest.py`).

*   **Step 4.1: Remove `db_session` Fixture**
    *   **File:** `sologm/tests/conftest.py`
    *   **Action:** Delete the `db_session` fixture function.
    *   **Rationale:** This fixture is replaced by using `session_context`.

*   **Step 4.2: Remove Individual Manager Fixtures**
    *   **File:** `sologm/tests/conftest.py`
    *   **Action:** Delete all individual manager fixtures (`game_manager`, `act_manager`, `scene_manager`, `event_manager`, `dice_manager`, `oracle_manager`).
    *   **Rationale:** Managers will now be created within tests using the factory.

*   **Step 4.3: Update `database_manager` Fixture**
    *   **File:** `sologm/tests/conftest.py`
    *   **Action:** Review the `database_manager` fixture. Ensure it correctly instantiates the modified `DatabaseManager` (which now uses `sessionmaker`). No changes might be needed if it already passes the engine correctly.
    *   **Rationale:** Ensures the test database setup uses the refactored `DatabaseManager`.

*   **Step 4.4: Refactor Factory Fixtures (`create_test_*`)**
    *   **File:** `sologm/tests/conftest.py`
    *   **Action:** For *each* `create_test_*` fixture:
        *   Add `session: Session` as the first parameter to the inner factory function (`_create_*`).
        *   Remove any injection of `db_session` or manager fixtures into the main fixture signature.
        *   Inside the inner factory function, before calling the manager method: Instantiate the required manager(s) directly using the passed `session` (e.g., `game_manager = GameManager(session=session)`) OR call `managers = create_all_managers(session)` and use `managers.<name>`.
        *   Call the appropriate manager method (e.g., `game = game_manager.create_game(...)`).
        *   Remove any `db_session.merge(obj)` calls. The object returned by the manager is already bound to the correct session.
        *   If relationships need to be loaded for subsequent test steps, add `session.refresh(obj, attribute_names=[...])` using the *passed-in* `session`.
        *   Return the object `obj`.
    *   **Rationale:** Aligns test data creation with the new pattern, ensuring objects are created and managed within the test's specific session context.

*   **Step 4.5: Refactor/Remove Object Fixtures (`test_game`, etc.)**
    *   **File:** `sologm/tests/conftest.py`
    *   **Action:**
        *   Review fixtures like `test_game`, `test_act`, `test_scene`, `test_events`, etc.
        *   Option 1 (Preferred): Delete these fixtures. Tests should explicitly create the exact data they need using the refactored `create_test_*` factories within their `session_context` block.
        *   Option 2 (If complex setup is truly reusable): Refactor them similarly to the factory fixtures, ensuring they accept the `session`, use factories, and perform refreshes within that session. Avoid `merge`.
    *   **Rationale:** Promotes clearer, self-contained tests and avoids detached instance issues caused by fixtures creating objects outside the test function's session context.

*   **Verification (Phase 4):**
    *   Run `uv run pytest -v --log-cli-level=DEBUG`. Expect a very large number of failures due to removed fixtures and changed signatures.
    *   Check that `pytest --fixtures` shows the updated list (no `db_session`, no manager fixtures).
    *   Ensure `sologm/tests/conftest.py` itself loads without syntax errors.

---

## Phase 5: Refactor Individual Test Files (Iterative)

**Goal:** Update all test files to use the new session context, manager factory, and refactored data factories. This phase is **iterative** and will involve modifying multiple test files (e.g., `test_game.py`, `test_act.py`, `test_scene.py`, `test_event.py`, etc.).

*   **Step 5.1: Choose a Test Module**
    *   **Action:** Select one test file to start with (e.g., `sologm/core/tests/test_game.py`).
    *   **Rationale:** Work module by module to manage complexity.

*   **Step 5.2: Refactor Test Functions**
    *   **File:** The chosen test module (e.g., `sologm/core/tests/test_game.py`)
    *   **Action:** For *each* test function within the module:
        *   Ensure the test function signature includes `session_context` (if not already present). Remove any direct requests for manager fixtures or `db_session`.
        *   Wrap the main body of the test logic within `with session_context as session:`.
        *   Inside the `with` block, add `from sologm.core.factory import create_all_managers` (if not already imported).
        *   Inside the `with` block, call `managers = create_all_managers(session)`.
        *   Replace any usage of old manager fixtures (e.g., `game_manager.create_game`) with calls via the factory result (e.g., `managers.game.create_game`).
        *   Update all calls to `create_test_*` factory fixtures to pass the `session` as the first argument (e.g., `game = create_test_game(session, name="My Game")`).
        *   If the test used object fixtures (like `test_game`), replace that usage by calling the appropriate `create_test_*` factory inside the `with` block instead.
        *   Ensure assertions that check database state use the `session` from the context (e.g., `retrieved = session.get(Game, game.id)`).
    *   **Rationale:** Applies the new pattern consistently to each test.

*   **Step 5.3: Verify Module Tests**
    *   **Action:** Run pytest specifically for the modified module (e.g., `uv run pytest -v --log-cli-level=DEBUG sologm/core/tests/test_game.py`).
    *   **Action:** Debug and fix any errors within the module until all its tests pass. Pay attention to `AttributeError` (removed fixtures), `TypeError` (missing `session` argument), and potential issues with relationship loading (may require adding `session.refresh` in factory fixtures or the test itself).
    *   **Rationale:** Ensures each module is fully refactored and working before moving on.

*   **Step 5.4: Repeat for All Test Modules**
    *   **Action:** Repeat steps 5.1-5.3 for all other test modules (`test_act.py`, `test_scene.py`, `test_event.py`, `test_dice.py`, `test_oracle.py`, CLI tests, etc.).
    *   **Rationale:** Completes the test refactoring across the entire suite.

*   **Verification (Phase 5):**
    *   The number of passing tests should increase as each module is refactored.
    *   The original problematic test (`test_add_event_with_active_scene`) should pass once `test_event.py` is correctly refactored.
    *   Eventually, `uv run pytest -v --log-cli-level=DEBUG` should show all tests passing.

---

## Phase 6: Final Cleanup and Review (One-time)

**Goal:** Tidy up the codebase and ensure documentation is consistent.

*   **Step 6.1: Remove Comments**
    *   **Action:** Search for and remove any commented-out code related to the old session management or fixtures.
    *   **Rationale:** Code hygiene.

*   **Step 6.2: Update Docstrings**
    *   **Action:** Review and update docstrings for modified classes and functions (`DatabaseManager`, `SessionContext`, `BaseManager`, `create_all_managers`, refactored fixtures in `conftest.py`).
    *   **Rationale:** Keep documentation accurate.

*   **Step 6.3: Run Linters/Formatters**
    *   **Action:** Run `ruff format` and any other configured linters.
    *   **Rationale:** Ensure code style consistency.

*   **Step 6.4: Review TDD**
    *   **Action:** Read through `features/session_management/tdd.md` and compare it against the final implemented code. Ensure the solution matches the design.
    *   **Rationale:** Final design verification.

*   **Verification (Phase 6):**
    *   Clean codebase.
    *   All tests passing.
    *   Manual testing of key CLI commands confirms functionality.

---
