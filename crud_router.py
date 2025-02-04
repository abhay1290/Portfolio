from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Type, TypeVar, Generic, Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from uuid import UUID

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
    def __init__(self, model: Type[ModelType], create_schema: Type[CreateSchemaType],
                 response_schema: Type[ResponseSchemaType], base_path: str = None,
                 tags: List[str] = None):
        self.model = model
        self.create_schema = create_schema
        self.response_schema = response_schema
        self.router = APIRouter()
        self.base_path = base_path or model.__name__.lower()
        self.tags = tags or [self.model.__name__]
        self.pk_name, self.pk_type = self._get_primary_key_info()

        # Define routes
        self.router.post(f"/{self.base_path}/",
                         response_model=response_schema,
                         status_code=status.HTTP_201_CREATED,
                         tags=self.tags)(self.create_item)

        self.router.get(f"/{self.base_path}/",
                        response_model=List[response_schema],
                        tags=self.tags)(self.read_items)

        self.router.get(f"/{self.base_path}/{{item_id}}",
                        response_model=response_schema,
                        tags=self.tags)(self.read_item)

        self.router.get(f"/{self.base_path}/by-{{fk_name}}/{{fk_value}}",
                        response_model=List[response_schema],
                        tags=self.tags)(self.read_by_foreign_key)

        self.router.put(f"/{self.base_path}/{{item_id}}",
                        response_model=response_schema,
                        tags=self.tags)(self.update_item)

        self.router.delete(f"/{self.base_path}/{{item_id}}",
                           tags=self.tags)(self.delete_item)

    def _get_primary_key_info(self):
        inspector = inspect(self.model)
        pk_columns = inspector.primary_key
        if not pk_columns:
            raise ValueError(f"Model {self.model.__name__} has no primary key.")
        if len(pk_columns) > 1:
            raise ValueError(f"Model {self.model.__name__} has a composite primary key, which is not supported.")
        pk_column = pk_columns[0]
        return pk_column.name, pk_column.type.python_type

    def _parse_item_id(self, item_id: str):
        try:
            return UUID(item_id) if self.pk_type == UUID else self.pk_type(item_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid ID format for {self.pk_type.__name__}.")

    async def create_item(self, item: CreateSchemaType, db: db_dependency):
        db_item = self.model(**item.model_dump())
        db.add(db_item)
        try:
            db.commit()
            db.refresh(db_item)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        return self.response_schema.model_validate(db_item)

    async def read_items(self, db: db_dependency):
        return [self.response_schema.model_validate(item) for item in db.query(self.model).all()]

    async def read_item(self, item_id: str, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")
        return self.response_schema.model_validate(item)

    async def read_by_foreign_key(self, fk_name: str, fk_value: str, db: db_dependency):
        model_columns = {column.name: column for column in inspect(self.model).columns}
        if fk_name not in model_columns:
            raise HTTPException(status_code=400,
                                detail=f"Foreign key '{fk_name}' does not exist in {self.model.__name__}.")

        fk_column = model_columns[fk_name]
        fk_type = fk_column.type.python_type
        try:
            fk_value = UUID(fk_value) if fk_type == UUID else fk_type(fk_value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid foreign key format for {fk_name}.")

        items = db.query(self.model).filter(fk_column == fk_value).all()
        return [self.response_schema.model_validate(item) for item in items]

    async def update_item(self, item_id: str, updated_item: CreateSchemaType, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")
        for key, value in updated_item.model_dump().items():
            setattr(item, key, value)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        db.refresh(item)
        return self.response_schema.model_validate(item)

    async def delete_item(self, item_id: str, db: db_dependency):
        parsed_id = self._parse_item_id(item_id)
        item = db.query(self.model).filter(getattr(self.model, self.pk_name) == parsed_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")
        db.delete(item)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        return {"detail": f"{self.model.__name__} deleted successfully"}
