# RPG Helper Bot for Slack

A Slack bot designed to assist with GM-less and solo RPG play, providing tools for dice rolling, outcome generation, and collaborative interpretation through voting.

## Features

- **Dice Rolling**: Roll dice using standard RPG notation (e.g., `2d6+3`)
- **Interpretation Voting**: Generate multiple interpretation options and create polls for players to vote based on AI-generated ideas
- **Customizable**: Set preferences for number of options and voting timeout
- **AI-Powered Ideas**: Generate creative scene outcomes using Claude AI

## Environment Variables

Set these environment variables to configure the application:

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude AI integration
- `RPG_HELPER_LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Example Usage

Here's a complete example showing how to use the main features:

```python
import os
from sologm.rpg_helper.utils.logging import get_logger, LogLevel
from sologm.rpg_helper.models.game import create_game
from sologm.rpg_helper.services.ai import AIServiceFactory, GameAIHelper

# Setup logging
logger = get_logger(level=LogLevel.INFO)
logger.info("Starting SoloGM RPG Helper example")

# Make sure Claude API key is set
if not os.environ.get("ANTHROPIC_API_KEY"):
    logger.error("ANTHROPIC_API_KEY environment variable not set")
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable")

# Create a new game
game = create_game(
    name="The Lost Kingdom",
    creator_id="user123",
    channel_id="channel456",
    game_type="mythic",  # Using the Mythic GME system
    setting_info="A high fantasy world where magic is fading and ancient ruins hold forgotten power."
)
logger.info("Created new game", game_id=game.id, game_name=game.name)

# Create a scene
scene = game.create_scene(
    title="The Forbidden Library",
    description="The party has discovered an ancient library hidden beneath the city. "
                "Dusty tomes line the walls, and strange magical symbols glow faintly on the floor."
)
logger.info("Created new scene", scene_id=scene.id, scene_title=scene.title)

# Add some events to the scene
scene.add_event("The party carefully enters the library, weapons drawn.")
scene.add_event("Mara discovers a tome that seems to react to her touch, glowing with arcane energy.")
scene.add_event("A strange mechanical sound comes from behind a bookshelf.")
logger.info("Added events to scene", event_count=len(scene.events))

# Set up AI service and game helper
ai_service = AIServiceFactory.create_service("claude")
game_helper = GameAIHelper(ai_service)

# Generate outcome ideas based on the current situation
logger.info("Generating outcome ideas...")
ideas = game_helper.generate_outcome_ideas(
    game=game,
    scene=scene,
    additional_context="The party is looking for information about an ancient artifact called 'The Crown of Stars'.",
    focus_words=["guardian", "secret"]
)

# Display the generated ideas
print("\n=== Potential Outcomes ===\n")
for i, idea in enumerate(ideas, 1):
    print(f"{i}. {idea}\n")

# Update the chaos factor (Mythic GME specific)
game.increment_chaos_factor()
logger.info("Updated chaos factor", new_chaos_factor=game.chaos_factor)

# Complete the scene
scene.complete(
    title="The Guardian's Challenge",
    description="The party encountered the library's guardian and made a deal to access the restricted section."
)
logger.info("Completed scene", scene_id=scene.id)

logger.info("Example completed successfully")
```

## Key Components

- **Game Management**: Create and manage RPG games with different systems
- **Scene Tracking**: Record and track scenes and events within your game
- **AI Integration**: Use Claude AI to generate creative ideas for your game
- **Logging**: Structured logging with context for debugging and tracking

## Project Structure

## Development

### Running Tests

```bash
pytest
```

### Setting Up Development Environment

```bash
pip install -e ".[dev]"
```

## License

This project is licensed under the MIT License.