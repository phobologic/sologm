# Solo RPG Helper CLI

A command-line application designed to assist players of solo or GM-less roleplaying games by tracking game scenes, providing dice rolling functionality, and leveraging AI to help interpret "oracle" results.

## Features

- **Game Management**: Create, list, and activate games to organize your solo RPG sessions
- **Scene Tracking**: Create scenes, mark them as complete, and track the current active scene
- **Event Recording**: Log important events that occur during gameplay
- **Oracle Interpretation**: Use Claude AI to interpret oracle results in the context of your game
- **Dice Rolling**: Roll dice using standard notation (e.g., 2d6+1) with optional reasons

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
sologm game create --name "Fantasy Adventure" --description "A solo adventure in a fantasy world"

# List all games
sologm game list

# Switch active game
sologm game activate --id fantasy-adventure

# Show current game info
sologm game info
```

### Scene Management
```bash
# Create a new scene (becomes current automatically)
sologm scene create --title "The Forest" --description "A dark and mysterious forest"

# List all scenes
sologm scene list

# Complete current scene
sologm scene complete

# Switch current scene
sologm scene set-current --id forest-scene
```

### Event Recording
```bash
# Add an event to current scene
sologm event add --text "Encountered a strange creature in the woods"

# List recent events
sologm event list
sologm event list --limit 10  # Show more events
```

### Dice Rolling
```bash
# Basic roll
sologm dice roll 2d6

# Roll with modifier and reason
sologm dice roll 2d6+1 --reason "Skill check"

# Multiple dice
sologm dice roll 3d6 --reason "Damage roll"
```

### Oracle Interpretation
```bash
# Get AI interpretations
sologm oracle interpret --context "What happens next?" --results "Danger, Mystery" --count 3

# Select an interpretation
sologm oracle select --id interp-1

# Get new interpretations for same context
sologm oracle retry
```

## Configuration

The application stores data in `~/.sologm/` directory and uses environment variables for configuration:

```bash
# Required for oracle interpretation
export ANTHROPIC_API_KEY=your_api_key_here

# Optional: Enable debug logging
export SOLOGM_DEBUG=1
```

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
