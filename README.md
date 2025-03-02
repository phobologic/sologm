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
    name="Mythic Adventure",
    creator_id="user123",
    channel_id="channel789",
    game_type="mythic",
    setting_info="A sci-fi universe with alien civilizations",
    chaos_factor=4  # Initial chaos factor for Mythic GME
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
# Create a new scene directly through the game object
scene = mythic_game.add_scene(
    title="The Abandoned Space Station",
    description="The crew docks with a derelict space station that's been sending out an automated distress signal."
)
logger.info("Created new scene", scene_id=scene.id, scene_title=scene.title)

# Add events to the scene
scene.add_event("The airlock opens with a hiss, revealing a dark corridor.")
scene.add_event("Emergency lights flicker on as the team steps inside.")
logger.info("Added events to scene", event_count=len(scene.events))

# Get all events in the scene
logger.info("Scene events:")
for i, event in enumerate(scene.events, 1):
    logger.info(f"Event {i}: {event.description}")
```

### Creating Polls

```python
from sologm.rpg_helper.models.poll import Poll
import uuid

# Create a poll
poll = Poll(
    id=str(uuid.uuid4()),
    title="What should the crew investigate first?",
    options=[
        "The bridge, to access ship logs",
        "The engineering section, to check power systems",
        "The crew quarters, to look for survivors"
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

```python
import os
from sologm.rpg_helper.services.ai.factory import AIServiceFactory
from sologm.rpg_helper.services.ai.game_helper import GameAIHelper

# Make sure Claude API key is set
if not os.environ.get("ANTHROPIC_API_KEY"):
    logger.error("ANTHROPIC_API_KEY environment variable not set")
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable")

# Create an AI service
ai_service = AIServiceFactory.create_service("claude")
logger.info("Created Claude AI service")

# Create a game helper
game_helper = GameAIHelper(ai_service)

# Generate outcome ideas for the current scene
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

## License

This project is licensed under the MIT License.