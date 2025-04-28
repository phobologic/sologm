# TDD: Pluggable Renderers & Plain Text Output Mode

**Version:** 1.0
**Status:** Proposed
**Date:** 2025-04-20
**Author:** Senior Software Developer

## 1. Introduction

This document outlines the technical design for implementing a pluggable renderer system in SoloGM, enabling a switch between the default Rich-based UI and a standard Markdown output format. This design follows the requirements specified in `features/renderers/prd.md` and utilizes the Strategy pattern for a clean and extensible implementation.

## 2. Goals

*   Implement a `Renderer` strategy pattern to decouple display logic from command logic.
*   Create two concrete renderer implementations: `RichRenderer` (using existing Rich components) and `MarkdownRenderer` (generating standard Markdown).
*   Introduce a global `--no-ui` command-line flag to select the `MarkdownRenderer`.
*   Inject the selected renderer instance into command functions for use.
*   Refactor all user-facing display logic within CLI commands to utilize the injected renderer instance.
*   Ensure the Markdown output is clear, valid, and informationally equivalent to the Rich output where feasible.
*   Handle error message display through the selected renderer.

## 3. Proposed Solution: Strategy Pattern

The core of the solution is the Strategy pattern:

1.  **Renderer Interface (`ABC`):** Define an abstract base class `Renderer` in `sologm.cli.rendering.base` that specifies the contract for all rendering operations (e.g., displaying game details, lists, errors).
2.  **Concrete Strategies:**
    *   `RichRenderer`: Implements the `Renderer` interface using `rich.panel.Panel`, `rich.table.Table`, `sologm.cli.utils.styled_text.StyledText`, etc. This will encapsulate most of the existing display logic from `sologm.cli.utils.display`.
    *   `MarkdownRenderer`: Implements the `Renderer` interface by constructing Markdown strings and printing them to the console. It will prioritize standard Markdown syntax (CommonMark).
3.  **Context/Client:** The CLI command functions act as the clients. They will receive the selected `Renderer` instance.
4.  **Strategy Selection:** The main application entry point (`sologm.cli.main.main`) will inspect the `--no-ui` flag and instantiate the appropriate `Renderer` (`RichRenderer` or `MarkdownRenderer`).
5.  **Dependency Injection:** The selected `Renderer` instance will be passed to the command functions. Using Typer's context object (`ctx.obj`) is the recommended approach for clean injection.

## 4. Detailed Design

### 4.1. Code Structure

The existing directory `sologm/cli/rendering/` will house the renderer implementations:

```
sologm/
├── cli/
│   ├── rendering/
│   │   ├── __init__.py
│   │   ├── base.py         # Renderer ABC definition
│   │   ├── rich_renderer.py  # RichRenderer implementation
│   │   └── markdown_renderer.py # MarkdownRenderer implementation
│   ├── main.py         # Flag definition, renderer selection/injection
│   ├── game.py         # Refactored commands using renderer
│   ├── act.py          # Refactored commands using renderer
│   ├── scene.py        # Refactored commands using renderer
│   ├── event.py        # Refactored commands using renderer
│   │   └── ...         # Other command modules
│   └── utils/
│       ├── display.py      # Refactored: logic moved to RichRenderer, helpers remain/move
│       ├── markdown.py     # Potentially reusable helpers for MarkdownRenderer
│       └── styled_text.py  # Used by RichRenderer
│       └── ...
└── ...
```

### 4.2. Renderer Interface (`sologm/cli/rendering/base.py`)

The existing Abstract Base Class `Renderer` defines the methods required for displaying different kinds of application output. Both renderers must implement these methods.

```python
# Key aspects of the existing base.py:
import abc
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from rich.console import Console

# Import necessary models and potentially manager types for type hinting
from sologm.models.act import Act
# ... other model imports ...

if TYPE_CHECKING:
    from sologm.core.oracle import OracleManager
    from sologm.core.scene import SceneManager


class Renderer(abc.ABC):
    """
    Abstract base class for different output renderers (e.g., Rich, Markdown).
    Defines the interface for all display operations within the CLI.
    """

    def __init__(self, console: Console, markdown_mode: bool = False):
        self.console = console
        self.markdown_mode = markdown_mode

    @abc.abstractmethod
    def display_dice_roll(self, roll: 'DiceRoll') -> None: ...

    @abc.abstractmethod
    def display_interpretation(self, interp: 'Interpretation', ...) -> None: ...

    @abc.abstractmethod
    def display_events_table(self, events: List['Event'], ...) -> None: ...

    @abc.abstractmethod
    def display_games_table(self, games: List['Game'], ...) -> None: ...

    # ... signatures for all other required display methods ...

    @abc.abstractmethod
    def display_error(self, message: str) -> None: ...

    # Note: The actual base.py provided contains a comprehensive list
    # of required abstract methods.
```

### 4.3. Rich Renderer (`sologm/cli/rendering/rich_renderer.py`)

This class implements the `Renderer` interface using Rich components.

*   **Initialization:** Takes a `rich.console.Console` instance.
*   **Implementation:**
    *   Implements each method from the `Renderer` ABC.
    *   Contains the logic moved from the original `sologm.cli.utils.display.py`.
    *   Utilizes Rich components (`Panel`, `Table`, `Text`, `Layout`, etc.).
    *   Uses `sologm.cli.utils.styled_text.StyledText` and `BORDER_STYLES`.
    *   Uses helpers like `truncate_text` and `StyledText.format_metadata`.
    *   Outputs via `self.console.print(...)`.
    *   *Needs completion:* Implement methods currently marked `NotImplementedError` (e.g., `display_act_completion_success`, `display_act_ai_feedback_prompt`).

```python
# Example Snippet (Structure from provided file)
from rich.console import Console
from rich.panel import Panel
# ... other rich imports

from sologm.models import Game # etc.
from sologm.cli.utils.styled_text import StyledText, BORDER_STYLES
from sologm.cli.utils.display import truncate_text # Keep useful helpers

# Corrected import based on file structure
from .base import Renderer

class RichRenderer(Renderer): # Inherits from Renderer
    # ... __init__ ...

    def display_game_info(self, game: 'Game', active_scene: Optional['Scene'] = None) -> None:
        # --- Logic moved from original display_game_info function ---
        st = StyledText
        # ... construct title, content, metadata using st ...
        panel = Panel(
            # content,
            title=panel_title,
            border_style=BORDER_STYLES["game_info"],
            title_align="left",
        )
        self.console.print(panel)
        # --- End of moved logic ---

    def display_error(self, message: str) -> None:
        # Use a styled Panel for errors
        self.console.print(f"[red]Error: {message}[/red]") # As currently implemented

    # ... Implement ALL methods from Renderer ABC ...
    # ... including those currently marked NotImplementedError ...
```

### 4.4. Markdown Renderer (`sologm/cli/rendering/markdown_renderer.py`)

This class implements the `Renderer` interface by generating Markdown text.

*   **Initialization:** Takes a `rich.console.Console` instance.
*   **Implementation:**
    *   Implements each method from the `Renderer` ABC.
    *   Constructs strings containing standard Markdown syntax.
    *   Prioritizes semantic structure and readability.
    *   Formats tabular data using Markdown tables or lists.
    *   Uses helpers like `truncate_text`.
    *   Outputs via `self.console.print(...)`.
    *   *Needs completion:* Implement `display_game_status`.

```python
# Example Snippet (Structure from provided file)
from rich.console import Console

from sologm.models import Game # etc.
from sologm.cli.utils.display import truncate_text # Keep useful helpers
from sologm.utils.datetime_utils import format_datetime
# from ._markdown_helpers import _format_markdown_table # Example helper

from .base import Renderer

class MarkdownRenderer(Renderer): # Inherits from Renderer
    # ... __init__ ...

    def display_game_info(self, game: 'Game', active_scene: Optional['Scene'] = None) -> None:
        output_lines = []
        output_lines.append(f"## {game.name} (`{game.slug}` / `{game.id}`)")
        # ... construct rest of Markdown output ...
        self.console.print("\n".join(output_lines))

    def display_error(self, message: str) -> None:
        # Use blockquotes or code blocks for errors
        self.console.print(f"> **Error:** {message}") # As currently implemented

    def display_game_status(self, ...) -> None:
        raise NotImplementedError # Needs implementation

    # ... Implement ALL methods from Renderer ABC ...
```

### 4.5. CLI Flag and Renderer Injection (`sologm/cli/main.py`)

Modify the main Typer application setup (Requires editing `sologm/cli/main.py`).

1.  **Add Flag:** Define the `--no-ui` boolean option in the `main` callback.
2.  **Instantiate Console:** Ensure a single `rich.console.Console` instance is created.
3.  **Select Renderer:** Based on `no_ui`, instantiate `RichRenderer(console)` or `MarkdownRenderer(console)`.
4.  **Inject Renderer:** Store the chosen renderer onto `ctx.obj`.

```python
# Conceptual Snippet for main.py (Needs implementation in the actual file)
import typer
from rich.console import Console
# from typing import Dict, Any # Or a dedicated context class

# Import Renderers
from .rendering.base import Renderer
from .rendering.rich_renderer import RichRenderer
from .rendering.markdown_renderer import MarkdownRenderer

# ... other imports ...

app = typer.Typer(...)
console = Console() # Shared console

# Optional: Define a context object structure
class AppContext:
    def __init__(self, renderer: Renderer):
        self.renderer = renderer

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    # ... other global options ...
    no_ui: bool = typer.Option(
        False, "--no-ui", help="Disable rich UI and use plain Markdown output.",
    ),
) -> None:
    # ... version handling ...

    # --- Renderer Selection and Injection ---
    renderer_instance: Renderer
    if no_ui:
        renderer_instance = MarkdownRenderer(console=console)
    else:
        renderer_instance = RichRenderer(console=console)

    # Inject using ctx.obj
    ctx.obj = AppContext(renderer=renderer_instance) # Or use a dict: {'renderer': renderer_instance}

    # ... rest of main function ...
    # Ensure early errors use the injected renderer
    # try: # db init
    # except Exception as e:
    #    ctx.obj.renderer.display_error(str(e)) # Use str(e) as display_error expects string
    #    raise typer.Exit(1)

# ... register subcommands ...
```

### 4.6. Refactoring Command Functions (e.g., `sologm/cli/game.py`)

Update all CLI command functions producing output (Requires editing `sologm/cli/game.py`, `act.py`, etc.).

1.  Add `ctx: typer.Context` parameter.
2.  Retrieve renderer: `renderer = ctx.obj.renderer`.
3.  Replace display calls (e.g., `display_game_info(game)`) with renderer calls (e.g., `renderer.display_game_info(game)`).
4.  Replace direct error/success printing with `renderer.display_error(str(e))`, `renderer.display_success(...)`, etc.

```python
# Conceptual Snippet for game.py command (Needs implementation in the actual file)
import typer
# from typing import cast # If using dict for ctx.obj
# from .main import AppContext # If using class for ctx.obj

# No direct display imports needed

@game_app.command("info")
def game_info(ctx: typer.Context): # Removed game_id assuming it gets active game
    renderer: Renderer = ctx.obj.renderer # Get renderer

    try:
        # ... (get game data using managers and get_db_context) ...
        # game = manager.get_active_game(...)
        if game:
            renderer.display_game_info(game, active_scene) # Use renderer method
        else:
            renderer.display_warning("No active game found.") # Use renderer method
    except Exception as e:
        renderer.display_error(str(e)) # Use renderer method with string message
        raise typer.Exit(code=1)
```

### 4.7. Markdown Formatting Guidelines (`MarkdownRenderer`)

*   **Structure:** Use headings (`#`, `##`), lists (`*`, `1.`), rules (`---`).
*   **Clarity:** Prioritize clear information transfer.
*   **Tables:** Use Markdown pipe tables for lists; fallback to lists if tables are complex. Use `truncate_text`.
*   **Emphasis:** Use `**bold**` for titles, labels; `*italics*` for notes.
*   **Code:** Use backticks (`) for IDs, counts; triple backticks (``` ```) for errors.
*   **Blockquotes:** Use `>` for errors or generated content.
*   **Consistency:** Apply rules uniformly.

### 4.8. Error Handling

Route all user-visible errors caught in CLI commands through `renderer.display_error(str(error))`. Ensure commands `raise typer.Exit(code=1)` after displaying errors.

## 5. Implementation Steps Summary

1.  **Complete Renderer Methods:** Implement remaining `NotImplementedError` methods in `RichRenderer` and `MarkdownRenderer`.
2.  **Implement `main.py` Changes:** Add the `--no-ui` flag, renderer selection logic, and context injection.
3.  **Refactor Command Files:** Systematically update all command functions in `cli/*.py` to use the injected renderer via `ctx`.
4.  **Test:** Thoroughly test all commands with and without the `--no-ui` flag.
5.  **Documentation:** Update user/developer docs.

## 6. Future Considerations

*   **Extensibility:** Easily add `JsonRenderer`, `YamlRenderer`, etc.
*   **Configuration:** Allow renderer selection via config file.
*   **Testing:** Mock the `Renderer` interface in command tests.

## 7. Open Questions / Risks

*   **Markdown Equivalence:** Ensuring Markdown conveys the same essential info as complex Rich layouts requires careful design. Simplification might be needed.
*   **Refactoring Scope:** Refactoring all commands is a significant task requiring careful execution.
*   **Helper Scope:** Finalize location/scope of shared helpers (`truncate_text`, etc.).
