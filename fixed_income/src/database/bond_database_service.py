import logging
from datetime import datetime
from typing import Annotated, Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import inspect, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from fixed_income.src.celery.tasks.analytics import compute_bond_analytics
from fixed_income.src.database.session import get_db
from fixed_income.src.model.bonds.BondBase import BondBase

logger = logging.getLogger(__name__)

# Type variables for generic typing
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)

db_dependency = Annotated[Session, Depends(get_db)]


class DatabaseError(Exception):
    """Custom database operation error"""

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


def _get_model_fields(model_class) -> List[str]:
    """Get all column names from a SQLAlchemy model"""
    return [column.name for column in inspect(model_class).columns]


class BondDatabaseService(Generic[ModelType, CreateSchemaType, ResponseSchemaType]):
    """
    Generic Database Service for Bond Operations

    Provides comprehensive CRUD operations for any bond model with automatic
    response schema conversion, field separation for BondBase inheritance,
    and integrated analytics triggering.
    """

    def __init__(
            self,
            bond_base_model: Type[BondBase],
            model: Type[ModelType],
            create_schema: Type[CreateSchemaType],
            response_schema: Type[ResponseSchemaType],
            update_schema: Optional[Type[UpdateSchemaType]] = None,
            db: Optional[Session] = None
    ):
        self.bond_base_model = bond_base_model
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema or create_schema
        self.response_schema = response_schema
        self.pk_name, self.pk_type = self._get_primary_key_info()
        self.db = db or get_db()

        # Get common fields from BondBase and specific fields from the model
        self.bond_base_fields = _get_model_fields(self.bond_base_model)
        self.specific_fields = self._get_specific_fields()

    def _get_specific_fields(self) -> List[str]:
        """Get fields that are specific to the bond type (not in BondBase)"""
        model_fields = _get_model_fields(self.model)
        return [field for field in model_fields if field not in self.bond_base_fields]

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

    def _separate_fields(self, data: Dict) -> tuple[Dict, Dict]:
        """Separate fields into BondBase fields and specific bond type fields"""
        bond_base_data = {}
        specific_data = {}

        for key, value in data.items():
            if key in self.bond_base_fields:
                bond_base_data[key] = value
            else:
                specific_data[key] = value

        return bond_base_data, specific_data

    def _apply_field_updates(self, item, bond_base_data: Dict, specific_data: Dict):
        """Apply field updates to a model instance"""
        # Set BondBase fields
        for key, value in bond_base_data.items():
            setattr(item, key, value)

        # Set bond-type specific fields
        for key, value in specific_data.items():
            setattr(item, key, value)

    def _trigger_analytics(self, item):
        """Trigger analytics computation for a bond item"""
        if hasattr(item, 'id') and hasattr(item, 'bond_type'):
            compute_bond_analytics.delay(item.id, item.bond_type)

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
        Create a new bond item in the database

        Args:
            item_data: Data for creating the bond item

        Returns:
            Created item as response schema

        Raises:
            HTTPException: For validation errors or database constraints
            DatabaseError: For unexpected database errors
        """
        try:
            # Extract all data from the request model
            item_dict = item_data.model_dump(mode="json", exclude_unset=True)

            # Create a new instance of the specific bond model
            db_item = self.model()

            # Separate and set base fields and specific fields
            bond_base_data, specific_data = self._separate_fields(item_dict)
            self._apply_field_updates(db_item, bond_base_data, specific_data)

            # Add to database
            self.db.add(db_item)
            self.db.commit()
            self.db.refresh(db_item)

            # Trigger analytics computation
            # self._trigger_analytics(db_item)

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
        Update an existing bond item

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

            # Extract data from the request model
            update_dict = update_data.model_dump(mode="json")

            # Separate and update base fields and specific fields
            bond_base_data, specific_data = self._separate_fields(update_dict)
            self._apply_field_updates(item, bond_base_data, specific_data)

            # Update timestamp if model has updated_at field
            if hasattr(item, 'updated_at'):
                setattr(item, 'updated_at', datetime.now())

            self.db.commit()
            self.db.refresh(item)

            # Trigger analytics computation
            # self._trigger_analytics(item)

            logger.info(f"Updated {self.model.__name__} with ID: {item_id}")
            return self._convert_to_response(item)

        except HTTPException:
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"Integrity constraint violation updating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update violates database constraints"
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
        Partially update an existing bond item (only provided fields)

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

            # Extract data from the request model (only fields that were set)
            update_dict = update_data.model_dump(mode="json", exclude_unset=True, exclude_defaults=True)

            # Separate and update base fields and specific fields
            bond_base_data, specific_data = self._separate_fields(update_dict)
            self._apply_field_updates(item, bond_base_data, specific_data)

            # Update timestamp if model has updated_at field
            if hasattr(item, 'updated_at'):
                setattr(item, 'updated_at', datetime.now())

            self.db.commit()
            self.db.refresh(item)

            # Trigger analytics computation
            # self._trigger_analytics(item)

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
        Delete a bond item by ID

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

    async def get_by_id(self, item_id: Union[str, int]) -> Optional[ResponseSchemaType]:
        """
        Get bond item by ID

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
        Get all bond items with pagination and optional ordering

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
        Get bond items by column value

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
        Get multiple bond items by their IDs

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
        Count bond items with optional filters

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
        Check if a bond item exists by ID

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
        Create multiple bond items in bulk

        Args:
            items_data: List of data for creating items

        Returns:
            List of created items as response schemas
        """
        try:
            db_items = []
            for item_data in items_data:
                item_dict = item_data.model_dump(exclude_unset=True)

                # Create a new instance of the specific bond model
                db_item = self.model()

                # Separate and set base fields and specific fields
                bond_base_data, specific_data = self._separate_fields(item_dict)
                self._apply_field_updates(db_item, bond_base_data, specific_data)

                db_items.append(db_item)

            self.db.add_all(db_items)
            self.db.commit()

            # Refresh all items and trigger analytics
            for db_item in db_items:
                self.db.refresh(db_item)
                # self._trigger_analytics(db_item)

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
        Search bond items across multiple columns

        Args:
            search_term: Term to search for
            search_columns: List of column names to search in

        Returns:
            List of matching items as response schemas
        """
        try:
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
