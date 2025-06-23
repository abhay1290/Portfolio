# fixed_income_service/models/bond_identifier_history.py
from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from Identifier_management.model.abs_identifier_history import AbstractIdentifierHistory
from fixed_income.src.database import Base


class BondIdentifierHistory(Base, AbstractIdentifierHistory):
    """Bond-specific identifier history"""

    __tablename__ = 'bond_identifier_history'
    __table_args__ = (
        Index('idx_bond_hist_bond_type', 'bond_id', 'identifier_type'),
        Index('idx_bond_hist_value', 'identifier_value'),
        Index('idx_bond_hist_effective', 'effective_from', 'effective_to'),
        Index('idx_bond_hist_status', 'status'),
        Index('idx_bond_hist_version', 'bond_id', 'identifier_type', 'version'),
        Index('idx_bond_hist_rating', 'rating_agency'),
    )

    bond_id = Column(Integer, ForeignKey('bond.id'), nullable=False)

    # Bond-specific fields
    rating_agency = Column(String(50), nullable=True)  # For rating identifiers
    maturity_bucket = Column(String(20), nullable=True)  # Short, Medium, Long term
    is_callable = Column(Boolean, nullable=True)  # For callable bonds

    # Relationship
    bond = relationship("Bond", back_populates="identifier_history")
    supersedes = relationship("BondIdentifierHistory", remote_side=[AbstractIdentifierHistory.id])

    def get_entity_id(self) -> int:
        return self.bond_id
