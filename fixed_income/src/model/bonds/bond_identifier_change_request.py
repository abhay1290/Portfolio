# fixed_income_service/models/bond_identifier_change_request.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from Identifier_management.model.abs_change_request import AbstractChangeRequest
from fixed_income.src.database import Base


class BondIdentifierChangeRequest(Base, AbstractChangeRequest):
    """Bond-specific change request"""

    __tablename__ = 'bond_identifier_change_requests'

    bond_id = Column(Integer, ForeignKey('bond.id'), nullable=False)

    # Bond-specific fields
    requires_rating_review = Column(Boolean, default=False)  # For rating-related changes

    # Relationship
    bond = relationship("Bond")

    def get_entity_id(self) -> int:
        return self.bond_id
