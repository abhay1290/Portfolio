from enum import Enum


class StatusEnum(str, Enum):
    """Status values for corporate actions"""
    DRAFT = "DRAFT"  # Initial draft state
    PENDING = "PENDING"  # Pending execution
    PROCESSING = "PROCESSING"  # Currently being processed
    CLOSED = "CLOSED"  # Successfully completed
    FAILED = "FAILED"  # Processing failed
    CANCELLED = "CANCELLED"  # Action was cancelled
    EXPIRED = "EXPIRED"  # Action expired without execution
    ON_HOLD = "ON_HOLD"  # Processing on hold
