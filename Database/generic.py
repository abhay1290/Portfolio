from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Type, TypeVar, Optional, List


from Database.database2 import Base

# Define a type variable for ORM models
T = TypeVar("T", bound=Base)


class DatabaseManager:
    def __init__(self, db_url: str = DATABASE_URL):
        self.engine = create_engine(db_url, echo=True)
        Base.metadata.create_all(self.engine)  # Create tables if they don't exist
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
            raise
        finally:
            session.close()

    def add(self, obj: T):
        """Add a new record to the database."""
        with self.session_scope() as session:
            session.add(obj)

    def get_by_id(self, model: Type[T], record_id: int) -> Optional[T]:
        """Retrieve a record by its primary key ID."""
        with self.session_scope() as session:
            return session.query(model).filter_by(id=record_id).first()

    def get_all(self, model: Type[T]) -> List[T]:
        """Retrieve all records of a given model."""
        with self.session_scope() as session:
            return session.query(model).all()

    def update(self, model: Type[T], record_id: int, **kwargs):
        """Update a record by its primary key ID."""
        with self.session_scope() as session:
            record = session.query(model).filter_by(id=record_id).first()
            if record:
                for key, value in kwargs.items():
                    if hasattr(record, key):
                        setattr(record, key, value)

    def delete(self, model: Type[T], record_id: int):
        """Delete a record by its primary key ID."""
        with self.session_scope() as session:
            record = session.query(model).filter_by(id=record_id).first()
            if record:
                session.delete(record)
