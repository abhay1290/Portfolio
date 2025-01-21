from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated



from Portfolios.Portfolio import Portfolio
from Portfolios.portfolio_schema import PortfolioCreate, PortfolioResponse
from Database.database import  SessionLocal
from sqlalchemy.orm import Session

router = APIRouter()

# Dependency for session injection
def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Create a new portfolio
@router.post("/portfolios/", response_model=PortfolioResponse)
async def create_portfolio(portfolio: PortfolioCreate, db: db_dependency):
    db_portfolio = Portfolio(**portfolio.model_dump())
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return PortfolioResponse.from_orm(db_portfolio)


# Read all portfolios
@router.get("/portfolios/", response_model=List[PortfolioResponse])
async def read_portfolios(db: db_dependency):
    portfolios = db.query(Portfolio).all()
    return [PortfolioResponse.from_orm(portfolio) for portfolio in portfolios]


# Read a specific portfolio by ID
@router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def read_portfolio(portfolio_id: int, db: db_dependency):
    portfolio =  db.query(Portfolio).filter_by(id=portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found.")
    return PortfolioResponse.from_orm(portfolio)


# Update a portfolio by ID
@router.put("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(portfolio_id: int, updated_portfolio: PortfolioCreate, db: db_dependency):
    portfolio = db.query(Portfolio).filter_by(id=portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    for key, value in updated_portfolio.model_dump().items():
        setattr(portfolio, key, value)

    db.commit()
    db.refresh(portfolio)
    return PortfolioResponse.from_orm(portfolio)


# Delete a portfolio by ID
@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: int, db: db_dependency):
    portfolio = db.query(Portfolio).filter_by(id=portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    db.delete(portfolio)
    db.commit()

    return {"detail": "Portfolio deleted successfully"}
