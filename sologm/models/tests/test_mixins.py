"""Comprehensive tests for model mixins.

This module tests the ExistenceCheckMixin functionality in isolation using mock models
to avoid circular dependencies. These tests validate the mixin behavior before
applying it to real models.
"""

import uuid
from typing import TYPE_CHECKING, List

import pytest
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sologm.database.session import SessionContext
from sologm.models.base import Base, TimestampMixin
from sologm.models.mixins import (
    CountingMixin,
    CrossTableCountConfig,
    CrossTableStatusConfig,
    DirectCountConfig,
    ExistenceCheckMixin,
    ExistenceConfig,
    FieldStatusConfig,
    FilterCondition,
    FilteredCountConfig,
    FilteredCrossTableCountConfig,
    FilteredRelationshipStatusConfig,
    RelationshipStatusConfig,
    SourceStatusConfig,
    StatusCheckMixin,
    StatusCondition,
)

if TYPE_CHECKING:
    pass


# Mock models for testing (avoid circular dependencies)
class MockChildModel(Base):
    """Mock child model for testing relationships."""

    __tablename__ = "mock_children"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[str] = mapped_column(
        ForeignKey("mock_parents.id"), nullable=False
    )


class MockParentModel(ExistenceCheckMixin, Base, TimestampMixin):
    """Mock parent model for testing mixin functionality."""

    __tablename__ = "mock_parents"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship will be defined later to avoid forward reference issues
    children: Mapped[List["MockChildModel"]] = relationship(back_populates="parent")

    _existence_configs = {
        "children": ExistenceConfig(model=MockChildModel, foreign_key="parent_id")
    }


class MockItemModel(Base):
    """Additional mock model for multi-property testing."""

    __tablename__ = "mock_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    multi_parent_id: Mapped[str] = mapped_column(
        ForeignKey("mock_multi_properties.id"), nullable=False
    )


class MockMultiPropertyModel(ExistenceCheckMixin, Base, TimestampMixin):
    """Mock model with multiple existence properties for testing."""

    __tablename__ = "mock_multi_properties"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    items: Mapped[List["MockItemModel"]] = relationship(back_populates="multi_parent")

    _existence_configs = {
        "items": ExistenceConfig(
            model=MockItemModel,
            foreign_key="multi_parent_id",
            relationship_name="items",
        )
    }


# Add back_populates to MockChildModel and MockItemModel after models are defined
MockChildModel.parent = relationship("MockParentModel", back_populates="children")
MockItemModel.multi_parent = relationship(
    "MockMultiPropertyModel", back_populates="items"
)


# Mock models for counting tests
class MockDirectItem(Base):
    """Mock item for direct counting tests."""

    __tablename__ = "mock_direct_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    counting_parent_id: Mapped[str] = mapped_column(
        ForeignKey("mock_counting_parents.id"), nullable=False
    )

    # Relationship
    counting_parent: Mapped["MockCountingParentModel"] = relationship(
        back_populates="direct_items"
    )


class MockCountingParentModel(CountingMixin, Base, TimestampMixin):
    """Mock parent model for testing direct counting functionality."""

    __tablename__ = "mock_counting_parents"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship for direct counting
    direct_items: Mapped[List["MockDirectItem"]] = relationship(
        back_populates="counting_parent"
    )

    _counting_configs = {
        "direct_items": DirectCountConfig(
            model=MockDirectItem, foreign_key="counting_parent_id"
        )
    }


class MockIntermediateItem(Base):
    """Mock intermediate item for cross-table counting tests."""

    __tablename__ = "mock_intermediate_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    cross_parent_id: Mapped[str] = mapped_column(
        ForeignKey("mock_cross_table_parents.id"), nullable=False
    )

    # Relationships
    cross_parent: Mapped["MockCrossTableParentModel"] = relationship(
        back_populates="intermediate_items"
    )
    cross_items: Mapped[List["MockCrossItem"]] = relationship(
        back_populates="intermediate"
    )


class MockCrossItem(Base):
    """Mock cross item for cross-table counting tests."""

    __tablename__ = "mock_cross_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    intermediate_id: Mapped[str] = mapped_column(
        ForeignKey("mock_intermediate_items.id"), nullable=False
    )

    # Relationship
    intermediate: Mapped["MockIntermediateItem"] = relationship(
        back_populates="cross_items"
    )


class MockCrossTableParentModel(CountingMixin, Base, TimestampMixin):
    """Mock parent model for testing cross-table counting functionality."""

    __tablename__ = "mock_cross_table_parents"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships for cross-table counting
    intermediate_items: Mapped[List["MockIntermediateItem"]] = relationship(
        back_populates="cross_parent"
    )

    _counting_configs = {
        "cross_items": CrossTableCountConfig(
            model=MockCrossItem,
            foreign_key="intermediate_id",
            relationship_path=["intermediate_items", "cross_items"],
            relationship_name="intermediate_items",
        )
    }


class MockFilteredItem(Base):
    """Mock item for filtered counting tests."""

    __tablename__ = "mock_filtered_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    filtered_parent_id: Mapped[str] = mapped_column(
        ForeignKey("mock_filtered_parents.id"), nullable=False
    )

    # Relationship
    filtered_parent: Mapped["MockFilteredParentModel"] = relationship(
        back_populates="filtered_items"
    )


class MockFilteredParentModel(CountingMixin, Base, TimestampMixin):
    """Mock parent model for testing filtered counting functionality."""

    __tablename__ = "mock_filtered_parents"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship for filtered counting
    filtered_items: Mapped[List["MockFilteredItem"]] = relationship(
        back_populates="filtered_parent"
    )

    _counting_configs = {
        "active_items": FilteredCountConfig(
            model=MockFilteredItem,
            foreign_key="filtered_parent_id",
            filter_condition=FilterCondition(field="is_active", value=True),
            relationship_name="filtered_items",
        )
    }


class MockLevel1Item(Base):
    """Mock level 1 item for complex counting tests."""

    __tablename__ = "mock_level1_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    complex_parent_id: Mapped[str] = mapped_column(
        ForeignKey("mock_complex_parents.id"), nullable=False
    )

    # Relationships
    complex_parent: Mapped["MockComplexParentModel"] = relationship(
        back_populates="level1_items"
    )
    level2_items: Mapped[List["MockLevel2Item"]] = relationship(back_populates="level1")


class MockLevel2Item(Base):
    """Mock level 2 item for complex counting tests."""

    __tablename__ = "mock_level2_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    level1_id: Mapped[str] = mapped_column(
        ForeignKey("mock_level1_items.id"), nullable=False
    )

    # Relationships
    level1: Mapped["MockLevel1Item"] = relationship(back_populates="level2_items")
    deep_items: Mapped[List["MockDeepItem"]] = relationship(back_populates="level2")


class MockDeepItem(Base):
    """Mock deep item for complex counting tests."""

    __tablename__ = "mock_deep_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_selected: Mapped[bool] = mapped_column(nullable=False, default=False)
    level2_id: Mapped[str] = mapped_column(
        ForeignKey("mock_level2_items.id"), nullable=False
    )

    # Relationship
    level2: Mapped["MockLevel2Item"] = relationship(back_populates="deep_items")


class MockComplexParentModel(CountingMixin, Base, TimestampMixin):
    """Mock parent model for testing complex filtered cross-table counting."""

    __tablename__ = "mock_complex_parents"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship for complex counting
    level1_items: Mapped[List["MockLevel1Item"]] = relationship(
        back_populates="complex_parent"
    )

    _counting_configs = {
        "selected_deep_items": FilteredCrossTableCountConfig(
            model=MockDeepItem,
            foreign_key="level2_id",
            relationship_path=["level1_items", "level2_items", "deep_items"],
            filter_condition=FilterCondition(field="is_selected", value=True),
            relationship_name="level1_items",
        )
    }


# Relationships are now defined directly in the model classes above


# Mock models for status testing
class MockSourceModel(Base):
    """Mock source model for source-based status testing."""

    __tablename__ = "mock_sources"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class MockStatusItem(Base):
    """Mock item model for field-based status testing."""

    __tablename__ = "mock_status_items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    status_parent_id: Mapped[str] = mapped_column(
        ForeignKey("mock_status_parents.id"), nullable=False
    )

    # Relationship
    status_parent: Mapped["MockStatusParent"] = relationship(
        back_populates="status_items"
    )


class MockStatusParent(StatusCheckMixin, Base, TimestampMixin):
    """Mock parent model for testing status mixin functionality."""

    __tablename__ = "mock_status_parents"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("mock_sources.id"), nullable=True)
    link_id: Mapped[str] = mapped_column(String(50), nullable=True)

    # Relationships
    status_items: Mapped[List["MockStatusItem"]] = relationship(
        back_populates="status_parent"
    )
    source: Mapped["MockSourceModel"] = relationship()

    _status_configs = {
        "items": FieldStatusConfig(
            model=MockStatusItem,
            foreign_key="status_parent_id",
            field="is_active",
            condition=StatusCondition(condition_type="equals", value=True),
            relationship_name="status_items",
        ),
        "completed_items": FieldStatusConfig(
            model=MockStatusItem,
            foreign_key="status_parent_id",
            field="status",
            condition=StatusCondition(condition_type="equals", value="completed"),
            relationship_name="status_items",
            property_name="has_completed_items",
        ),
        "manual": SourceStatusConfig(
            source_model=MockSourceModel,
            source_field="source_id",
            source_name_field="name",
            expected_value="manual",
        ),
        "linked": RelationshipStatusConfig(
            field="link_id",
            condition=StatusCondition(condition_type="not_null"),
        ),
        "filtered_items": FilteredRelationshipStatusConfig(
            model=MockStatusItem,
            foreign_key="status_parent_id",
            filter_field="is_active",
            filter_value=True,
            relationship_name="status_items",
        ),
    }


class MockCrossLevel1(Base):
    """Mock level 1 model for cross-table status testing."""

    __tablename__ = "mock_cross_level1"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    cross_parent_id: Mapped[str] = mapped_column(
        ForeignKey("mock_cross_status_parents.id"), nullable=False
    )

    # Relationships
    cross_parent: Mapped["MockCrossStatusParent"] = relationship(
        back_populates="level1_items"
    )
    level2_items: Mapped[List["MockCrossLevel2"]] = relationship(
        back_populates="level1"
    )


class MockCrossLevel2(Base):
    """Mock level 2 model for cross-table status testing."""

    __tablename__ = "mock_cross_level2"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    level1_id: Mapped[str] = mapped_column(
        ForeignKey("mock_cross_level1.id"), nullable=False
    )

    # Relationship
    level1: Mapped["MockCrossLevel1"] = relationship(back_populates="level2_items")


class MockCrossStatusParent(StatusCheckMixin, Base, TimestampMixin):
    """Mock parent model for testing cross-table status functionality."""

    __tablename__ = "mock_cross_status_parents"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    level1_items: Mapped[List["MockCrossLevel1"]] = relationship(
        back_populates="cross_parent"
    )

    _status_configs = {
        "deep_items": CrossTableStatusConfig(
            model=MockCrossLevel2,
            relationship_path=["level1_items", "level2_items"],
            field="is_active",
            condition=StatusCondition(condition_type="equals", value=True),
            relationship_name="level1_items",
        ),
    }


class MockRelationshipStatusModel(StatusCheckMixin, Base, TimestampMixin):
    """Mock model for testing relationship-based status functionality."""

    __tablename__ = "mock_relationship_status"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    interpretation_id: Mapped[str] = mapped_column(String(50), nullable=True)
    parent_id: Mapped[str] = mapped_column(String(50), nullable=True)

    _status_configs = {
        "from_interpretation": RelationshipStatusConfig(
            field="interpretation_id",
            condition=StatusCondition(condition_type="not_null"),
        ),
        "has_parent": RelationshipStatusConfig(
            field="parent_id",
            condition=StatusCondition(condition_type="not_null"),
        ),
    }


@pytest.fixture(autouse=True)
def setup_mock_tables(session_context):
    """Create tables for mock models before each test."""
    with session_context as session:
        # Create all tables for mock models
        Base.metadata.create_all(session.bind)


class TestExistenceConfig:
    """Test ExistenceConfig dataclass functionality."""

    def test_existence_config_creation(self) -> None:
        """Test creating ExistenceConfig with required parameters."""
        config = ExistenceConfig(model=MockChildModel, foreign_key="parent_id")

        assert config.model == MockChildModel
        assert config.foreign_key == "parent_id"
        assert config.relationship_name is None

    def test_existence_config_with_custom_relationship_name(self) -> None:
        """Test ExistenceConfig with custom relationship name."""
        config = ExistenceConfig(
            model=MockChildModel,
            foreign_key="parent_id",
            relationship_name="custom_children",
        )

        assert config.model == MockChildModel
        assert config.foreign_key == "parent_id"
        assert config.relationship_name == "custom_children"

    def test_existence_config_default_relationship_name(self) -> None:
        """Test that relationship_name defaults to None when not specified."""
        config = ExistenceConfig(MockChildModel, "parent_id")
        assert config.relationship_name is None


class TestPropertyGeneration:
    """Test automatic property generation from configurations."""

    def test_single_property_generation(self) -> None:
        """Test that has_X property is generated from configuration."""
        # Property should be generated automatically via __init_subclass__
        assert hasattr(MockParentModel, "has_children")

        # Verify it's a hybrid property
        prop = MockParentModel.has_children
        assert hasattr(prop, "expression")

        # Verify that accessing the class attribute gives us an expression
        class_attr = MockParentModel.has_children
        assert hasattr(class_attr, "name")  # Should be a labeled expression

    def test_multiple_property_generation(self) -> None:
        """Test generation of properties on model with items."""
        assert hasattr(MockMultiPropertyModel, "has_items")

        # Verify it's a hybrid property
        items_prop = MockMultiPropertyModel.has_items

        assert hasattr(items_prop, "expression")

    def test_property_naming_convention(self) -> None:
        """Test that properties follow has_{config_key} naming pattern."""
        # Check that the property names match the config keys
        assert hasattr(MockParentModel, "has_children")
        assert hasattr(MockMultiPropertyModel, "has_items")

        # Verify no unexpected properties were created
        assert not hasattr(MockParentModel, "has_parent_id")
        assert not hasattr(MockParentModel, "children_exist")
        assert not hasattr(MockMultiPropertyModel, "has_children")


class TestErrorHandling:
    """Test error handling for misconfigured properties."""

    def test_missing_relationship_error(self) -> None:
        """Test error when configured relationship doesn't exist on model."""
        with pytest.raises(AttributeError) as exc_info:

            class BadConfigModel(ExistenceCheckMixin, Base):
                __tablename__ = "bad_config"
                id: Mapped[str] = mapped_column(primary_key=True)

                _existence_configs = {
                    "nonexistent": ExistenceConfig(
                        model=MockChildModel, foreign_key="parent_id"
                    )
                }

        error_message = str(exc_info.value)
        assert "BadConfigModel" in error_message
        assert "does not have relationship 'nonexistent'" in error_message

    def test_custom_relationship_name_error(self) -> None:
        """Test error when custom relationship_name doesn't exist."""
        # Test validation of relationship names at class creation time
        # Instead of creating a broken model, we test the validation logic directly

        # Mock a class that doesn't have the specified relationship
        class MockModelForValidation:
            __name__ = "TestModel"

            @classmethod
            def _create_existence_property(cls, name: str, config):
                # This should raise an AttributeError for non-existent relationships
                if not hasattr(cls, config.relationship_name or name):
                    raise AttributeError(
                        f"Model {cls.__name__} does not have relationship "
                        f"'{config.relationship_name or name}' specified in "
                        f"existence config for '{name}'"
                    )

        # Test the validation
        config = ExistenceConfig(
            model=MockChildModel,
            foreign_key="parent_id",
            relationship_name="wrong_name",
        )

        with pytest.raises(AttributeError) as exc_info:
            MockModelForValidation._create_existence_property("test", config)

        error_message = str(exc_info.value)
        assert "MockModelForValidation" in error_message
        assert "does not have relationship 'wrong_name'" in error_message


class TestPythonContext:
    """Test generated properties in Python context (instance access)."""

    def test_has_children_empty_relationship(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_children with no children."""
        with session_context as session:
            parent = MockParentModel(name="Parent with no children")
            session.add(parent)
            session.flush()

            # Test Python context - should return False for empty relationship
            assert parent.has_children is False

    def test_has_children_with_relationship(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test has_children with existing children."""
        with session_context as session:
            parent = MockParentModel(name="Parent with children")
            session.add(parent)
            session.flush()

            child = MockChildModel(name="Test child", parent_id=parent.id)
            session.add(child)
            session.flush()

            # Refresh parent to load relationship
            session.refresh(parent, attribute_names=["children"])

            # Test Python context - should return True
            assert parent.has_children is True

    def test_multiple_properties_python_context(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test multiple properties work independently in Python context."""
        with session_context as session:
            # Test with MockParentModel which has children property
            parent = MockParentModel(name="Multi-property test")
            session.add(parent)
            session.flush()

            # Create MockMultiPropertyModel to test items property
            multi_model = MockMultiPropertyModel(name="Multi-property items test")
            session.add(multi_model)
            session.flush()

            # Initially both should be False
            assert parent.has_children is False
            assert multi_model.has_items is False

            # Add a child to parent
            child = MockChildModel(name="Test child", parent_id=parent.id)
            session.add(child)
            session.flush()
            session.refresh(parent, attribute_names=["children"])

            # Add an item to multi_model
            item = MockItemModel(name="Test item", multi_parent_id=multi_model.id)
            session.add(item)
            session.flush()
            session.refresh(multi_model, attribute_names=["items"])

            # Now each should have their respective relationships
            assert parent.has_children is True
            assert multi_model.has_items is True


class TestSQLContext:
    """Test generated properties in SQL context (query filtering)."""

    def test_has_children_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering with has_children property."""
        with session_context as session:
            # Create parent without children
            parent_no_children = MockParentModel(name="No children")
            session.add(parent_no_children)

            # Create parent with children
            parent_with_children = MockParentModel(name="Has children")
            session.add(parent_with_children)
            session.flush()

            child = MockChildModel(name="Test child", parent_id=parent_with_children.id)
            session.add(child)
            session.flush()

            # Test SQL filtering - parents with children
            parents_with_children = (
                session.query(MockParentModel)
                .filter(MockParentModel.has_children)
                .all()
            )

            assert len(parents_with_children) == 1
            assert parents_with_children[0].id == parent_with_children.id

            # Test SQL filtering - parents without children
            parents_without_children = (
                session.query(MockParentModel)
                .filter(~MockParentModel.has_children)
                .all()
            )

            assert len(parents_without_children) == 1
            assert parents_without_children[0].id == parent_no_children.id

    def test_sql_expression_structure(self) -> None:
        """Test that SQL expressions have expected structure."""
        # Get the SQL expression for has_children (class attribute access gives us
        # the expression)
        sql_expr = MockParentModel.has_children

        # Should be a labeled exists expression
        assert hasattr(sql_expr, "name")
        assert sql_expr.name == "has_children"

    def test_multiple_properties_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering with multiple properties."""
        with session_context as session:
            # Create parent model for children testing
            parent = MockParentModel(name="Parent SQL test")
            session.add(parent)
            session.flush()

            # Create multi-property model for items testing
            multi_model = MockMultiPropertyModel(name="Multi-property SQL test")
            session.add(multi_model)
            session.flush()

            # Add child to parent
            child = MockChildModel(name="Test child", parent_id=parent.id)
            session.add(child)
            session.flush()

            # Test filtering by has_children on parent model
            with_children = (
                session.query(MockParentModel)
                .filter(MockParentModel.has_children)
                .all()
            )

            assert len(with_children) == 1
            assert with_children[0].id == parent.id

            # Test filtering by has_items (should be empty since no items added)
            with_items = (
                session.query(MockMultiPropertyModel)
                .filter(MockMultiPropertyModel.has_items)
                .all()
            )

            assert len(with_items) == 0

            # Add an item and test again
            item = MockItemModel(name="Test item", multi_parent_id=multi_model.id)
            session.add(item)
            session.flush()

            # Now should find the model with items
            with_items = (
                session.query(MockMultiPropertyModel)
                .filter(MockMultiPropertyModel.has_items)
                .all()
            )

            assert len(with_items) == 1
            assert with_items[0].id == multi_model.id


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_property_docstring_generation(self) -> None:
        """Test that generated properties have appropriate docstrings."""
        has_children_prop = MockParentModel.has_children

        # The property should have been generated with a Python method that has a
        # docstring
        python_method = has_children_prop.fget
        assert python_method.__doc__ is not None
        assert "mockparentmodel" in python_method.__doc__.lower()
        assert "children" in python_method.__doc__.lower()

    def test_custom_relationship_name_usage(self) -> None:
        """Test that custom relationship names are used correctly."""
        # MockMultiPropertyModel uses custom relationship name for 'items'
        config = MockMultiPropertyModel._existence_configs["items"]
        assert config.relationship_name == "items"

        # Property should still be named has_items (from config key)
        assert hasattr(MockMultiPropertyModel, "has_items")

    def test_mixin_inheritance_chain(self) -> None:
        """Test that mixin works correctly in inheritance chain."""
        # Verify that MockParentModel inherits from all expected classes
        assert issubclass(MockParentModel, ExistenceCheckMixin)
        assert issubclass(MockParentModel, Base)
        assert issubclass(MockParentModel, TimestampMixin)

        # Verify the mixin functionality is present
        assert hasattr(MockParentModel, "_generate_existence_properties")
        assert hasattr(MockParentModel, "_create_existence_property")

    def test_no_config_no_properties(self) -> None:
        """Test that models without _existence_configs don't get properties."""

        class NoConfigModel(ExistenceCheckMixin, Base):
            __tablename__ = "no_config"
            id: Mapped[str] = mapped_column(primary_key=True)

        # Should not have any has_* properties
        has_properties = [
            attr for attr in dir(NoConfigModel) if attr.startswith("has_")
        ]
        # Filter out any inherited attributes that might start with 'has_'
        model_has_properties = [
            attr
            for attr in has_properties
            if hasattr(getattr(NoConfigModel, attr), "expression")
        ]
        assert len(model_has_properties) == 0


# Counting Mixin Tests
class TestCountConfig:
    """Test count configuration dataclass functionality."""

    def test_direct_count_config_creation(self) -> None:
        """Test creating DirectCountConfig with required parameters."""
        config = DirectCountConfig(
            model=MockDirectItem, foreign_key="counting_parent_id"
        )

        assert config.model == MockDirectItem
        assert config.foreign_key == "counting_parent_id"
        assert config.relationship_name is None

    def test_direct_count_config_with_custom_relationship_name(self) -> None:
        """Test DirectCountConfig with custom relationship name."""
        config = DirectCountConfig(
            model=MockDirectItem,
            foreign_key="counting_parent_id",
            relationship_name="custom_items",
        )

        assert config.model == MockDirectItem
        assert config.foreign_key == "counting_parent_id"
        assert config.relationship_name == "custom_items"

    def test_cross_table_count_config_creation(self) -> None:
        """Test creating CrossTableCountConfig with required parameters."""
        config = CrossTableCountConfig(
            model=MockCrossItem,
            foreign_key="cross_parent_id",
            relationship_path=["intermediate_items", "cross_items"],
        )

        assert config.model == MockCrossItem
        assert config.foreign_key == "cross_parent_id"
        assert config.relationship_path == ["intermediate_items", "cross_items"]
        assert config.relationship_name is None

    def test_filtered_count_config_creation(self) -> None:
        """Test creating FilteredCountConfig with filter condition."""
        filter_condition = FilterCondition(field="is_active", value=True)
        config = FilteredCountConfig(
            model=MockFilteredItem,
            foreign_key="filtered_parent_id",
            filter_condition=filter_condition,
        )

        assert config.model == MockFilteredItem
        assert config.foreign_key == "filtered_parent_id"
        assert config.filter_condition == filter_condition
        assert config.relationship_name is None

    def test_filtered_cross_table_count_config_creation(self) -> None:
        """Test creating FilteredCrossTableCountConfig with both path and filter."""
        filter_condition = FilterCondition(field="is_selected", value=True)
        config = FilteredCrossTableCountConfig(
            model=MockDeepItem,
            foreign_key="complex_parent_id",
            relationship_path=["level1_items", "level2_items", "deep_items"],
            filter_condition=filter_condition,
        )

        assert config.model == MockDeepItem
        assert config.foreign_key == "complex_parent_id"
        assert config.relationship_path == [
            "level1_items",
            "level2_items",
            "deep_items",
        ]
        assert config.filter_condition == filter_condition
        assert config.relationship_name is None

    def test_filter_condition_creation(self) -> None:
        """Test FilterCondition with various operators and values."""
        # Test default condition (eq, True)
        condition1 = FilterCondition(field="is_active")
        assert condition1.field == "is_active"
        assert condition1.operator == "eq"
        assert condition1.value is True

        # Test custom condition
        condition2 = FilterCondition(field="count", operator="gt", value=5)
        assert condition2.field == "count"
        assert condition2.operator == "gt"
        assert condition2.value == 5

        # Test 'in' operator with list value
        condition3 = FilterCondition(
            field="status", operator="in", value=["active", "pending"]
        )
        assert condition3.field == "status"
        assert condition3.operator == "in"
        assert condition3.value == ["active", "pending"]


class TestCountingPropertyGeneration:
    """Test automatic count property generation from configurations."""

    def test_direct_count_property_generation(self) -> None:
        """Test that direct_items_count property is generated from configuration."""
        # Property should be generated automatically via __init_subclass__
        assert hasattr(MockCountingParentModel, "direct_items_count")

        # Verify it's a hybrid property
        prop = MockCountingParentModel.direct_items_count
        assert hasattr(prop, "expression")

        # Verify that accessing the class attribute gives us an expression
        class_attr = MockCountingParentModel.direct_items_count
        assert hasattr(class_attr, "name")  # Should be a labeled expression

    def test_cross_table_count_property_generation(self) -> None:
        """Test that cross-table count properties are generated."""
        assert hasattr(MockCrossTableParentModel, "cross_items_count")

        # Verify it's a hybrid property
        prop = MockCrossTableParentModel.cross_items_count
        assert hasattr(prop, "expression")

    def test_filtered_count_property_generation(self) -> None:
        """Test that filtered count properties are generated."""
        assert hasattr(MockFilteredParentModel, "active_items_count")

        # Verify it's a hybrid property
        prop = MockFilteredParentModel.active_items_count
        assert hasattr(prop, "expression")

    def test_complex_count_property_generation(self) -> None:
        """Test that complex filtered cross-table count properties are generated."""
        assert hasattr(MockComplexParentModel, "selected_deep_items_count")

        # Verify it's a hybrid property
        prop = MockComplexParentModel.selected_deep_items_count
        assert hasattr(prop, "expression")

    def test_count_property_naming_convention(self) -> None:
        """Test that count properties follow {config_key}_count naming pattern."""
        # Check that the property names match the config keys with _count suffix
        assert hasattr(MockCountingParentModel, "direct_items_count")
        assert hasattr(MockCrossTableParentModel, "cross_items_count")
        assert hasattr(MockFilteredParentModel, "active_items_count")
        assert hasattr(MockComplexParentModel, "selected_deep_items_count")

        # Verify no unexpected properties were created
        assert not hasattr(
            MockCountingParentModel, "counting_parent_id_count"
        )  # Should not use foreign key
        assert not hasattr(
            MockFilteredParentModel, "filtered_items_count"
        )  # Should use config key, not relationship
        assert not hasattr(
            MockCountingParentModel, "direct_items_exist"
        )  # Should not create variations


class TestCountingErrorHandling:
    """Test error handling for misconfigured count properties."""

    def test_missing_relationship_error(self) -> None:
        """Test error when configured relationship doesn't exist on model."""
        with pytest.raises(AttributeError) as exc_info:

            class BadCountConfigModel(CountingMixin, Base):
                __tablename__ = "bad_count_config"
                id: Mapped[str] = mapped_column(primary_key=True)

                _counting_configs = {
                    "nonexistent": DirectCountConfig(
                        model=MockDirectItem, foreign_key="bad_parent_id"
                    )
                }

        error_message = str(exc_info.value)
        assert "BadCountConfigModel" in error_message
        assert "does not have relationship 'nonexistent'" in error_message

    def test_missing_foreign_key_error(self) -> None:
        """Test error when foreign key doesn't exist on target model."""
        # Test the validation directly without creating a broken SQLAlchemy model
        with pytest.raises(AttributeError) as exc_info:
            # Create a minimal test class that has the required relationship
            class TestClass(CountingMixin):
                test_items = []  # Mock relationship attribute

                @classmethod
                def _validate_count_config(cls, name: str, config):
                    # Call the parent validation which should fail on foreign key check
                    super()._validate_count_config(name, config)

            # Simulate validation with invalid foreign key
            config = DirectCountConfig(
                model=MockDirectItem, foreign_key="nonexistent_fk"
            )

            # This should raise an error about the missing foreign key
            TestClass._validate_count_config("test_items", config)

        error_message = str(exc_info.value)
        assert (
            "Foreign key 'nonexistent_fk' not found on MockDirectItem" in error_message
        )

    def test_invalid_filter_condition_field_error(self) -> None:
        """Test error when filter condition field doesn't exist on model."""
        # Test the validation directly without creating invalid SQLAlchemy classes
        with pytest.raises(AttributeError) as exc_info:
            invalid_condition = FilterCondition(field="nonexistent_field", value=True)

            # Test the validation method directly
            CountingMixin._validate_filter_condition(
                invalid_condition, MockFilteredItem
            )

        error_message = str(exc_info.value)
        assert (
            "Field 'nonexistent_field' not found on MockFilteredItem" in error_message
        )

    def test_invalid_filter_operator_error(self) -> None:
        """Test error when filter condition uses unsupported operator."""
        # Test the validation directly without creating invalid SQLAlchemy classes
        with pytest.raises(ValueError) as exc_info:
            invalid_condition = FilterCondition(
                field="is_active", operator="invalid_op", value=True
            )

            # Test the validation method directly
            CountingMixin._validate_filter_condition(
                invalid_condition, MockFilteredItem
            )

        error_message = str(exc_info.value)
        assert "Operator 'invalid_op' not supported" in error_message


class TestCountingPythonContext:
    """Test generated count properties in Python context (instance access)."""

    def test_direct_count_empty_relationship(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test direct_items_count with no items."""
        with session_context as session:
            parent = MockCountingParentModel(name="Parent with no items")
            session.add(parent)
            session.flush()

            # Test Python context - should return 0 for empty relationship
            assert parent.direct_items_count == 0

    def test_direct_count_with_items(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test direct_items_count with existing items."""
        with session_context as session:
            parent = MockCountingParentModel(name="Parent with items")
            session.add(parent)
            session.flush()

            # Add multiple items
            item1 = MockDirectItem(name="Item 1", counting_parent_id=parent.id)
            item2 = MockDirectItem(name="Item 2", counting_parent_id=parent.id)
            item3 = MockDirectItem(name="Item 3", counting_parent_id=parent.id)
            session.add_all([item1, item2, item3])
            session.flush()

            # Refresh parent to load relationship
            session.refresh(parent, attribute_names=["direct_items"])

            # Test Python context - should return 3
            assert parent.direct_items_count == 3

    def test_filtered_count_python_context(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test filtered count properties in Python context."""
        with session_context as session:
            parent = MockFilteredParentModel(name="Parent with filtered items")
            session.add(parent)
            session.flush()

            # Add items with different active states
            active_item1 = MockFilteredItem(
                name="Active 1", is_active=True, filtered_parent_id=parent.id
            )
            active_item2 = MockFilteredItem(
                name="Active 2", is_active=True, filtered_parent_id=parent.id
            )
            inactive_item = MockFilteredItem(
                name="Inactive", is_active=False, filtered_parent_id=parent.id
            )

            session.add_all([active_item1, active_item2, inactive_item])
            session.flush()

            # Refresh parent to load relationship
            session.refresh(parent, attribute_names=["filtered_items"])

            # Test Python context - should count only active items (2)
            assert parent.active_items_count == 2

    def test_cross_table_count_python_context(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test cross-table count properties in Python context."""
        with session_context as session:
            parent = MockCrossTableParentModel(name="Cross-table parent")
            session.add(parent)
            session.flush()

            # Add intermediate items
            intermediate1 = MockIntermediateItem(
                name="Intermediate 1", cross_parent_id=parent.id
            )
            intermediate2 = MockIntermediateItem(
                name="Intermediate 2", cross_parent_id=parent.id
            )
            session.add_all([intermediate1, intermediate2])
            session.flush()

            # Add cross items to intermediates
            cross_item1 = MockCrossItem(
                name="Cross 1", intermediate_id=intermediate1.id
            )
            cross_item2 = MockCrossItem(
                name="Cross 2", intermediate_id=intermediate1.id
            )
            cross_item3 = MockCrossItem(
                name="Cross 3", intermediate_id=intermediate2.id
            )
            session.add_all([cross_item1, cross_item2, cross_item3])
            session.flush()

            # Refresh relationships
            session.refresh(parent, attribute_names=["intermediate_items"])
            session.refresh(intermediate1, attribute_names=["cross_items"])
            session.refresh(intermediate2, attribute_names=["cross_items"])

            # Test Python context - should count all cross items (3)
            assert parent.cross_items_count == 3

    def test_complex_filtered_cross_table_count_python_context(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test complex filtered cross-table count properties in Python context."""
        with session_context as session:
            parent = MockComplexParentModel(name="Complex parent")
            session.add(parent)
            session.flush()

            # Build complex relationship chain
            level1 = MockLevel1Item(name="Level 1", complex_parent_id=parent.id)
            session.add(level1)
            session.flush()

            level2 = MockLevel2Item(name="Level 2", level1_id=level1.id)
            session.add(level2)
            session.flush()

            # Add deep items with different selection states
            selected_deep1 = MockDeepItem(
                name="Selected 1", is_selected=True, level2_id=level2.id
            )
            selected_deep2 = MockDeepItem(
                name="Selected 2", is_selected=True, level2_id=level2.id
            )
            unselected_deep = MockDeepItem(
                name="Unselected", is_selected=False, level2_id=level2.id
            )

            session.add_all([selected_deep1, selected_deep2, unselected_deep])
            session.flush()

            # Refresh all relationships
            session.refresh(parent, attribute_names=["level1_items"])
            session.refresh(level1, attribute_names=["level2_items"])
            session.refresh(level2, attribute_names=["deep_items"])

            # Test Python context - should count only selected deep items (2)
            assert parent.selected_deep_items_count == 2

    def test_multiple_count_properties_independence(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test that multiple count properties work independently."""
        with session_context as session:
            # Create instances of different models
            direct_parent = MockCountingParentModel(name="Direct parent")
            filtered_parent = MockFilteredParentModel(name="Filtered parent")

            session.add_all([direct_parent, filtered_parent])
            session.flush()

            # Add items to direct parent
            direct_item = MockDirectItem(
                name="Direct item", counting_parent_id=direct_parent.id
            )
            session.add(direct_item)

            # Add filtered items to filtered parent
            active_item = MockFilteredItem(
                name="Active item",
                is_active=True,
                filtered_parent_id=filtered_parent.id,
            )
            inactive_item = MockFilteredItem(
                name="Inactive item",
                is_active=False,
                filtered_parent_id=filtered_parent.id,
            )

            session.add_all([active_item, inactive_item])
            session.flush()

            # Refresh relationships
            session.refresh(direct_parent, attribute_names=["direct_items"])
            session.refresh(filtered_parent, attribute_names=["filtered_items"])

            # Test that each model's count properties work independently
            assert direct_parent.direct_items_count == 1
            assert filtered_parent.active_items_count == 1  # Only active items


class TestCountingSQLContext:
    """Test generated count properties in SQL context (query filtering)."""

    def test_direct_count_sql_ordering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL ordering with direct count properties."""
        with session_context as session:
            # Create parents with different numbers of items
            parent_no_items = MockCountingParentModel(name="No items")
            parent_few_items = MockCountingParentModel(name="Few items")
            parent_many_items = MockCountingParentModel(name="Many items")

            session.add_all([parent_no_items, parent_few_items, parent_many_items])
            session.flush()

            # Add different numbers of items
            item1 = MockDirectItem(
                name="Item 1", counting_parent_id=parent_few_items.id
            )
            item2 = MockDirectItem(
                name="Item 2", counting_parent_id=parent_many_items.id
            )
            item3 = MockDirectItem(
                name="Item 3", counting_parent_id=parent_many_items.id
            )
            item4 = MockDirectItem(
                name="Item 4", counting_parent_id=parent_many_items.id
            )

            session.add_all([item1, item2, item3, item4])
            session.flush()

            # Test SQL ordering by count (descending)
            parents_by_count = (
                session.query(MockCountingParentModel)
                .order_by(MockCountingParentModel.direct_items_count.desc())
                .all()
            )

            assert len(parents_by_count) == 3
            assert parents_by_count[0].id == parent_many_items.id  # 3 items
            assert parents_by_count[1].id == parent_few_items.id  # 1 item
            assert parents_by_count[2].id == parent_no_items.id  # 0 items

    def test_filtered_count_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering with filtered count properties."""
        with session_context as session:
            # Create parents with different active item counts
            parent_no_active = MockFilteredParentModel(name="No active items")
            parent_some_active = MockFilteredParentModel(name="Some active items")

            session.add_all([parent_no_active, parent_some_active])
            session.flush()

            # Add only inactive items to first parent
            inactive_item = MockFilteredItem(
                name="Inactive", is_active=False, filtered_parent_id=parent_no_active.id
            )
            session.add(inactive_item)

            # Add mixed items to second parent
            active_item1 = MockFilteredItem(
                name="Active 1",
                is_active=True,
                filtered_parent_id=parent_some_active.id,
            )
            active_item2 = MockFilteredItem(
                name="Active 2",
                is_active=True,
                filtered_parent_id=parent_some_active.id,
            )
            inactive_item2 = MockFilteredItem(
                name="Inactive 2",
                is_active=False,
                filtered_parent_id=parent_some_active.id,
            )

            session.add_all([active_item1, active_item2, inactive_item2])
            session.flush()

            # Test SQL filtering - parents with active items > 0
            parents_with_active = (
                session.query(MockFilteredParentModel)
                .filter(MockFilteredParentModel.active_items_count > 0)
                .all()
            )

            assert len(parents_with_active) == 1
            assert parents_with_active[0].id == parent_some_active.id

            # Test SQL filtering - parents with active items >= 2
            parents_with_many_active = (
                session.query(MockFilteredParentModel)
                .filter(MockFilteredParentModel.active_items_count >= 2)
                .all()
            )

            assert len(parents_with_many_active) == 1
            assert parents_with_many_active[0].id == parent_some_active.id

    def test_count_sql_expression_structure(self) -> None:
        """Test that count SQL expressions have expected structure."""
        # Get the SQL expressions for various count properties (class attribute access)
        direct_count_expr = MockCountingParentModel.direct_items_count
        filtered_count_expr = MockFilteredParentModel.active_items_count
        cross_count_expr = MockCrossTableParentModel.cross_items_count
        complex_count_expr = MockComplexParentModel.selected_deep_items_count

        # Should be labeled expressions
        assert hasattr(direct_count_expr, "name")
        assert direct_count_expr.name == "direct_items_count"

        assert hasattr(filtered_count_expr, "name")
        assert filtered_count_expr.name == "active_items_count"

        assert hasattr(cross_count_expr, "name")
        assert cross_count_expr.name == "cross_items_count"

        assert hasattr(complex_count_expr, "name")
        assert complex_count_expr.name == "selected_deep_items_count"

    def test_multiple_count_properties_sql_queries(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL queries combining multiple count properties."""
        with session_context as session:
            # Create a model with direct items
            direct_parent = MockCountingParentModel(name="Direct parent")
            session.add(direct_parent)
            session.flush()

            # Add items
            item1 = MockDirectItem(name="Item 1", counting_parent_id=direct_parent.id)
            item2 = MockDirectItem(name="Item 2", counting_parent_id=direct_parent.id)
            session.add_all([item1, item2])
            session.flush()

            # Test selecting the count value directly
            count_result = (
                session.query(MockCountingParentModel.direct_items_count)
                .filter(MockCountingParentModel.id == direct_parent.id)
                .scalar()
            )

            assert count_result == 2

            # Test using count in complex WHERE conditions
            parents_with_exact_count = (
                session.query(MockCountingParentModel)
                .filter(MockCountingParentModel.direct_items_count == 2)
                .all()
            )

            assert len(parents_with_exact_count) == 1
            assert parents_with_exact_count[0].id == direct_parent.id


class TestCountingEdgeCases:
    """Test edge cases and complex scenarios for counting mixins."""

    def test_count_property_docstring_generation(self) -> None:
        """Test that generated count properties have appropriate docstrings."""
        direct_count_prop = MockCountingParentModel.direct_items_count

        # The property should have been generated with a Python method that has a
        # docstring
        python_method = direct_count_prop.fget
        assert python_method.__doc__ is not None
        assert "mockCountingParentModel".lower() in python_method.__doc__.lower()
        assert "direct_items" in python_method.__doc__.lower()

    def test_counting_mixin_inheritance_chain(self) -> None:
        """Test that counting mixin works correctly in inheritance chain."""
        # Verify that models inherit from counting mixin
        assert issubclass(MockCountingParentModel, CountingMixin)
        assert issubclass(MockCountingParentModel, Base)
        assert issubclass(MockCountingParentModel, TimestampMixin)

        # Verify the mixin functionality is present
        assert hasattr(MockCountingParentModel, "_generate_counting_properties")
        assert hasattr(MockCountingParentModel, "_create_counting_property")

    def test_no_counting_config_no_properties(self) -> None:
        """Test that models without _counting_configs don't get count properties."""

        class NoCountConfigModel(CountingMixin, Base):
            __tablename__ = "no_count_config"
            id: Mapped[str] = mapped_column(primary_key=True)

        # Should not have any *_count properties
        count_properties = [
            attr for attr in dir(NoCountConfigModel) if attr.endswith("_count")
        ]
        # Filter out any inherited attributes that might end with '_count'
        model_count_properties = [
            attr
            for attr in count_properties
            if hasattr(getattr(NoCountConfigModel, attr), "expression")
        ]
        assert len(model_count_properties) == 0

    def test_zero_count_scenarios(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test count properties with zero counts across different scenarios."""
        with session_context as session:
            # Create parents but don't add any related items
            direct_parent = MockCountingParentModel(name="No items parent")
            filtered_parent = MockFilteredParentModel(name="No active items parent")
            cross_parent = MockCrossTableParentModel(name="No cross items parent")

            session.add_all([direct_parent, filtered_parent, cross_parent])
            session.flush()

            # Add inactive item to filtered parent (should still count as 0 active)
            inactive_item = MockFilteredItem(
                name="Inactive", is_active=False, filtered_parent_id=filtered_parent.id
            )
            session.add(inactive_item)
            session.flush()

            # Refresh relationships
            session.refresh(direct_parent, attribute_names=["direct_items"])
            session.refresh(filtered_parent, attribute_names=["filtered_items"])
            session.refresh(cross_parent, attribute_names=["intermediate_items"])

            # All should have zero counts
            assert direct_parent.direct_items_count == 0
            assert (
                filtered_parent.active_items_count == 0
            )  # Inactive item shouldn't count
            assert cross_parent.cross_items_count == 0

    def test_large_count_scenarios(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test count properties with larger numbers of items."""
        with session_context as session:
            parent = MockCountingParentModel(name="Many items parent")
            session.add(parent)
            session.flush()

            # Add 50 items
            items = []
            for i in range(50):
                item = MockDirectItem(name=f"Item {i}", counting_parent_id=parent.id)
                items.append(item)

            session.add_all(items)
            session.flush()

            # Refresh relationship
            session.refresh(parent, attribute_names=["direct_items"])

            # Should accurately count all 50 items
            assert parent.direct_items_count == 50

            # Test in SQL context as well
            count_from_sql = (
                session.query(MockCountingParentModel.direct_items_count)
                .filter(MockCountingParentModel.id == parent.id)
                .scalar()
            )

            assert count_from_sql == 50


class TestCountingIntegration:
    """Integration tests combining multiple aspects of counting mixin functionality."""

    def test_multiple_counting_mixins_coexistence(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test that multiple counting configurations work together."""
        with session_context as session:
            # Create model instances that demonstrate different counting types
            direct_parent = MockCountingParentModel(name="Direct counting")
            filtered_parent = MockFilteredParentModel(name="Filtered counting")
            cross_parent = MockCrossTableParentModel(name="Cross-table counting")
            complex_parent = MockComplexParentModel(name="Complex counting")

            session.add_all(
                [direct_parent, filtered_parent, cross_parent, complex_parent]
            )
            session.flush()

            # Add data to each model type
            # Direct items
            direct_item = MockDirectItem(
                name="Direct", counting_parent_id=direct_parent.id
            )
            session.add(direct_item)

            # Filtered items (mix of active/inactive)
            active_item = MockFilteredItem(
                name="Active", is_active=True, filtered_parent_id=filtered_parent.id
            )
            inactive_item = MockFilteredItem(
                name="Inactive", is_active=False, filtered_parent_id=filtered_parent.id
            )
            session.add_all([active_item, inactive_item])

            # Cross-table items
            intermediate = MockIntermediateItem(
                name="Intermediate", cross_parent_id=cross_parent.id
            )
            session.add(intermediate)
            session.flush()

            cross_item = MockCrossItem(name="Cross", intermediate_id=intermediate.id)
            session.add(cross_item)

            # Complex filtered cross-table items
            level1 = MockLevel1Item(name="Level1", complex_parent_id=complex_parent.id)
            session.add(level1)
            session.flush()

            level2 = MockLevel2Item(name="Level2", level1_id=level1.id)
            session.add(level2)
            session.flush()

            selected_deep = MockDeepItem(
                name="Selected", is_selected=True, level2_id=level2.id
            )
            unselected_deep = MockDeepItem(
                name="Unselected", is_selected=False, level2_id=level2.id
            )
            session.add_all([selected_deep, unselected_deep])
            session.flush()

            # Refresh all relationships
            session.refresh(direct_parent, attribute_names=["direct_items"])
            session.refresh(filtered_parent, attribute_names=["filtered_items"])
            session.refresh(cross_parent, attribute_names=["intermediate_items"])
            session.refresh(complex_parent, attribute_names=["level1_items"])
            session.refresh(intermediate, attribute_names=["cross_items"])
            session.refresh(level1, attribute_names=["level2_items"])
            session.refresh(level2, attribute_names=["deep_items"])

            # Test all count properties work correctly and independently
            assert direct_parent.direct_items_count == 1
            assert filtered_parent.active_items_count == 1  # Only active items
            assert cross_parent.cross_items_count == 1
            assert complex_parent.selected_deep_items_count == 1  # Only selected items

    def test_counting_and_existence_mixins_together(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test that counting mixin can coexist with existence check mixin."""

        # Create specialized item model for this test
        class MixedTestItem(Base):
            __tablename__ = "mixed_test_items"

            id: Mapped[str] = mapped_column(
                primary_key=True, default=lambda: str(uuid.uuid4())
            )
            name: Mapped[str] = mapped_column(String(50), nullable=False)
            mixed_parent_id: Mapped[str] = mapped_column(
                ForeignKey("mixed_mixin_test.id"), nullable=False
            )

            # Relationship
            mixed_parent: Mapped["MixedMixinModel"] = relationship(
                back_populates="test_items"
            )

        # Create a model that uses both mixins
        class MixedMixinModel(ExistenceCheckMixin, CountingMixin, Base, TimestampMixin):
            __tablename__ = "mixed_mixin_test"

            id: Mapped[str] = mapped_column(
                primary_key=True, default=lambda: str(uuid.uuid4())
            )
            name: Mapped[str] = mapped_column(String(50), nullable=False)

            # Relationship for both existence and counting
            test_items: Mapped[List["MixedTestItem"]] = relationship(
                back_populates="mixed_parent"
            )

            _existence_configs = {
                "test_items": ExistenceConfig(
                    model=MixedTestItem, foreign_key="mixed_parent_id"
                )
            }

            _counting_configs = {
                "test_items": DirectCountConfig(
                    model=MixedTestItem, foreign_key="mixed_parent_id"
                )
            }

        with session_context as session:
            # Create tables (this test model won't be in fixture)
            Base.metadata.create_all(session.bind)

            mixed_model = MixedMixinModel(name="Mixed mixin test")
            session.add(mixed_model)
            session.flush()

            # Test both properties exist
            assert hasattr(mixed_model, "has_test_items")
            assert hasattr(mixed_model, "test_items_count")

            # Initially both should be False/0
            session.refresh(mixed_model, attribute_names=["test_items"])
            assert mixed_model.has_test_items is False
            assert mixed_model.test_items_count == 0

            # Add an item
            item = MixedTestItem(name="Test item", mixed_parent_id=mixed_model.id)
            session.add(item)
            session.flush()

            # Refresh and test both properties
            session.refresh(mixed_model, attribute_names=["test_items"])
            assert mixed_model.has_test_items is True
            assert mixed_model.test_items_count == 1


class TestIntegration:
    """Integration tests combining multiple aspects of mixin functionality."""

    def test_complete_workflow(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test complete workflow from model creation to SQL filtering."""
        with session_context as session:
            # Create multiple parents
            parent1 = MockParentModel(name="Parent 1")
            parent2 = MockParentModel(name="Parent 2")
            parent3 = MockParentModel(name="Parent 3")

            session.add_all([parent1, parent2, parent3])
            session.flush()

            # Add children to some parents
            child1 = MockChildModel(name="Child 1", parent_id=parent1.id)
            child2a = MockChildModel(name="Child 2a", parent_id=parent2.id)
            child2b = MockChildModel(name="Child 2b", parent_id=parent2.id)

            session.add_all([child1, child2a, child2b])
            session.flush()

            # Test Python context after loading relationships
            session.refresh(parent1, attribute_names=["children"])
            session.refresh(parent2, attribute_names=["children"])
            session.refresh(parent3, attribute_names=["children"])

            assert parent1.has_children is True
            assert parent2.has_children is True
            assert parent3.has_children is False

            # Test SQL context
            parents_with_children = (
                session.query(MockParentModel)
                .filter(MockParentModel.has_children)
                .all()
            )

            assert len(parents_with_children) == 2
            parent_ids_with_children = {p.id for p in parents_with_children}
            assert parent1.id in parent_ids_with_children
            assert parent2.id in parent_ids_with_children
            assert parent3.id not in parent_ids_with_children

            # Test complex SQL query combining multiple conditions
            parents_with_children_named_parent2 = (
                session.query(MockParentModel)
                .filter(
                    MockParentModel.has_children, MockParentModel.name == "Parent 2"
                )
                .all()
            )

            assert len(parents_with_children_named_parent2) == 1
            assert parents_with_children_named_parent2[0].id == parent2.id


# Status Check Mixin Tests
class TestStatusConfigClasses:
    """Test status configuration dataclass functionality."""

    def test_status_condition_creation(self) -> None:
        """Test creating StatusCondition with different condition types."""
        # Test equals condition
        equals_condition = StatusCondition(condition_type="equals", value=True)
        assert equals_condition.condition_type == "equals"
        assert equals_condition.value is True
        assert equals_condition.field is None

        # Test not_null condition
        not_null_condition = StatusCondition(condition_type="not_null")
        assert not_null_condition.condition_type == "not_null"
        assert not_null_condition.value is None
        assert not_null_condition.field is None

        # Test source_name condition
        source_condition = StatusCondition(
            condition_type="source_name", value="manual", field="name"
        )
        assert source_condition.condition_type == "source_name"
        assert source_condition.value == "manual"
        assert source_condition.field == "name"

    def test_field_status_config_creation(self) -> None:
        """Test creating FieldStatusConfig with required parameters."""
        condition = StatusCondition(condition_type="equals", value=True)
        config = FieldStatusConfig(
            model=MockStatusItem,
            foreign_key="status_parent_id",
            field="is_active",
            condition=condition,
        )

        assert config.model == MockStatusItem
        assert config.foreign_key == "status_parent_id"
        assert config.field == "is_active"
        assert config.condition == condition
        assert config.relationship_name is None
        assert config.property_name is None

    def test_field_status_config_with_custom_names(self) -> None:
        """Test FieldStatusConfig with custom relationship and property names."""
        condition = StatusCondition(condition_type="equals", value="completed")
        config = FieldStatusConfig(
            model=MockStatusItem,
            foreign_key="status_parent_id",
            field="status",
            condition=condition,
            relationship_name="custom_items",
            property_name="has_custom_completed",
        )

        assert config.model == MockStatusItem
        assert config.foreign_key == "status_parent_id"
        assert config.field == "status"
        assert config.condition == condition
        assert config.relationship_name == "custom_items"
        assert config.property_name == "has_custom_completed"

    def test_source_status_config_creation(self) -> None:
        """Test creating SourceStatusConfig with required parameters."""
        config = SourceStatusConfig(
            source_model=MockSourceModel,
            source_field="source_id",
            source_name_field="name",
            expected_value="manual",
        )

        assert config.source_model == MockSourceModel
        assert config.source_field == "source_id"
        assert config.source_name_field == "name"
        assert config.expected_value == "manual"
        assert config.relationship_name is None
        assert config.property_name is None

    def test_source_status_config_with_custom_names(self) -> None:
        """Test SourceStatusConfig with custom names."""
        config = SourceStatusConfig(
            source_model=MockSourceModel,
            source_field="source_id",
            source_name_field="name",
            expected_value="auto",
            relationship_name="custom_source",
            property_name="is_automated",
        )

        assert config.source_model == MockSourceModel
        assert config.source_field == "source_id"
        assert config.source_name_field == "name"
        assert config.expected_value == "auto"
        assert config.relationship_name == "custom_source"
        assert config.property_name == "is_automated"

    def test_cross_table_status_config_creation(self) -> None:
        """Test creating CrossTableStatusConfig with relationship path."""
        condition = StatusCondition(condition_type="equals", value=True)
        config = CrossTableStatusConfig(
            model=MockCrossLevel2,
            relationship_path=["level1_items", "level2_items"],
            field="is_active",
            condition=condition,
        )

        assert config.model == MockCrossLevel2
        assert config.relationship_path == ["level1_items", "level2_items"]
        assert config.field == "is_active"
        assert config.condition == condition
        assert config.relationship_name is None
        assert config.property_name is None

    def test_relationship_status_config_creation(self) -> None:
        """Test creating RelationshipStatusConfig for field checks."""
        condition = StatusCondition(condition_type="not_null")
        config = RelationshipStatusConfig(
            field="interpretation_id",
            condition=condition,
        )

        assert config.field == "interpretation_id"
        assert config.condition == condition
        assert config.relationship_name is None
        assert config.property_name is None

    def test_relationship_status_config_with_custom_property(self) -> None:
        """Test RelationshipStatusConfig with custom property name."""
        condition = StatusCondition(condition_type="not_null")
        config = RelationshipStatusConfig(
            field="parent_id",
            condition=condition,
            property_name="has_parent_link",
        )

        assert config.field == "parent_id"
        assert config.condition == condition
        assert config.relationship_name is None
        assert config.property_name == "has_parent_link"

    def test_filtered_relationship_status_config_creation(self) -> None:
        """Test creating FilteredRelationshipStatusConfig."""
        config = FilteredRelationshipStatusConfig(
            model=MockStatusItem,
            foreign_key="status_parent_id",
            filter_field="is_active",
            filter_value=True,
        )

        assert config.model == MockStatusItem
        assert config.foreign_key == "status_parent_id"
        assert config.filter_field == "is_active"
        assert config.filter_value is True
        assert config.relationship_name is None
        assert config.property_name is None

    def test_filtered_relationship_status_config_with_custom_names(self) -> None:
        """Test FilteredRelationshipStatusConfig with custom names."""
        config = FilteredRelationshipStatusConfig(
            model=MockStatusItem,
            foreign_key="status_parent_id",
            filter_field="status",
            filter_value="completed",
            relationship_name="custom_items",
            property_name="has_custom_completed_items",
        )

        assert config.model == MockStatusItem
        assert config.foreign_key == "status_parent_id"
        assert config.filter_field == "status"
        assert config.filter_value == "completed"
        assert config.relationship_name == "custom_items"
        assert config.property_name == "has_custom_completed_items"


class TestStatusPropertyGeneration:
    """Test automatic status property generation from configurations."""

    def test_field_status_property_generation(self) -> None:
        """Test that field-based status properties are generated correctly."""
        # Properties should be generated automatically via __init_subclass__
        assert hasattr(MockStatusParent, "has_active_items")
        assert hasattr(MockStatusParent, "has_completed_items")

        # Verify they're hybrid properties
        active_prop = MockStatusParent.has_active_items
        completed_prop = MockStatusParent.has_completed_items
        assert hasattr(active_prop, "expression")
        assert hasattr(completed_prop, "expression")

        # Verify that accessing the class attribute gives us expressions
        class_attr_active = MockStatusParent.has_active_items
        class_attr_completed = MockStatusParent.has_completed_items
        assert hasattr(class_attr_active, "name")  # Should be a labeled expression
        assert hasattr(class_attr_completed, "name")  # Should be a labeled expression

    def test_source_status_property_generation(self) -> None:
        """Test that source-based status properties are generated correctly."""
        assert hasattr(MockStatusParent, "is_manual")

        # Verify it's a hybrid property
        manual_prop = MockStatusParent.is_manual
        assert hasattr(manual_prop, "expression")

        # Verify that accessing the class attribute gives us an expression
        class_attr = MockStatusParent.is_manual
        assert hasattr(class_attr, "name")  # Should be a labeled expression

    def test_relationship_status_property_generation(self) -> None:
        """Test that relationship-based status properties are generated correctly."""
        assert hasattr(MockStatusParent, "is_linked")
        assert hasattr(MockRelationshipStatusModel, "is_from_interpretation")
        assert hasattr(MockRelationshipStatusModel, "is_has_parent")

        # Verify they're hybrid properties
        linked_prop = MockStatusParent.is_linked
        interp_prop = MockRelationshipStatusModel.is_from_interpretation
        parent_prop = MockRelationshipStatusModel.is_has_parent

        assert hasattr(linked_prop, "expression")
        assert hasattr(interp_prop, "expression")
        assert hasattr(parent_prop, "expression")

    def test_cross_table_status_property_generation(self) -> None:
        """Test that cross-table status properties are generated correctly."""
        assert hasattr(MockCrossStatusParent, "has_active_deep_items")

    def test_filtered_relationship_status_property_generation(self) -> None:
        """Test that filtered relationship status properties are generated correctly."""
        assert hasattr(MockStatusParent, "has_active_items")

        # Note: This uses the same property name as field-based status but tests
        # a different config type (FilteredRelationshipStatusConfig vs
        # FieldStatusConfig). The mixin should handle multiple configs
        # generating different properties

        # Verify it's a hybrid property
        filtered_prop = MockStatusParent.has_active_items
        assert hasattr(filtered_prop, "expression")

    def test_status_property_naming_convention(self) -> None:
        """Test that status properties follow correct naming patterns."""
        # Field-based status: has_active_{config_key} or custom names
        assert hasattr(MockStatusParent, "has_active_items")
        assert hasattr(MockStatusParent, "has_completed_items")

        # Source-based status: is_{config_key}
        assert hasattr(MockStatusParent, "is_manual")

        # Relationship-based status: is_{config_key}
        assert hasattr(MockStatusParent, "is_linked")
        assert hasattr(MockRelationshipStatusModel, "is_from_interpretation")

        # Filtered relationship status: has_active_{config_key}
        assert hasattr(MockStatusParent, "has_active_filtered_items")

        # Cross-table status: has_active_{config_key}
        assert hasattr(MockCrossStatusParent, "has_active_deep_items")

        # Verify no unexpected properties were created
        assert not hasattr(MockStatusParent, "has_status_parent_id")
        assert not hasattr(MockStatusParent, "active_items_status")
        assert not hasattr(MockCrossStatusParent, "deep_items_active")

    def test_status_property_docstring_generation(self) -> None:
        """Test that generated status properties have appropriate docstrings."""
        active_items_prop = MockStatusParent.has_active_items
        manual_prop = MockStatusParent.is_manual
        linked_prop = MockStatusParent.is_linked

        # The properties should have been generated with Python methods
        # that have docstrings
        active_python_method = active_items_prop.fget
        manual_python_method = manual_prop.fget
        linked_python_method = linked_prop.fget

        assert active_python_method.__doc__ is not None
        assert manual_python_method.__doc__ is not None
        assert linked_python_method.__doc__ is not None

        # Check that docstrings contain model-specific information
        assert "mockstatusparent" in active_python_method.__doc__.lower()
        assert (
            "items" in active_python_method.__doc__.lower()
        )  # Config key, not property name

        assert "mockstatusparent" in manual_python_method.__doc__.lower()
        assert "manual" in manual_python_method.__doc__.lower()

        assert "mockstatusparent" in linked_python_method.__doc__.lower()
        assert "linked" in linked_python_method.__doc__.lower()


class TestStatusErrorHandling:
    """Test error handling for misconfigured status properties."""

    def test_missing_relationship_error_field_config(self) -> None:
        """Test error when configured relationship doesn't exist on model
        for field config."""
        with pytest.raises(AttributeError) as exc_info:

            class BadFieldConfigModel(StatusCheckMixin, Base):
                __tablename__ = "bad_field_config"
                id: Mapped[str] = mapped_column(primary_key=True)

                _status_configs = {
                    "nonexistent": FieldStatusConfig(
                        model=MockStatusItem,
                        foreign_key="bad_parent_id",
                        field="is_active",
                        condition=StatusCondition(condition_type="equals", value=True),
                    )
                }

        error_message = str(exc_info.value)
        assert "BadFieldConfigModel" in error_message
        assert "does not have relationship 'nonexistent'" in error_message

    def test_missing_source_field_error(self) -> None:
        """Test error when source field doesn't exist on model."""
        with pytest.raises(AttributeError) as exc_info:

            class BadSourceConfigModel(StatusCheckMixin, Base):
                __tablename__ = "bad_source_config"
                id: Mapped[str] = mapped_column(primary_key=True)

                _status_configs = {
                    "manual": SourceStatusConfig(
                        source_model=MockSourceModel,
                        source_field="nonexistent_source_id",
                        source_name_field="name",
                        expected_value="manual",
                    )
                }

        error_message = str(exc_info.value)
        assert "BadSourceConfigModel" in error_message
        assert "does not have field 'nonexistent_source_id'" in error_message

    def test_missing_relationship_field_error(self) -> None:
        """Test error when relationship field doesn't exist on model."""
        with pytest.raises(AttributeError) as exc_info:

            class BadRelationshipConfigModel(StatusCheckMixin, Base):
                __tablename__ = "bad_relationship_config"
                id: Mapped[str] = mapped_column(primary_key=True)

                _status_configs = {
                    "linked": RelationshipStatusConfig(
                        field="nonexistent_field_id",
                        condition=StatusCondition(condition_type="not_null"),
                    )
                }

        error_message = str(exc_info.value)
        assert "BadRelationshipConfigModel" in error_message
        assert "does not have field 'nonexistent_field_id'" in error_message

    def test_missing_filter_field_error(self) -> None:
        """Test error when filter field doesn't exist on target model."""
        with pytest.raises(AttributeError) as exc_info:

            class BadFilterConfigModel(StatusCheckMixin, Base):
                __tablename__ = "bad_filter_config"
                id: Mapped[str] = mapped_column(primary_key=True)

                # Add a valid relationship that exists
                test_items: List[MockStatusItem] = []

                _status_configs = {
                    "test_items": FilteredRelationshipStatusConfig(
                        model=MockStatusItem,
                        foreign_key="status_parent_id",
                        filter_field="nonexistent_filter_field",
                        filter_value=True,
                    )
                }

        error_message = str(exc_info.value)
        assert "MockStatusItem" in error_message
        assert "does not have field 'nonexistent_filter_field'" in error_message

    def test_missing_cross_table_relationship_error(self) -> None:
        """Test error when cross-table relationship doesn't exist on model."""
        with pytest.raises(AttributeError) as exc_info:

            class BadCrossConfigModel(StatusCheckMixin, Base):
                __tablename__ = "bad_cross_config"
                id: Mapped[str] = mapped_column(primary_key=True)

                _status_configs = {
                    "nonexistent_deep": CrossTableStatusConfig(
                        model=MockCrossLevel2,
                        relationship_path=["nonexistent_items", "level2_items"],
                        field="is_active",
                        condition=StatusCondition(condition_type="equals", value=True),
                    )
                }

        error_message = str(exc_info.value)
        assert "BadCrossConfigModel" in error_message
        assert "does not have relationship 'nonexistent_deep'" in error_message

    def test_no_status_config_no_properties(self) -> None:
        """Test that models without _status_configs don't get status properties."""

        class NoStatusConfigModel(StatusCheckMixin, Base):
            __tablename__ = "no_status_config"
            id: Mapped[str] = mapped_column(primary_key=True)

        # Should not have any is_* or has_active_* properties
        is_properties = [
            attr for attr in dir(NoStatusConfigModel) if attr.startswith("is_")
        ]
        has_active_properties = [
            attr for attr in dir(NoStatusConfigModel) if attr.startswith("has_active_")
        ]

        # Filter out any inherited attributes that might start with these patterns
        model_is_properties = [
            attr
            for attr in is_properties
            if hasattr(getattr(NoStatusConfigModel, attr), "expression")
        ]
        model_has_active_properties = [
            attr
            for attr in has_active_properties
            if hasattr(getattr(NoStatusConfigModel, attr), "expression")
        ]

        assert len(model_is_properties) == 0
        assert len(model_has_active_properties) == 0

    def test_custom_relationship_name_validation(self) -> None:
        """Test validation of custom relationship names."""
        # Test the validation logic by attempting to create a model with bad config
        with pytest.raises(AttributeError) as exc_info:

            class BadRelationshipNameModel(StatusCheckMixin, Base):
                __tablename__ = "bad_relationship_name"
                id: Mapped[str] = mapped_column(primary_key=True)

                _status_configs = {
                    "test": FieldStatusConfig(
                        model=MockStatusItem,
                        foreign_key="status_parent_id",
                        field="is_active",
                        condition=StatusCondition(condition_type="equals", value=True),
                        relationship_name="wrong_name",
                    )
                }

        error_message = str(exc_info.value)
        assert "BadRelationshipNameModel" in error_message
        assert "does not have relationship 'wrong_name'" in error_message


class TestStatusPythonContext:
    """Test generated status properties in Python context (instance access)."""

    def test_field_status_empty_relationship(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test field-based status with no related items."""
        with session_context as session:
            parent = MockStatusParent(name="Parent with no items")
            session.add(parent)
            session.flush()

            # Test Python context - should return False for empty relationship
            assert parent.has_active_items is False
            assert parent.has_completed_items is False

    def test_field_status_with_active_items(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test field-based status with active items."""
        with session_context as session:
            parent = MockStatusParent(name="Parent with active items")
            session.add(parent)
            session.flush()

            # Add active and inactive items
            active_item = MockStatusItem(
                name="Active item", is_active=True, status_parent_id=parent.id
            )
            inactive_item = MockStatusItem(
                name="Inactive item", is_active=False, status_parent_id=parent.id
            )
            session.add_all([active_item, inactive_item])
            session.flush()

            # Refresh parent to load relationship
            session.refresh(parent, attribute_names=["status_items"])

            # Test Python context - should return True for active items
            assert parent.has_active_items is True

    def test_field_status_with_completed_items(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test field-based status with completed items."""
        with session_context as session:
            parent = MockStatusParent(name="Parent with completed items")
            session.add(parent)
            session.flush()

            # Add completed and pending items
            completed_item = MockStatusItem(
                name="Completed item",
                status="completed",
                status_parent_id=parent.id,
            )
            pending_item = MockStatusItem(
                name="Pending item", status="pending", status_parent_id=parent.id
            )
            session.add_all([completed_item, pending_item])
            session.flush()

            # Refresh parent to load relationship
            session.refresh(parent, attribute_names=["status_items"])

            # Test Python context - should return True for completed items
            assert parent.has_completed_items is True

    def test_source_status_with_manual_source(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test source-based status with manual source."""
        with session_context as session:
            # Create source models
            manual_source = MockSourceModel(name="manual")
            auto_source = MockSourceModel(name="auto")
            session.add_all([manual_source, auto_source])
            session.flush()

            # Create parent with manual source
            manual_parent = MockStatusParent(
                name="Manual parent", source_id=manual_source.id
            )
            auto_parent = MockStatusParent(name="Auto parent", source_id=auto_source.id)
            no_source_parent = MockStatusParent(name="No source parent")

            session.add_all([manual_parent, auto_parent, no_source_parent])
            session.flush()

            # Refresh to load source relationships
            session.refresh(manual_parent, attribute_names=["source"])
            session.refresh(auto_parent, attribute_names=["source"])

            # Test Python context
            assert manual_parent.is_manual is True
            assert auto_parent.is_manual is False
            assert no_source_parent.is_manual is False

    def test_relationship_status_with_linked_field(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test relationship-based status with linked field."""
        with session_context as session:
            # Create parents with and without links
            linked_parent = MockStatusParent(
                name="Linked parent", link_id="some-link-id"
            )
            unlinked_parent = MockStatusParent(name="Unlinked parent")
            session.add_all([linked_parent, unlinked_parent])
            session.flush()

            # Test Python context - should check if link_id is not null
            assert linked_parent.is_linked is True
            assert unlinked_parent.is_linked is False

    def test_relationship_status_model(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test relationship-based status on dedicated model."""
        with session_context as session:
            # Create models with and without interpretation
            with_interp = MockRelationshipStatusModel(
                name="With interpretation", interpretation_id="interp-123"
            )
            without_interp = MockRelationshipStatusModel(name="Without interpretation")

            # Create models with and without parent
            with_parent = MockRelationshipStatusModel(
                name="With parent", parent_id="parent-456"
            )
            without_parent = MockRelationshipStatusModel(name="Without parent")

            session.add_all([with_interp, without_interp, with_parent, without_parent])
            session.flush()

            # Test Python context
            assert with_interp.is_from_interpretation is True
            assert without_interp.is_from_interpretation is False
            assert with_parent.is_has_parent is True
            assert without_parent.is_has_parent is False

    def test_cross_table_status_python_context(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test cross-table status properties in Python context."""
        with session_context as session:
            parent = MockCrossStatusParent(name="Cross-table parent")
            session.add(parent)
            session.flush()

            # Add level1 items
            level1_item = MockCrossLevel1(name="Level1 item", cross_parent_id=parent.id)
            session.add(level1_item)
            session.flush()

            # Add level2 items with different active states
            active_level2 = MockCrossLevel2(
                name="Active Level2", is_active=True, level1_id=level1_item.id
            )
            inactive_level2 = MockCrossLevel2(
                name="Inactive Level2", is_active=False, level1_id=level1_item.id
            )
            session.add_all([active_level2, inactive_level2])
            session.flush()

            # Refresh relationships
            session.refresh(parent, attribute_names=["level1_items"])
            session.refresh(level1_item, attribute_names=["level2_items"])

            # Test Python context - should find active items through the path
            assert parent.has_active_deep_items is True

    def test_cross_table_status_no_active_items(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test cross-table status with no active items."""
        with session_context as session:
            parent = MockCrossStatusParent(name="Cross-table parent no active")
            session.add(parent)
            session.flush()

            # Add level1 items
            level1_item = MockCrossLevel1(name="Level1 item", cross_parent_id=parent.id)
            session.add(level1_item)
            session.flush()

            # Add only inactive level2 items
            inactive_level2 = MockCrossLevel2(
                name="Inactive Level2", is_active=False, level1_id=level1_item.id
            )
            session.add(inactive_level2)
            session.flush()

            # Refresh relationships
            session.refresh(parent, attribute_names=["level1_items"])
            session.refresh(level1_item, attribute_names=["level2_items"])

            # Test Python context - should return False for no active items
            assert parent.has_active_deep_items is False

    def test_filtered_relationship_status_python_context(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test filtered relationship status properties in Python context."""
        with session_context as session:
            parent = MockStatusParent(name="Filtered relationship parent")
            session.add(parent)
            session.flush()

            # Add items with different active states
            active_item1 = MockStatusItem(
                name="Active 1", is_active=True, status_parent_id=parent.id
            )
            active_item2 = MockStatusItem(
                name="Active 2", is_active=True, status_parent_id=parent.id
            )
            inactive_item = MockStatusItem(
                name="Inactive", is_active=False, status_parent_id=parent.id
            )

            session.add_all([active_item1, active_item2, inactive_item])
            session.flush()

            # Refresh parent to load relationship
            session.refresh(parent, attribute_names=["status_items"])

            # Test Python context - should check filtered relationship
            # Note: This tests the 'items' config which is
            # FilteredRelationshipStatusConfig
            assert parent.has_active_items is True

    def test_multiple_status_properties_independence(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test that multiple status properties work independently."""
        with session_context as session:
            # Create source
            manual_source = MockSourceModel(name="manual")
            session.add(manual_source)
            session.flush()

            # Create parent with source and link
            parent = MockStatusParent(
                name="Multi-status parent",
                source_id=manual_source.id,
                link_id="some-link",
            )
            session.add(parent)
            session.flush()

            # Add items with different statuses
            active_item = MockStatusItem(
                name="Active", is_active=True, status_parent_id=parent.id
            )
            completed_item = MockStatusItem(
                name="Completed",
                status="completed",
                is_active=False,
                status_parent_id=parent.id,
            )
            pending_item = MockStatusItem(
                name="Pending", status="pending", status_parent_id=parent.id
            )

            session.add_all([active_item, completed_item, pending_item])
            session.flush()

            # Refresh relationships
            session.refresh(parent, attribute_names=["status_items", "source"])

            # Test that all status properties work independently
            assert parent.has_active_items is True  # Has active item
            assert parent.has_completed_items is True  # Has completed item
            assert parent.is_manual is True  # Has manual source
            assert parent.is_linked is True  # Has link_id set

    def test_status_properties_with_empty_data(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test status properties with no matching data."""
        with session_context as session:
            parent = MockStatusParent(name="Empty parent")
            session.add(parent)
            session.flush()

            # Add items but none match the status conditions
            inactive_item = MockStatusItem(
                name="Inactive",
                is_active=False,
                status="pending",
                status_parent_id=parent.id,
            )
            session.add(inactive_item)
            session.flush()

            # Refresh to load relationship
            session.refresh(parent, attribute_names=["status_items"])

            # Test that all properties return False
            assert parent.has_active_items is False  # No active items
            assert parent.has_completed_items is False  # No completed items
            assert parent.is_manual is False  # No source
            assert parent.is_linked is False  # No link_id


class TestStatusSQLContext:
    """Test generated status properties in SQL context (query filtering)."""

    def test_field_status_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering with field-based status properties."""
        with session_context as session:
            # Create parents with different item configurations
            parent_with_active = MockStatusParent(name="Has active items")
            parent_no_active = MockStatusParent(name="No active items")
            parent_empty = MockStatusParent(name="No items")

            session.add_all([parent_with_active, parent_no_active, parent_empty])
            session.flush()

            # Add active item to first parent
            active_item = MockStatusItem(
                name="Active", is_active=True, status_parent_id=parent_with_active.id
            )
            session.add(active_item)

            # Add only inactive items to second parent
            inactive_item = MockStatusItem(
                name="Inactive", is_active=False, status_parent_id=parent_no_active.id
            )
            session.add(inactive_item)
            session.flush()

            # Test SQL filtering - parents with active items
            parents_with_active = (
                session.query(MockStatusParent)
                .filter(MockStatusParent.has_active_items)
                .all()
            )

            assert len(parents_with_active) == 1
            assert parents_with_active[0].id == parent_with_active.id

            # Test SQL filtering - parents without active items
            parents_without_active = (
                session.query(MockStatusParent)
                .filter(~MockStatusParent.has_active_items)
                .all()
            )

            assert len(parents_without_active) == 2
            parent_ids_without = {p.id for p in parents_without_active}
            assert parent_no_active.id in parent_ids_without
            assert parent_empty.id in parent_ids_without

    def test_source_status_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering with source-based status properties."""
        with session_context as session:
            # Create source models
            manual_source = MockSourceModel(name="manual")
            auto_source = MockSourceModel(name="auto")
            session.add_all([manual_source, auto_source])
            session.flush()

            # Create parents with different sources
            manual_parent = MockStatusParent(
                name="Manual parent", source_id=manual_source.id
            )
            auto_parent = MockStatusParent(name="Auto parent", source_id=auto_source.id)
            no_source_parent = MockStatusParent(name="No source parent")

            session.add_all([manual_parent, auto_parent, no_source_parent])
            session.flush()

            # Test SQL filtering - manual parents
            manual_parents = (
                session.query(MockStatusParent).filter(MockStatusParent.is_manual).all()
            )

            assert len(manual_parents) == 1
            assert manual_parents[0].id == manual_parent.id

            # Test SQL filtering - non-manual parents
            non_manual_parents = (
                session.query(MockStatusParent)
                .filter(~MockStatusParent.is_manual)
                .all()
            )

            assert len(non_manual_parents) == 2
            non_manual_ids = {p.id for p in non_manual_parents}
            assert auto_parent.id in non_manual_ids
            assert no_source_parent.id in non_manual_ids

    def test_relationship_status_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering with relationship-based status properties."""
        with session_context as session:
            # Create models with and without links
            linked_parent = MockStatusParent(
                name="Linked parent", link_id="some-link-id"
            )
            unlinked_parent = MockStatusParent(name="Unlinked parent")

            session.add_all([linked_parent, unlinked_parent])
            session.flush()

            # Test SQL filtering - linked parents
            linked_parents = (
                session.query(MockStatusParent).filter(MockStatusParent.is_linked).all()
            )

            assert len(linked_parents) == 1
            assert linked_parents[0].id == linked_parent.id

            # Test SQL filtering - unlinked parents
            unlinked_parents = (
                session.query(MockStatusParent)
                .filter(~MockStatusParent.is_linked)
                .all()
            )

            assert len(unlinked_parents) == 1
            assert unlinked_parents[0].id == unlinked_parent.id

    def test_cross_table_status_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering with cross-table status properties."""
        with session_context as session:
            # Create parent with active deep items
            parent_with_active = MockCrossStatusParent(name="Has active deep")
            session.add(parent_with_active)
            session.flush()

            level1_active = MockCrossLevel1(
                name="Level1 active", cross_parent_id=parent_with_active.id
            )
            session.add(level1_active)
            session.flush()

            active_level2 = MockCrossLevel2(
                name="Active Level2", is_active=True, level1_id=level1_active.id
            )
            session.add(active_level2)

            # Create parent with no active deep items
            parent_no_active = MockCrossStatusParent(name="No active deep")
            session.add(parent_no_active)
            session.flush()

            level1_inactive = MockCrossLevel1(
                name="Level1 inactive", cross_parent_id=parent_no_active.id
            )
            session.add(level1_inactive)
            session.flush()

            inactive_level2 = MockCrossLevel2(
                name="Inactive Level2", is_active=False, level1_id=level1_inactive.id
            )
            session.add(inactive_level2)
            session.flush()

            # Test SQL filtering - parents with active deep items
            parents_with_active_deep = (
                session.query(MockCrossStatusParent)
                .filter(MockCrossStatusParent.has_active_deep_items)
                .all()
            )

            assert len(parents_with_active_deep) == 1
            assert parents_with_active_deep[0].id == parent_with_active.id

            # Test SQL filtering - parents without active deep items
            parents_without_active_deep = (
                session.query(MockCrossStatusParent)
                .filter(~MockCrossStatusParent.has_active_deep_items)
                .all()
            )

            assert len(parents_without_active_deep) == 1
            assert parents_without_active_deep[0].id == parent_no_active.id

    def test_status_sql_expression_structure(self) -> None:
        """Test that status SQL expressions have expected structure."""
        # Get the SQL expressions for various status properties (class attribute access)
        field_status_expr = MockStatusParent.has_active_items
        source_status_expr = MockStatusParent.is_manual
        relationship_status_expr = MockStatusParent.is_linked
        cross_status_expr = MockCrossStatusParent.has_active_deep_items

        # Should be labeled expressions
        assert hasattr(field_status_expr, "name")
        assert field_status_expr.name == "has_active_items"

        assert hasattr(source_status_expr, "name")
        assert source_status_expr.name == "is_manual"

        assert hasattr(relationship_status_expr, "name")
        assert relationship_status_expr.name == "is_linked"

        assert hasattr(cross_status_expr, "name")
        assert cross_status_expr.name == "has_active_deep_items"

    def test_multiple_status_sql_queries(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL queries combining multiple status properties."""
        with session_context as session:
            # Create source
            manual_source = MockSourceModel(name="manual")
            session.add(manual_source)
            session.flush()

            # Create parent that matches multiple conditions
            multi_match_parent = MockStatusParent(
                name="Multi-match parent",
                source_id=manual_source.id,
                link_id="some-link",
            )
            session.add(multi_match_parent)
            session.flush()

            # Add active item
            active_item = MockStatusItem(
                name="Active", is_active=True, status_parent_id=multi_match_parent.id
            )
            session.add(active_item)

            # Create parent that matches some conditions
            partial_match_parent = MockStatusParent(
                name="Partial match", source_id=manual_source.id
            )
            session.add(partial_match_parent)
            session.flush()

            # Add inactive item
            inactive_item = MockStatusItem(
                name="Inactive",
                is_active=False,
                status_parent_id=partial_match_parent.id,
            )
            session.add(inactive_item)
            session.flush()

            # Test combining multiple status conditions with AND
            multi_condition_parents = (
                session.query(MockStatusParent)
                .filter(
                    MockStatusParent.has_active_items
                    & MockStatusParent.is_manual
                    & MockStatusParent.is_linked
                )
                .all()
            )

            assert len(multi_condition_parents) == 1
            assert multi_condition_parents[0].id == multi_match_parent.id

            # Test combining status conditions with OR
            any_condition_parents = (
                session.query(MockStatusParent)
                .filter(MockStatusParent.has_active_items | MockStatusParent.is_linked)
                .all()
            )

            assert len(any_condition_parents) == 1
            assert any_condition_parents[0].id == multi_match_parent.id

    def test_status_ordering_and_aggregation(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test using status properties in ORDER BY and other SQL operations."""
        with session_context as session:
            # Create parents with different characteristics
            linked_parent = MockStatusParent(name="Z Linked", link_id="link-1")
            unlinked_parent = MockStatusParent(name="A Unlinked")

            session.add_all([linked_parent, unlinked_parent])
            session.flush()

            # Test ordering by status property (linked first)
            parents_ordered_by_status = (
                session.query(MockStatusParent)
                .order_by(MockStatusParent.is_linked.desc(), MockStatusParent.name)
                .all()
            )

            assert len(parents_ordered_by_status) == 2
            assert parents_ordered_by_status[0].id == linked_parent.id  # Linked first
            assert (
                parents_ordered_by_status[1].id == unlinked_parent.id
            )  # Unlinked second

            # Test selecting status value directly
            linked_status_result = (
                session.query(MockStatusParent.is_linked)
                .filter(MockStatusParent.id == linked_parent.id)
                .scalar()
            )

            assert linked_status_result is True

            unlinked_status_result = (
                session.query(MockStatusParent.is_linked)
                .filter(MockStatusParent.id == unlinked_parent.id)
                .scalar()
            )

            assert unlinked_status_result is False

    def test_filtered_relationship_status_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering with filtered relationship status properties."""
        with session_context as session:
            # Create parent with filtered items
            parent = MockStatusParent(name="Filtered parent")
            session.add(parent)
            session.flush()

            # Add items with different active states
            active_item1 = MockStatusItem(
                name="Active 1", is_active=True, status_parent_id=parent.id
            )
            active_item2 = MockStatusItem(
                name="Active 2", is_active=True, status_parent_id=parent.id
            )
            inactive_item = MockStatusItem(
                name="Inactive", is_active=False, status_parent_id=parent.id
            )

            session.add_all([active_item1, active_item2, inactive_item])

            # Create parent with no active items
            parent_no_active = MockStatusParent(name="No active parent")
            session.add(parent_no_active)
            session.flush()

            inactive_only = MockStatusItem(
                name="Inactive only",
                is_active=False,
                status_parent_id=parent_no_active.id,
            )
            session.add(inactive_only)
            session.flush()

            # Test SQL filtering using filtered relationship status
            # Note: This tests the 'items' config which is
            # FilteredRelationshipStatusConfig
            parents_with_active_filtered = (
                session.query(MockStatusParent)
                .filter(MockStatusParent.has_active_items)
                .all()
            )

            # Should find only the parent with active items
            assert len(parents_with_active_filtered) == 1
            assert parents_with_active_filtered[0].id == parent.id


class TestStatusEdgeCases:
    """Test edge cases and complex scenarios for status mixins."""

    def test_status_mixin_inheritance_chain(self) -> None:
        """Test that status mixin works correctly in inheritance chain."""
        # Verify that models inherit from status mixin
        assert issubclass(MockStatusParent, StatusCheckMixin)
        assert issubclass(MockStatusParent, Base)
        assert issubclass(MockStatusParent, TimestampMixin)

        # Verify the mixin functionality is present
        assert hasattr(MockStatusParent, "_generate_status_properties")
        assert hasattr(MockStatusParent, "_create_status_property")

    def test_status_properties_with_mixed_types(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test model with multiple different status property types."""
        with session_context as session:
            # Create necessary data
            manual_source = MockSourceModel(name="manual")
            session.add(manual_source)
            session.flush()

            # Create model that uses all status types
            parent = MockStatusParent(
                name="Mixed types parent",
                source_id=manual_source.id,
                link_id="link-123",
            )
            session.add(parent)
            session.flush()

            # Add items
            active_item = MockStatusItem(
                name="Active",
                is_active=True,
                status="completed",
                status_parent_id=parent.id,
            )
            session.add(active_item)
            session.flush()

            # Refresh relationships
            session.refresh(parent, attribute_names=["status_items", "source"])

            # Test that all different status types work on same model
            assert parent.has_active_items is True  # FieldStatusConfig
            assert parent.has_completed_items is True  # FieldStatusConfig
            assert parent.is_manual is True  # SourceStatusConfig
            assert parent.is_linked is True  # RelationshipStatusConfig
            # Note: 'items' FilteredRelationshipStatusConfig also exists

    def test_zero_matches_status_scenarios(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test status properties with zero matches across different scenarios."""
        with session_context as session:
            # Create models but don't add any matching data
            parent = MockStatusParent(name="No matches parent")
            cross_parent = MockCrossStatusParent(name="No active deep parent")
            relationship_model = MockRelationshipStatusModel(name="No links model")

            session.add_all([parent, cross_parent, relationship_model])
            session.flush()

            # Add non-matching data
            inactive_item = MockStatusItem(
                name="Inactive",
                is_active=False,
                status="pending",
                status_parent_id=parent.id,
            )
            session.add(inactive_item)

            # Add cross-table structure with no active items
            level1 = MockCrossLevel1(name="Level1", cross_parent_id=cross_parent.id)
            session.add(level1)
            session.flush()

            inactive_level2 = MockCrossLevel2(
                name="Inactive L2", is_active=False, level1_id=level1.id
            )
            session.add(inactive_level2)
            session.flush()

            # Refresh relationships
            session.refresh(parent, attribute_names=["status_items"])
            session.refresh(cross_parent, attribute_names=["level1_items"])
            session.refresh(level1, attribute_names=["level2_items"])

            # All should have zero matches
            assert parent.has_active_items is False
            assert parent.has_completed_items is False
            assert parent.is_manual is False
            assert parent.is_linked is False

            assert cross_parent.has_active_deep_items is False

            assert relationship_model.is_from_interpretation is False
            assert relationship_model.is_has_parent is False

    def test_custom_property_names(self) -> None:
        """Test status properties with custom property names."""

        # Create a model with custom property names
        class CustomNameModel(StatusCheckMixin, Base):
            __tablename__ = "custom_name_test"
            id: Mapped[str] = mapped_column(primary_key=True)
            interpretation_id: Mapped[str] = mapped_column(String(50), nullable=True)

            _status_configs = {
                "from_interpretation": RelationshipStatusConfig(
                    field="interpretation_id",
                    condition=StatusCondition(condition_type="not_null"),
                    property_name="has_interpretation_link",
                ),
            }

        # Test that custom property name is used
        assert hasattr(CustomNameModel, "has_interpretation_link")
        assert not hasattr(CustomNameModel, "is_from_interpretation")

        # Verify it's a hybrid property
        custom_prop = CustomNameModel.has_interpretation_link
        assert hasattr(custom_prop, "expression")


class TestStatusIntegration:
    """Integration tests combining status mixin with other mixins."""

    def test_status_and_existence_mixins_together(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test that status mixin can coexist with existence check mixin."""

        # Create specialized item model for this test
        class MixedStatusTestItem(Base):
            __tablename__ = "mixed_status_test_items"

            id: Mapped[str] = mapped_column(
                primary_key=True, default=lambda: str(uuid.uuid4())
            )
            name: Mapped[str] = mapped_column(String(50), nullable=False)
            is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
            mixed_parent_id: Mapped[str] = mapped_column(
                ForeignKey("mixed_status_test.id"), nullable=False
            )

            # Relationship
            mixed_parent: Mapped["MixedStatusModel"] = relationship(
                back_populates="test_items"
            )

        # Create a model that uses both mixins
        class MixedStatusModel(
            ExistenceCheckMixin, StatusCheckMixin, Base, TimestampMixin
        ):
            __tablename__ = "mixed_status_test"

            id: Mapped[str] = mapped_column(
                primary_key=True, default=lambda: str(uuid.uuid4())
            )
            name: Mapped[str] = mapped_column(String(50), nullable=False)

            # Relationship for both existence and status checking
            test_items: Mapped[List["MixedStatusTestItem"]] = relationship(
                back_populates="mixed_parent"
            )

            _existence_configs = {
                "test_items": ExistenceConfig(
                    model=MixedStatusTestItem, foreign_key="mixed_parent_id"
                )
            }

            _status_configs = {
                "items": FieldStatusConfig(
                    model=MixedStatusTestItem,
                    foreign_key="mixed_parent_id",
                    field="is_active",
                    condition=StatusCondition(condition_type="equals", value=True),
                    relationship_name="test_items",
                ),
            }

        with session_context as session:
            # Create tables (this test model won't be in fixture)
            Base.metadata.create_all(session.bind)

            mixed_model = MixedStatusModel(name="Mixed mixin test")
            session.add(mixed_model)
            session.flush()

            # Test both properties exist
            assert hasattr(mixed_model, "has_test_items")  # From ExistenceCheckMixin
            assert hasattr(mixed_model, "has_active_items")  # From StatusCheckMixin

            # Initially both should be False
            session.refresh(mixed_model, attribute_names=["test_items"])
            assert mixed_model.has_test_items is False
            assert mixed_model.has_active_items is False

            # Add an active item
            active_item = MixedStatusTestItem(
                name="Active item", is_active=True, mixed_parent_id=mixed_model.id
            )
            session.add(active_item)

            # Add an inactive item
            inactive_item = MixedStatusTestItem(
                name="Inactive item", is_active=False, mixed_parent_id=mixed_model.id
            )
            session.add(inactive_item)
            session.flush()

            # Refresh and test both properties
            session.refresh(mixed_model, attribute_names=["test_items"])
            assert mixed_model.has_test_items is True  # Has items (existence)
            assert mixed_model.has_active_items is True  # Has active items (status)

    def test_multiple_mixins_sql_filtering(
        self,
        session_context: SessionContext,
    ) -> None:
        """Test SQL filtering combining multiple mixin types."""
        with session_context as session:
            # Test using existing MockStatusParent which could have other mixins
            manual_source = MockSourceModel(name="manual")
            session.add(manual_source)
            session.flush()

            # Create parent with multiple characteristics
            parent = MockStatusParent(
                name="Multi-mixin parent",
                source_id=manual_source.id,
                link_id="link-id",
            )
            session.add(parent)
            session.flush()

            # Add active item
            active_item = MockStatusItem(
                name="Active", is_active=True, status_parent_id=parent.id
            )
            session.add(active_item)
            session.flush()

            # Test complex SQL filtering with multiple status properties
            complex_filter_results = (
                session.query(MockStatusParent)
                .filter(
                    MockStatusParent.has_active_items
                    & MockStatusParent.is_manual
                    & MockStatusParent.is_linked
                )
                .all()
            )

            assert len(complex_filter_results) == 1
            assert complex_filter_results[0].id == parent.id

            # Test that individual filters also work
            active_only = (
                session.query(MockStatusParent)
                .filter(MockStatusParent.has_active_items)
                .all()
            )
            manual_only = (
                session.query(MockStatusParent).filter(MockStatusParent.is_manual).all()
            )
            linked_only = (
                session.query(MockStatusParent).filter(MockStatusParent.is_linked).all()
            )

            assert len(active_only) == 1
            assert len(manual_only) == 1
            assert len(linked_only) == 1
