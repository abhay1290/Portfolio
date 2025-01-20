from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Database:
    def __init__(self, db_url: str, echo: bool = False):
        """
        Initialize the database connection.

        :param db_url: Database connection URL (e.g., 'sqlite:///example.db').
        :param echo: If True, SQLAlchemy will log SQL statements.
        """
        self.engine = create_engine(db_url, echo=echo)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """
        Create all tables defined with SQLAlchemy models.
        """
        print(f"Registered tables: {Base.metadata.tables.keys()}")
        Base.metadata.create_all(bind=self.engine)
        print("Tables created successfully.")

    def drop_tables(self):
        """
        Drop all tables defined with SQLAlchemy models.
        """
        Base.metadata.drop_all(self.engine)
        print("Tables dropped successfully.")

    def get_session(self):
        """
        Create and return a new database session.

        :return: SQLAlchemy session object.
        """
        return self.Session()
