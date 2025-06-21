import logging
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import text

from equity.src.database import get_db

logger = logging.getLogger(__name__)

# Type variables for generic typing
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class DatabaseError(Exception):
    """Custom database operation error"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class EquityDatabaseService(Generic[ModelType, CreateSchemaType, ResponseSchemaType]):
    """
    Generic Database Service Layer

    Provides CRUD operations for any SQLAlchemy model with automatic
    response schema conversion and comprehensive error handling.
    """

    def __init__(
            self,
            model: Type[ModelType],
            create_schema: Type[CreateSchemaType],
            response_schema: Type[ResponseSchemaType],
            update_schema: Optional[Type[UpdateSchemaType]] = None
    ):
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema or create_schema
        self.response_schema = response_schema
        self.pk_name, self.pk_type = self._get_primary_key_info()
        self.db = get_db()

    def _get_primary_key_info(self) -> tuple[str, Type]:
        """Get primary key information from the model"""
        try:
            inspector = inspect(self.model)
            pk_columns = inspector.primary_key

            if not pk_columns:
                raise ValueError(f"Model {self.model.__name__} has no primary key.")

            if len(pk_columns) > 1:
                raise ValueError(f"Composite primary keys are not supported in {self.model.__name__}.")

            pk_column = pk_columns[0]
            return pk_column.name, pk_column.type.python_type

        except Exception as e:
            logger.error(f"Error getting primary key info for {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to analyze model {self.model.__name__}", e)

    def _parse_item_id(self, item_id: Union[str, int, Any]) -> Any:
        """Parse and validate item ID to the correct type"""
        try:
            return self.pk_type(item_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ID format. Expected {self.pk_type.__name__}, got {type(item_id).__name__}."
            )

    def _convert_to_response(self, db_item: ModelType) -> ResponseSchemaType:
        """Convert database model instance to response schema"""
        try:
            return self.response_schema.model_validate(db_item, from_attributes=True)
        except Exception as e:
            logger.error(f"Error converting {self.model.__name__} to response schema: {str(e)}")
            raise DatabaseError(f"Failed to convert {self.model.__name__} to response format", e)

    def _convert_to_response_list(self, db_items: List[ModelType]) -> List[ResponseSchemaType]:
        """Convert list of database model instances to response schemas"""
        try:
            return [self._convert_to_response(item) for item in db_items]
        except Exception as e:
            logger.error(f"Error converting {self.model.__name__} list to response schemas: {str(e)}")
            raise DatabaseError(f"Failed to convert {self.model.__name__} list to response format", e)

    # Core CRUD Operations

    async def create(self, item_data: CreateSchemaType) -> ResponseSchemaType:
        """
        Create a new item in the database

        Args:
            item_data: Data for creating the item

        Returns:
            Created item as response schema

        Raises:
            HTTPException: For validation errors or database constraints
            DatabaseError: For unexpected database errors
        """
        try:
            # Convert schema to model instance
            item_dict = item_data.model_dump(exclude_unset=True)
            db_item = self.model(**item_dict)

            # Add to database
            self.db.add(db_item)
            self.db.commit()
            self.db.refresh(db_item)

            logger.info(f"Created {self.model.__name__} with ID: {getattr(db_item, self.pk_name)}")
            return self._convert_to_response(db_item)

        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"Integrity constraint violation creating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{self.model.__name__} violates database constraints. Possible duplicate or invalid reference."
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error occurred while creating {self.model.__name__}"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to create {self.model.__name__}", e)

    async def update(
            self,
            item_id: Union[str, int],
            update_data: Union[UpdateSchemaType, CreateSchemaType]
    ) -> ResponseSchemaType:
        """
        Update an existing item

        Args:
            item_id: ID of the item to update
            update_data: Data to update the item with

        Returns:
            Updated item as response schema

        Raises:
            HTTPException: 404 if item not found, 400 for validation errors
        """
        try:
            parsed_id = self._parse_item_id(item_id)
            item = self.db.query(self.model).filter(
                getattr(self.model, self.pk_name) == parsed_id
            ).first()

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} with ID {item_id} not found"
                )

            # Update item attributes
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if hasattr(item, key):
                    setattr(item, key, value)

            # Update timestamp if model has updated_at field
            if hasattr(item, 'updated_at'):
                setattr(item, 'updated_at', datetime.now())

            self.db.commit()
            self.db.refresh(item)

            logger.info(f"Updated {self.model.__name__} with ID: {item_id}")
            return self._convert_to_response(item)

        except HTTPException:
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"Integrity constraint violation updating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Update violates database constraints"
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred during update"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to update {self.model.__name__}", e)

    async def partial_update(
            self,
            item_id: Union[str, int],
            update_data: Union[UpdateSchemaType, CreateSchemaType]
    ) -> ResponseSchemaType:
        """
        Partially update an existing item (only provided fields)

        Args:
            item_id: ID of the item to update
            update_data: Partial data to update the item with

        Returns:
            Updated item as response schema
        """
        try:
            parsed_id = self._parse_item_id(item_id)
            item = self.db.query(self.model).filter(
                getattr(self.model, self.pk_name) == parsed_id
            ).first()

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} with ID {item_id} not found"
                )

            # Update only provided fields
            update_dict = update_data.model_dump(exclude_unset=True, exclude_defaults=True)
            for key, value in update_dict.items():
                if hasattr(item, key):
                    setattr(item, key, value)

            # Update timestamp if model has updated_at field
            if hasattr(item, 'updated_at'):
                setattr(item, 'updated_at', datetime.now())

            self.db.commit()
            self.db.refresh(item)

            logger.info(f"Partially updated {self.model.__name__} with ID: {item_id}")
            return self._convert_to_response(item)

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error partially updating {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to partially update {self.model.__name__}", e)

    async def delete(self, item_id: Union[str, int]) -> bool:
        """
        Delete an item by ID

        Args:
            item_id: ID of the item to delete

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: 404 if item not found, 400 for constraint violations
        """
        try:
            parsed_id = self._parse_item_id(item_id)
            item = self.db.query(self.model).filter(
                getattr(self.model, self.pk_name) == parsed_id
            ).first()

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} with ID {item_id} not found"
                )

            self.db.delete(item)
            self.db.commit()

            logger.info(f"Deleted {self.model.__name__} with ID: {item_id}")
            return True

        except HTTPException:
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"Integrity constraint violation deleting {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete {self.model.__name__} due to foreign key constraints"
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred during deletion"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error deleting {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to delete {self.model.__name__}", e)

    async def get_by_id(self, item_id: int) -> Optional[ResponseSchemaType]:
        """
        Get item by ID

        Args:
            item_id: ID of the item to retrieve

        Returns:
            Item as response schema or None if not found
        """
        try:
            parsed_id = self._parse_item_id(item_id)
            item = self.db.query(self.model).filter(
                getattr(self.model, self.pk_name) == parsed_id
            ).first()

            return self._convert_to_response(item) if item else None

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by ID {item_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve {self.model.__name__}", e)

    async def get_all(
            self,
            order_by: Optional[str] = None,
            desc: bool = False
    ) -> List[ResponseSchemaType]:
        """
        Get all items with pagination and optional ordering

        Args:
            order_by: Column name to order by
            desc: Whether to order in descending order

        Returns:
            List of items as response schemas
        """
        try:
            query = self.db.query(self.model)

            # Apply ordering if specified
            if order_by:
                if hasattr(self.model, order_by):
                    order_column = getattr(self.model, order_by)
                    query = query.order_by(order_column.desc() if desc else order_column.asc())
                else:
                    logger.warning(f"Column {order_by} not found in {self.model.__name__}, skipping ordering")

            return self._convert_to_response_list(query)

        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve {self.model.__name__} list", e)

    async def get_by_column(
            self,
            column_name: str,
            value: Any
    ) -> List[ResponseSchemaType]:
        """
        Get items by column value

        Args:
            column_name: Name of the column to filter by
            value: Value to filter by

        Returns:
            List of items as response schemas
        """
        try:
            # Validate column exists
            model_columns = {column.name: column for column in inspect(self.model).columns}
            if column_name not in model_columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Column '{column_name}' does not exist in {self.model.__name__}"
                )

            # Parse value to correct type
            column = model_columns[column_name]
            col_type = column.type.python_type
            try:
                parsed_value = col_type(value)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid value format for column '{column_name}'. Expected {col_type.__name__}"
                )

            # Query items
            items = (
                self.db.query(self.model)
                .filter(getattr(self.model, column_name) == parsed_value)
                .all()
            )

            return self._convert_to_response_list(items)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by {column_name}={value}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve {self.model.__name__} by column", e)

    # Advanced Query Operations

    async def get_by_ids(self, item_ids: List[Union[str, int]]) -> List[ResponseSchemaType]:
        """
        Get multiple items by their IDs

        Args:
            item_ids: List of IDs to retrieve

        Returns:
            List of items as response schemas
        """
        try:
            parsed_ids = [self._parse_item_id(item_id) for item_id in item_ids]
            items = self.db.query(self.model).filter(
                getattr(self.model, self.pk_name).in_(parsed_ids)
            ).all()

            return self._convert_to_response_list(items)

        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by IDs: {str(e)}")
            raise DatabaseError(f"Failed to retrieve {self.model.__name__} by IDs", e)

    async def count(self, **filters) -> int:
        """
        Count items with optional filters

        Args:
            **filters: Column filters as keyword arguments

        Returns:
            Count of matching items
        """
        try:
            query = self.db.query(self.model)

            # Apply filters
            for column_name, value in filters.items():
                if hasattr(self.model, column_name):
                    query = query.filter(getattr(self.model, column_name) == value)

            return query.count()

        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to count {self.model.__name__}", e)

    async def exists(self, item_id: Union[str, int]) -> bool:
        """
        Check if an item exists by ID

        Args:
            item_id: ID to check

        Returns:
            True if item exists, False otherwise
        """
        try:
            parsed_id = self._parse_item_id(item_id)
            return self.db.query(self.model).filter(
                getattr(self.model, self.pk_name) == parsed_id
            ).first() is not None

        except Exception as e:
            logger.error(f"Error checking {self.model.__name__} existence: {str(e)}")
            return False

    async def bulk_create(self, items_data: List[CreateSchemaType]) -> List[ResponseSchemaType]:
        """
        Create multiple items in bulk

        Args:
            items_data: List of data for creating items

        Returns:
            List of created items as response schemas
        """
        try:
            db_items = []
            for item_data in items_data:
                item_dict = item_data.model_dump(exclude_unset=True)
                db_item = self.model(**item_dict)
                db_items.append(db_item)

            self.db.add_all(db_items)
            self.db.commit()

            # Refresh all items
            for db_item in db_items:
                self.db.refresh(db_item)

            logger.info(f"Bulk created {len(db_items)} {self.model.__name__} items")
            return self._convert_to_response_list(db_items)

        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"Integrity constraint violation in bulk create: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more items violate database constraints"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in bulk create {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to bulk create {self.model.__name__}", e)

    async def search(
            self,
            search_term: str,
            search_columns: List[str]
    ) -> List[ResponseSchemaType]:
        """
        Search items across multiple columns

        Args:
            search_term: Term to search for
            search_columns: List of column names to search in
        Returns:
            List of matching items as response schemas
        """
        try:
            from sqlalchemy import or_

            query = self.db.query(self.model)

            # Build search conditions
            search_conditions = []
            for column_name in search_columns:
                if hasattr(self.model, column_name):
                    column = getattr(self.model, column_name)
                    # Use ilike for case-insensitive search (PostgreSQL)
                    # Use like for other databases
                    try:
                        search_conditions.append(column.ilike(f"%{search_term}%"))
                    except AttributeError:
                        search_conditions.append(column.like(f"%{search_term}%"))

            if search_conditions:
                query = query.filter(or_(*search_conditions))

            return self._convert_to_response_list(query)

        except Exception as e:
            logger.error(f"Error searching {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to search {self.model.__name__}", e)

    # Raw SQL Support

    async def execute_raw_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute raw SQL query and return results

        Args:
            query: Raw SQL query
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        try:
            result = self.db.execute(text(query), params or {})
            return [dict(row) for row in result]

        except Exception as e:
            logger.error(f"Error executing raw query: {str(e)}")
            raise DatabaseError("Failed to execute raw query", e)
