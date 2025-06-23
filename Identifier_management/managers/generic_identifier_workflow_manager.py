import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

from Identifier_management.enums.base_change_reason_enum import BaseChangeReasonEnum
from Identifier_management.managers.generic_identifier_version_manager import GenericVersionManager

# Generic types for flexibility
TIdentifierType = TypeVar('TIdentifierType', bound=Enum)
TSecurityEntity = TypeVar('TSecurityEntity')
TChangeReason = TypeVar('TChangeReason', bound=Enum)
TIdentifierStatus = TypeVar('TIdentifierStatus', bound=Enum)


class GenericWorkflowManager(Generic[TIdentifierType, TSecurityEntity, TChangeReason]):
    """Enhanced generic workflow manager with all equity functionality"""

    def __init__(self, session: Session, change_request_model, version_manager: GenericVersionManager,
                 identifier_enum_class, change_reason_enum_class=None):
        self.session = session
        self.change_request_model = change_request_model
        self.version_manager = version_manager
        self.identifier_enum_class = identifier_enum_class
        self.change_reason_enum_class = change_reason_enum_class or BaseChangeReasonEnum

    def create_change_request(self, entity_id: int, identifier_type: TIdentifierType,
                              new_value: str, reason, requested_by: str,
                              description: str = None, exchange_mic: str = None,
                              currency: str = None, **kwargs):
        """Create a new identifier change request"""

        # Get current value for comparison
        current_record = self.version_manager.get_current_version(entity_id, identifier_type)
        current_value = current_record.identifier_value if current_record else None

        # Validate new value format
        validation_result = self._validate_identifier_format(identifier_type, new_value)
        if not validation_result['is_valid']:
            raise ValueError(f"Invalid identifier format: {validation_result['validation_errors']}")

        # Create change request
        change_request_kwargs = {
            self._get_entity_id_field(): entity_id,
            'identifier_type': identifier_type.value,
            'old_value': current_value,
            'new_value': validation_result['normalized_value'],
            'change_reason': reason.value if hasattr(reason, 'value') else reason,
            'change_description': description,
            'requested_by': requested_by,
            **kwargs
        }

        change_request = self.change_request_model(**change_request_kwargs)

        # Perform impact analysis
        impact_analysis = self._get_change_impact_analysis(entity_id, identifier_type, new_value)
        change_request.risk_level = impact_analysis['risk_level']
        change_request.impact_assessment = str(impact_analysis)

        self.session.add(change_request)
        self.session.commit()
        return change_request

    def approve_change_request(self, change_request_id: uuid.UUID, approved_by: str):
        """Approve and apply identifier change request"""

        change_request = self._get_change_request(change_request_id)
        if change_request.status != "PENDING":
            raise ValueError(f"Change request is not pending. Current status: {change_request.status}")

        # Create new version through version manager
        identifier_type = self.identifier_enum_class(change_request.identifier_type)
        change_reason = None

        # Try to convert change reason to enum
        if self.change_reason_enum_class:
            try:
                change_reason = self.change_reason_enum_class(change_request.change_reason)
            except ValueError:
                change_reason = change_request.change_reason
        else:
            change_reason = change_request.change_reason

        new_record = self.version_manager.create_new_version(
            entity_id=change_request.get_entity_id(),
            identifier_type=identifier_type,
            new_value=change_request.new_value,
            change_reason=change_reason,
            change_description=change_request.change_description,
            created_by=change_request.requested_by,
            approved_by=approved_by
        )

        # Update change request status
        change_request.status = "APPLIED"
        change_request.reviewed_by = approved_by
        change_request.reviewed_at = datetime.now()
        change_request.applied_at = datetime.now()

        self.session.commit()
        return new_record

    def reject_change_request(self, change_request_id: uuid.UUID,
                              rejected_by: str, rejection_reason: str = None):
        """Reject identifier change request"""

        change_request = self._get_change_request(change_request_id)
        if change_request.status != "PENDING":
            raise ValueError(f"Change request is not pending. Current status: {change_request.status}")

        change_request.status = "REJECTED"
        change_request.reviewed_by = rejected_by
        change_request.reviewed_at = datetime.now()

        if rejection_reason:
            original_desc = change_request.change_description or ""
            change_request.change_description = f"{original_desc}\nREJECTION REASON: {rejection_reason}"

        self.session.commit()

    def get_pending_requests(self, entity_id: Optional[int] = None,
                             identifier_type: Optional[TIdentifierType] = None) -> List:
        """Get pending change requests with optional filters"""

        query = self.session.query(self.change_request_model).filter(
            self.change_request_model.status == "PENDING"
        )

        if entity_id:
            entity_id_field = self._get_entity_id_field()
            query = query.filter(getattr(self.change_request_model, entity_id_field) == entity_id)

        if identifier_type:
            query = query.filter(self.change_request_model.identifier_type == identifier_type.value)

        return query.order_by(self.change_request_model.requested_at).all()

    def get_request_history(self, entity_id: int,
                            identifier_type: Optional[TIdentifierType] = None) -> List:
        """Get all change requests for an entity"""

        entity_id_field = self._get_entity_id_field()
        query = self.session.query(self.change_request_model).filter(
            getattr(self.change_request_model, entity_id_field) == entity_id
        )

        if identifier_type:
            query = query.filter(self.change_request_model.identifier_type == identifier_type.value)

        return query.order_by(self.change_request_model.requested_at.desc()).all()

    def bulk_approve_requests(self, change_request_ids: List[uuid.UUID],
                              approved_by: str) -> List:
        """Approve multiple change requests in batch"""

        results = []
        for request_id in change_request_ids:
            try:
                new_record = self.approve_change_request(request_id, approved_by)
                results.append(new_record)
            except ValueError as e:
                # Log error and continue with other requests
                print(f"Failed to approve request {request_id}: {e}")
                continue

        return results

    def _get_change_request(self, change_request_id: uuid.UUID):
        """Get change request by ID with validation"""
        change_request = self.session.query(self.change_request_model).filter(
            self.change_request_model.id == change_request_id
        ).first()

        if not change_request:
            raise ValueError(f"Change request {change_request_id} not found")

        return change_request

    def _get_entity_id_field(self) -> str:
        """Get the entity ID field name"""
        for attr_name in dir(self.change_request_model):
            if attr_name.endswith('_id') and attr_name != 'id':
                return attr_name
        raise ValueError("Could not determine entity ID field")

    def _validate_identifier_format(self, identifier_type: TIdentifierType, value: str) -> Dict[str, Any]:
        """Basic validation - can be overridden per service"""
        value = value.strip().upper()

        # Common validators that can be used across services
        common_validators = {
            'ISIN': lambda v: len(v) == 12 and v[:2].isalpha() and v[2:11].isalnum() and v[11].isdigit(),
            'CUSIP': lambda v: len(v) == 9 and v[:8].isalnum() and v[8].isdigit(),
            'SEDOL': lambda v: len(v) == 7 and v[:6].isalnum() and v[6].isdigit(),
            'LEI': lambda v: len(v) == 20 and v.isalnum(),
            'WKN': lambda v: len(v) == 6 and v.isalnum()
        }

        validator = common_validators.get(identifier_type.value, lambda v: True)
        is_valid = validator(value)

        return {
            'is_valid': is_valid,
            'normalized_value': value,
            'validation_errors': [] if is_valid else [f"Invalid {identifier_type.value} format"]
        }

    def _get_change_impact_analysis(self, entity_id: int, identifier_type: TIdentifierType,
                                    new_value: str) -> Dict[str, Any]:
        """Analyze impact of proposed identifier change"""

        current_record = self.version_manager.get_current_version(entity_id, identifier_type)
        current_value = current_record.identifier_value if current_record else None

        validation_result = self._validate_identifier_format(identifier_type, new_value)

        # Basic risk assessment
        risk_level = "LOW"
        if not validation_result['is_valid']:
            risk_level = "HIGH"
        elif identifier_type.value in ['TICKER', 'ISIN']:
            risk_level = "MEDIUM"

        return {
            'current_value': current_value,
            'proposed_value': new_value,
            'validation': validation_result,
            'risk_level': risk_level,
            'requires_manual_review': risk_level in ["MEDIUM", "HIGH"],
            'affected_systems': ['trading_system', 'risk_management', 'reporting'],
            'estimated_downtime': '5 minutes' if risk_level == "MEDIUM" else '0 minutes'
        }
