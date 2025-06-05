from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, validates

from equity.src.database import Base
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.enums.PriorityEnum import PriorityEnum
from equity.src.model.corporate_actions.enums.ProcessingModeEnum import ProcessingModeEnum
from equity.src.model.corporate_actions.enums.StatusEnum import StatusEnum
from equity.src.model.enums.CurrencyEnum import CurrencyEnum
from equity.src.utils.Exceptions import CorporateActionValidationError


class CorporateActionBase(Base):
    __tablename__ = 'corporate_action'
    __mapper_args__ = {
        'polymorphic_on': 'action_type',  # Uses the action_type column to determine subclass
        'polymorphic_identity': 'base'  # Default identity (unused if all actions have subtypes)
    }
    __table_args__ = (
        Index('idx_ca_equity_status', 'equity_id', 'status'),
        Index('idx_ca_execution_date', 'execution_date'),
        Index('idx_ca_record_date', 'record_date'),
        Index('idx_ca_action_type', 'action_type'),
        Index('idx_ca_priority_status', 'priority', 'status'),
        Index('idx_ca_created_at', 'created_at'),
    )

    # Primary identifiers - absolutely mandatory for all corporate actions
    id = Column(Integer, primary_key=True, autoincrement=True)
    equity_id = Column(Integer, ForeignKey('equity.id', ondelete='CASCADE'), nullable=False)

    # Timestamps - all records need these
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Core action details - minimal required to identify any corporate action
    action_type = Column(Enum(CorporateActionTypeEnum), nullable=False)
    currency = Column(Enum(CurrencyEnum), nullable=False)

    # Status and processing - needed for workflow management
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.PENDING)
    priority = Column(Enum(PriorityEnum), nullable=False, default=PriorityEnum.NORMAL)
    processing_mode = Column(Enum(ProcessingModeEnum), nullable=False, default=ProcessingModeEnum.AUTOMATIC)

    # Key dates - minimal set that applies to all corporate actions
    record_date = Column(Date, nullable=False)
    execution_date = Column(Date, nullable=False)

    # Flags - basic flags that apply to all actions
    is_mandatory = Column(Boolean, nullable=False, default=True)
    is_taxable = Column(Boolean, nullable=False, default=False)

    # Processing metadata
    external_id = Column(String(100), nullable=True, unique=True)
    source_system = Column(String(50), nullable=True)
    processing_notes = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Celery task tracking
    celery_task_id = Column(String(100), nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Error handling
    last_error = Column(JSONB, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)

    # Relationships
    equity = relationship("Equity", back_populates="corporate_action")

    @validates('execution_date', 'record_date')
    def validate_dates(self, key, date_value):
        if date_value is None:
            raise CorporateActionValidationError(f"{key} cannot be None")
        return date_value

    @validates('retry_count', 'max_retries', 'error_count')
    def validate_non_negative_integers(self, key, value):
        if value is not None and value < 0:
            raise CorporateActionValidationError(f"{key} cannot be negative")
        return value

    @hybrid_property
    def can_retry(self):
        """Check if action can be retried"""
        return self.retry_count < self.max_retries and self.status in [StatusEnum.FAILED, StatusEnum.PENDING]

    @hybrid_property
    def is_overdue(self):
        """Check if action is overdue for processing"""
        from datetime import date
        return self.execution_date < date.today() and self.status == StatusEnum.PENDING

    def mark_processing(self, celery_task_id: str = None):
        """Mark corporate action as being processed"""
        self.status = StatusEnum.PROCESSING
        self.processing_started_at = func.now()
        if celery_task_id:
            self.celery_task_id = celery_task_id

    def mark_completed(self):
        """Mark corporate action as completed"""
        self.status = StatusEnum.CLOSED
        self.processing_completed_at = func.now()

    def mark_failed(self, error_details: dict = None):
        """Mark corporate action as failed"""
        self.status = StatusEnum.FAILED
        self.retry_count += 1
        self.error_count += 1
        if error_details:
            self.last_error = error_details

    def reset_for_retry(self):
        """Reset action for retry"""
        if self.can_retry:
            self.status = StatusEnum.PENDING
            self.celery_task_id = None
            self.processing_started_at = None
            self.processing_completed_at = None

    def __repr__(self):
        return f"<CorporateActionBase(id={self.id}, type='{self.action_type}', status='{self.status}')>"
