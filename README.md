# Solo RPG Helper CLI

A command-line application designed to assist players of solo or GM-less roleplaying games by tracking game scenes, providing dice rolling functionality, and leveraging AI to help interpret "oracle" results.

![Example output of the sologm game status command](sologm_game_status.png)

*Example output of the `sologm game status` command, showing the current state of an active game.*

## Features

- **Game Management**: Create, list, activate, edit, and export games to organize your solo RPG sessions. View game status.
- **Act Management**: Organize your game into narrative acts. Create, list, view, edit, and complete acts. AI can optionally summarize completed acts.
- **Scene Tracking**: Create scenes within acts, mark them as complete, edit them, and track the current active scene.
- **Event Recording**: Log important events that occur during gameplay, associating them with scenes. Edit existing events and manage event sources.
- **Dice Rolling**: Roll dice using standard notation (e.g., 2d6+1) with optional reasons and scene association. View roll history.
- **Oracle Interpretation**: Use AI (e.g., Claude) to interpret oracle results in the context of your game. Manage interpretation sets, retry interpretations, and select interpretations to become events.

## Core Concepts

SoloGM organizes your solo roleplaying sessions using a hierarchical structure:

*   **Game:** The top-level container representing a single campaign or long-running adventure. You typically have one *active* game at a time.
    *   **Act:** A major narrative division within a Game, similar to an act in a play or a chapter in a book. A Game can have multiple Acts. You usually have one *active* act within the active game.
        *   **Scene:** A specific situation, location, or encounter within an Act. An Act can have multiple Scenes. Most actions (like recording events or rolling dice) happen within the context of the *current* scene.
            *   **Event:** A record of something significant that happened during a Scene (e.g., "Found a clue," "NPC interaction," "Combat outcome"). Scenes can have many Events.
            *   **Dice Roll:** A record of a dice roll made during a Scene, including the notation, result, and optional reason. Scenes can have many Dice Rolls.
            *   **Interpretation Set:** A collection of AI-generated interpretations based on an oracle query (context + results) made during a Scene. Scenes can have multiple Interpretation Sets.
                *   **Interpretation:** A single AI-generated suggestion within an Interpretation Set. You can *select* an Interpretation to automatically create a new Event in the Scene.

Understanding this hierarchy helps clarify why certain commands require an active game, act, or scene. For example, `sologm event add` needs to know the *current scene* to associate the event correctly. Commands like `sologm game activate`, `sologm act create` (which activates the new act), and `sologm scene set-current` are used to manage this context.

## AI-Powered Features

SoloGM integrates AI (currently Anthropic's Claude) to assist your creative process and streamline game management. Using these features requires configuring an API key (see [Configuration](#configuration)).

### Oracle Interpretation (`sologm oracle interpret`)

*   **Purpose:** Helps turn abstract oracle results (like keywords, dice results, or card draws) into concrete narrative events or answers relevant to your game's situation.
*   **How it Works:** When you provide a question/context (`--context`) and the oracle's raw result (`--results`), the command sends this information, along with details about the current scene (description, recent events), to the AI. The AI generates multiple possible interpretations (controlled by `--count`).
*   **Interaction:** You can review the generated interpretations. The `sologm oracle select` command allows you to choose one interpretation, optionally edit it, and add it directly as a new Event in the current scene. `sologm oracle retry` lets you request new interpretations, potentially refining the context first (`--edit`).
*   **Benefit:** Overcomes creative blocks and helps weave abstract prompts seamlessly into your ongoing narrative.

### Act Completion Summarization (`sologm act complete --ai`)

*   **Purpose:** Automatically generates a concise title and a narrative summary for an entire Act when you mark it as complete.
*   **How it Works:** When invoked with the `--ai` flag, the command gathers the details of all Scenes and Events within the Act being completed. This data, potentially augmented by your specific instructions (`--context`), is sent to the AI with a request to synthesize a title and summary capturing the Act's key developments and story arc.
*   **Interaction:** The AI-generated title and summary are presented to you. You then enter an interactive loop where you can:
    *   **Accept (A):** Use the generated content as is.
    *   **Edit (E):** Modify the generated title and/or summary in your text editor.
    *   **Regenerate (R):** Ask the AI to try again, optionally providing specific feedback on what to change or keep.
*   **Benefit:** Saves significant time compared to manually reviewing all act content. Provides a consistent narrative summary, useful for tracking the story's progression and for later review (e.g., using `sologm game dump`).

*Note: The AI acts as a creative assistant and summarizer; it does not make decisions or play the game for you.*

### Using Game Data with External AI

The `sologm game dump` command outputs your game's structure (acts, scenes, events) in a clean markdown format. This structured text is ideal for use with external AI tools like Anthropic's Claude or OpenAI's ChatGPT to perform tasks like:

*   Generating narrative prose based on game events.
*   Summarizing specific acts or the entire game in different styles.
*   Brainstorming plot twists or character motivations based on existing data.
*   Analyzing game events for patterns or themes.

**Example Workflow: Generating Narrative with Claude**

1.  Dump the game data to your clipboard:
    ```bash
    # On macOS
    sologm game dump | pbcopy
    # On Linux (requires xclip)
    # sologm game dump | xclip -selection clipboard
    # On Windows (PowerShell)
    # sologm game dump | Set-Clipboard
    ```
2.  Paste the markdown content into your AI chat interface (e.g., Claude.ai).
3.  Provide a prompt asking the AI to use the data. For example:
    > "Using the provided game log, write a narrative story focusing on the events of Act 1 from Marcus's perspective."

**Example Result:**

The output of the 'Sweetwater Vale' game (shown in the status image above) was processed this way using Claude.

*   **See the resulting story artifact here:**
    [Claude Artifact: Sweetwater Vale - Act 1 Narrative](https://claude.site/artifacts/b3884460-c7ea-4a3d-876e-a4e7f47a4dc6)

*   **Snippet from the generated story:**
    > The familiar din of The Golden Deer Tavern enveloped Marcus Autumnvale like a well-worn cloak. Evening shadows stretched across the worn floorboards as he finished his third—or perhaps fourth—cup of apple brandy. The warm glow of the hearth fire caught the amber liquid, reminding him of days when the Autumnvale name commanded respect rather than whispers of faded glory.

This demonstrates how SoloGM's structured data export can serve as a powerful foundation for further AI-assisted creative writing and analysis.

## Installation

### From PyPI
```bash
pip install sologm
```

### From Source
```bash
git clone https://github.com/yourusername/sologm.git
cd sologm
uv venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate  # On Windows
uv sync
```

## Development Setup

This project uses modern Python development tools:

- **uv**: For virtual environment and package management
- **pytest**: For testing
- **ruff**: For code formatting
- **mypy**: For type checking

### Setting Up Development Environment

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate  # On Windows

# Install development dependencies
uv sync --all-extras

# Run tests
pytest sologm/
pytest --cov sologm/  # With coverage

# Format code
ruff format sologm

# Type checking
mypy sologm
```

## Usage

### Game Management
```bash
# Create a new game (becomes active automatically)
sologm game create --name "Cyberpunk Noir" --description "A gritty investigation in Neo-Kyoto"

# List all games
sologm game list

# Switch active game
sologm game activate --id cyberpunk-noir

# Show basic info about the active game
sologm game info

# Show detailed status (active/latest act/scene, recent events/rolls)
sologm game status

# Edit the active game's name/description (opens editor)
sologm game edit

# Edit a specific game by ID (opens editor)
sologm game edit --id cyberpunk-noir

# Export the active game to markdown (stdout)
sologm game dump

# (on mac) Export the active game to markdown to your clipboard.
# This output can be easily used with external AI tools for narrative generation,
# summarization, etc. See the "Using Game Data with External AI" section below
# for a detailed example.
sologm game dump | pbcopy

# Export a specific game including metadata
sologm game dump --id cyberpunk-noir --metadata
```

### Act Management
```bash
# Create a new act in the current game (opens editor for title/summary)
sologm act create

# Create an act with title and summary directly
sologm act create --title "The First Clue" --summary "Following the trail of the missing data courier"

# List all acts in the current game
sologm act list

# Show details of the current active act
sologm act info

# Edit the current active act (opens editor)
sologm act edit

# Edit a specific act by ID, setting only the title
sologm act edit --id the-first-clue --title "The Digital Ghost"

# Complete the current act, marking it as finished.
# This prepares the game for the next act. You can provide a final
# title and summary manually via an editor, or use AI.
sologm act complete

# Use AI (--ai) to analyze all scenes and events within the completed act
# and generate a suggested title and narrative summary. This saves time
# and helps create a cohesive overview of the act's story arc.
# The command presents the AI suggestions for you to accept, edit, or regenerate.
sologm act complete --ai

# Guide the AI summary generation by providing additional context.
sologm act complete --ai --context "Focus on the betrayal by the informant, make the summary 5 paragraphs long"

# Force AI generation, overwriting any existing title/summary without prompting.
sologm act complete --ai --force
```

### Scene Management
```bash
# Add a new scene to the current act (becomes current automatically)
sologm scene add --title "Rainy Alley" --description "Searching for contacts in the neon-drenched backstreets"

# List all scenes in the current act
sologm scene list

# Show info about the current scene (includes events by default)
sologm scene info

# Show info about the current scene without events
sologm scene info --no-events

# Edit the current scene (opens editor)
sologm scene edit

# Edit a specific scene by ID (opens editor)
sologm scene edit --id rainy-alley

# Complete the current scene
sologm scene complete

# Switch the current scene
sologm scene set-current <insert scene ID from scene list>
```

### Event Recording
```bash
# Add an event to the current scene (opens editor for description/source)
sologm event add

# Add an event with description directly
sologm event add --description "Found a cryptic message on a datapad"

# Add an event from a specific source
sologm event add --description "Oracle suggested 'Unexpected Ally'" --source oracle

# List available event sources
sologm event sources

# List recent events in the current scene
sologm event list
sologm event list --limit 10  # Show more events
sologm event list --scene-id rainy-alley # List events for a specific scene

# Edit the most recent event in the current scene (opens editor)
sologm event edit

# Edit a specific event by ID (opens editor)
sologm event edit --id evt_abc123
```

### Dice Rolling
```bash
# Basic roll (associated with current scene if active)
sologm dice roll 2d6

# Roll with modifier and reason
sologm dice roll 1d20+3 --reason "Perception check"

# Roll associated with a specific scene (uses current scene if not specified)
sologm dice roll 3d10 --reason "Combat damage" --scene-id rainy-alley

# Show recent dice roll history (for current scene if active)
sologm dice history
sologm dice history --limit 10
sologm dice history --scene-id rainy-alley # History for a specific scene
```

### Oracle Interpretation
```bash
# Get AI interpretations for the current scene
sologm oracle interpret --context "Does the contact show up?" --results "Yes, but..."

# Specify number of interpretations
sologm oracle interpret --context "What complication arises?" --results "Betrayal, Ambush" --count 5

# Show the prompt that would be sent to the AI without sending it
sologm oracle interpret --context "What complication arises?" --results "Betrayal, Ambush" --show-prompt

# Get new interpretations for the last query (retry)
sologm oracle retry

# List interpretation sets for the current scene
sologm oracle list
sologm oracle list --limit 20
sologm oracle list --scene-id rainy-alley # List for a specific scene
sologm oracle list --act-id the-first-clue # List for a specific act

# Show details of a specific interpretation set
sologm oracle show set_xyz789

# Show the status of the current interpretation set for the active scene
sologm oracle status

# Select an interpretation (e.g., the 2nd one) from the current set to add as an event
sologm oracle select 2

# Select an interpretation by slug from a specific set
sologm oracle select --set-id set_xyz789 unexpected-visitor 
```

## Configuration

SoloGM manages its configuration using a combination of a YAML file and environment variables, providing flexibility for different setups.

**Configuration File:**

*   **Location:** By default, configuration is stored in `~/.sologm/config.yaml`.
*   **Creation:** If this file does not exist when the application first runs, it will be created automatically with default settings.
*   **Format:** The file uses YAML format with simple key-value pairs.

**Environment Variables:**

*   Environment variables can override settings defined in the configuration file.
*   Most configuration keys can be set using an environment variable prefixed with `SOLOGM_` and converted to uppercase (e.g., `debug` becomes `SOLOGM_DEBUG`).
*   **API Keys Exception:** API keys have a special format. They use the provider name followed by `_API_KEY` *without* the `SOLOGM_` prefix (e.g., `anthropic_api_key` becomes `ANTHROPIC_API_KEY`).

**Priority Order:**

Settings are loaded in the following order of precedence (highest priority first):

1.  **Environment Variables:** (e.g., `SOLOGM_DEBUG`, `ANTHROPIC_API_KEY`)
2.  **Configuration File:** (`~/.sologm/config.yaml`)
3.  **Built-in Defaults:** (Defined within the application code)

**Key Configuration Options:**

| Setting Purpose             | `config.yaml` Key         | Environment Variable        | Default Value                                  |
| :-------------------------- | :------------------------ | :-------------------------- | :--------------------------------------------- |
| Database Connection URL     | `database_url`            | `SOLOGM_DATABASE_URL`       | `sqlite:///~/.sologm/sologm.db`                |
| Anthropic API Key           | `anthropic_api_key`       | `ANTHROPIC_API_KEY`         | `""` (Empty String)                            |
| Default Oracle Interpretations | `default_interpretations` | `SOLOGM_DEFAULT_INTERPRETATIONS` | `5`                                            |
| Oracle Interpretation Retries | `oracle_retries`          | `SOLOGM_ORACLE_RETRIES`     | `2`                                            |
| Enable Debug Logging        | `debug`                   | `SOLOGM_DEBUG`              | `false`                                        |
| Log File Path               | `log_file_path`           | `SOLOGM_LOG_FILE_PATH`      | `~/.sologm/sologm.log`                         |
| Max Log File Size (Bytes)   | `log_max_bytes`           | `SOLOGM_LOG_MAX_BYTES`      | `5242880` (5 MB)                               |
| Log File Backup Count       | `log_backup_count`        | `SOLOGM_LOG_BACKUP_COUNT`   | `1`                                            |

**Example:**

To enable debug logging without editing the file, you could set the environment variable:

```bash
export SOLOGM_DEBUG=true
sologm game status # This command will now run with debug logging enabled

# you can also use --debug
sologm --debug game status
```

To use a different database file:

```bash
export SOLOGM_DATABASE_URL="sqlite:////path/to/my/custom_sologm.db"
sologm game list
```

## Development Conventions

This project follows a set of coding and design conventions to ensure consistency, maintainability, and quality. These are documented in the `conventions/` directory. Contributors should familiarize themselves with these guidelines:

*   **[Architecture (`conventions/architecture.md`)](conventions/architecture.md):** Describes the separation of concerns between the CLI (user interaction) and Manager (business logic) layers.
*   **[CLI Conventions (`conventions/cli.md`)](conventions/cli.md):** Outlines patterns for command structure, parameter handling (options vs. editor), structured editor usage, display output, and error handling within the command-line interface.
*   **[Code Style (`conventions/code_style.md`)](conventions/code_style.md):** Details Python code formatting (line length, whitespace, quotes), import ordering, naming conventions (PEP 8), docstring standards (Google Style), commenting, and type hinting usage.
*   **[Database Access (`conventions/database_access.md`)](conventions/database_access.md):** Explains session management (`get_db_context`), the Manager pattern for database interactions, transaction boundaries (`_execute_db_operation`), and common query patterns.
*   **[Display Design (`conventions/display.md`)](conventions/display.md):** Covers UI and output formatting using Rich, including panel structure, the `StyledText` helper class, border styles, layout patterns (grids, tables), and text truncation.
*   **[Documentation (`conventions/documentation.md`)](conventions/documentation.md):** Specifies standards for writing docstrings (Google Style) and application logging practices (levels, formatting, content).
*   **[Error Handling (`conventions/error_handling.md`)](conventions/error_handling.md):** Defines how exceptions should be handled, propagated, and presented to the user, particularly in the CLI.
*   **[Manager Pattern (`conventions/managers.md`)](conventions/managers.md):** Details the design of Manager classes for encapsulating business logic, including base class usage, session handling, and lazy initialization of related managers.
*   **[Models (`conventions/models.md`)](conventions/models.md):** Outlines conventions for defining SQLAlchemy ORM models, including primary keys, relationships (owning vs. non-owning), and the use of hybrid properties.
*   **[Testing (`conventions/testing.md`)](conventions/testing.md):** Describes the testing strategy, focusing on testing Manager logic with session injection and avoiding direct CLI tests. Includes fixture patterns.
*   **[Type Annotations (`conventions/type_annotations.md`)](conventions/type_annotations.md):** Specifies the requirements for using Python type hints, including function signatures, containers, `Optional`/`Union`, and SQLAlchemy `Mapped` types.

## Example Playthrough

An example playthrough demonstrating many of the features is available:

*   **[Markdown Walkthrough (`example_game.md`)](example_game.md):** A step-by-step guide with explanations and example commands.
*   **[Executable Bash Script (`example_game.sh`)](example_game.sh):** A script that runs the commands from the walkthrough (requires bash and may need manual interaction for editor steps). You can run it like: `bash example_game.sh`.

## Project Documentation

This project was developed using a comprehensive documentation-driven approach:

- **ORIGINAL_PRD.md**: The original Product Requirements Document detailing the complete feature set and user stories. This was built by interacting with Claude to figure out the design.  We have iterated a bunch since then, but this has been useful in the beginning - now we rely more on the conventions documentation.
- **ORIGINAL_TDD.md**: The original Technical Design Document outlining the system architecture and implementation details. Similar to the PRD.
- **PLAN.md**: The original Development plan breaking down the work into phases and parts.
- **COMPLETED.md**: Tracking document recording completed work and test results

## Original Development Process

This project was developed using [Aider](https://github.com/paul-gauthier/aider), an AI-powered coding assistant. The development process followed these steps:

1. Created detailed PRD (in Claude) to define the product requirements
2. Re-ran the PRD through AI to help refine with further question asking.
3. Fed PRD into Claude to generate a TDD, and refine with further question asking.
4. Created PLAN.md to break down work into manageable phases
5. Used Aider to implement each phase, tracking progress in COMPLETED.md
6. Maintained high test coverage throughout development

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`ruff format sologm`)
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

MIT

## Database Migrations

This project uses Alembic for database migrations. To manage migrations:

### Generate a new migration

```bash
# Create a migration with auto-detection of model changes
# Note, this often won't work because we use SQLite by default, which
# requires batch operations/seemingly custom migrations - most of the
# migrations were started this way, then edited in Aider.
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations to the database

```bash
# Apply all pending migrations
alembic upgrade head
```

### Downgrade the database

```bash
# Go back one revision
alembic downgrade -1
```

### View migration history

```bash
# See migration history
alembic history
```

### Get current revision

```bash
# Check current database version
alembic current
```
