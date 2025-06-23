from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from Identifier_management.model.abs_change_request import AbstractChangeRequest
from equity.src.database import Base


class EquityIdentifierChangeRequest(Base, AbstractChangeRequest):
    """Equity-specific change request"""

    __tablename__ = 'equity_identifier_change_requests'

    equity_id = Column(Integer, ForeignKey('equity.id'), nullable=False)

    # Relationship
    equity = relationship("Equity")

    def get_entity_id(self) -> int:
        return self.equity_id
