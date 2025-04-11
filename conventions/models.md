# Models

## Model Design
- Inherit from `Base` and `TimestampMixin`
- Use UUIDs (as strings) for primary keys
- Include `slug` field for human-readable identifiers where appropriate
- Use SQLAlchemy 2.0 ORM Declarative Models

## Relationships
- Define "owning" relationships in model classes (model with foreign key)
- Define "non-owning" relationships in `relationships.py`
- Use proper type annotations with `Mapped[Type]` or `Mapped[List[Type]]`
- Define cascade behavior explicitly

See [examples/models.md](examples/models.md) for relationship examples.

## Helper Properties

- Use `@property` for simple derived values and Python-only operations
- Use `@hybrid_property` for properties that need to work in both Python and SQL contexts:
  - Properties used in filtering (has_events, is_completed)
  - Properties used for aggregation (event_count)
  - Properties that check status or relationships (is_active)
- Always implement both instance-level and class-level expressions for hybrid properties
- Document hybrid properties in model documentation with both contexts

See [examples/models.md](examples/models.md) for hybrid property examples.
