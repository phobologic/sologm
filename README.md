# Solo RPG Helper CLI

A command-line application designed to assist players of solo or GM-less roleplaying games by tracking game scenes, providing dice rolling functionality, and leveraging AI to help interpret "oracle" results.

## Features

- Game management (create, list, activate)
- Scene tracking (create, complete, list)
- Event recording
- Oracle interpretation with AI assistance
- Dice rolling with standard notation

## Installation

```bash
# Install from source
pip install -e .

# Or once published
pip install sologm
```

## Usage

```bash
# Create a new game
sologm game create --name "Fantasy Adventure" --description "A solo adventure in a fantasy world"

# Create a scene
sologm scene create --title "The Forest" --description "A dark and mysterious forest"

# Add an event
sologm event add --text "Encountered a strange creature in the woods"

# Roll dice
sologm dice roll 2d6+1 --reason "Skill check"

# Interpret oracle results
sologm oracle interpret --context "What happens next?" --results "Danger, Mystery, Magic"
```

## Configuration

The application stores data in `~/.sologm/` directory and uses environment variables for API keys:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

## License

MIT
