# Product Requirements Document: Solo RPG Helper Command-Line Application

## 1. Introduction

### 1.1 Purpose
The Solo RPG Helper is a command-line application designed to assist players of solo or GM-less roleplaying games by tracking game scenes, providing dice rolling functionality, and leveraging AI to help interpret "oracle" results - a common concept in solo RPG gameplay.

### 1.2 Target Users
This application targets semi-experienced solo RPG players or individuals who are knowledgeable about RPGs and have played them before. Users are expected to have a basic understanding of RPG mechanics and terminology.

### 1.3 Scope
The application will provide a command-line interface, allowing users to manage games, scenes, events, and oracle interpretations. It will not include built-in oracle tables but will instead help players interpret results from their own oracle systems.

## 2. Features and Requirements

### 2.1 Core Functionality

#### 2.1.1 Game Management
- Users should be able to create a Game with a description
- Only one game can be the "active game" at a time
- Users should be able to list all their games
- Users should be able to switch between games easily

##### Active Game Concept
- The active game is the currently selected game that commands operate on
- Only one game can be the active game at any time
- The active game is tracked in ~/.sologm/active_game
- When creating a new game, it becomes the active game by default unless specified otherwise

#### 2.1.2 Scene Management
- Users should be able to create Scenes with descriptions
- Each scene has a status (active/completed)
- A game should only have one "current" scene at a time (the scene being played)
- The current scene is tracked separately from scene status
- When a scene is completed, its status changes but it remains preserved
- Completing a scene is separate from changing which scene is current

#### 2.1.3 Event Tracking
- Users should be able to create events in the currently active scene
- Events should have descriptive text
- The system should maintain a history of events

#### 2.1.4 Oracle Interpretation System
- Users should be able to submit oracle results for AI interpretation
- Oracle interpretation requests should include:
  - User-provided context/question detailing what needs an answer
  - User-provided oracle words/results from their external oracle system
  - Number of interpretations to generate (configurable, default: 5)
- System should automatically include:
  - Game description (providing genre, setting, tone, and background)
  - Current Scene description (location, situation, characters present)
  - Last 5 Scene Events descriptions (if they exist) to provide narrative continuity
- The system tracks the most recently generated interpretation set as the "current" interpretation
- AI should return the requested number of possible interpretations in a simple, parseable plaintext format:
  ```
  === BEGIN INTERPRETATIONS ===
  
  --- INTERPRETATION 1 ---
  TITLE: Short title for the interpretation
  DESCRIPTION: Detailed description of interpretation idea
  --- END INTERPRETATION 1 ---
  
  --- INTERPRETATION 2 ---
  TITLE: Short title for the interpretation
  DESCRIPTION: Detailed description of interpretation idea
  --- END INTERPRETATION 2 ---
  
  ... and so on
  
  === END INTERPRETATIONS ===
  ```
- The user will select from the presented interpretations through numbered options
- If none of the interpretations work:
  - The user can request new interpretations using the same context and results
  - The system will instruct the AI to provide different interpretations
  - The system tracks the number of retry attempts for the current interpretation
- If a specific interpretation is selected:
  - The selected interpretation is displayed with the original context/question
  - The interpretation is added as an event to the current scene
  - The interpretation set remains "current" until a new one is generated

#### 2.1.5 Dice System
- Support for standard dice notation (e.g., "2d6+3")
- Supported dice format:
  - `XdY+Z` where:
    - X = number of dice to roll (integer > 0)
    - Y = number of sides on each die (integer > 1)
    - +Z = optional modifier to add to total (can be + or -)
  - Examples: "1d20", "3d6", "2d10+4", "1d8-2"
- Optional "reason" field to provide context for the roll
- Display individual dice results and the final total
- System should be simple but extensible for future enhancements

### 2.2 Interface Requirements

#### 2.2.1 Command-Line Interface
- Built using appropriate Python CLI libraries (e.g., Click, Typer, or argparse)
- Commands should follow a logical hierarchy: `sologm [command] [subcommand] [arguments] [--flags]`
- All inputs provided directly as command-line arguments and flags
- Clear, readable output with appropriate formatting
- Help text available for all commands and subcommands
- Tab completion support where possible

#### 2.2.2 User Experience
- Single command execution pattern (non-interactive)
- Color-coded output for better readability
- Session persistence between commands
- Consistent command structure throughout the application

### 2.3 Technical Requirements

#### 2.3.1 Technology Stack
- Python 3
- File-based storage rather than a database
- Best-in-class 3rd party libraries for external APIs
- uv for package management and development environment management

#### 2.3.2 Data Storage
- Simple YAML file structure for data persistence
- File organization:
  ```
  ~/.sologm/
  ├── games/
  │   ├── game1/
  │   │   ├── game.yaml       # Game metadata
  │   │   ├── scene1/         # Each scene as a directory
  │   │   │   ├── scene.yaml  # Scene metadata
  │   │   │   ├── events.yaml # All events in this scene
  │   │   │   └── interpretations/ # Interpretations in this scene
  │   │   │       ├── interp_20250401_121530.yaml
  │   │   │       └── interp_20250401_123045.yaml
  │   │   ├── scene2/
  │   │   │   ├── scene.yaml
  │   │   │   ├── events.yaml
  │   │   │   └── interpretations/
  │   │   └── active_scene    # Text file containing ID of active scene
  │   └── game2/
  ├── active_game             # Text file containing ID of active game
  └── config.yaml             # Global configuration
  ```
- Automatic backup creation before significant changes
- Small footprint for easy backup and transportation

#### 2.3.3 Configuration
- Simple config file for user preferences
- Environment variables for API keys and sensitive information
- Command-line flags for temporary overrides

#### 2.3.4 Development Standards
- Type hints throughout the codebase
- Google Doc string format for documentation
- Python logging library for application logging
- MIT license

#### 2.3.5 Deployment
- Installable via pip
- Self-contained with minimal dependencies
- Cross-platform compatibility (Windows, macOS, Linux)

#### 2.3.6 Error Handling
- Clear error messages that explain the current state causing issues
- Contextual guidance on how to resolve errors
- Appropriate error logging for troubleshooting

## 3. User Stories

### 3.1 Game Creation and Management
- As a player, I want to create a new solo RPG game so that I can start tracking my gameplay
- As a player, I want to see information about my active game
- As a player, I want to list all my games
- As a player, I want to switch between different games easily

### 3.2 Scene Management
- As a player, I want to create a new scene with a description to advance my story
- As a player, I want to mark a scene as complete and create a new active scene
- As a player, I want to view the history of scenes in my game

### 3.3 Event Tracking
- As a player, I want to record significant events that occur in the current scene
- As a player, I want to view the recent events in the current scene for continuity

### 3.4 Oracle Interpretation
- As a player, I want to submit oracle results and context for AI interpretation
- As a player, I want to specify how many interpretation options I receive
- As a player, I want to select the interpretation that best fits my narrative
- As a player, I want the selected interpretation to be automatically added as a scene event
- As a player, I want the system to remember my last oracle interpretation request so I can easily work with it
- As a player, I want to get different interpretations for the same oracle results if the first set wasn't helpful
- As a player, I want to select from the current interpretation set without having to specify its ID

### 3.5 Dice Rolling
- As a player, I want to roll dice using standard notation to determine outcomes
- As a player, I want to provide a reason for my dice roll for context
- As a player, I want to see both individual dice results and the final total

## 4. Technical Specifications

### 4.1 Data Organization and Relationships

#### 4.1.1 Overall Structure
- One directory per game (named with game identifier)
- One YAML file (`game.yaml`) for game metadata
- One directory per scene within each game directory
- Each scene directory contains:
  - `scene.yaml` for scene metadata
  - `events.yaml` for all events in the scene
  - `interpretations/` directory for all oracle interpretations in the scene
- Simple text files to track the active game and active scene

#### 4.1.2 Game Data
- Each game has a unique identifier (UUID or slug)
- Game metadata stored in `game.yaml` with:
  - Name, description
  - Created/modified dates
  - List of all scene IDs
  - Current interpretation data:
    - Interpretation set ID
    - Original context/question
    - Oracle results
    - Number of retry attempts
- Active game tracking:
  - Current active game ID stored in `~/.sologm/active_game`
  - This file contains only the game ID of the currently active game
  - When empty, no game is currently active

#### 4.1.3 Scene Data
- Each scene has its own directory named with scene identifier
- Scene metadata stored in `scene.yaml` with:
  - Title, description, status, sequence number
  - Created/modified dates
  - Reference to parent game ID

#### 4.1.4 Event Data
- All events for a scene stored in `events.yaml`
- Each event contains:
  - Description text
  - Created date
  - Optional source (manual, oracle interpretation, etc.)

#### 4.1.5 AI Interpretation Data
- Each interpretation stored as separate YAML file in the scene's `interpretations/` directory
- Filename based on timestamp
- Contains:
  - Original user context/question
  - Oracle results provided
  - AI response with all interpretations
  - Reference to selected interpretation (if any)
  - Number of retry attempts for this context/results pair
- Current interpretation tracking:
  - Each game stores reference to its current interpretation set in game.yaml:
    ```yaml
    current_interpretation:
      id: "interpretation_set_id"
      context: "Original question/context"
      results: "Original oracle results"
      retry_count: 1
    ```

### 4.2 Command Structure

#### 4.2.1 Commands
- `sologm game create --name "Game Name" --description "Game description" [--no-activate]` - Create a new game
- `sologm game list` - List all games showing which is active
- `sologm game activate --id [game_id]` - Set a game as active
- `sologm game info` - Show details of current active game

Example command sequence:
```bash
# Create and manage multiple games
sologm game create --name "Fantasy Quest" --description "A magical journey"
sologm game create --name "Space Adventure" --description "Exploring the stars"
sologm game list
# Shows:
# - Fantasy Quest
# - Space Adventure [active game]

# Switch active game
sologm game activate --id fantasy-quest
sologm game list
# Shows:
# - Fantasy Quest [active game]
# - Space Adventure
```
- `sologm scene create --title "Scene Title" --description "Scene description"` - Create a new scene in active game
- `sologm scene list` - List all scenes in active game
- `sologm scene info` - Show details of current active scene
- `sologm event add --text "Event description"` - Add an event to the current scene
- `sologm event list` - List recent events in current scene
- `sologm oracle interpret --context "Your question" --results "Oracle result" --count 5` - Submit oracle results for AI interpretation (becomes current)
- `sologm oracle select [--id interpretation_id]` - Select an interpretation to add as an event (uses current if no ID provided)
- `sologm oracle retry` - Request new interpretations using current context and results
- `sologm dice roll [notation] --reason "Reason for roll"` - Roll dice with specified notation and optional reason

### 4.3 External Integrations

#### 4.3.1 AI API
- Integration with Claude or other AI for oracle interpretation
- Plaintext formatted responses for simple parsing of interpretations

## 5. Non-Functional Requirements

### 5.1 Performance
- Commands should execute with minimal latency
- File operations should be optimized for quick access to game state

### 5.2 Security
- Appropriate handling of local data
- Secure storage of API credentials

### 5.3 Maintainability
- Well-documented code following Google Doc string format
- Type hints throughout for better IDE support and validation
- Modular design to allow for future expansion

### 5.4 Scalability
- Initial focus on core functionality rather than scalability concerns
- File structure design that will support later scaling if needed

## 6. Future Considerations (Not in Initial Scope, DO NOT BUILD)

- Built-in oracle tables and generators
- Character sheet management
- Multi-user support
- Database integration for larger game histories
- Integration with other RPG tools
- Data export/import functionality
- Campaign backup mechanisms
- Enhanced dice mechanics for specific game systems
- Pagination and filtering for long event histories
- Automated summaries or narratives from game history
- Direct integration between dice rolls and events
- Advanced feedback mechanisms for improving oracle interpretations
- Web or GUI interface options
