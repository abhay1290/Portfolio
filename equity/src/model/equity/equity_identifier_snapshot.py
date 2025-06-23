from sqlalchemy import Column, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship

from Identifier_management.model.abs_identifier_snapshot import AbstractIdentifierSnapshot
from equity.src.database import Base


class EquityIdentifierSnapshot(Base, AbstractIdentifierSnapshot):
    """Equity-specific identifier snapshot"""

    __tablename__ = 'equity_identifier_snapshot'
    __table_args__ = (
        Index('idx_equity_snapshot_identifiers', 'identifiers'),
        Index('idx_equity_snapshot_primary', 'primary_identifier_type', 'primary_identifier_value'),
    )

    equity_id = Column(Integer, ForeignKey('equity.id'), primary_key=True)

    # Relationship
    equity = relationship("Equity", back_populates="current_identifiers", uselist=False)

    def get_entity_id(self) -> int:
        return self.equity_id
