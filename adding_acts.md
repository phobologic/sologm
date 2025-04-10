## Act: Relationships and Functionality

The intent of integrating Acts into the Solo RPG Helper is to create a more natural narrative structure that bridges the gap between the overall Game and individual Scenes. Acts represent complete narrative situations or problems that unfold through multiple connected Scenes, allowing for better organization of storytelling while supporting the emergent nature of solo roleplaying by enabling players to name and describe these narrative units retrospectively once their significance becomes clear.

### Game to Act Relationship
- A Game can contain multiple Acts
- Acts belong to exactly one Game
- A Game can have one "active" Act at a time
- Acts are sequenced within a Game (Act 1, Act 2, etc.)
- When a new Game is created, an initial untitled Act can be automatically created

### Act Creation and Naming
- Acts can be created without a title or description ("Untitled Act")
- The active Act accumulates scenes and events as the story progresses
- When an Act is completed, the user can:
  - Manually provide a title and description
  - Use AI to generate a title and description based on the scenes and events that occurred
  - Leave it untitled if desired

### Act to Scene Relationship
- An Act contains multiple Scenes
- Scenes belong to exactly one Act (not directly to a Game)
- An Act can have one "active" Scene at a time
- Scenes are sequenced within an Act
- An untitled Act can still contain Scenes and progress normally

### Command Structure Updates
- `sologm act create` - Creates a new act (optionally with title/description)
- `sologm act list` - Lists all acts, including untitled ones
- `sologm act info` - Shows details of current active act
- `sologm act edit` - Edit details of current active act (optionally take title/description as options, or use editor)
- `sologm act complete` - Marks the current act as complete, and opens an editor to set title and description with options:
  - `--ai` - Use AI to generate a title and description if they don't already exist based on act content in the editor
  - `--force` - Override the title/description, even if they are already set, with AI

### AI Title/Description Generation
When using the `--ai` flag:
- The system would gather all scenes and events from the act, as well as context from the game itself for overall direction.
- Format this information as context for the AI
- Request a concise, thematic title and/or description that summarizes the act's narrative
- Apply the generated content to the act metadata
- Only generate a field (title, description) if it hasn't been provided manually.
- If a field has been added manually to an act, provide that in the context to AI to generate the other field.
- If both fields have been provided, and the "--force" flag is not given, throw an error.

### Oracle Integration
- Oracle interpretations would include the current act's context (even if untitled)
- The AI would be made aware of the concept of untitled acts in progress
- When interpreting oracle results, the system would provide:
  - Game description
  - Current Act information (even if untitled)
  - Current Scene description
  - Recent Events

### Workflow Considerations
- When completing an Act, the user is prompted to name it or generate a name
- When creating a new Act, the previous Act is automatically completed - but verify with the user that they are ready for that.
- When activating a different Game, the system remembers which Act was active in that Game
