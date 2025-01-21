from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated

from CorporateActions.CorporateAction import CorporateAction
from CorporateActions.corporate_action_schema import CorporateActionCreate, CorporateActionResponse
from Database.database import  SessionLocal
from sqlalchemy.orm import Session

ca_router = APIRouter()

# Dependency for session injection
def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Create a new ca
@ca_router.post("/corporate_action/", response_model=CorporateActionResponse)
async def create_ca(ca: CorporateActionCreate, db: db_dependency):
    db_ca = CorporateAction(**ca.model_dump())
    db.add(db_ca)
    db.commit()
    db.refresh(db_ca)
    return CorporateActionResponse.from_orm(db_ca)


# Read all cas
@ca_router.get("/corporate_actions/", response_model=List[CorporateActionResponse])
async def read_cas(db: db_dependency):
    cas = db.query(CorporateAction).all()
    return [CorporateActionResponse.from_orm(ca) for ca in cas]


# Read a specific ca by ID
@ca_router.get("/corporate_actions/{ca_id}", response_model=CorporateActionResponse)
async def read_ca(ca_id: int, db: db_dependency):
    ca =  db.query(CorporateAction).filter_by(id=ca_id).first()
    if not ca:
        raise HTTPException(status_code=404, detail="CorporateAction not found.")
    return CorporateActionResponse.from_orm(ca)


# Update a ca by ID
@ca_router.put("/corporate_actions/{ca_id}", response_model=CorporateActionResponse)
async def update_ca(ca_id: int, updated_ca: CorporateActionCreate, db: db_dependency):
    ca = db.query(CorporateAction).filter_by(id=ca_id).first()
    if not ca:
        raise HTTPException(status_code=404, detail="CorporateAction not found.")

    for key, value in updated_ca.model_dump().items():
        setattr(ca, key, value)

    db.commit()
    db.refresh(ca)
    return CorporateActionResponse.from_orm(ca)


# Delete a ca by ID
@ca_router.delete("/corporate_actions/{ca_id}")
async def delete_ca(ca_id: int, db: db_dependency):
    ca = db.query(CorporateAction).filter_by(id=ca_id).first()
    if not ca:
        raise HTTPException(status_code=404, detail="CorporateAction not found.")

    db.delete(ca)
    db.commit()

    return {"detail": "CorporateAction deleted successfully"}
