# Solo RPG Helper CLI Development Plan

## Phase Instructions

### For Each Phase

1. **Start of Phase**
   - Create a branch for the phase (e.g., `git checkout -b phase-1-setup`)
   - Review the phase goals and expected deliverables
   - Prepare any necessary resources or dependencies

2. **For Each Part**
   - Create a feature branch from the phase branch (e.g., `git checkout -b part-1-1-environment`)
   - Work through each step in order
   - After completing a part, merge back to the phase branch
   - Update COMPLETED.md with completed steps (see format below)

3. **End of Phase**
   - Ensure all tests for the phase pass successfully
   - Create a comprehensive demo script showing the functionality added in the phase
   - Record a short video or prepare a live demonstration of the new features
   - Document any challenges, decisions, or design changes in PHASE-NOTES.md
   - Create a pull request to merge the phase branch to main
   - Tag the repository with the phase completion (e.g., `git tag v0.1-phase1`)
   - Update project timeline if necessary

### COMPLETED.md Format

Use the following format to track completed work in COMPLETED.md:

```markdown
# Completed Work

## Phase X: [Phase Name]
Completed: [Date]

### Part X.Y: [Part Name]
Completed: [Date]

#### Steps:
- [x] Step 1
- [x] Step 2
...

### Demo X:
Completed: [Date]
Demo Link: [Link to demo script or recording]
```

### Demo Requirements

Each phase demo should:
1. Include a script of commands to run
2. Show practical use cases for the new functionality
3. Highlight any user experience improvements
4. Include sample output or expected behaviors
5. Be reproducible by team members or stakeholders

## Phase 1: Project Setup and Basic CLI Framework

### Part 1.1: Development Environment Setup
1. Create project directory structure
2. Setup Python virtual environment using uv
3. Create initial pyproject.toml with dependencies
4. Setup Git repository and add .gitignore
5. Setup pre-commit hooks for code quality (black, isort, mypy)
6. Test environment setup by verifying dependencies installation
7. **Run environment tests and confirm successful operation**

### Part 1.2: Project Skeleton
1. Create the base package structure following TDD architecture
2. Add empty __init__.py files to create proper package hierarchy
3. Create placeholder files for main modules
4. Add basic README.md with project overview
5. Test package structure by installing in development mode
6. **Run package installation tests and confirm successful operation**

### Part 1.3: Config and Logging
1. Implement configuration management in utils/config.py
2. Add environment variable handling for sensitive information
3. Create logging utilities in utils/logger.py
4. Implement custom error classes in utils/errors.py
5. Write tests for configuration, logging, and error handling
6. **Run utility tests and verify all tests pass successfully**

### Part 1.4: Basic CLI Framework
1. Create cli/main.py with Typer app setup
2. Implement global options (--debug, --config)
3. Add error handling decorator
4. Create basic CLI command structure
5. Write tests for CLI entry point
6. **Run CLI framework tests and confirm successful operation**

### Demo 1: Show project structure and basic CLI
```bash
# Show project structure
ls -la

# Install package in development mode
pip install -e .

# Run basic CLI with help command
sologm --help

# Show version information
sologm --version

# Show debug output
sologm --debug --help

# Try a command that doesn't exist yet to demonstrate error handling
sologm nonexistent-command
# Should show a friendly error message rather than a stack trace
```

## Phase 2: Game and Scene Management

### Part 2.1: Storage Foundation
1. Create the storage/file_manager.py module
2. Implement directory structure creation
3. Add YAML read/write functionality
4. Create active game/scene tracking
5. Write tests for file operations
6. **Run storage tests and verify all tests pass successfully**

### Part 2.2: Game Models and Logic
1. Create Game data model
2. Implement core/game.py functionality with active game tracking
3. Add create_game, list_games, and activate_game functions
4. Write tests for game management functions
5. **Run game logic tests and verify all tests pass successfully**

### Part 2.3: Game CLI Commands
1. Implement cli/game.py with game-related commands
2. Add game create command with interactive options
3. Add game list command with formatted output
4. Add game activate and info commands

### Part 2.4: Scene Models and Logic
1. Create Scene data model with separate status and current tracking
2. Implement core/scene.py functionality
3. Add create_scene, list_scenes, complete_scene, and set_current_scene functions
4. Add functions to track current scene separately from scene status
5. Write tests for scene management functions including status/current separation
6. **Run scene logic tests and verify all tests pass successfully**

### Part 2.5: Scene CLI Commands
1. Implement cli/scene.py with scene-related commands
2. Add scene create command
3. Add scene list and info commands showing both status and current indicators
4. Add scene complete command that only changes status
5. Add scene set-current command that only changes which scene is current
6. Write tests for scene commands verifying status/current separation
7. **Run scene CLI tests and verify all tests pass successfully**

### Demo 2: Game and Scene Management
```bash
# Create a new game
sologm game create --name "Fantasy Adventure" --description "A solo adventure in a fantasy world"
# Should create game and make it active

# Show game info
sologm game info
# Should display details of the active game

# Create another game
sologm game create --name "Space Explorer" --description "Exploring the galaxy alone"
# Should create game and make it active, replacing Fantasy Adventure

# List all games
sologm game list
# Should show both games, with Space Explorer marked as [active game]

# Switch active game
sologm game activate --id fantasy-adventure
# Should set Fantasy Adventure as active game

# Create a scene in the active game
sologm scene create --title "Departure" --description "Starting the journey"
# Should create scene with active status and set as current

# Create another scene
sologm scene create --title "Forest Path" --description "Entering the dark woods"
# Should create scene with active status and set as current

# List all scenes
sologm scene list
# Should show both scenes, with Forest Path marked as [current] and both showing status

# Show details of current scene
sologm scene info
# Should display details of the active scene

# Complete the current scene
sologm scene complete
# Should mark scene as complete without changing which scene is current

# Switch to a different scene
sologm scene set-current --id forest-path
# Should set Forest Path as current scene without changing its status

# Show directory structure to demonstrate storage
ls -la ~/.sologm/
# Should show organized file structure with games and scenes
```

## Phase 3: Event Tracking and Dice System

### Part 3.1: Event Models and Logic
1. Create Event data model
2. Implement core/event.py functionality
3. Add add_event and list_events functions
4. Write tests for event tracking functions
5. **Run event logic tests and verify all tests pass successfully**

### Part 3.2: Event CLI Commands
1. Implement cli/event.py with event-related commands
2. Add event add command
3. Add event list command with formatting
4. Write tests for event commands
5. **Run event CLI tests and verify all tests pass successfully**

### Part 3.3: Dice System Logic
1. Implement core/dice.py functionality
2. Create dice notation parser
3. Implement dice rolling logic
4. Add roll formatting with result breakdown
5. Write tests for dice system with multiple scenarios
6. **Run dice system tests and verify all tests pass successfully**

### Part 3.4: Dice CLI Commands
1. Implement cli/dice.py with dice-related commands
2. Add dice roll command with optional reason
3. Create colored output for dice results
4. Write tests for dice commands
5. **Run dice CLI tests and verify all tests pass successfully**

### Demo 3: Event Tracking and Dice Rolling
```bash
# Make sure we have an active game and scene
sologm game info
sologm scene info

# Add events to the current scene
sologm event add --text "Discovered an abandoned ship floating in space"
# Should add event and show confirmation

sologm event add --text "Found strange symbols etched into the hull"
# Should add another event

# List events in the current scene
sologm event list
# Should show the 2 events with timestamps

# List more events with a higher limit
sologm event list --limit 10
# Should show all events up to 10

# Roll some dice
sologm dice roll 1d20 --reason "Perception check"
# Should show a d20 roll with reason and formatted output

sologm dice roll 3d6+2 --reason "Damage roll"
# Should show 3d6+2 roll with individual dice results and the total

# Try complex dice notation
sologm dice roll 2d10-1 --reason "Skill check with penalty"
# Should show proper parsing of the modifier

# Roll without a reason
sologm dice roll 1d100
# Should work fine without the reason parameter
```

## Phase 4: Oracle Interpretation System

### Part 4.1: Anthropic API Client
1. Create integrations/anthropic.py module
2. Implement API key handling
3. Add client initialization with error handling
4. Implement basic message sending
5. Write tests with mocked API responses
6. **Run API client tests and verify all tests pass successfully**

### Part 4.2: Oracle Models and Logic
1. Create Interpretation data model
2. Implement core/oracle.py functionality
3. Create prompt building based on game context
4. Add response parsing for interpretations
5. Implement interpretation selection logic
6. Write tests for oracle interpretation system
7. **Run oracle logic tests and verify all tests pass successfully**

### Part 4.3: Oracle CLI Commands
1. Implement cli/oracle.py with oracle-related commands
2. Add oracle interpret command that stores result as current interpretation
3. Add oracle select command with interactive selection
4. Create user-friendly interpretation display

### Part 4.3.1: Current Interpretation Management
1. Add current interpretation tracking in game.yaml
2. Implement retry functionality for current interpretation
3. Update oracle select to use current interpretation by default
4. Add retry attempt tracking and context
5. Write tests for current interpretation management
6. **Run current interpretation tests and verify all tests pass successfully**

### Demo 4: Oracle Interpretation
```bash
# First make sure we have a game with some context
sologm game info
sologm scene info
sologm event list

# Set the API key (if not set via environment variable)
export ANTHROPIC_API_KEY=your_api_key_here

# Submit oracle results for interpretation
sologm oracle interpret --context "What do I find inside the abandoned ship?" --results "Focus, Danger, Technology" --count 3
# Should return 3 different interpretations with IDs and store as current interpretation

# The output should look something like:
# === INTERPRETATIONS ===
# 1. [interp-123] "Advanced Defense System"
#    You find a sophisticated defensive technology that's still active...
# 
# 2. [interp-456] "Alien Research Station"
#    The ship appears to be a research facility focused on studying...
# 
# 3. [interp-789] "Malfunctioning Engine Core"
#    The heart of the ship is unstable, with a dangerously overloaded...

# Select from current interpretation set (no need to specify set ID)
sologm oracle select --id interp-456
# Should add the selected interpretation as an event

# Verify the event was added
sologm event list
# Should show the new event from the interpretation

# Request new interpretations for the same context/results
sologm oracle retry
# Should show 3 new, different interpretations for the same context

# Try another interpretation with more context
sologm oracle interpret --context "I try to access the ship's computer. What happens?" --results "Success, Information, Danger" --count 4
# Should show 4 new interpretations and update current interpretation
```

## Phase 5: Advanced Features and Enhancement

### Part 5.1: Enhanced Data Models
1. Add additional fields and validation to models
2. Implement data migration for existing files
3. Add metadata and relationship improvements
4. Write tests for enhanced models
5. **Run enhanced model tests and verify all tests pass successfully**

### Part 5.2: CLI Experience Enhancements
1. Add tab completion for commands
2. Improve help text and documentation
3. Enhance error messages with suggestions
4. Add progress indicators for long-running operations
5. Write tests for CLI enhancements
6. **Run CLI enhancement tests and verify all tests pass successfully**

### Part 5.3: Advanced Oracle Features
1. Implement interpretation history browsing
2. Add context refinement options
3. Create interpretation templates
4. Write tests for advanced oracle features
5. **Run advanced oracle feature tests and verify all tests pass successfully**

### Demo 5: Enhanced User Experience
```bash
# Enable tab completion (bash example)
source <(sologm --install-completion bash)
# Then demonstrate tab completion working
sologm g<TAB>  # Should complete to "game"
sologm game <TAB>  # Should show available game subcommands

# Show improved help text
sologm --help
# Should display more detailed help with examples

# Show improved error messages
sologm scene create  # Missing required arguments
# Should show helpful error with suggestion on correct usage

# Demonstrate interpretation history
sologm oracle history
# Should show previous oracle interpretations

# View a specific interpretation from history
sologm oracle history --id interp-456
# Should show full details of that interpretation

# Use a template for oracle interpretation
sologm oracle interpret --template "discovery" --results "Mystery, Ancient, Power"
# Should use a predefined template for the context

# Refine an existing interpretation with more context
sologm oracle refine --id interp-789 --additional-context "I examine it more carefully"
# Should generate new interpretations based on the original plus additional context
```

## Phase 6: Final Polish and Distribution

### Part 6.1: Documentation
1. Create detailed README.md with installation and usage instructions
2. Add docstrings to all public functions and classes
3. Create user guide with examples
4. Add changelog.md for version tracking
5. Test documentation by having someone follow the instructions
6. **Verify documentation accuracy and completeness**

### Part 6.2: Distribution Package
1. Finalize pyproject.toml for distribution
2. Create setup.py as needed
3. Add package metadata and entry points
4. Build distribution package
5. Test installation from package
6. **Verify successful installation from distribution package**

### Part 6.3: Final Testing
1. Perform integration testing for complete workflows
2. Test on multiple platforms (Windows, macOS, Linux)
3. Check performance with large datasets
4. Validate error handling in edge cases
5. Ensure test coverage meets targets
6. **Run comprehensive test suite and verify all tests pass successfully**

### Demo 6: Final Product
```bash
# Build the distribution package
python -m build

# Install from the package
pip install dist/sologm-0.1.0.tar.gz

# Run test coverage report
pytest --cov=sologm

# Demonstrate complete workflow from start to finish
sologm game create --name "Epic Quest" --description "A heroic journey"
sologm scene create --title "The Village" --description "Starting in a small village"
sologm event add --text "Meet a mysterious stranger who needs help"
sologm dice roll 2d6+1 --reason "Persuasion check to hear their story"
sologm oracle interpret --context "What task does the stranger need help with?" --results "Danger, Ancient, Secret"
sologm oracle select --id [generated-id]
sologm scene create --title "The Journey Begins" --description "Setting out from the village"

# Show data export
sologm export --game-id epic-quest --format json
# Should output game data in JSON format

# Demonstrate cross-platform compatibility by showing it working on different systems
# (if available during demo)

# Show full help with all available commands
sologm --help
```

## Implementation Notes

1. **Feature-First Development**: Each feature is developed end-to-end from storage to CLI in a single phase.

2. **Minimal Viable Commands**: Implement basic CLI commands early, then enhance them in later phases.

3. **Interactive Testing**: Use the CLI throughout development to identify usability issues.

4. **Continuous Integration**: Setup CI to run tests automatically for each commit.

5. **User Feedback Loop**: Collect feedback on the CLI experience during each demo.

6. **Test-Driven Development**: Always write tests before implementing functionality and verify tests pass after implementation.
