from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from portfolio.src.database import Base
from portfolio.src.model.enums.VersionOperationEnum import VersionOperationTypeEnum


class PortfolioVersion(Base):
    """Stores versioned portfolio states"""
    __tablename__ = 'portfolio_version'
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'version_id', name='uq_portfolio_version'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'), nullable=False)
    version_id = Column(Integer, nullable=False)

    # State data
    portfolio_state = Column(JSONB, nullable=False)  # Complete portfolio state
    constituents_state = Column(JSONB, nullable=False)  # All constituents state

    # Metadata
    operation_type = Column(Enum(VersionOperationTypeEnum), nullable=False)
    change_reason = Column(Text, nullable=True)
    approved_by = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

    # Hash for integrity checking
    state_hash = Column(String(64), nullable=False)

    # Previous version reference for change tracking
    previous_version_id = Column(Integer, ForeignKey('portfolio_version.id'), nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="versions", foreign_keys=[portfolio_id])
    previous_version = relationship("PortfolioVersion", remote_side=[id], foreign_keys=[previous_version_id])


@dataclass
class PortfolioStateSnapshot:
    """Complete state snapshot of a portfolio at a point in time"""
    portfolio_data: Dict[str, Any]
    constituents_data: List[Dict[str, Any]]
    timestamp: datetime
    version_id: int
    change_reason: Optional[str] = None
    operation_type: Optional[VersionOperationTypeEnum] = None
    approved_by: Optional[str] = None
    state_hash: Optional[str] = None
