import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

from Identifier_management.enums.base_change_reason_enum import BaseChangeReasonEnum
from Identifier_management.managers.generic_identifer_operations_manager import GenericOperationsManager
from Identifier_management.managers.generic_identifier_version_manager import GenericVersionManager
from Identifier_management.managers.generic_identifier_workflow_manager import GenericWorkflowManager

# Generic types for flexibility
TIdentifierType = TypeVar('TIdentifierType', bound=Enum)
TSecurityEntity = TypeVar('TSecurityEntity')
TChangeReason = TypeVar('TChangeReason', bound=Enum)
TIdentifierStatus = TypeVar('TIdentifierStatus', bound=Enum)


class GenericIdentifierManager(Generic[TIdentifierType, TSecurityEntity, TChangeReason]):
    """Generic composite manager that coordinates all three specialized managers"""

    def __init__(self, session: Session, history_model, snapshot_model, change_request_model,
                 entity_model, identifier_enum_class, change_reason_enum_class=None):
        self.session = session
        self.identifier_enum_class = identifier_enum_class
        self.change_reason_enum_class = change_reason_enum_class or BaseChangeReasonEnum

        # Create the three specialized managers
        self.version_manager = GenericVersionManager(
            session, history_model, identifier_enum_class, change_reason_enum_class
        )
        self.workflow_manager = GenericWorkflowManager(
            session, change_request_model, self.version_manager,
            identifier_enum_class, change_reason_enum_class
        )
        self.operations_manager = GenericOperationsManager(
            session, snapshot_model, entity_model, self.version_manager,
            identifier_enum_class, change_reason_enum_class
        )

    # ==========================================
    # HIGH-LEVEL CONVENIENCE METHODS
    # ==========================================

    def get_current_identifier(self, entity_id: int, identifier_type: TIdentifierType) -> Optional[str]:
        """Get current active identifier value"""
        return self.operations_manager.get_current_identifier(entity_id, identifier_type)

    def get_all_current_identifiers(self, entity_id: int) -> Dict[str, str]:
        """Get all current active identifiers"""
        return self.operations_manager.get_all_current_identifiers(entity_id)

    def find_entity_by_identifier(self, identifier_type: TIdentifierType, value: str):
        """Find entity by identifier value"""
        return self.operations_manager.find_entity_by_identifier(identifier_type, value)

    def get_identifier_history(self, entity_id: int, identifier_type: TIdentifierType) -> List:
        """Get full identifier history"""
        return self.version_manager.get_identifier_history(entity_id, identifier_type)

    def get_identifier_at_date(self, entity_id: int, identifier_type: TIdentifierType,
                               as_of_date: datetime) -> Optional[str]:
        """Get identifier value as of specific date"""
        return self.version_manager.get_identifier_at_date(entity_id, identifier_type, as_of_date)

    def request_identifier_change(self, entity_id: int, identifier_type: TIdentifierType,
                                  new_value: str, reason, requested_by: str,
                                  description: str = None, **kwargs):
        """Submit identifier change request"""
        return self.workflow_manager.create_change_request(
            entity_id, identifier_type, new_value, reason, requested_by, description, **kwargs
        )

    def approve_identifier_change(self, change_request_id: uuid.UUID, approved_by: str):
        """Approve and apply identifier change"""
        new_record = self.workflow_manager.approve_change_request(change_request_id, approved_by)
        # Rebuild snapshot after approval
        self.operations_manager.rebuild_identifier_snapshot(new_record.get_entity_id())
        return new_record

    def reject_identifier_change(self, change_request_id: uuid.UUID, rejected_by: str,
                                 rejection_reason: str = None):
        """Reject identifier change request"""
        return self.workflow_manager.reject_change_request(
            change_request_id, rejected_by, rejection_reason
        )

    def rollback_identifier(self, entity_id: int, identifier_type: TIdentifierType,
                            target_version: int, reason: str, performed_by: str) -> bool:
        """Rollback identifier to specific version"""
        success = self.version_manager.rollback_to_version(
            entity_id, identifier_type, target_version, reason, performed_by
        )
        if success:
            self.operations_manager.rebuild_identifier_snapshot(entity_id)
        return success

    def bulk_add_identifiers(self, entity_id: int, identifiers: Dict[TIdentifierType, str],
                             created_by: str, source: str = None, reason=None):
        """Add multiple identifiers in bulk"""
        return self.operations_manager.bulk_add_identifiers(
            entity_id, identifiers, created_by, source, reason
        )

    def get_pending_change_requests(self, entity_id: Optional[int] = None,
                                    identifier_type: Optional[TIdentifierType] = None) -> List:
        """Get pending change requests"""
        return self.workflow_manager.get_pending_requests(entity_id, identifier_type)

    def search_identifiers(self, search_term: str,
                           identifier_types: Optional[List[TIdentifierType]] = None) -> List[Dict[str, Any]]:
        """Search for identifiers"""
        return self.operations_manager.search_identifiers(search_term, identifier_types)

    def get_version_diff(self, entity_id: int, identifier_type: TIdentifierType,
                         version1: int, version2: int) -> Dict[str, Any]:
        """Compare two versions"""
        return self.version_manager.get_version_diff(entity_id, identifier_type, version1, version2)

    def get_version_timeline(self, entity_id: int, identifier_type: TIdentifierType) -> List[Dict[str, Any]]:
        """Get complete version timeline"""
        return self.version_manager.get_version_timeline(entity_id, identifier_type)

    def get_identifier_statistics(self) -> Dict[str, Any]:
        """Get system-wide identifier statistics"""
        return self.operations_manager.get_identifier_statistics()

    def validate_identifier_integrity(self, entity_id: Optional[int] = None) -> Dict[str, List[str]]:
        """Validate data integrity"""
        return self.operations_manager.validate_identifier_integrity(entity_id)

    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """Clean up orphaned data"""
        return self.operations_manager.cleanup_orphaned_data()

    def rebuild_all_snapshots(self):
        """Rebuild all snapshots"""
        return self.operations_manager.rebuild_all_snapshots()
