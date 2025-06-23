import uuid
from abc import ABC, abstractmethod

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func


class AbstractIdentifierHistory(ABC):
    """Abstract base class for identifier history - to be inherited per service"""

    # Common fields that all services will have
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # entity_id will be defined in concrete classes (equity_id, bond_id, etc.)

    identifier_type = Column(String(50), nullable=False)
    identifier_value = Column(String(255), nullable=False)
    exchange_mic = Column(String(10), nullable=True)
    currency = Column(String(3), nullable=True)

    version = Column(Integer, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False)

    change_reason = Column(String(50), nullable=True)
    change_description = Column(Text, nullable=True)
    supersedes_id = Column(UUID(as_uuid=True), nullable=True)

    source = Column(String(100), nullable=True)
    confidence_level = Column(String(20), nullable=True, default="HIGH")
    validation_status = Column(String(20), nullable=True)
    validation_errors = Column(JSONB, nullable=True)

    created_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    metadata = Column(JSONB, nullable=True, default=dict)

    @abstractmethod
    def get_entity_id(self) -> int:
        """Return the entity ID (equity_id, bond_id, etc.)"""
        pass
