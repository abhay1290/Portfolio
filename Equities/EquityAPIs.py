from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated

from Equities.Equity import Equity
from Equities.equity_schema import EquityCreate, EquityResponse
from Database.database import  SessionLocal
from sqlalchemy.orm import Session

equity_router = APIRouter()

# Dependency for session injection
def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Create a new ca
@equity_router.post("/equities/", response_model=EquityResponse)
async def create_equity(equity: EquityCreate, db: db_dependency):
    db_equity = Equity(**equity.model_dump())
    db.add(db_equity)
    db.commit()
    db.refresh(db_equity)
    return EquityResponse.from_orm(db_equity)


# Read all equities
@equity_router.get("/equities/", response_model=List[EquityResponse])
async def read_equities(db: db_dependency):
    equities = db.query(Equity).all()
    return [EquityResponse.from_orm(equity) for equity in equities]


# Read a specific ca by ID
@equity_router.get("/equities/{equity_id}", response_model=EquityResponse)
async def read_equity(equity_id: int, db: db_dependency):
    equity =  db.query(Equity).filter_by(id=equity_id).first()
    if not equity:
        raise HTTPException(status_code=404, detail="Equity not found.")
    return EquityResponse.from_orm(equity)


# Update an ca by ID
@equity_router.put("/equities/{equity_id}", response_model=EquityResponse)
async def update_equity(equity_id: int, updated_equity: EquityCreate, db: db_dependency):
    equity = db.query(Equity).filter_by(id=equity_id).first()
    if not equity:
        raise HTTPException(status_code=404, detail="Equity not found.")

    for key, value in updated_equity.model_dump().items():
        setattr(equity, key, value)

    db.commit()
    db.refresh(equity)
    return EquityResponse.from_orm(equity)


# Delete an ca by ID
@equity_router.delete("/equities/{equity_id}")
async def delete_equity(equity_id: int, db: db_dependency):
    equity = db.query(Equity).filter_by(id=equity_id).first()
    if not equity:
        raise HTTPException(status_code=404, detail="Equity not found.")

    db.delete(equity)
    db.commit()

    return {"detail": "Equity deleted successfully"}
