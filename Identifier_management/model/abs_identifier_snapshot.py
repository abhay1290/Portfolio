from abc import ABC, abstractmethod

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func


class AbstractIdentifierSnapshot(ABC):
    """Abstract base class for identifier snapshots"""

    # entity_id will be primary key in concrete classes
    identifiers = Column(JSONB, nullable=False, default=dict)
    primary_identifier_type = Column(String(50), nullable=True)
    primary_identifier_value = Column(String(255), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    snapshot_version = Column(Integer, nullable=False, default=1)

    @abstractmethod
    def get_entity_id(self) -> int:
        """Return the entity ID"""
        pass
