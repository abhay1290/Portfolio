import logging
from typing import Annotated, Dict, Generic, List, Optional, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fixed_income.src.celery.tasks.analytics import compute_bond_analytics
from fixed_income.src.database.session import get_db
from fixed_income.src.model.bonds.BondBase import BondBase

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)

logger.debug(f"ModelType: {ModelType}")
logger.debug(f"CreateSchemaType: {CreateSchemaType}")
logger.debug(f"ResponseSchemaType: {ResponseSchemaType}")

db_dependency = Annotated[Session, Depends(get_db)]


def _get_model_fields(model_class) -> List[str]:
    """Get all column names from a SQLAlchemy model"""
    return [column.name for column in inspect(model_class).columns]


class BondGenericRouter(Generic[ModelType, CreateSchemaType, ResponseSchemaType]):
    def __init__(
            self,
            bond_base_model: Type[BondBase],
            model: Type[ModelType],
            create_schema: Type[CreateSchemaType],
            response_schema: Type[ResponseSchemaType],
            base_path: Optional[str] = None,
            tags: Optional[List[str]] = None,
    ):
        self.bond_base_model = bond_base_model
        self.model = model
        self.create_schema = create_schema
        self.response_schema = response_schema
        self.router = APIRouter()
        self.base_path = base_path or f"{model.__name__.lower()}s"
        self.tags = tags or [self.model.__name__]
        self.pk_name, self.pk_type = self._get_primary_key_info()

        # Get common fields from BondBase and specific fields from the model
        self.bond_base_fields = _get_model_fields(self.bond_base_model)
        self.specific_fields = self._get_specific_fields()

        async def create_item_endpoint(db: db_dependency, item: create_schema):
            return await self.create_item(db, item)

        # Define routes
        self.router.post(
            f"/{self.base_path}/",
            response_model=self.response_schema,
            status_code=status.HTTP_201_CREATED,
            tags=self.tags,
        )(create_item_endpoint)

        self.router.get(
            f"/{self.base_path}/",
            response_model=List[self.response_schema],
            status_code=status.HTTP_200_OK,
            tags=self.tags,
        )(self.read_items)

        self.router.get(
            f"/{self.base_path}/{{item_id}}",
            response_model=self.response_schema,
            status_code=status.HTTP_200_OK,
            tags=self.tags,
        )(self.read_item)

        self.router.get(
            f"/{self.base_path}/by-{{column_name}}/{{value}}",
            response_model=List[self.response_schema],
            status_code=status.HTTP_200_OK,
            tags=self.tags,
        )(self.read_by_column)

        async def update_item_endpoint(item_id: str, updated_item: create_schema, db: db_dependency):
            return await self.update_item(item_id, updated_item, db)

        self.router.put(
            f"/{self.base_path}/{{item_id}}",
            response_model=self.response_schema,
            status_code=status.HTTP_200_OK,
            tags=self.tags,
        )(update_item_endpoint)

        async def partial_update_item_endpoint(item_id: str, updated_item: create_schema, db: db_dependency):
            return await self.partial_update_item(item_id, updated_item, db)

        self.router.patch(
            f"/{self.base_path}/{{item_id}}",
            response_model=self.response_schema,
            status_code=status.HTTP_200_OK,
            tags=self.tags,
        )(partial_update_item_endpoint)

        self.router.delete(
            f"/{self.base_path}/{{item_id}}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=self.tags,
        )(self.delete_item)

    def _get_specific_fields(self) -> List[str]:
        """Get fields that are specific to the bond type (not in BondBase)"""
        model_fields = _get_model_fields(self.model)
        return [field for field in model_fields if field not in self.bond_base_fields]

    def _get_primary_key_info(self):
        inspector = inspect(self.model)
        pk_columns = inspector.primary_key
        if not pk_columns:
            raise ValueError(f"Model {self.model.__name__} has no primary key.")
        if len(pk_columns) > 1:
            raise ValueError(f"Composite primary keys are not supported in {self.model.__name__}.")
        pk_column = pk_columns[0]
        return pk_column.name, pk_column.type.python_type

    def _parse_item_id(self, item_id):
        try:
            return self.pk_type(item_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ID format. Expected {self.pk_type.__name__}."
            )

    def _separate_fields(self, data: Dict) -> (Dict, Dict):
        """Separate fields into BondBase fields and specific bond type fields"""
        bond_base_data = {}
        specific_data = {}

        for key, value in data.items():
            if key in self.bond_base_fields:
                bond_base_data[key] = value
            else:
                specific_data[key] = value

        return bond_base_data, specific_data

    async def create_item(self, db: db_dependency, item: CreateSchemaType):
        try:
            # Extract all data from the request model
            item_data = item.model_dump(mode="json", exclude_unset=True)

            # Create a new instance of the specific bond model
            db_item = self.model()

            # Separate and set base fields and specific fields
            bond_base_data, specific_data = self._separate_fields(item_data)

            # Set BondBase fields
            for key, value in bond_base_data.items():
                setattr(db_item, key, value)

            # Set bond-type specific fields
            for key, value in specific_data.items():
                setattr(db_item, key, value)

            db.add(db_item)
            db.commit()
            db.refresh(db_item)

            # Computes analytics on creation
            compute_bond_analytics.delay(db_item.id, db_item.bond_type)  # Async trigger

            return self.response_schema.model_validate(db_item)
        except IntegrityError as e:
            db.rollback()
            logger.error(f"IntegrityError: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item violates database constraints.",
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while creating the item: {str(e)}",
            )

    async def read_items(
            self,
            db: db_dependency,
            skip: int = 0,
            limit: int = 100,
    ):
        items = db.query(self.model).offset(skip).limit(limit).all()
        return [self.response_schema.model_validate(item, from_attributes=True) for item in items]

    async def read_item(self, item_id: str, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found.",
            )
        return self.response_schema.model_validate(item, from_attributes=True)

    async def read_by_column(
            self,
            column_name: str,
            value: str,
            db: db_dependency,
            skip: int = 0,
            limit: int = 100,
    ):
        model_columns = {column.name: column for column in inspect(self.model).columns}
        if column_name not in model_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{column_name}' does not exist in {self.model.__name__}.",
            )

        column = model_columns[column_name]
        col_type = column.type.python_type
        try:
            parsed_value = col_type(value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value format for column '{column_name}'.",
            )

        items = (
            db.query(self.model)
            .filter(getattr(self.model, column_name) == parsed_value)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self.response_schema.model_validate(item, from_attributes=True) for item in items]

    async def update_item(self, item_id: str, updated_item: CreateSchemaType, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found.",
            )
        try:
            # Extract all data from the request model
            item_data = updated_item.model_dump(mode="json")

            # Separate and update base fields and specific fields
            bond_base_data, specific_data = self._separate_fields(item_data)

            # Update BondBase fields
            for key, value in bond_base_data.items():
                setattr(item, key, value)

            # Update bond-type specific fields
            for key, value in specific_data.items():
                setattr(item, key, value)

            db.commit()
            db.refresh(item)

            # Computes analytics on update
            compute_bond_analytics.delay(item.id, item.bond_type)  # Async trigger

        except Exception as e:
            db.rollback()
            logging.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update item: {str(e)}",
            )
        return self.response_schema.model_validate(item)

    async def partial_update_item(self, item_id: str, updated_item: CreateSchemaType, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found.",
            )
        try:
            # Extract data from the request model (only fields that were set)
            update_data = updated_item.model_dump(mode="json", exclude_unset=True, exclude_defaults=True)

            # Separate and update base fields and specific fields
            bond_base_data, specific_data = self._separate_fields(update_data)

            # Update BondBase fields
            for key, value in bond_base_data.items():
                setattr(item, key, value)

            # Update bond-type specific fields
            for key, value in specific_data.items():
                setattr(item, key, value)

            db.commit()
            db.refresh(item)

            # Computes analytics on update
            compute_bond_analytics.delay(item.id, item.bond_type)  # Async trigger

        except Exception as e:
            db.rollback()
            logging.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update item: {str(e)}")
        return self.response_schema.model_validate(item)

    async def delete_item(self, item_id: str, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found.",
            )
        try:
            db.delete(item)
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not delete item.",
            )
        return None
