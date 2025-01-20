# from CorporateActions.Definitions.CashDividend import CashDividend
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from contextlib import contextmanager
#
# Base = declarative_base()
# DATABASE_URL = "postgresql+psycopg2://postgres:HippO1290@localhost:4200/postgres"
#
#
# class CashDividendDatabase:
#     def __init__(self, db_url=DATABASE_URL):
#         self.engine = create_engine(db_url, echo=True)
#         Base.metadata.create_all(self.engine)
#         self.Session = sessionmaker(bind=self.engine)
#
#     @contextmanager
#     def session_scope(self):
#         session = self.Session()
#         try:
#             yield session
#             session.commit()
#         except Exception as e:
#             session.rollback()
#             print(f"An error occurred: {e}")
#             raise
#         finally:
#             session.close()
#
#     def add_dividend(self, dividend: CashDividend):
#         with self.session_scope() as session:
#             session.add(dividend)
#
#     def get_dividend_by_id(self, dividend_id):
#         with self.session_scope() as session:
#             return session.query(CashDividend).filter_by(id=dividend_id).first()
#
#     def update_dividend(self, dividend_id, **kwargs):
#         with self.session_scope() as session:
#             dividend = session.query(CashDividend).filter_by(id=dividend_id).first()
#             if dividend:
#                 for key, value in kwargs.items():
#                     if hasattr(dividend, key):
#                         setattr(dividend, key, value)
#
#     def delete_dividend(self, dividend_id):
#         with self.session_scope() as session:
#             dividend = session.query(CashDividend).filter_by(id=dividend_id).first()
#             if dividend:
#                 session.delete(dividend)
