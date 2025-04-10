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
- When creating a new Act, the system checks if there's an active, uncompleted Act
  - If an uncompleted Act exists, the system fails with a clear error message
  - The user must explicitly complete the current Act before creating a new one
  - This enforces a structured workflow and prevents accidental Act creation
- When activating a different Game, the system remembers which Act was active in that Game

## Act Model Design

### SQLAlchemy Model

```python
class ActStatus(enum.Enum):
    """Enumeration of possible act statuses."""
    
    ACTIVE = "active"
    COMPLETED = "completed"

class Act(Base, TimestampMixin):
    """SQLAlchemy model representing an act in a game."""
    
    __tablename__ = "acts"
    __table_args__ = (UniqueConstraint("game_id", "slug", name="uix_game_act_slug"),)
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(nullable=True)  # Can be null for untitled acts
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ActStatus] = mapped_column(
        Enum(ActStatus), nullable=False, default=ActStatus.ACTIVE
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    
    # Relationships this model owns
    scenes: Mapped[List["Scene"]] = relationship(
        "Scene", back_populates="act", cascade="all, delete-orphan"
    )
    
    @validates("slug")
    def validate_slug(self, _: str, slug: str) -> str:
        """Validate the act slug."""
        if not slug or not slug.strip():
            raise ValueError("Act slug cannot be empty")
        return slug
    
    @classmethod
    def create(
        cls, game_id: str, title: Optional[str], description: Optional[str], sequence: int
    ) -> "Act":
        """Create a new act with a unique ID and slug.
        
        Args:
            game_id: ID of the game this act belongs to.
            title: Optional title of the act (can be None for untitled acts).
            description: Optional description of the act.
            sequence: Sequence number of the act.
        Returns:
            A new Act instance.
        """
        # Generate a URL-friendly slug from the title and sequence
        # For untitled acts, use a placeholder
        if title:
            act_slug = f"act-{sequence}-{slugify(title)}"
        else:
            act_slug = f"act-{sequence}-untitled"
            
        return cls(
            id=str(uuid.uuid4()),
            slug=act_slug,
            game_id=game_id,
            title=title,
            description=description,
            status=ActStatus.ACTIVE,
            sequence=sequence,
        )
```

### Relationship Updates

The Act model introduces a new layer in the hierarchy between Game and Scene. This requires updates to the existing relationships:

1. In the Game model (game.py):
```python
# Game model owns the relationship to Act
acts: Mapped[List["Act"]] = relationship(
    "Act", back_populates="game", cascade="all, delete-orphan"
)
```

2. In the Scene model (scene.py):
```python
# Update the Scene model to reference acts instead of games
# Remove the game_id field
# game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False)

# Add the act_id field
act_id: Mapped[str] = mapped_column(ForeignKey("acts.id"), nullable=False)
```

3. In the relationships.py file:
```python
# Non-owning relationships only

# Act relationships
Act.game = relationship("Game", back_populates="acts")

# Scene relationships
Scene.act = relationship("Act", back_populates="scenes")
```

### Migration Considerations

When implementing this model, a database migration will be needed to:

1. Create the new acts table
2. For existing games, create a default "Act 1" for each game
3. Update all existing scenes to reference their game's default act
4. Set the is_active flag on the default act for each game

This ensures backward compatibility with existing data while introducing the new act structure.
