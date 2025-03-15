# SoloGM

A powerful Slack bot designed to enhance GM-less and solo RPG play. SoloGM combines AI-powered creativity with structured game management to provide a seamless solo gaming experience.

[View Live Demo](https://demo-link-here) | [Documentation](https://docs-link-here)

## Features

- **AI-Powered Creativity**: Generate scene outcomes and interpretations using Claude AI
- **Flexible Game Systems**: Support for both standard RPG play and Mythic Game Master Emulator
- **Interactive Decision Making**: Create polls for collaborative interpretation through voting
- **Structured Scene Management**: Track game progress with organized scenes and events
- **Dice Rolling**: Roll dice using standard RPG notation (e.g., `2d6+3`)

## Quick Start

### Installation

```bash
pip install sologm
```

### Environment Setup

```bash
# Required for AI features
export ANTHROPIC_API_KEY="your-api-key"

# Optional logging configuration
export RPG_HELPER_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Core Concepts

### Game Types

SoloGM supports two game types:

- **Standard**: Traditional RPG play with flexible scene management
- **Mythic GME**: Built-in support for the Mythic Game Master Emulator system, including chaos factor tracking and fate checks

### Scenes & Events

Games are organized into scenes, which contain:
- Title and description
- Chronological events
- Status tracking (active/completed)
- AI-generated outcomes

### AI Integration

The Claude AI integration provides:
- Creative scene outcome generation
- Context-aware suggestions
- Customizable idea generation based on game state
- Support for different narrative styles

### Polls & Voting

Collaborative decision making through:
- Customizable voting options
- Configurable timeouts
- Vote tracking and winner selection
- Integration with scene outcomes

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/sologm.git
cd sologm

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Database Management

SoloGM uses SQLAlchemy with Alembic for database migrations.

#### Initial Setup

```bash
python -m sologm.rpg_helper.models2.migrations.init_alembic
```

#### Creating Migrations

```bash
python -m sologm.rpg_helper.models2.migrations.create_migration "Description of changes"
```

#### Applying Migrations

```bash
python -m sologm.rpg_helper.models2.migrations.apply_migrations
```

By default, migrations apply to `~/.sologm/rpg_helper.db`. Use `--db` to specify a different path.

### Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Code style and standards
- Testing requirements
- Pull request process
- Issue reporting

## API Reference

For detailed API documentation, see our [API Reference](API.md). Key interfaces include:

- `GameService`: Core game management functionality
- `AIService`: AI integration interface
- `PollService`: Voting and poll management
- `MythicService`: Mythic GME specific features

## Examples

For practical examples and usage scenarios, check out our [Live Demo](https://demo-link-here). The demo showcases:
- Creating and managing games
- Using AI for scene outcomes
- Setting up and managing polls
- Integrating with Mythic GME

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.