"""
Base Repository class providing common CRUD operations.

Implements the Repository pattern for consistent data access across
socrates_auth and socrates_specs databases.
"""

from typing import List, Optional, Type, TypeVar, Generic, Any
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic repository class providing CRUD operations for any SQLAlchemy model.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: Session):
                super().__init__(User, session)

        repo = UserRepository(session)
        user = repo.get_by_id(user_id)
        users = repo.list(skip=0, limit=10)
    """

    def __init__(self, model_class: Type[T], session: Session):
        """
        Initialize repository with model class and session.

        Args:
            model_class: SQLAlchemy model class (e.g., User, Project)
            session: SQLAlchemy session bound to appropriate database
        """
        self.model_class = model_class
        self.session = session

    def create(self, **kwargs) -> T:
        """
        Create and persist a new model instance.

        Args:
            **kwargs: Model attributes

        Returns:
            Created model instance with ID

        Example:
            user = user_repo.create(email='test@example.com', username='test')
        """
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.flush()  # Populate ID without committing
        return instance

    def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Retrieve single model by primary key.

        Args:
            id: UUID primary key

        Returns:
            Model instance or None if not found
        """
        return self.session.query(self.model_class).filter(
            self.model_class.id == id
        ).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        List models with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of model instances
        """
        return self.session.query(self.model_class).offset(skip).limit(limit).all()

    def list_by_field(
        self,
        field_name: str,
        field_value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """
        List models filtered by a field value.

        Args:
            field_name: Name of the field to filter by
            field_value: Value to match
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of matching model instances

        Example:
            projects = project_repo.list_by_field('status', 'active')
        """
        field = getattr(self.model_class, field_name)
        return self.session.query(self.model_class).filter(
            field == field_value
        ).offset(skip).limit(limit).all()

    def get_by_field(self, field_name: str, field_value: Any) -> Optional[T]:
        """
        Get single model by field value.

        Args:
            field_name: Field name to filter by
            field_value: Value to match

        Returns:
            Model instance or None

        Example:
            user = user_repo.get_by_field('email', 'test@example.com')
        """
        field = getattr(self.model_class, field_name)
        return self.session.query(self.model_class).filter(
            field == field_value
        ).first()

    def update(self, id: UUID, **kwargs) -> Optional[T]:
        """
        Update model by ID.

        Args:
            id: Primary key
            **kwargs: Attributes to update

        Returns:
            Updated model instance or None if not found
        """
        instance = self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        self.session.flush()
        return instance

    def delete(self, id: UUID) -> bool:
        """
        Delete model by ID.

        Args:
            id: Primary key

        Returns:
            True if deleted, False if not found
        """
        instance = self.get_by_id(id)
        if not instance:
            return False

        self.session.delete(instance)
        self.session.flush()
        return True

    def exists(self, id: UUID) -> bool:
        """
        Check if model exists by ID.

        Args:
            id: Primary key

        Returns:
            True if exists, False otherwise
        """
        return self.session.query(self.model_class).filter(
            self.model_class.id == id
        ).exists()

    def count(self) -> int:
        """
        Count total models.

        Returns:
            Total count
        """
        return self.session.query(self.model_class).count()

    def count_by_field(self, field_name: str, field_value: Any) -> int:
        """
        Count models by field value.

        Args:
            field_name: Field to filter by
            field_value: Value to match

        Returns:
            Count of matching records
        """
        field = getattr(self.model_class, field_name)
        return self.session.query(self.model_class).filter(
            field == field_value
        ).count()

    def list_ordered(
        self,
        order_by: str = 'created_at',
        ascending: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """
        List models with ordering.

        Args:
            order_by: Field name to order by
            ascending: True for ASC, False for DESC
            skip: Offset
            limit: Limit

        Returns:
            Ordered list of models

        Example:
            recent = project_repo.list_ordered('created_at', ascending=False, limit=10)
        """
        field = getattr(self.model_class, order_by)
        query = self.session.query(self.model_class)

        if ascending:
            query = query.order_by(field.asc())
        else:
            query = query.order_by(desc(field))

        return query.offset(skip).limit(limit).all()

    def bulk_create(self, items: List[dict]) -> List[T]:
        """
        Create multiple models in bulk.

        Args:
            items: List of dicts with model attributes

        Returns:
            List of created instances

        Example:
            users = user_repo.bulk_create([
                {'email': 'user1@example.com', 'username': 'user1'},
                {'email': 'user2@example.com', 'username': 'user2'},
            ])
        """
        instances = [self.model_class(**item) for item in items]
        self.session.add_all(instances)
        self.session.flush()
        return instances

    def get_or_create(self, defaults: dict = None, **kwargs) -> tuple[T, bool]:
        """
        Get existing model or create if not found.

        Args:
            defaults: Default values for creation (only used if creating)
            **kwargs: Filter criteria

        Returns:
            Tuple of (model_instance, created: bool)

        Example:
            user, created = user_repo.get_or_create(
                defaults={'name': 'Test'},
                email='test@example.com'
            )
        """
        instance = self.get_by_field(
            list(kwargs.keys())[0],
            list(kwargs.values())[0]
        )

        if instance:
            return instance, False

        create_data = {**kwargs, **(defaults or {})}
        instance = self.create(**create_data)
        return instance, True

    def commit(self) -> None:
        """
        Commit changes to database.

        Call this after all create/update/delete operations are complete.
        """
        self.session.commit()

    def rollback(self) -> None:
        """
        Rollback all pending changes.
        """
        self.session.rollback()

    def refresh(self, instance: T) -> None:
        """
        Refresh model instance with fresh data from database.

        Args:
            instance: Model instance to refresh
        """
        self.session.refresh(instance)
