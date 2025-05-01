# Code Style Conventions

This document outlines the Python code style and documentation conventions for this project. Consistency is key for readability and maintainability.

## 1. Formatting & Layout

-   **Indentation:** Use 4 spaces per indentation level. No tabs.
-   **Line Length:** Limit lines to a maximum of 88 characters.
-   **Quotes:** Prefer double quotes (`"`) for strings. Use single quotes (`'`) consistently when needed (e.g., within double-quoted strings or for brevity in simple cases).
-   **Whitespace:**
    -   Use consistent whitespace around operators (`=`, `+`, `-`, `*`, `/`, `==`, etc.) and after commas.
    -   Use single blank lines to separate logical code blocks within functions/methods.
    -   Use two blank lines between top-level functions and class definitions.
-   **Trailing Commas:** Use trailing commas on the final item in multi-line lists, dictionaries, tuples, and function arguments/parameters.
-   **Comments:**
    - Comment on "why" not "what"
    - Use docstrings for functions and modules
    - Keep implementation comments rare and valuable
    - Remove commented-out code
    - Update comments when updating code

## 2. Imports

-   **Grouping:** Group imports in this specific order, separated by a blank line:
    1.  Standard library imports (e.g., `os`, `sys`, `datetime`).
    2.  Third-party library imports (e.g., `sqlalchemy`, `typer`, `rich`).
    3.  Local application/library imports (relative or absolute imports from within this project).
-   **Sorting:** Sort imports alphabetically within each group.

## 3. Naming (PEP 8)

-   **Variables, Functions, Methods, Modules, Packages:** Use `snake_case` (lowercase words separated by underscores). Example: `calculate_total`, `user_session`.
-   **Classes:** Use `PascalCase` (capitalize the first letter of each word). Example: `GameManager`, `DatabaseSession`.
-   **Constants:** Use `UPPER_SNAKE_CASE` (uppercase words separated by underscores). Example: `MAX_RETRIES`, `DEFAULT_TIMEOUT`.

## 4. Docstrings (Google Style - PEP 257)

-   Write docstrings using triple double quotes (`"""Docstring goes here."""`) for all public modules, classes, functions, and methods.
-   **Content:** Clearly describe *what* the object/function does.
-   **Sections:** Use standard sections like `Args:`, `Returns:`, and `Raises:` to document parameters, return values, and exceptions, respectively. Describe each item clearly.
    ```python
    def example_function(param1: str, param2: int) -> bool:
        """This is a summary line describing the function's purpose.

        This is a more detailed explanation if needed.

        Args:
            param1: Description of the first parameter.
            param2: Description of the second parameter.

        Returns:
            True if successful, False otherwise.

        Raises:
            ValueError: If param1 is invalid.
    """
    ```
-   **Overridden Methods:** For methods that override a base class method without changing functionality or signature significantly, use `"""See base class."""` as the docstring.

## 5. Comments

-   Use inline comments (`#`) sparingly.
-   Explain the *why* behind complex or non-obvious code, not *what* the code is doing (the code itself should explain the "what").
-   Keep comments accurate and up-to-date as the code evolves.
-   **No Temporary or Change History Comments:** 
    -   Do not add comments such as "TODO", "FIXME", "Refactor this later", or similar markers for future work directly in the code.
    -   Do not include comments describing past changes like "Removed method XXX in refactor." Use version control history for tracking changes.
    -   If you see something that needs improvement, share that in the chat output, rather than adding it as comments.
    -   This prevents the codebase from accumulating "comment debt" that rarely gets addressed and keeps the focus on current code rather than its history.
    -   *Examples of what NOT to do:* 
        -   `# TODO: This is inefficient, needs refactoring`
        -   `# Removed UserManager.authenticate() in authentication refactor`

## 6. Type Hinting (PEP 484+)

-   Add type hints to function and method signatures for all arguments and the return type.
-   Use type hints for significant variable assignments where the type isn't immediately obvious.
-   Example: `def get_user(user_id: str) -> Optional[User]:`

## 7. Logging

-   Use the standard `logging` module. Create a module-level logger: `logger = logging.getLogger(__name__)`.
-   **Levels:** Use appropriate logging levels:
    -   `DEBUG`: Detailed information, typically of interest only when diagnosing problems.
    -   `INFO`: Confirmation that things are working as expected.
    -   `WARNING`: An indication that something unexpected happened, or indicative of some problem in the near future (e.g., ‘disk space low’). The software is still working as expected.
    -   `ERROR`: Due to a more serious problem, the software has not been able to perform some function.
    -   `CRITICAL`: A serious error, indicating that the program itself may be unable to continue running.
-   **Messages:** Write clear, concise, and informative log messages. Include relevant context (e.g., IDs, operation names).
    -   *Good:* `logger.info("Processing order %s for user %s", order_id, user_id)`
    -   *Bad:* `logger.error("Something went wrong!")`
-   **Security:** **Never** log sensitive information like passwords, API keys, or personally identifiable information (PII).
-   **Avoid `print()`:** Do not use `print()` for debugging or informational output in library or application code. Use the logger.

## 8. Function & Method Length (Single Responsibility Principle)

-   **Conciseness:** Strive to keep functions and methods short and focused.
-   **Single Responsibility:** Each function/method should ideally do *one thing* and do it well. If a function performs multiple distinct steps, consider refactoring it into smaller, helper functions.
-   **Readability:** Shorter functions are generally easier to read, understand, test, and maintain.
-   **Guideline, Not Hard Rule:** There's no strict line limit, but if a function exceeds roughly 20-30 lines (excluding docstrings/comments/blank lines), critically evaluate if it can be broken down logically. Use judgment – sometimes slightly longer is clearer than excessive fragmentation.

## 9. General Principles

-   **Readability:** Write code that is easy for humans to understand. Prefer clarity over cleverness.
-   **Consistency:** Apply these conventions uniformly across the entire codebase.
