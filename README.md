# Solo RPG Helper CLI

A command-line application designed to assist players of solo or GM-less roleplaying games by tracking game scenes, providing dice rolling functionality, and leveraging AI to help interpret "oracle" results.

## Features

- **Game Management**: Create, list, activate, edit, and export games to organize your solo RPG sessions. View game status.
- **Act Management**: Organize your game into narrative acts. Create, list, view, edit, and complete acts. AI can optionally summarize completed acts.
- **Scene Tracking**: Create scenes within acts, mark them as complete, edit them, and track the current active scene.
- **Event Recording**: Log important events that occur during gameplay, associating them with scenes. Edit existing events and manage event sources.
- **Dice Rolling**: Roll dice using standard notation (e.g., 2d6+1) with optional reasons and scene association. View roll history.
- **Oracle Interpretation**: Use AI (e.g., Claude) to interpret oracle results in the context of your game. Manage interpretation sets, retry interpretations, and select interpretations to become events.

## Installation

### From PyPI (Coming Soon)
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
uv pip install -e .
```

## Development Setup

This project uses modern Python development tools:

- **uv**: For virtual environment and package management
- **pytest**: For testing
- **black**: For code formatting
- **isort**: For import sorting
- **mypy**: For type checking

### Setting Up Development Environment

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate  # On Windows

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest
pytest --cov=sologm  # With coverage

# Format code
black sologm
isort sologm

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

# Complete the current act (opens editor for final title/summary)
sologm act complete

# Complete act with AI-generated title and summary
sologm act complete --ai

# Complete act with AI, providing additional context
sologm act complete --ai --context "Focus on the betrayal by the informant"

# Force AI completion, overwriting existing title/summary
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
sologm scene set-current --id rainy-alley
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

# Roll associated with a specific scene
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

# Retry, but edit the context first (opens editor)
sologm oracle retry --edit

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
sologm oracle select --id 2

# Select an interpretation by slug from a specific set
sologm oracle select --id unexpected-visitor --set-id set_xyz789

# Select interpretation and edit the event description before adding
sologm oracle select --id 3 --edit
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

## Project Documentation

This project was developed using a comprehensive documentation-driven approach:

- **PRD.md**: Product Requirements Document detailing the complete feature set and user stories
- **TDD.md**: Technical Design Document outlining the system architecture and implementation details
- **PLAN.md**: Development plan breaking down the work into phases and parts
- **COMPLETED.md**: Tracking document recording completed work and test results

## Development Process

This project was developed using [Aider](https://github.com/paul-gauthier/aider), an AI-powered coding assistant. The development process followed these steps:

1. Created detailed PRD to define the product requirements
2. Developed comprehensive TDD to plan the technical implementation
3. Created PLAN.md to break down work into manageable phases
4. Used Aider to implement each phase, tracking progress in COMPLETED.md
5. Maintained high test coverage throughout development

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black . && isort .`)
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
