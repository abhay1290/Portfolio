from sqlalchemy import Column, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship

from Identifier_management.model.abs_identifier_history import AbstractIdentifierHistory
from equity.src.database import Base


class EquityIdentifierHistory(Base, AbstractIdentifierHistory):
    """Equity-specific identifier history"""

    __tablename__ = 'equity_identifier_history'
    __table_args__ = (
        Index('idx_equity_hist_equity_type', 'equity_id', 'identifier_type'),
        Index('idx_equity_hist_value', 'identifier_value'),
        Index('idx_equity_hist_effective', 'effective_from', 'effective_to'),
        Index('idx_equity_hist_status', 'status'),
        Index('idx_equity_hist_version', 'equity_id', 'identifier_type', 'version'),
    )

    equity_id = Column(Integer, ForeignKey('equity.id'), nullable=False)

    # Relationship
    equity = relationship("Equity", back_populates="identifier_history")
    supersedes = relationship("EquityIdentifierHistory", remote_side=[AbstractIdentifierHistory.id])

    def get_entity_id(self) -> int:
        return self.equity_id
