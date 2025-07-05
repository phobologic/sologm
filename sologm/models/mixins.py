"""Model mixins for automated property generation.

This module provides pattern-specific mixins that automatically generate hybrid
properties from configuration. This eliminates code duplication across models
while maintaining identical behavior to manually implemented properties.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property

if TYPE_CHECKING:
    from sologm.models.base import Base


@dataclass
class ExistenceConfig:
    """Configuration for existence check properties.

    This dataclass defines how to generate has_X hybrid properties that check
    for the existence of related entities.

    Args:
        model: The related model class (e.g., Event, DiceRoll)
        foreign_key: The foreign key column name (e.g., 'scene_id', 'act_id')
        relationship_name: Name of the relationship attribute. Defaults to config key.
    """

    model: Type["Base"]
    foreign_key: str
    relationship_name: Optional[str] = None


class ExistenceCheckMixin:
    """Mixin providing has_X hybrid properties for relationship existence checks.

    This mixin automatically generates hybrid properties that check whether related
    entities exist. Each property works in both Python and SQL contexts:

    - Python context: Uses loaded relationships (bool(self.relationship))
    - SQL context: Uses EXISTS subquery for efficient database queries

    Usage:
        class Scene(ExistenceCheckMixin, Base, TimestampMixin):
            _existence_configs = {
                'events': ExistenceConfig(
                    model=Event,
                    foreign_key='scene_id'
                ),
                'dice_rolls': ExistenceConfig(
                    model=DiceRoll,
                    foreign_key='scene_id'
                ),
            }
            # This automatically generates has_events and has_dice_rolls properties
    """

    # Configuration attribute (defined by implementing classes)
    _existence_configs: Dict[str, ExistenceConfig]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Generate hybrid properties when class is created.

        This method is called automatically when a class inherits from this mixin.
        It processes the _existence_configs attribute and generates the appropriate
        hybrid properties.

        Args:
            **kwargs: Additional keyword arguments passed to super().__init_subclass__
        """
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "_existence_configs"):
            cls._generate_existence_properties()

    @classmethod
    def _generate_existence_properties(cls) -> None:
        """Generate has_X properties from configuration.

        Iterates through _existence_configs and creates a hybrid property for each
        configured relationship. Each property follows the pattern:
        - Property name: has_{config_key}
        - Python behavior: bool(self.relationship)
        - SQL behavior: EXISTS subquery
        """
        for config_key, config in cls._existence_configs.items():
            cls._create_existence_property(config_key, config)

    @classmethod
    def _create_existence_property(cls, name: str, config: ExistenceConfig) -> None:
        """Create individual has_X hybrid property.

        Generates a hybrid property with both Python and SQL implementations
        that behave identically to manually written existence check properties.

        Args:
            name: The configuration key, used to generate property name (has_{name})
            config: ExistenceConfig containing model and foreign key information

        Raises:
            AttributeError: If the configured relationship doesn't exist on the model
            ValueError: If the configuration is invalid
        """
        property_name = f"has_{name}"
        relationship_name = config.relationship_name or name

        # Validate that the relationship exists on the model
        if not hasattr(cls, relationship_name):
            raise AttributeError(
                f"Model {cls.__name__} does not have relationship "
                f"'{relationship_name}' specified in existence config for '{name}'"
            )

        # Create Python context method
        def python_method(self) -> bool:
            """Check if this entity has any related items.

            Uses the loaded relationship to determine existence without
            triggering additional database queries.

            Returns:
                True if related items exist, False otherwise.
            """
            relationship = getattr(self, relationship_name)
            return bool(relationship)

        # Create SQL expression method
        def sql_expression(cls_inner):
            """SQL expression for existence check.

            Creates an EXISTS subquery to efficiently check for related items
            in the database without loading the actual relationships.

            Returns:
                SQLAlchemy expression that can be used in queries and filters.
            """
            return (
                select(1)
                .where(getattr(config.model, config.foreign_key) == cls_inner.id)
                .exists()
                .label(property_name)
            )

        # Set proper docstrings with model-specific information
        python_method.__doc__ = (
            f"Check if this {cls.__name__.lower()} has any {relationship_name}.\n\n"
            "Works in Python context by checking the loaded relationship.\n\n"
            "Returns:\n"
            f"    True if {relationship_name} exist, False otherwise."
        )

        sql_expression.__doc__ = f"SQL expression for {property_name}."

        # Create the hybrid property
        hybrid_prop = hybrid_property(python_method)
        hybrid_prop = hybrid_prop.expression(sql_expression)

        # Add the property to the class
        setattr(cls, property_name, hybrid_prop)


@dataclass
class FilterCondition:
    """Configuration for filtering conditions in count operations.

    This dataclass defines how to apply filtering conditions when counting
    related entities. It supports various comparison operators and values.

    Args:
        field: The field name to filter on (e.g., 'is_selected', 'is_active')
        operator: The comparison operator to use. Defaults to 'eq' (equals)
        value: The value to compare against. Defaults to True
    """

    field: str
    operator: str = "eq"  # eq, ne, gt, lt, gte, lte, in, not_in
    value: Any = True


@dataclass
class CountConfig:
    """Base configuration for count property generation.

    This is the base class for all count configurations. It defines the common
    fields needed for any type of counting operation.

    Args:
        model: The related model class to count (e.g., Event, DiceRoll)
        foreign_key: The foreign key column name (e.g., 'scene_id', 'act_id')
        relationship_name: Name of the relationship attribute. Defaults to config key.
    """

    model: Type["Base"]
    foreign_key: str
    relationship_name: Optional[str] = None


@dataclass
class DirectCountConfig:
    """Configuration for direct relationship counts.

    Used for simple counts where the target entity is directly related
    to the source entity via a single foreign key relationship.

    Example: Game.act_count - counts acts directly related to a game.
    """

    model: Type["Base"]
    foreign_key: str
    relationship_name: Optional[str] = None


@dataclass
class CrossTableCountConfig:
    """Configuration for counts across relationship paths.

    Used for counts where the target entity is related through one or more
    intermediate relationships that need to be traversed.

    Args:
        relationship_path: List of relationship attribute names to traverse

    Example: Act.event_count - counts events through the scenes relationship.
             relationship_path=['scenes', 'events']
    """

    model: Type["Base"]
    foreign_key: str
    relationship_path: List[str]
    relationship_name: Optional[str] = None


@dataclass
class FilteredCountConfig:
    """Configuration for filtered counts with no relationship path.

    Used for counts where the target entity is directly related but needs
    to be filtered based on some condition.

    Args:
        filter_condition: The filtering condition to apply

    Example: InterpretationSet.selected_interpretation_count
             filter_condition=FilterCondition(field='is_selected', value=True)
    """

    model: Type["Base"]
    foreign_key: str
    filter_condition: FilterCondition
    relationship_name: Optional[str] = None


@dataclass
class FilteredCrossTableCountConfig:
    """Configuration for filtered counts across relationships.

    Used for the most complex counts where the target entity is related
    through intermediate relationships AND needs to be filtered.

    Args:
        relationship_path: List of relationship attribute names to traverse
        filter_condition: The filtering condition to apply

    Example: Scene.selected_interpretation_count
             relationship_path=['interpretation_sets', 'interpretations']
             filter_condition=FilterCondition(field='is_selected', value=True)
    """

    model: Type["Base"]
    foreign_key: str
    relationship_path: List[str]
    filter_condition: FilterCondition
    relationship_name: Optional[str] = None


class CountingMixin:
    """Mixin providing X_count hybrid properties for relationship counting.

    This mixin automatically generates hybrid properties that count related
    entities. Each property works in both Python and SQL contexts:

    - Python context: Uses loaded relationships (len(self.relationship))
    - SQL context: Uses COUNT subquery for efficient database queries

    Supports four types of counting:
    1. Direct counts (DirectCountConfig)
    2. Cross-table counts (CrossTableCountConfig)
    3. Filtered counts (FilteredCountConfig)
    4. Filtered cross-table counts (FilteredCrossTableCountConfig)

    Usage:
        class Scene(CountingMixin, Base, TimestampMixin):
            _counting_configs = {
                'events': DirectCountConfig(
                    model=Event,
                    foreign_key='scene_id'
                ),
                'selected_interpretations': FilteredCrossTableCountConfig(
                    model=Interpretation,
                    foreign_key='scene_id',
                    relationship_path=['interpretation_sets', 'interpretations'],
                    filter_condition=FilterCondition(field='is_selected', value=True)
                ),
            }
            # This automatically generates event_count and selected_interpretation_count
    """

    # Configuration attribute (defined by implementing classes)
    _counting_configs: Dict[
        str,
        Union[
            DirectCountConfig,
            CrossTableCountConfig,
            FilteredCountConfig,
            FilteredCrossTableCountConfig,
        ],
    ]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Generate hybrid properties when class is created.

        This method is called automatically when a class inherits from this mixin.
        It processes the _counting_configs attribute and generates the appropriate
        hybrid properties.

        Args:
            **kwargs: Additional keyword arguments passed to super().__init_subclass__
        """
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "_counting_configs"):
            cls._generate_counting_properties()

    @classmethod
    def _generate_counting_properties(cls) -> None:
        """Generate X_count properties from configuration.

        Iterates through _counting_configs and creates a hybrid property for each
        configured relationship. Each property follows the pattern:
        - Property name: {config_key}_count
        - Python behavior: len(self.relationship) or sum/filter as needed
        - SQL behavior: COUNT subquery with appropriate JOINs and filters
        """
        for config_key, config in cls._counting_configs.items():
            cls._validate_count_config(config_key, config)
            cls._create_counting_property(config_key, config)

    @classmethod
    def _validate_count_config(
        cls,
        name: str,
        config: Union[
            DirectCountConfig,
            CrossTableCountConfig,
            FilteredCountConfig,
            FilteredCrossTableCountConfig,
        ],
    ) -> None:
        """Validate count configuration for correctness.

        Performs comprehensive validation of the count configuration to ensure
        all required relationships and fields exist and are properly configured.

        Args:
            name: The configuration key name
            config: The count configuration to validate

        Raises:
            AttributeError: If configured relationships or fields don't exist
            ValueError: If the configuration is invalid
        """
        # Validate base relationship exists
        relationship_name = config.relationship_name or name
        if not hasattr(cls, relationship_name):
            raise AttributeError(
                f"Model {cls.__name__} does not have relationship "
                f"'{relationship_name}' specified in counting config for '{name}'"
            )

        # Validate foreign key exists on target model
        # Check if the foreign key column exists using multiple approaches
        try:
            has_fk = False

            # Method 1: Check if it's a mapped column attribute
            if hasattr(config.model, config.foreign_key):
                has_fk = True

            # Method 2: Check the SQLAlchemy table columns if available
            elif (
                hasattr(config.model, "__table__")
                and config.model.__table__ is not None
            ):
                if config.foreign_key in config.model.__table__.columns:
                    has_fk = True

            # Method 3: Check __annotations__ for type hints
            elif (
                hasattr(config.model, "__annotations__")
                and config.foreign_key in config.model.__annotations__
            ):
                has_fk = True

            if not has_fk:
                raise AttributeError(
                    f"Foreign key '{config.foreign_key}' not found on "
                    f"{config.model.__name__} in counting config for '{name}'"
                )

        except AttributeError:
            # Re-raise AttributeError for missing foreign keys
            raise
        except Exception:
            # For other exceptions (e.g., table not configured yet), skip validation
            pass

        # Validate relationship path if specified
        # Note: Temporarily disable strict validation during class creation to avoid
        # SQLAlchemy configuration ordering issues. Validation will happen at runtime.
        # if isinstance(config, (CrossTableCountConfig, FilteredCrossTableCountConfig)):
        #     cls._validate_relationship_path(config.relationship_path, cls)

        # Validate filter condition if specified
        if isinstance(config, (FilteredCountConfig, FilteredCrossTableCountConfig)):
            cls._validate_filter_condition(config.filter_condition, config.model)

    @classmethod
    def _validate_relationship_path(
        cls, path: List[str], source_model: Type["Base"]
    ) -> None:
        """Validate that relationship path is valid.

        Walks through the relationship path to ensure each step exists and
        leads to the next expected model in the chain.

        Args:
            path: List of relationship attribute names to validate
            source_model: The starting model class

        Raises:
            AttributeError: If any step in the path doesn't exist
            ValueError: If any step is not a valid relationship
        """
        current_model = source_model

        for step in path:
            if not hasattr(current_model, step):
                raise AttributeError(
                    f"Relationship '{step}' not found on {current_model.__name__} "
                    f"in relationship path {path}"
                )

            relationship = getattr(current_model, step)
            # Validate it's actually a relationship by checking for mapper
            if not hasattr(relationship.property, "mapper"):
                raise ValueError(
                    f"'{step}' is not a valid relationship on {current_model.__name__} "
                    f"in relationship path {path}"
                )

            current_model = relationship.property.mapper.class_

    @classmethod
    def _validate_filter_condition(
        cls, condition: FilterCondition, model: Type["Base"]
    ) -> None:
        """Validate that filter condition is applicable to model.

        Checks that the specified field exists on the target model and that
        the operator is supported.

        Args:
            condition: The filter condition to validate
            model: The model class the condition will be applied to

        Raises:
            AttributeError: If the field doesn't exist on the model
            ValueError: If the operator is not supported
        """
        if not hasattr(model, condition.field):
            raise AttributeError(
                f"Field '{condition.field}' not found on {model.__name__} "
                f"in filter condition"
            )

        # Validate operator is supported
        supported_operators = {"eq", "ne", "gt", "lt", "gte", "lte", "in", "not_in"}
        if condition.operator not in supported_operators:
            raise ValueError(
                f"Operator '{condition.operator}' not supported. "
                f"Supported operators: {sorted(supported_operators)}"
            )

    @classmethod
    def _create_counting_property(
        cls,
        name: str,
        config: Union[
            DirectCountConfig,
            CrossTableCountConfig,
            FilteredCountConfig,
            FilteredCrossTableCountConfig,
        ],
    ) -> None:
        """Create individual X_count hybrid property.

        Generates a hybrid property with both Python and SQL implementations
        that behave identically to manually written count properties. The
        implementation varies based on the config type.

        Args:
            name: The configuration key, used to generate property name ({name}_count)
            config: Count configuration containing model and counting information
        """
        property_name = f"{name}_count"
        relationship_name = config.relationship_name or name

        # Create Python context method
        python_method = cls._build_python_count(relationship_name, config)

        # Create SQL expression method
        sql_expression = cls._build_sql_count(property_name, config)

        # Set proper docstrings with model-specific information
        python_method.__doc__ = (
            f"Get the number of {name} for this {cls.__name__.lower()}.\n\n"
            "Works in Python context by counting loaded relationships.\n\n"
            "Returns:\n"
            f"    The count of {name} as an integer."
        )

        sql_expression.__doc__ = f"SQL expression for {property_name}."

        # Create the hybrid property
        hybrid_prop = hybrid_property(python_method)
        hybrid_prop = hybrid_prop.expression(sql_expression)

        # Add the property to the class
        setattr(cls, property_name, hybrid_prop)

    @classmethod
    def _build_python_count(
        cls,
        relationship_name: str,
        config: Union[
            DirectCountConfig,
            CrossTableCountConfig,
            FilteredCountConfig,
            FilteredCrossTableCountConfig,
        ],
    ):
        """Build Python count method based on configuration type.

        Args:
            relationship_name: Name of the relationship to count
            config: Count configuration determining how to count

        Returns:
            Function that implements Python context counting
        """
        if isinstance(config, DirectCountConfig):
            # Simple direct count: len(self.relationship)
            def python_method(self) -> int:
                relationship = getattr(self, relationship_name)
                return len(relationship)

        elif isinstance(config, CrossTableCountConfig):
            # Cross-table count: navigate through relationship path and count
            # final items
            def python_method(self) -> int:
                def count_through_path(items, path_steps):
                    """Recursively count through nested relationship path."""
                    if not path_steps:
                        # Base case: we've reached the final collection, count its items
                        return len(items) if hasattr(items, "__len__") else 0

                    # Get the next step in the path
                    next_step = path_steps[0]
                    remaining_steps = path_steps[1:]

                    total_count = 0
                    # Iterate through current items and navigate to next level
                    for item in items:
                        next_items = getattr(item, next_step, [])
                        total_count += count_through_path(next_items, remaining_steps)

                    return total_count

                # Start with the initial relationship
                relationship = getattr(self, relationship_name)
                # Skip the first step in path since we already have that relationship
                remaining_path = config.relationship_path[1:]
                return count_through_path(relationship, remaining_path)

        elif isinstance(config, FilteredCountConfig):
            # Filtered count: count items that match filter condition
            def python_method(self) -> int:
                relationship = getattr(self, relationship_name)
                count = 0
                for item in relationship:
                    if cls._apply_filter_condition(item, config.filter_condition):
                        count += 1
                return count

        elif isinstance(config, FilteredCrossTableCountConfig):
            # Filtered cross-table count: navigate through relationship path
            # and count filtered items
            def python_method(self) -> int:
                def count_filtered_through_path(items, path_steps):
                    """Recursively count through nested relationship path.

                    Applies filtering at the final level.
                    """
                    if not path_steps:
                        # Base case: we've reached the final collection,
                        # count filtered items
                        filtered_count = 0
                        for item in items:
                            if cls._apply_filter_condition(
                                item, config.filter_condition
                            ):
                                filtered_count += 1
                        return filtered_count

                    # Get the next step in the path
                    next_step = path_steps[0]
                    remaining_steps = path_steps[1:]

                    total_count = 0
                    # Iterate through current items and navigate to next level
                    for item in items:
                        next_items = getattr(item, next_step, [])
                        total_count += count_filtered_through_path(
                            next_items, remaining_steps
                        )

                    return total_count

                # Start with the initial relationship
                relationship = getattr(self, relationship_name)
                # Skip the first step in path since we already have that relationship
                remaining_path = config.relationship_path[1:]
                return count_filtered_through_path(relationship, remaining_path)

        return python_method

    @classmethod
    def _build_sql_count(
        cls,
        property_name: str,
        config: Union[
            DirectCountConfig,
            CrossTableCountConfig,
            FilteredCountConfig,
            FilteredCrossTableCountConfig,
        ],
    ):
        """Build SQL count expression based on configuration type.

        Args:
            property_name: Name of the property being created
            config: Count configuration determining SQL generation

        Returns:
            Function that returns SQLAlchemy expression for counting
        """

        def sql_expression(cls_inner):
            """SQL expression for count property."""

            if isinstance(config, DirectCountConfig):
                # Simple direct count with single WHERE clause
                return (
                    select(func.count(config.model.id))
                    .where(getattr(config.model, config.foreign_key) == cls_inner.id)
                    .scalar_subquery()
                    .label(property_name)
                )

            elif isinstance(config, CrossTableCountConfig):
                # Cross-table count with explicit JOINs
                query = select(func.count(config.model.id)).select_from(config.model)

                # Build JOIN chain through relationship path
                # Start from the target model and work backwards
                # Note: This is a simplified approach - in practice, we'd need to
                # resolve the actual model classes from the relationship path
                # Implementation would require relationship introspection
                pass

                # For now, use implicit JOIN with WHERE clause (like existing code)
                return cls._build_implicit_join_count(cls_inner, config, property_name)

            elif isinstance(config, FilteredCountConfig):
                # Direct count with filter condition
                query = select(func.count(config.model.id))
                query = query.where(
                    getattr(config.model, config.foreign_key) == cls_inner.id
                )
                query = cls._add_filter_condition_to_query(
                    query, config.filter_condition, config.model
                )
                return query.scalar_subquery().label(property_name)

            elif isinstance(config, FilteredCrossTableCountConfig):
                # Cross-table count with filter - use implicit JOIN for simplicity
                return cls._build_implicit_join_count(
                    cls_inner, config, property_name, config.filter_condition
                )

        return sql_expression

    @classmethod
    def _build_implicit_join_count(
        cls,
        cls_inner,
        config: Union[
            DirectCountConfig,
            CrossTableCountConfig,
            FilteredCountConfig,
            FilteredCrossTableCountConfig,
        ],
        property_name: str,
        filter_condition: Optional[FilterCondition] = None,
    ):
        """Build count query using implicit JOINs via WHERE clauses.

        This mirrors the existing pattern used in the codebase for cross-table counts.
        """
        if isinstance(config, (CrossTableCountConfig, FilteredCrossTableCountConfig)):
            # Build cross-table count using implicit JOINs via WHERE clauses
            # This mirrors the existing pattern used in Act and Scene models
            query = select(func.count(config.model.id))

            # Build WHERE conditions based on relationship path
            where_conditions = cls._build_relationship_path_conditions(
                cls_inner, config.relationship_path, config.model
            )

            if where_conditions is not None:
                query = query.where(where_conditions)

            # Add filter condition if specified
            if filter_condition:
                query = cls._add_filter_condition_to_query(
                    query, filter_condition, config.model
                )

            return query.scalar_subquery().label(property_name)

        # Fallback to direct count
        query = select(func.count(config.model.id))
        query = query.where(getattr(config.model, config.foreign_key) == cls_inner.id)

        if filter_condition:
            query = cls._add_filter_condition_to_query(
                query, filter_condition, config.model
            )

        return query.scalar_subquery().label(property_name)

    @classmethod
    def _build_relationship_path_conditions(
        cls, source_model, relationship_path: List[str], target_model: Type["Base"]
    ):
        """Build WHERE conditions for cross-table counts via relationship paths.

        This method creates implicit JOIN conditions using WHERE clauses that mirror
        the patterns used in existing manual implementations like Act.event_count.

        Args:
            source_model: The source model class (e.g., Act)
            relationship_path: List of relationship names to traverse
                (e.g., ['scenes', 'events'])
            target_model: The target model to count (e.g., Event)

        Returns:
            SQLAlchemy condition that can be used in WHERE clause,
                or None if path is empty

        Examples:
            For Act.event_count with path ['scenes', 'events']:
                Returns: (Scene.act_id == source_model.id) &
                    (Event.scene_id == Scene.id)
        """
        if not relationship_path:
            return None

        # Import models locally to avoid circular dependencies
        # This mirrors the pattern used in existing manual implementations
        intermediate_models = cls._resolve_intermediate_models(
            source_model, relationship_path
        )

        if not intermediate_models:
            return None

        conditions = []

        # Build conditions step by step through the relationship path
        # First condition: connect source to first intermediate
        if len(intermediate_models) >= 1:
            first_intermediate = intermediate_models[0]
            foreign_key = cls._get_foreign_key_name(source_model, first_intermediate)
            if foreign_key:
                condition = getattr(first_intermediate, foreign_key) == source_model.id
                conditions.append(condition)

        # Middle conditions: connect intermediate models to each other
        for i in range(len(intermediate_models) - 1):
            current_model = intermediate_models[i]
            next_model = intermediate_models[i + 1]
            foreign_key = cls._get_foreign_key_name(current_model, next_model)
            if foreign_key:
                condition = getattr(next_model, foreign_key) == current_model.id
                conditions.append(condition)

        # Last condition: connect last intermediate to target (if different)
        if len(intermediate_models) >= 1:
            last_intermediate = intermediate_models[-1]
            if last_intermediate != target_model:
                foreign_key = cls._get_foreign_key_name(last_intermediate, target_model)
                if foreign_key:
                    condition = (
                        getattr(target_model, foreign_key) == last_intermediate.id
                    )
                    conditions.append(condition)

        # Combine all conditions with AND
        if conditions:
            result = conditions[0]
            for condition in conditions[1:]:
                result = result & condition
            return result

        return None

    @classmethod
    def _resolve_intermediate_models(
        cls, source_model, relationship_path: List[str]
    ) -> List[Type["Base"]]:
        """Resolve the intermediate models in a relationship path.

        This walks through the relationship path and returns the model classes
        for each step in the path.
        """
        models = []
        current_model = source_model

        for relationship_name in relationship_path:
            if not hasattr(current_model, relationship_name):
                return []

            relationship = getattr(current_model, relationship_name)
            if hasattr(relationship.property, "mapper"):
                next_model = relationship.property.mapper.class_
                models.append(next_model)
                current_model = next_model
            else:
                return []

        return models

    @classmethod
    def _get_foreign_key_name(
        cls, source_model: Type["Base"], target_model: Type["Base"]
    ) -> Optional[str]:
        """Get the foreign key name that connects source_model to target_model.

        This searches through target_model's columns to find foreign keys
        that reference source_model's table.
        """
        source_table = getattr(source_model, "__tablename__", "")
        if not source_table:
            return None

        # Check each column in target_model for foreign keys to source_model
        for column in target_model.__table__.columns:
            # Check if this column has foreign keys
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    # Check if this foreign key references the source table
                    if fk.column.table.name == source_table:
                        return column.name

        # Fallback to naming patterns if introspection fails
        if source_table.endswith("s"):
            # scenes -> scene_id, acts -> act_id
            fk_name = f"{source_table[:-1]}_id"
        else:
            fk_name = f"{source_table}_id"

        # Special case for InterpretationSet -> set_id
        if source_model.__name__ == "InterpretationSet":
            fk_name = "set_id"

        if hasattr(target_model, fk_name):
            return fk_name

        return None

    @classmethod
    def _add_filter_condition_to_query(
        cls, query, condition: FilterCondition, model: Type["Base"]
    ):
        """Add filter condition to SQL query.

        Args:
            query: SQLAlchemy query to add condition to
            condition: Filter condition to apply
            model: Model class the condition applies to

        Returns:
            Modified query with filter condition applied
        """
        field = getattr(model, condition.field)

        if condition.operator == "eq":
            return query.where(field == condition.value)
        elif condition.operator == "ne":
            return query.where(field != condition.value)
        elif condition.operator == "gt":
            return query.where(field > condition.value)
        elif condition.operator == "lt":
            return query.where(field < condition.value)
        elif condition.operator == "gte":
            return query.where(field >= condition.value)
        elif condition.operator == "lte":
            return query.where(field <= condition.value)
        elif condition.operator == "in":
            return query.where(field.in_(condition.value))
        elif condition.operator == "not_in":
            return query.where(~field.in_(condition.value))
        else:
            # This should never happen due to validation, but just in case
            raise ValueError(f"Unsupported operator: {condition.operator}")

    @classmethod
    def _apply_filter_condition(cls, item: Any, condition: FilterCondition) -> bool:
        """Apply filter condition to an item in Python context.

        Args:
            item: The item to test the condition against
            condition: Filter condition to apply

        Returns:
            True if the item matches the condition, False otherwise
        """
        field_value = getattr(item, condition.field)

        if condition.operator == "eq":
            return field_value == condition.value
        elif condition.operator == "ne":
            return field_value != condition.value
        elif condition.operator == "gt":
            return field_value > condition.value
        elif condition.operator == "lt":
            return field_value < condition.value
        elif condition.operator == "gte":
            return field_value >= condition.value
        elif condition.operator == "lte":
            return field_value <= condition.value
        elif condition.operator == "in":
            return field_value in condition.value
        elif condition.operator == "not_in":
            return field_value not in condition.value
        else:
            # This should never happen due to validation, but just in case
            raise ValueError(f"Unsupported operator: {condition.operator}")


@dataclass
class StatusCondition:
    """Configuration for status checking conditions.

    This dataclass defines how to check for specific status conditions
    in status properties. It supports various types of status checks.

    Args:
        condition_type: The type of condition ('equals', 'not_null', 'source_name')
        value: The value to compare against (optional, depends on condition type)
        field: The field to check (optional, for field-based conditions)
    """

    condition_type: str  # 'equals', 'not_null', 'source_name'
    value: Any = None
    field: Optional[str] = None


@dataclass
class StatusConfig:
    """Base configuration for status property generation.

    This is the base class for all status configurations. It defines the common
    fields needed for any type of status checking operation.

    Args:
        field: The field to check status on (e.g., 'is_active', 'interpretation_id')
        condition: The status condition to check
        relationship_name: Name of the relationship attribute. Defaults to config key.
    """

    field: str
    condition: StatusCondition
    relationship_name: Optional[str] = None


@dataclass
class FieldStatusConfig:
    """Configuration for direct field status checks.

    Used for status checks where we need to check a field value on a related entity
    through a direct relationship.

    Args:
        model: The related model class to check status on
        foreign_key: The foreign key column name
        field: The field to check status on
        condition: The status condition to check
        relationship_name: Name of the relationship attribute. Defaults to config key.
        property_name: Custom property name. Defaults to has_active_{config_key}.

    Example: Act.has_active_scene - checks if act has scenes with is_active=True
    """

    model: Type["Base"]
    foreign_key: str
    field: str
    condition: StatusCondition
    relationship_name: Optional[str] = None
    property_name: Optional[str] = None


@dataclass
class SourceStatusConfig:
    """Configuration for source-based status checks.

    Used for status checks where we need to check a value in a related source table
    through a JOIN operation.

    Args:
        source_model: The source model class to check
        source_field: The field that links to the source (e.g., 'source_id')
        source_name_field: The field in source model containing the name
        expected_value: The expected value in the source name field
        relationship_name: Name of the relationship attribute. Defaults to config key.
        property_name: Custom property name. Defaults to is_{config_key}.

    Example: Event.is_manual - checks if event_sources.name = 'manual'
    """

    source_model: Type["Base"]
    source_field: str
    source_name_field: str
    expected_value: str
    relationship_name: Optional[str] = None
    property_name: Optional[str] = None


@dataclass
class CrossTableStatusConfig:
    """Configuration for status checks across relationship paths.

    Used for status checks where we need to check status through one or more
    intermediate relationships.

    Args:
        model: The target model class to check status on
        relationship_path: List of relationship attribute names to traverse
        field: The field to check status on
        condition: The status condition to check
        relationship_name: Name of the relationship attribute. Defaults to config key.
        property_name: Custom property name. Defaults to has_active_{config_key}.

    Example: Game.has_active_scene - checks through acts.scenes.is_active=True
    """

    model: Type["Base"]
    relationship_path: List[str]
    field: str
    condition: StatusCondition
    relationship_name: Optional[str] = None
    property_name: Optional[str] = None


@dataclass
class RelationshipStatusConfig:
    """Configuration for relationship-based status checks.

    Used for status checks where we need to check if a relationship field
    meets a certain condition (e.g., is_not_null).

    Args:
        field: The relationship field to check (e.g., 'interpretation_id')
        condition: The status condition to check
        relationship_name: Name of the relationship attribute. Defaults to config key.
        property_name: Custom property name. Defaults to is_{config_key}.

    Example: Event.is_from_oracle - checks if interpretation_id is not null
    """

    field: str
    condition: StatusCondition
    relationship_name: Optional[str] = None
    property_name: Optional[str] = None


@dataclass
class FilteredRelationshipStatusConfig:
    """Configuration for filtered relationship status checks.

    Used for status checks where we need to check if any related entities
    meet a specific field condition (filtered existence check).

    Args:
        model: The related model class to check
        foreign_key: The foreign key column name
        filter_field: The field to filter on
        filter_value: The value the filter field must equal
        relationship_name: Name of the relationship attribute. Defaults to config key.
        property_name: Custom property name. Defaults to has_active_{config_key}.

    Example: Game.has_active_act - checks if game has acts with is_active=True
    """

    model: Type["Base"]
    foreign_key: str
    filter_field: str
    filter_value: Any
    relationship_name: Optional[str] = None
    property_name: Optional[str] = None


class StatusCheckMixin:
    """Mixin providing is_X and has_active_X hybrid properties for status checking.

    This mixin automatically generates hybrid properties that check for specific
    status conditions on related entities. Each property works in both Python and SQL
    contexts:

    - Python context: Uses loaded relationships and field checking
    - SQL context: Uses appropriate SQL expressions with JOINs and WHERE clauses

    Supports four types of status checking:
    1. Field-based status (FieldStatusConfig)
    2. Source-based status (SourceStatusConfig)
    3. Cross-table status (CrossTableStatusConfig)
    4. Relationship-based status (RelationshipStatusConfig)

    Usage:
        class Event(StatusCheckMixin, Base, TimestampMixin):
            _status_configs = {
                'manual': SourceStatusConfig(
                    source_model=EventSource,
                    source_field='source_id',
                    source_name_field='name',
                    expected_value='manual'
                ),
                'from_oracle': RelationshipStatusConfig(
                    field='interpretation_id',
                    condition=StatusCondition(condition_type='not_null')
                ),
            }
            # This automatically generates is_manual and is_from_oracle properties
    """

    # Configuration attribute (defined by implementing classes)
    _status_configs: Dict[
        str,
        Union[
            FieldStatusConfig,
            SourceStatusConfig,
            CrossTableStatusConfig,
            RelationshipStatusConfig,
            FilteredRelationshipStatusConfig,
        ],
    ]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Generate hybrid properties when class is created.

        This method is called automatically when a class inherits from this mixin.
        It processes the _status_configs attribute and generates the appropriate
        hybrid properties.

        Args:
            **kwargs: Additional keyword arguments passed to super().__init_subclass__
        """
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "_status_configs"):
            cls._generate_status_properties()

    @classmethod
    def _generate_status_properties(cls) -> None:
        """Generate is_X and has_active_X properties from configuration.

        Iterates through _status_configs and creates a hybrid property for each
        configured status check. Each property follows the pattern:
        - Property name: is_{config_key} or has_active_{config_key}
        - Python behavior: appropriate field/relationship checking
        - SQL behavior: appropriate SQL expressions with JOINs and WHERE clauses
        """
        for config_key, config in cls._status_configs.items():
            cls._validate_status_config(config_key, config)
            cls._create_status_property(config_key, config)

    @classmethod
    def _validate_status_config(
        cls,
        name: str,
        config: Union[
            FieldStatusConfig,
            SourceStatusConfig,
            CrossTableStatusConfig,
            RelationshipStatusConfig,
            FilteredRelationshipStatusConfig,
        ],
    ) -> None:
        """Validate status configuration for correctness.

        Performs comprehensive validation of the status configuration to ensure
        all required relationships and fields exist and are properly configured.

        Args:
            name: The configuration key name
            config: The status configuration to validate

        Raises:
            AttributeError: If configured relationships or fields don't exist
            ValueError: If the configuration is invalid
        """
        # Validate base relationship exists for applicable configs
        if isinstance(config, (FieldStatusConfig, CrossTableStatusConfig)):
            relationship_name = config.relationship_name or name
            if not hasattr(cls, relationship_name):
                raise AttributeError(
                    f"Model {cls.__name__} does not have relationship "
                    f"'{relationship_name}' specified in status config for '{name}'"
                )

        # Validate source model for source-based configs
        elif isinstance(config, SourceStatusConfig):
            if not hasattr(cls, config.source_field):
                raise AttributeError(
                    f"Model {cls.__name__} does not have field "
                    f"'{config.source_field}' specified in status config for '{name}'"
                )

        # Validate field exists for relationship-based configs
        elif isinstance(config, RelationshipStatusConfig):
            if not hasattr(cls, config.field):
                raise AttributeError(
                    f"Model {cls.__name__} does not have field "
                    f"'{config.field}' specified in status config for '{name}'"
                )

        # Validate filtered relationship configs
        elif isinstance(config, FilteredRelationshipStatusConfig):
            relationship_name = config.relationship_name or name
            if not hasattr(cls, relationship_name):
                raise AttributeError(
                    f"Model {cls.__name__} does not have relationship "
                    f"'{relationship_name}' specified in status config for '{name}'"
                )

            # Validate filter field exists on target model
            if not hasattr(config.model, config.filter_field):
                raise AttributeError(
                    f"Target model {config.model.__name__} does not have field "
                    f"'{config.filter_field}' specified in status config for '{name}'"
                )

    @classmethod
    def _create_status_property(
        cls,
        name: str,
        config: Union[
            FieldStatusConfig,
            SourceStatusConfig,
            CrossTableStatusConfig,
            RelationshipStatusConfig,
            FilteredRelationshipStatusConfig,
        ],
    ) -> None:
        """Create individual status hybrid property.

        Generates a hybrid property with both Python and SQL implementations
        that behave identically to manually written status properties. The
        implementation varies based on the config type.

        Args:
            name: The configuration key, used to generate property name
            config: Status configuration containing checking information
        """
        # Determine property name - use custom name if provided, otherwise use defaults
        if config.property_name:
            property_name = config.property_name
        elif isinstance(config, FieldStatusConfig):
            property_name = f"has_active_{name}"
        elif isinstance(config, SourceStatusConfig):
            property_name = f"is_{name}"
        elif isinstance(config, CrossTableStatusConfig):
            property_name = f"has_active_{name}"
        elif isinstance(config, RelationshipStatusConfig):
            property_name = f"is_{name}"
        elif isinstance(config, FilteredRelationshipStatusConfig):
            property_name = f"has_active_{name}"
        else:
            property_name = f"is_{name}"

        # Create Python context method
        python_method = cls._build_python_status(name, config)

        # Create SQL expression method
        sql_expression = cls._build_sql_status(property_name, config)

        # Set proper docstrings with model-specific information
        python_method.__doc__ = (
            f"Check status condition for {name} on this {cls.__name__.lower()}.\n\n"
            "Works in Python context by checking loaded relationships and fields.\n\n"
            "Returns:\n"
            f"    True if {name} status condition is met, False otherwise."
        )

        sql_expression.__doc__ = f"SQL expression for {property_name}."

        # Create the hybrid property
        hybrid_prop = hybrid_property(python_method)
        hybrid_prop = hybrid_prop.expression(sql_expression)

        # Add the property to the class
        setattr(cls, property_name, hybrid_prop)

    @classmethod
    def _build_python_status(
        cls,
        name: str,
        config: Union[
            FieldStatusConfig,
            SourceStatusConfig,
            CrossTableStatusConfig,
            RelationshipStatusConfig,
            FilteredRelationshipStatusConfig,
        ],
    ):
        """Build Python status method based on configuration type.

        Args:
            name: The configuration key name
            config: Status configuration determining how to check status

        Returns:
            Function that implements Python context status checking
        """
        if isinstance(config, FieldStatusConfig):
            # Field-based status: check field value on related entities
            def python_method(self) -> bool:
                relationship_name = config.relationship_name or name
                relationship = getattr(self, relationship_name)

                for item in relationship:
                    if cls._check_status_condition(
                        item, config.field, config.condition
                    ):
                        return True
                return False

        elif isinstance(config, SourceStatusConfig):
            # Source-based status: check source relationship
            def python_method(self) -> bool:
                # Get the source ID from the configured field
                source_id = getattr(self, config.source_field)
                if not source_id:
                    return False

                # Try to get the source via loaded relationship first
                source_relationship_name = config.source_field.replace("_id", "")
                if hasattr(self, source_relationship_name):
                    source = getattr(self, source_relationship_name)
                    if source:
                        source_name = getattr(source, config.source_name_field)
                        return source_name == config.expected_value

                # Fallback: If source relationship is not loaded, we need to query it
                # This is more expensive but ensures reliability
                try:
                    from sologm.database.session import get_db_context

                    with get_db_context() as context:
                        source = context.session.get(config.source_model, source_id)
                        if source:
                            source_name = getattr(source, config.source_name_field)
                            return source_name == config.expected_value
                except Exception:
                    # If we can't load the source, return False
                    pass

                return False

        elif isinstance(config, CrossTableStatusConfig):
            # Cross-table status: navigate through relationship path
            def python_method(self) -> bool:
                def check_status_through_path(items, path_steps):
                    """Recursively check status through nested relationship path."""
                    if not path_steps:
                        # Base case: check status condition on final items
                        for item in items:
                            if cls._check_status_condition(
                                item, config.field, config.condition
                            ):
                                return True
                        return False

                    # Navigate to next level in relationship path
                    next_step = path_steps[0]
                    remaining_steps = path_steps[1:]

                    for item in items:
                        next_items = getattr(item, next_step, [])
                        if check_status_through_path(next_items, remaining_steps):
                            return True
                    return False

                # Start with the initial relationship
                relationship_name = config.relationship_name or name
                relationship = getattr(self, relationship_name)
                # Skip first step since we already have that relationship
                remaining_path = config.relationship_path[1:]
                return check_status_through_path(relationship, remaining_path)

        elif isinstance(config, RelationshipStatusConfig):
            # Relationship-based status: check field condition directly
            def python_method(self) -> bool:
                return cls._check_status_condition(self, config.field, config.condition)

        elif isinstance(config, FilteredRelationshipStatusConfig):
            # Filtered relationship status: check if any related items meet filter
            def python_method(self) -> bool:
                relationship_name = config.relationship_name or name
                relationship = getattr(self, relationship_name)

                for item in relationship:
                    filter_value = getattr(item, config.filter_field)
                    if filter_value == config.filter_value:
                        return True
                return False

        return python_method

    @classmethod
    def _build_sql_status(
        cls,
        property_name: str,
        config: Union[
            FieldStatusConfig,
            SourceStatusConfig,
            CrossTableStatusConfig,
            RelationshipStatusConfig,
            FilteredRelationshipStatusConfig,
        ],
    ):
        """Build SQL status expression based on configuration type.

        Args:
            property_name: Name of the property being created
            config: Status configuration determining SQL generation

        Returns:
            Function that returns SQLAlchemy expression for status checking
        """

        def sql_expression(cls_inner):
            """SQL expression for status property."""

            if isinstance(config, FieldStatusConfig):
                # Field-based status with EXISTS subquery
                condition = cls._build_sql_condition(
                    config.model, config.field, config.condition
                )
                return (
                    select(1)
                    .where(getattr(config.model, config.foreign_key) == cls_inner.id)
                    .where(condition)
                    .exists()
                    .label(property_name)
                )

            elif isinstance(config, SourceStatusConfig):
                # Source-based status with JOIN
                source_field = getattr(config.source_model, config.source_name_field)
                return (
                    select(1)
                    .where(
                        getattr(cls_inner, config.source_field)
                        == config.source_model.id
                    )
                    .where(source_field == config.expected_value)
                    .exists()
                    .label(property_name)
                )

            elif isinstance(config, CrossTableStatusConfig):
                # Cross-table status with complex WHERE conditions
                where_conditions = cls._build_relationship_path_conditions(
                    cls_inner, config.relationship_path, config.model
                )

                condition = cls._build_sql_condition(
                    config.model, config.field, config.condition
                )
                query = select(1).where(condition)

                if where_conditions is not None:
                    query = query.where(where_conditions)

                return query.exists().label(property_name)

            elif isinstance(config, RelationshipStatusConfig):
                # Relationship-based status - direct field check
                condition = cls._build_sql_condition(
                    cls_inner, config.field, config.condition
                )
                return condition.label(property_name)

            elif isinstance(config, FilteredRelationshipStatusConfig):
                # Filtered relationship status with EXISTS subquery and filter
                filter_condition = (
                    getattr(config.model, config.filter_field) == config.filter_value
                )
                return (
                    select(1)
                    .where(getattr(config.model, config.foreign_key) == cls_inner.id)
                    .where(filter_condition)
                    .exists()
                    .label(property_name)
                )

        return sql_expression

    @classmethod
    def _check_status_condition(
        cls, item: Any, field: str, condition: StatusCondition
    ) -> bool:
        """Check status condition on an item in Python context.

        Args:
            item: The item to check the condition on
            field: The field name to check
            condition: The status condition to apply

        Returns:
            True if the condition is met, False otherwise
        """
        field_value = getattr(item, field)

        if condition.condition_type == "equals":
            return field_value == condition.value
        elif condition.condition_type == "not_null":
            return field_value is not None
        elif condition.condition_type == "source_name":
            # This would require loading the source relationship
            # For now, simplified implementation
            return field_value == condition.value
        else:
            raise ValueError(f"Unsupported condition type: {condition.condition_type}")

    @classmethod
    def _build_sql_condition(
        cls, model: Type["Base"], field: str, condition: StatusCondition
    ):
        """Build SQL condition expression for status checking.

        Args:
            model: The model class to build condition for
            field: The field name to check
            condition: The status condition to apply

        Returns:
            SQLAlchemy condition expression
        """
        field_attr = getattr(model, field)

        if condition.condition_type == "equals":
            return field_attr == condition.value
        elif condition.condition_type == "not_null":
            return field_attr.is_not(None)
        elif condition.condition_type == "source_name":
            return field_attr == condition.value
        else:
            raise ValueError(f"Unsupported condition type: {condition.condition_type}")

    @classmethod
    def _build_relationship_path_conditions(
        cls, source_model, relationship_path: List[str], target_model: Type["Base"]
    ):
        """Build WHERE conditions for cross-table status checks via relationship paths.

        This method creates implicit JOIN conditions using WHERE clauses that mirror
        the patterns used in existing manual implementations like Act.event_count.

        Args:
            source_model: The source model class (e.g., Act)
            relationship_path: List of relationship names to traverse
                (e.g., ['scenes', 'events'])
            target_model: The target model to check (e.g., Event)

        Returns:
            SQLAlchemy condition that can be used in WHERE clause,
                or None if path is empty

        Examples:
            For Act.event_count with path ['scenes', 'events']:
                Returns: (Scene.act_id == source_model.id) &
                    (Event.scene_id == Scene.id)
        """
        if not relationship_path:
            return None

        # Import models locally to avoid circular dependencies
        # This mirrors the pattern used in existing manual implementations
        intermediate_models = cls._resolve_intermediate_models(
            source_model, relationship_path
        )

        if not intermediate_models:
            return None

        conditions = []

        # Build conditions step by step through the relationship path
        # First condition: connect source to first intermediate
        if len(intermediate_models) >= 1:
            first_intermediate = intermediate_models[0]
            foreign_key = cls._get_foreign_key_name(source_model, first_intermediate)
            if foreign_key:
                condition = getattr(first_intermediate, foreign_key) == source_model.id
                conditions.append(condition)

        # Middle conditions: connect intermediate models to each other
        for i in range(len(intermediate_models) - 1):
            current_model = intermediate_models[i]
            next_model = intermediate_models[i + 1]
            foreign_key = cls._get_foreign_key_name(current_model, next_model)
            if foreign_key:
                condition = getattr(next_model, foreign_key) == current_model.id
                conditions.append(condition)

        # Last condition: connect last intermediate to target (if different)
        if len(intermediate_models) >= 1:
            last_intermediate = intermediate_models[-1]
            if last_intermediate != target_model:
                foreign_key = cls._get_foreign_key_name(last_intermediate, target_model)
                if foreign_key:
                    condition = (
                        getattr(target_model, foreign_key) == last_intermediate.id
                    )
                    conditions.append(condition)

        # Combine all conditions with AND
        if conditions:
            result = conditions[0]
            for condition in conditions[1:]:
                result = result & condition
            return result

        return None

    @classmethod
    def _resolve_intermediate_models(
        cls, source_model, relationship_path: List[str]
    ) -> List[Type["Base"]]:
        """Resolve the intermediate models in a relationship path.

        This walks through the relationship path and returns the model classes
        for each step in the path.
        """
        models = []
        current_model = source_model

        for relationship_name in relationship_path:
            if not hasattr(current_model, relationship_name):
                return []

            relationship = getattr(current_model, relationship_name)
            if hasattr(relationship.property, "mapper"):
                next_model = relationship.property.mapper.class_
                models.append(next_model)
                current_model = next_model
            else:
                return []

        return models

    @classmethod
    def _get_foreign_key_name(
        cls, source_model: Type["Base"], target_model: Type["Base"]
    ) -> Optional[str]:
        """Get the foreign key name that connects source_model to target_model.

        This searches through target_model's columns to find foreign keys
        that reference source_model's table.
        """
        source_table = getattr(source_model, "__tablename__", "")
        if not source_table:
            return None

        # Check each column in target_model for foreign keys to source_model
        for column in target_model.__table__.columns:
            # Check if this column has foreign keys
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    # Check if this foreign key references the source table
                    if fk.column.table.name == source_table:
                        return column.name

        # Fallback to naming patterns if introspection fails
        if source_table.endswith("s"):
            # scenes -> scene_id, acts -> act_id
            fk_name = f"{source_table[:-1]}_id"
        else:
            fk_name = f"{source_table}_id"

        # Special case for InterpretationSet -> set_id
        if source_model.__name__ == "InterpretationSet":
            fk_name = "set_id"

        if hasattr(target_model, fk_name):
            return fk_name

        return None
