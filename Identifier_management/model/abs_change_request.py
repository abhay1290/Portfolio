import uuid
from abc import ABC, abstractmethod

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class AbstractChangeRequest(ABC):
    """Abstract base class for change requests"""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # entity_id will be defined in concrete classes

    identifier_type = Column(String(50), nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=False)
    change_reason = Column(String(50), nullable=False)
    change_description = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default="PENDING")
    requested_by = Column(String(100), nullable=False)
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    risk_level = Column(String(10), nullable=True)
    impact_assessment = Column(Text, nullable=True)

    @abstractmethod
    def get_entity_id(self) -> int:
        """Return the entity ID"""
        pass
