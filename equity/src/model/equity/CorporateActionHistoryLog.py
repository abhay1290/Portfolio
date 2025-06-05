from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates

from equity.src.database import Base
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.utils.Exceptions import CorporateActionValidationError


class CorporateActionHistoryLog(Base):
    """Model for tracking changes to equities over time"""

    __tablename__ = 'corporate_action_history_log'
    __table_args__ = (
        Index('idx_ca_history_equity_date', 'equity_id', 'effective_date'),
        Index('idx_ca_history_executed_at', 'executed_at'),
        Index('idx_ca_history_action_type', 'action_type'),
        Index('idx_ca_history_rollback', 'is_rolled_back'),
        Index('idx_ca_history_action_id', 'action_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    equity_id = Column(Integer, ForeignKey('equity.id'), nullable=False)

    # Timestamp information
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    effective_date = Column(DateTime(timezone=True), nullable=False)

    # Corporate action details
    action_type = Column(Enum(CorporateActionTypeEnum), nullable=False)
    action_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)

    # State snapshots
    state_before = Column(JSONB, nullable=False)
    state_after = Column(JSONB, nullable=False)

    # Action-specific parameters # TODO is this needed ?
    action_parameters = Column(JSONB, nullable=True)

    # Rollback tracking
    is_rolled_back = Column(Boolean, default=False)
    rolled_back_at = Column(DateTime(timezone=True))
    rolled_back_by = Column(String(100))
    rollback_reason = Column(Text)

    # Additional metadata
    created_by = Column(String(100), nullable=True)  # User/system that created the action
    external_source = Column(String(100), nullable=True)  # Data provider, manual, etc.
    confidence_score = Column(Float, nullable=True)  # Data confidence (0.0 to 1.0)

    # Processing metadata
    processing_duration_ms = Column(Integer, nullable=True)
    error_details = Column(JSONB, nullable=True)

    # Relationships
    equity = relationship("Equity", back_populates="corporate_action_history_log")

    @validates('confidence_score')
    def validate_confidence_score(self, confidence_score):
        if confidence_score is not None and not (0.0 <= confidence_score <= 1.0):
            raise CorporateActionValidationError("Confidence score must be between 0.0 and 1.0")
        return confidence_score

    @validates('effective_date')
    def validate_effective_date(self, effective_date):
        if effective_date is None:
            raise CorporateActionValidationError("Effective date cannot be None")
        return effective_date

    def __repr__(self):
        return f"<CorporateActionHistoryLog(id={self.id}, equity_id={self.equity_id}, action_type='{self.action_type}')>"
