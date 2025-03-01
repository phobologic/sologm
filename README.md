# RPG Helper Bot for Slack

A Slack bot designed to assist with GM-less and solo RPG play, providing tools for dice rolling, Mythic GM Emulator-style fate checks, and collaborative interpretation through voting.

## Features

- **Dice Rolling**: Roll dice using standard RPG notation (e.g., `2d6+3`)
- **Fate Checks**: Perform Mythic GM Emulator-style fate checks based on chaos factor and likelihood
- **Interpretation Voting**: Generate multiple interpretation options and create polls for players to vote
- **Customizable**: Set preferences for number of options and voting timeout

## Project Structure

```
rpg_helper_bot/
├── .env                           # Environment variables
├── README.md                      # This file
├── main.py                        # Entry point for the application
└── rpg_helper/                    # Main package
    ├── __init__.py                # Package initialization
    ├── app.py                     # Slack app configuration
    ├── commands/                  # Command handlers
    │   ├── __init__.py
    │   ├── dice.py                # Dice rolling commands
    │   ├── fate.py                # Fate check commands
    │   ├── interpret.py           # Interpretation commands
    │   └── preferences.py         # User preference commands
    ├── handlers/                  # Event handlers
    │   ├── __init__.py
    │   └── actions.py             # Button/interactive action handlers
    ├── models/                    # Data models
    │   ├── __init__.py
    │   ├── poll.py                # Poll data structures
    │   └── user.py                # User preference data structures
    ├── services/                  # Business logic
    │   ├── __init__.py
    │   ├── dice_service.py        # Dice rolling logic
    │   ├── fate_service.py        # Fate check logic
    │   ├── interpreter_service.py # Interpretation generation
    │   └── poll_service.py        # Poll management
    └── utils/                     # Utility functions
        ├── __init__.py
        └── formatting.py          # Message formatting utilities
```

## Setup

### Prerequisites

- Python 3.7 or higher
- A Slack workspace where you have permissions to create apps
- [uv](https://github.com/astral-sh/uv) for Python package and environment management

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rpg-helper-bot.git
   cd rpg-helper-bot
   ```

2. Create a virtual environment with uv:
   ```bash
   uv venv
   ```

3. Activate the virtual environment:
   ```bash
   # On Unix/macOS
   source .venv/bin/activate
   
   # On Windows
   .venv\Scripts\activate
   ```

4. Install dependencies using uv:
   ```bash
   uv pip install slack-bolt python-dotenv
   ```

5. Create a `.env` file in the root directory with the following variables:
   ```
   SLACK_BOT_TOKEN=xoxb-your-bot-token-here
   SLACK_APP_TOKEN=xapp-your-app-token-here
   ```

### Slack App Setup

1. Go to [Slack API](https://api.slack.com/apps) and click "Create New App"
2. Choose "From scratch"
3. Name your app (e.g., "RPG Helper") and select your workspace
4. Click "Create App"

5. Configure Bot Permissions
   - In the left sidebar, click on "OAuth & Permissions"
   - Scroll down to "Bot Token Scopes" and add these permissions:
     - `chat:write` - To send messages
     - `commands` - To create slash commands
     - `users:read` - To read user information
   - Scroll up and click "Install to Workspace"
   - Authorize the app when prompted

6. Create Slash Commands
   - In the left sidebar, click on "Slash Commands"
   - Create the following commands:
     - Command: `/roll` - Description: "Roll dice using standard notation (e.g., 2d6+3)"
     - Command: `/fate` - Description: "Make a Mythic GM Emulator fate check"
     - Command: `/interpret` - Description: "Generate interpretation options and create a vote"
     - Command: `/preferences` - Description: "Set your preferences for the RPG Helper"
     - Command: `/endpoll` - Description: "Manually end an active poll"

7. Enable Socket Mode
   - In the left sidebar, click on "Socket Mode"
   - Toggle "Enable Socket Mode" to On
   - Click "Generate" to create an app-level token
   - Save the generated token (this is your `SLACK_APP_TOKEN`)

8. Set Up Interactivity
   - In the left sidebar, click on "Interactivity & Shortcuts"
   - Toggle "Interactivity" to On
   - Click "Save Changes"

### Running the Bot

Run the bot:
```bash
python main.py
```

## Development with uv

uv makes dependency management faster and more reliable. Here are some useful commands:

- Install a new package:
  ```bash
  uv pip install package-name
  ```

- Update dependencies:
  ```bash
  uv pip install --upgrade slack-bolt python-dotenv
  ```

- Create a requirements file:
  ```bash
  uv pip freeze > requirements.txt
  ```

- Install from requirements file:
  ```bash
  uv pip install -r requirements.txt
  ```

## Usage

### Roll Dice
```
/roll 2d6+3
```
This will roll two six-sided dice and add 3 to the total.

### Fate Check
```
/fate 5 Likely
```
This will perform a Mythic GM Emulator fate check with a chaos factor of 5 and a likelihood of "Likely".

### Generate Interpretations
```
/interpret What happens when we open the chest?
```
This will generate multiple interpretation options for what happens when the chest is opened, and create a poll for players to vote.

### Set Preferences
```
/preferences options 7
```
This sets the number of interpretation options to 7.

```
/preferences timeout 2
```
This sets the poll timeout to 2 hours.

```
/preferences show
```
This shows your current preferences.

### End a Poll
```
/endpoll
```
This manually ends the current poll in the channel (if you created it).

## Customization

### Interpretation Options
You can customize the list of base interpretations by modifying the `BASE_INTERPRETATIONS` in `rpg_helper/services/interpreter_service.py`.

### Fate Chart
The current implementation uses a simplified fate chart. For a more accurate Mythic GM Emulator experience, you can update the logic in `rpg_helper/services/fate_service.py`.

## Future Enhancements

- Database integration for persistence
- More advanced random generation tools
- Integration with specific game systems
- Character tracking
- Campaign notes and session logs

## License

This project is licensed under the MIT License.