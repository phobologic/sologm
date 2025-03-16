"""
Base SQLAlchemy models and utilities for the RPG Helper application.
"""
from datetime import datetime, UTC
from typing import Optional, Dict, Any, TypeVar, Type, List, ClassVar
import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, object_session

from sologm.rpg_helper.db.config import Base, get_session, close_session
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

T = TypeVar('T', bound='BaseModel')

class ModelError(Exception):
    """Base exception for model-related errors."""
    pass

class SaveError(ModelError):
    """Exception raised when a model cannot be saved."""
    pass

class DeleteError(ModelError):
    """Exception raised when a model cannot be deleted."""
    pass

class NotFoundError(ModelError):
    """Exception raised when a model cannot be found."""
    pass

class BaseModel(Base):
    """
    Base model for all SQLAlchemy models in the application.
    
    Provides common functionality like:
    - UUID primary key
    - Created/updated timestamps
    - Common CRUD operations
    - Serialization methods
    """
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower() + 's'
    
    def save(self) -> None:
        """
        Save the model to the database.
        
        Raises:
            SaveError: If the model cannot be saved
        """
        session = object_session(self) or get_session()
        try:
            # If this is a new session, add the model
            if session != object_session(self):
                session.add(self)
            
            # Commit changes
            session.commit()
            
            logger.debug(
                f"Saved {self.__class__.__name__}",
                id=self.id
            )
        except Exception as e:
            session.rollback()
            logger.error(
                f"Error saving {self.__class__.__name__}",
                id=self.id,
                error=str(e)
            )
            raise SaveError(f"Could not save {self.__class__.__name__}: {str(e)}") from e
        finally:
            if session != object_session(self):
                close_session(session)
    
    def delete(self) -> None:
        """
        Delete the model from the database.
        
        Raises:
            DeleteError: If the model cannot be deleted
        """
        session = object_session(self) or get_session()
        try:
            # If this is a new session, add the model
            if session != object_session(self):
                session.add(self)
            
            # Delete the model
            session.delete(self)
            session.commit()
            
            logger.debug(
                f"Deleted {self.__class__.__name__}",
                id=self.id
            )
        except Exception as e:
            session.rollback()
            logger.error(
                f"Error deleting {self.__class__.__name__}",
                id=self.id,
                error=str(e)
            )
            raise DeleteError(f"Could not delete {self.__class__.__name__}: {str(e)}") from e
        finally:
            if session != object_session(self):
                close_session(session)
    
    @classmethod
    def get(cls: Type[T], id: str) -> T:
        """
        Get a model by ID.
        
        Args:
            id: The ID of the model to get
            
        Returns:
            The model
            
        Raises:
            NotFoundError: If the model cannot be found
        """
        session = get_session()
        try:
            model = session.query(cls).filter_by(id=id).first()
            if model is None:
                raise NotFoundError(f"{cls.__name__} with ID {id} not found")
            return model
        finally:
            close_session(session)
    
    @classmethod
    def get_or_none(cls: Type[T], id: str) -> Optional[T]:
        """
        Get a model by ID, or None if not found.
        
        Args:
            id: The ID of the model to get
            
        Returns:
            The model if found, None otherwise
        """
        session = get_session()
        try:
            return session.query(cls).filter_by(id=id).first()
        finally:
            close_session(session)
    
    @classmethod
    def get_all(cls: Type[T]) -> List[T]:
        """
        Get all models.
        
        Returns:
            List of all models
        """
        session = get_session()
        try:
            return session.query(cls).all()
        finally:
            close_session(session)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model from a dictionary.
        
        Args:
            data: Dictionary representation of the model
            
        Returns:
            New model instance
        """
        return cls(**data)
    
    def __repr__(self) -> str:
        """Return a string representation of the model."""
        return f"<{self.__class__.__name__}(id='{self.id}')>"
    
    @classmethod
    def get_by_id(cls, id: str) -> Optional[T]:
        """Get a model by ID."""
        session = get_session()
        try:
            return session.query(cls).filter_by(id=id).first()
        finally:
            close_session(session) 