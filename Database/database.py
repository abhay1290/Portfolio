# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import create_engine
#
# from typing import TypeVar
#
# Base = declarative_base()
#
# DATABASE_URL = "postgresql+psycopg2://postgres:HippO1290@localhost:4200/postgres"
#
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
# # Define a type variable for ORM models
# T = TypeVar("T", bound=Base)
#
