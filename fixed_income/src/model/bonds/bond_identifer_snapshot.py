# fixed_income_service/models/bond_identifier_snapshot.py
from sqlalchemy import Column, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship

from Identifier_management.model.abs_identifier_snapshot import AbstractIdentifierSnapshot
from fixed_income.src.database import Base


class BondIdentifierSnapshot(Base, AbstractIdentifierSnapshot):
    """Bond-specific identifier snapshot"""

    __tablename__ = 'bond_identifier_snapshot'
    __table_args__ = (
        Index('idx_bond_snapshot_identifiers', 'identifiers'),
        Index('idx_bond_snapshot_primary', 'primary_identifier_type', 'primary_identifier_value'),
    )

    bond_id = Column(Integer, ForeignKey('bond.id'), primary_key=True)

    # Relationship
    bond = relationship("Bond", back_populates="current_identifiers", uselist=False)

    def get_entity_id(self) -> int:
        return self.bond_id
