from fastapi import APIRouter, HTTPException, Depends
from typing import List, Type, TypeVar, Generic, Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Generic type variables
ModelType = TypeVar("ModelType")  # SQLAlchemy model
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)  # Pydantic Create Schema
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)  # Pydantic Response Schema

# Dependency for session injection
def get_db():
    from Database.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Generalized router class
class GenericRouter(Generic[ModelType, CreateSchemaType, ResponseSchemaType]):
    def __init__(self,
                 model: Type[ModelType],
                 create_schema: Type[CreateSchemaType],
                 response_schema: Type[ResponseSchemaType],
                 base_path: str = None,
                 tags: List[str] = None):
        self.model = model
        self.create_schema = create_schema
        self.response_schema = response_schema
        self.router = APIRouter()

        # Use custom base_path if provided, otherwise default to model name
        self.base_path = base_path or self.model.__name__.lower()
        self.tags = tags or [self.model.__name__]  # Default tag is the model name

        # Define routes
        self.router.post(
            f"/{self.base_path}/",
            response_model=response_schema,
            tags=self.tags
        )(self.create_item)
        self.router.get(
            f"/{self.base_path}s/",
            response_model=List[response_schema],
            tags=self.tags
        )(self.read_items)
        self.router.get(
            f"/{self.base_path}s/{{item_id}}",
            response_model=response_schema,
            tags=self.tags
        )(self.read_item)
        self.router.put(
            f"/{self.base_path}s/{{item_id}}",
            response_model=response_schema,
            tags=self.tags
        )(self.update_item)
        self.router.delete(
            f"/{self.base_path}s/{{item_id}}",
            tags=self.tags
        )(self.delete_item)

    async def create_item(self, item: CreateSchemaType, db: db_dependency):
        db_item = self.model(**item.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return self.response_schema.from_orm(db_item)

    async def read_items(self, db: db_dependency):
        items = db.query(self.model).all()
        return [self.response_schema.from_orm(item) for item in items]

    async def read_item(self, item_id: int, db: db_dependency):
        item = db.query(self.model).filter_by(id=item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")
        return self.response_schema.from_orm(item)

    async def update_item(self, item_id: int, updated_item: CreateSchemaType, db: db_dependency):
        item = db.query(self.model).filter_by(id=item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")
        for key, value in updated_item.dict().items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return self.response_schema.from_orm(item)

    async def delete_item(self, item_id: int, db: db_dependency):
        item = db.query(self.model).filter_by(id=item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")
        db.delete(item)
        db.commit()
        return {"detail": f"{self.model.__name__} deleted successfully"}

