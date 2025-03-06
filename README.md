# SoloGM

A Slack bot designed to assist with GM-less and solo RPG play, providing tools for dice rolling, outcome generation, and collaborative interpretation through voting.

## Features

- **Dice Rolling**: Roll dice using standard RPG notation (e.g., `2d6+3`)
- **Interpretation Voting**: Generate multiple interpretation options and create polls for players to vote based on AI-generated ideas
- **Customizable**: Set preferences for number of options and voting timeout
- **AI-Powered Ideas**: Generate creative scene outcomes using Claude AI
- **Mythic GME Support**: Built-in support for the Mythic Game Master Emulator system

## Environment Variables

Set these environment variables to configure the application:

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude AI integration
- `RPG_HELPER_LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Example Usage

### Creating a Mythic GME Game

```python
import os
from sologm.rpg_helper.utils.logging import get_logger, LogLevel
from sologm.rpg_helper.models.game.functions import create_game
from sologm.rpg_helper.models.game.mythic import MythicGMEGame

# Setup logging
logger = get_logger(level=LogLevel.INFO)
logger.info("Starting SoloGM RPG Helper example")

# Create a Mythic GME game
mythic_game = create_game(
    name="Mythic Adventure", # The name of the game
    creator_id="user123", # The user ID of the creator
    channel_id="channel789", # The channel ID to post messages to
    game_type="mythic", # The type of game to create
    setting_info="A sci-fi universe with alien civilizations", # The setting info for the game
    chaos_factor=5 # Initial chaos factor for Mythic GME
)
# Access game properties
logger.info("Game details", 
           game_id=mythic_game.id,
           game_name=mythic_game.name,
           creator=mythic_game.creator_id,
           members=list(mythic_game.members),
           chaos_factor=mythic_game.chaos_factor)
```

### Managing Scenes

```python
# Access the automatically created initial scene on the Game object
# This is the first scene that is created, and is the default scene for the game
# Note: It has no description, title or events
initial_scene = mythic_game.current_scene
logger.info("Initial scene created", 
           scene_id=initial_scene.id, 
           scene_title=initial_scene.title)

# Update the initial scene's title and description
initial_scene.title = "The Abandoned Space Station"
initial_scene.description = "The crew docks with a derelict space station that's been sending out an automated distress signal."
logger.info("Updated initial scene", scene_id=initial_scene.id, scene_title=initial_scene.title)

# Add events to the scene
initial_scene.add_event("The airlock opens with a hiss, revealing a dark corridor.")
initial_scene.add_event("Emergency lights flicker on as the team steps inside.")
logger.info("Added events to scene", event_count=len(initial_scene.events))

# Get all events in the scene
logger.info("Scene events:")
for i, event in enumerate(initial_scene.events, 1):
    logger.info(f"Event {i}: {event.description}")

# When ready to move to a new scene, complete the current one first
initial_scene.complete()
logger.info("Completed initial scene", scene_id=initial_scene.id)

# Now create a new scene
new_scene = mythic_game.create_scene(
    title="Engineering Deck",
    description="The team descends to the engineering deck, where the energy readings are strongest."
)
logger.info("Created new scene", scene_id=new_scene.id, scene_title=new_scene.title)

# Add events to the new scene that follow logically from the description
new_scene.add_event("The team's energy scanner begins beeping rapidly as they approach the main reactor.")
new_scene.add_event("Strange symbols are etched into the control panels, unlike any human language.")
new_scene.add_event("A faint humming sound grows louder as they move deeper into the engineering section.")
new_scene.add_event("One team member notices that the reactor appears to be running, despite the station being abandoned.")
logger.info("Added events to new scene", event_count=len(new_scene.events))

# The new scene is automatically set as the current scene
assert mythic_game.current_scene is new_scene
```

### Creating Polls

```python
from sologm.rpg_helper.models.poll import Poll
import uuid

# Create a poll for what happens when the team investigates the control panels
poll = Poll(
    title="The team investigates the control panels, something goes wrong!",
    options=[
        "Touching the symbols causes them to glow, triggering an alarm system",
        "A holographic interface suddenly activates, displaying alien text",
        "The reactor power levels spike dangerously when the panels are touched",
        "One team member receives a strange electric shock when examining the symbols",
        "The control room door suddenly seals shut, trapping the team inside"
    ],
    creator_id="user123",
    game=mythic_game,
    max_votes_per_user=1,
    timeout_seconds=60  # Auto-close after 60 seconds
)
logger.info("Created new poll", poll_id=poll.id, option_count=len(poll.options))

# Add votes
poll.add_vote("user456", 0)  # Vote for the first option
poll.add_vote("user789", 2)  # Vote for the third option

# Get vote counts
vote_counts = poll.get_vote_counts()
logger.info("Vote counts", counts=vote_counts)

# Get winning options
winners = poll.get_winning_options()
logger.info("Winning options", winners=winners)

# Close the poll
poll.close()
logger.info("Closed poll", poll_id=poll.id, winning_options=winners)
```

### Using AI Assistance

This can be used to generate outcome ideas for the current scene, or for a poll.

```python
import os
from sologm.rpg_helper.services.ai.factory import AIServiceFactory
from sologm.rpg_helper.services.ai.game_helper import GameAIHelper

# Make sure Claude API key is set
if not os.environ.get("ANTHROPIC_API_KEY"):
    logger.error("ANTHROPIC_API_KEY environment variable not set")
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable")

# Create an AI service - using Claude in this case
ai_service = AIServiceFactory.create_service("claude")
logger.info("Created Claude AI service")

# Create a game helper
game_helper = GameAIHelper(ai_service)

# Generate outcome ideas for the current scene
# This will use the current scene description, and the game setting info to generate ideas
# The additional_context is optional, and can be used to provide more specific context for the AI
# The focus_words are used to refine the ideas, and the num_ideas is the number of ideas to generate
# Often times the focus words come from something like the Mythic GME system, or other oracles
logger.info("Generating outcome ideas...")
ideas = game_helper.generate_outcome_ideas(
    game=mythic_game,
    scene=mythic_game.current_scene,
    additional_context="The crew is searching for the source of strange energy readings.",
    focus_words=["alien", "technology"],
    num_ideas=3
)

# Log the generated ideas
logger.info("Generated outcome ideas", count=len(ideas))
logger.info("=== Potential Outcomes ===")
for i, idea in enumerate(ideas, 1):
    logger.info(f"Outcome {i}: {idea}")
```

## Installation

```bash
pip install sologm
```

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/sologm.git
cd sologm

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```


## Database Models

The application uses SQLAlchemy models to represent entities like games, scenes, polls, and users. These models are defined in the `sologm/rpg_helper/models2` package.

## Database Migrations

This project uses Alembic for database migrations. This allows you to update the database schema without losing data when you make changes to the models.

### Setting Up Alembic

If you're setting up the project for the first time, you need to initialize Alembic:

```bash
python -m sologm.rpg_helper.models2.migrations.init_alembic
```

This will create the necessary Alembic files in the `sologm/rpg_helper/models2/migrations` directory.

### Creating a Migration

When you make changes to the models, you need to create a migration:

```bash
python -m sologm.rpg_helper.models2.migrations.create_migration "Description of your changes"
```

This will create a new migration file in the `sologm/rpg_helper/models2/migrations/alembic/versions` directory.

### Applying Migrations

To apply pending migrations to the database:

```bash
python -m sologm.rpg_helper.models2.migrations.apply_migrations
```

By default, this will apply migrations to the database at `~/.sologm/rpg_helper.db`. You can specify a different database path with the `--db` option.

### Automatic Migrations

The `init_db` function in `sologm/rpg_helper/models2/init_db.py` will automatically apply migrations when initializing the database. If migrations fail (e.g., if Alembic is not installed), it will fall back to creating all tables from scratch.

## Development

### Running Tests

To run the tests:

```bash
python -m unittest discover tests
```

### Example Usage

See `examples/models_demo.py` for an example of how to use the models.

## Models Overview

### Game

The `Game` model represents a game, which can have multiple scenes, polls, and members. It supports different game types through polymorphism.

### MythicGame

The `MythicGame` model extends the base `Game` model with Mythic GME specific functionality, such as chaos factor management.

### Scene

The `Scene` model represents a scene in a game. Scenes can have events and can be in different states (active, completed, abandoned).

### Poll

The `Poll` model represents a poll in a game. Polls can have options and votes, and can be open or closed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.