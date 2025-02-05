from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Type, TypeVar, Generic, Annotated, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from uuid import UUID
import logging

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


def get_db():
    from Database.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class GenericRouter(Generic[ModelType, CreateSchemaType, ResponseSchemaType]):
    def __init__(
        self,
        model: Type[ModelType],
        create_schema: Type[CreateSchemaType],
        response_schema: Type[ResponseSchemaType],
        base_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        self.model = model
        self.create_schema = create_schema
        self.response_schema = response_schema
        self.router = APIRouter()
        self.base_path = base_path or f"{model.__name__.lower()}s"
        self.tags = tags or [self.model.__name__]
        self.pk_name, self.pk_type = self._get_primary_key_info()

        # Define routes
        self.router.post(
            f"/{self.base_path}/",
            response_model=response_schema,
            status_code=status.HTTP_201_CREATED,
            tags=self.tags,
        )(self.create_item)

        self.router.get(
            f"/{self.base_path}/",
            response_model=List[response_schema],
            status_code=status.HTTP_200_OK,
            tags=self.tags,
        )(self.read_items)

        self.router.get(
            f"/{self.base_path}/{{item_id}}",
            response_model=response_schema,
            status_code=status.HTTP_200_OK,
            tags=self.tags,
        )(self.read_item)

        self.router.get(
            f"/{self.base_path}/by-{{column_name}}/{{value}}",
            response_model=List[response_schema],
            status_code=status.HTTP_200_OK,
            tags=self.tags,
        )(self.read_by_column)

        self.router.put(
            f"/{self.base_path}/{{item_id}}",
            response_model=response_schema,
            status_code=status.HTTP_200_OK,  # Changed from 201 to 200
            tags=self.tags,
        )(self.update_item)

        # self.router.patch(  # Added PATCH route for partial updates
        #     f"/{self.base_path}/{{item_id}}",
        #     response_model=response_schema,
        #     status_code=status.HTTP_200_OK,
        #     tags=self.tags,
        # )(self.partial_update_item)

        self.router.delete(
            f"/{self.base_path}/{{item_id}}",
            status_code=status.HTTP_204_NO_CONTENT,  # Changed to 204 No Content
            tags=self.tags,
        )(self.delete_item)

    def _get_primary_key_info(self):
        inspector = inspect(self.model)
        pk_columns = inspector.primary_key
        if not pk_columns:
            raise ValueError(f"Model {self.model.__name__} has no primary key.")
        if len(pk_columns) > 1:
            raise ValueError(f"Composite primary keys are not supported in {self.model.__name__}.")
        pk_column = pk_columns[0]
        return pk_column.name, pk_column.type.python_type

    def _parse_item_id(self, item_id: str):
        try:
            return UUID(item_id) if self.pk_type == UUID else self.pk_type(item_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ID format. Expected {self.pk_type.__name__}.",
            )

    async def create_item(self, item: CreateSchemaType, db: db_dependency):
        db_item = self.model(**item.model_dump(mode="json"))
        db.add(db_item)
        try:
            db.commit()
            db.refresh(db_item)
        except Exception as e:
            db.rollback()
            logging.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create item.",
            )
        return self.response_schema.model_validate(db_item)

    async def read_items(
        self,
        db: db_dependency,
        skip: int = 0,
        limit: int = 100,  # Added pagination
    ):
        items = db.query(self.model).offset(skip).limit(limit).all()
        return [self.response_schema.model_validate(item) for item in items]

    async def read_item(self, item_id: str, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found.",
            )
        return self.response_schema.model_validate(item)

    async def read_by_column(
        self,
        column_name: str,
        value: str,
        db: db_dependency,
        skip: int = 0,
        limit: int = 100,  # Added pagination
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
            parsed_value = UUID(value) if col_type == UUID else col_type(value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value format for column '{column_name}'.",
            )

        items = (
            db.query(self.model)
            .filter(column == parsed_value)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self.response_schema.model_validate(item) for item in items]

    async def update_item(self, item_id: str, updated_item: CreateSchemaType, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found.",
            )
        try:
            for key, value in updated_item.model_dump(exclude_unset=True, mode="json").items():
                setattr(item, key, value)
            db.commit()
            db.refresh(item)
        except Exception as e:
            db.rollback()
            logging.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update item.",
            )
        return self.response_schema.model_validate(item)
    #
    # async def partial_update_item(  # New method for PATCH
    #     self, item_id: str, updated_item: CreateSchemaType, db: db_dependency
    # ):
    #     parsed_id = self._parse_item_id(item_id)
    #     item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
    #     if not item:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail=f"{self.model.__name__} not found.",
    #         )
    #     try:
    #         update_data = updated_item.model_dump(exclude_unset=True, mode="json")
    #         for key, value in update_data.items():
    #             setattr(item, key, value)
    #         db.commit()
    #         db.refresh(item)
    #     except Exception as e:
    #         db.rollback()
    #         logging.error(f"Database error: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Could not update item.",
    #         )
    #     return self.response_schema.model_validate(item)

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
        return None  # 204 No Content should have empty body