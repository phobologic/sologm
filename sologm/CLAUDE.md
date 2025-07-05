# SoloGM Development Guidelines

This is a solo RPG helper application built with Python, SQLAlchemy, and a CLI interface using Rich for display and Typer for commands.

## Architecture Overview
- **CLI Layer** (`sologm/cli/`): User interaction only - delegates all business logic to managers
- **Core/Managers** (`sologm/core/`): Business logic and database operations using the manager pattern
- **Models** (`sologm/models/`): SQLAlchemy ORM models with hybrid properties and mixins
- **Database** (`sologm/database/`): Session management with context managers

## Key Conventions
All development follows comprehensive conventions in `../conventions/`:

- [Architecture](../conventions/architecture.md) - Separation of concerns between CLI and managers
- [Code Style](../conventions/code_style.md) - Python formatting, naming, and documentation standards
- [Testing](../conventions/testing.md) - Test managers with session injection, not CLI commands
- [Error Handling](../conventions/error_handling.md) - Exception propagation and user-friendly messages

## Development Patterns

### Linting
Whenever you modify python files, you must then run two ruff commands against them:

- ruff format $filename
- ruff check --select=E,F,W,I,N,B,A,C4,SIM,ARG $filename

Fix any issues you find as they come up.

### Database Operations
Always use the session context pattern:
```python
with get_db_context() as context:
    result = context.managers.my_manager.do_operation(params)
```

### Manager Pattern
Business logic lives in managers, not CLI:
```python
# CLI delegates to manager
result = context.managers.scene.create_scene(title, description)
# Manager handles all database operations
```

### Error Handling
Let exceptions propagate with context:
```python
try:
    # operation
except SpecificException as e:
    raise NewException("Context information") from e
```

## Quick Reference
- **Database Sessions**: Use `get_db_context()` for all database operations
- **Business Logic**: All logic goes through managers in `sologm/core/`
- **Primary Keys**: All models use UUIDs as strings
- **Testing**: Test managers directly with session injection
- **CLI Commands**: Focus only on user interaction and parameter collection

## Project Structure
```
sologm/
├── cli/           # User interface layer
├── core/          # Business logic (managers)
├── models/        # SQLAlchemy ORM models
├── database/      # Session management
├── integrations/  # External services (Anthropic API)
├── storage/       # File operations
└── utils/         # Shared utilities
```
