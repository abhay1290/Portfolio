from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

from Identifier_management.enums.base_change_reason_enum import BaseChangeReasonEnum
from Identifier_management.enums.base_identifier_status_enum import BaseIdentifierStatusEnum

# Generic types for flexibility
TIdentifierType = TypeVar('TIdentifierType', bound=Enum)
TSecurityEntity = TypeVar('TSecurityEntity')
TChangeReason = TypeVar('TChangeReason', bound=Enum)
TIdentifierStatus = TypeVar('TIdentifierStatus', bound=Enum)


class GenericVersionManager(Generic[TIdentifierType, TSecurityEntity, TChangeReason, TIdentifierStatus]):
    """Enhanced generic version manager with all equity functionality"""

    def __init__(self, session: Session, history_model, identifier_enum_class,
                 change_reason_enum_class=None, identifier_status_enum_class=None):
        self.session = session
        self.history_model = history_model
        self.identifier_enum_class = identifier_enum_class
        self.change_reason_enum_class = change_reason_enum_class or BaseChangeReasonEnum
        self.identifier_status_enum_class = identifier_status_enum_class or BaseIdentifierStatusEnum

    def get_identifier_history(self, entity_id: int, identifier_type: TIdentifierType) -> List:
        """Get full version history for an identifier type"""
        return self.session.query(self.history_model).filter(
            self.history_model.get_entity_id() == entity_id,
            self.history_model.identifier_type == identifier_type.value
        ).order_by(self.history_model.version.desc()).all()

    def get_identifier_at_date(self, entity_id: int, identifier_type: TIdentifierType,
                               as_of_date: datetime) -> Optional[str]:
        """Get identifier value as of specific date (point-in-time query)"""
        record = self.session.query(self.history_model).filter(
            self.history_model.get_entity_id() == entity_id,
            self.history_model.identifier_type == identifier_type.value,
            self.history_model.effective_from <= as_of_date,
            (self.history_model.effective_to.is_(None) |
             (self.history_model.effective_to > as_of_date)),
            self.history_model.status == BaseIdentifierStatusEnum.ACTIVE.value
        ).first()

        return record.identifier_value if record else None

    def get_current_version(self, entity_id: int, identifier_type: TIdentifierType):
        """Get the current active version of an identifier"""
        return self.session.query(self.history_model).filter(
            self.history_model.get_entity_id() == entity_id,
            self.history_model.identifier_type == identifier_type.value,
            self.history_model.effective_to.is_(None),
            self.history_model.status == BaseIdentifierStatusEnum.ACTIVE.value
        ).first()

    def get_version_by_number(self, entity_id: int, identifier_type: TIdentifierType,
                              version: int):
        """Get specific version of an identifier"""
        return self.session.query(self.history_model).filter(
            self.history_model.get_entity_id() == entity_id,
            self.history_model.identifier_type == identifier_type.value,
            self.history_model.version == version
        ).first()

    def get_version_diff(self, entity_id: int, identifier_type: TIdentifierType,
                         version1: int, version2: int) -> Dict[str, Any]:
        """Compare two versions of an identifier"""
        v1_record = self.get_version_by_number(entity_id, identifier_type, version1)
        v2_record = self.get_version_by_number(entity_id, identifier_type, version2)

        if not v1_record or not v2_record:
            return {}

        return {
            'version1': {
                'version': v1_record.version,
                'value': v1_record.identifier_value,
                'effective_from': v1_record.effective_from,
                'change_reason': v1_record.change_reason,
                'created_by': v1_record.created_by,
                'approved_by': v1_record.approved_by
            },
            'version2': {
                'version': v2_record.version,
                'value': v2_record.identifier_value,
                'effective_from': v2_record.effective_from,
                'change_reason': v2_record.change_reason,
                'created_by': v2_record.created_by,
                'approved_by': v2_record.approved_by
            },
            'differences': {
                'value_changed': v1_record.identifier_value != v2_record.identifier_value,
                'exchange_changed': getattr(v1_record, 'exchange_mic', None) != getattr(v2_record, 'exchange_mic',
                                                                                        None),
                'currency_changed': getattr(v1_record, 'currency', None) != getattr(v2_record, 'currency', None),
                'source_changed': getattr(v1_record, 'source', None) != getattr(v2_record, 'source', None),
                'time_diff': (
                        v2_record.effective_from - v1_record.effective_from).total_seconds() if v1_record.effective_from and v2_record.effective_from else None
            }
        }

    def rollback_to_version(self, entity_id: int, identifier_type: TIdentifierType,
                            target_version: int, rollback_reason: str, performed_by: str) -> bool:
        """Rollback identifier to a specific version"""

        target_record = self.get_version_by_number(entity_id, identifier_type, target_version)
        if not target_record:
            raise ValueError(f"Target version {target_version} not found")

        current_record = self.get_current_version(entity_id, identifier_type)

        # Close current active record if exists
        if current_record:
            current_record.effective_to = datetime.now()
            current_record.status = BaseIdentifierStatusEnum.SUPERSEDED.value

        # Create new record based on target version
        new_version = (current_record.version + 1) if current_record else 1

        rollback_kwargs = {
            self._get_entity_id_field(): entity_id,
            'identifier_type': target_record.identifier_type,
            'identifier_value': target_record.identifier_value,
            'version': new_version,
            'effective_from': datetime.now(),
            'change_reason': BaseChangeReasonEnum.DATA_CORRECTION.value,
            'change_description': f"Rollback to version {target_version}: {rollback_reason}",
            'supersedes_id': current_record.id if current_record else None,
            'created_by': performed_by,
            'approved_by': performed_by,
            'approved_at': datetime.now()
        }

        # Copy optional fields from target record
        optional_fields = ['exchange_mic', 'currency', 'source', 'confidence_level']
        for field in optional_fields:
            if hasattr(target_record, field):
                rollback_kwargs[field] = getattr(target_record, field)

        rollback_record = self.history_model(**rollback_kwargs)
        self.session.add(rollback_record)
        self.session.commit()
        return True

    def create_new_version(self, entity_id: int, identifier_type: TIdentifierType,
                           new_value: str, change_reason, change_description: str,
                           created_by: str, approved_by: str, **kwargs):
        """Create a new version of an identifier"""

        current_record = self.get_current_version(entity_id, identifier_type)

        # Close current record if exists
        if current_record:
            current_record.effective_to = datetime.now()
            current_record.status = BaseIdentifierStatusEnum.SUPERSEDED.value

        # Create new version
        new_version = (current_record.version + 1) if current_record else 1

        new_record_kwargs = {
            self._get_entity_id_field(): entity_id,
            'identifier_type': identifier_type.value,
            'identifier_value': new_value.strip().upper(),
            'version': new_version,
            'effective_from': datetime.now(),
            'change_reason': change_reason.value if hasattr(change_reason, 'value') else change_reason,
            'change_description': change_description,
            'supersedes_id': current_record.id if current_record else None,
            'created_by': created_by,
            'approved_by': approved_by,
            'approved_at': datetime.now(),
            **kwargs
        }

        new_record = self.history_model(**new_record_kwargs)
        self.session.add(new_record)
        return new_record

    def get_version_timeline(self, entity_id: int, identifier_type: TIdentifierType) -> List[Dict[str, Any]]:
        """Get complete timeline of identifier changes"""
        history = self.get_identifier_history(entity_id, identifier_type)

        timeline = []
        for record in history:
            timeline.append({
                'version': record.version,
                'value': record.identifier_value,
                'effective_from': record.effective_from,
                'effective_to': record.effective_to,
                'status': record.status,
                'change_reason': record.change_reason,
                'change_description': record.change_description,
                'created_by': record.created_by,
                'approved_by': record.approved_by,
                'duration_days': (
                        (record.effective_to or datetime.now()) - record.effective_from
                ).days if record.effective_from else None
            })

        return timeline

    def _get_entity_id_field(self) -> str:
        """Get the entity ID field name for this model"""
        for attr_name in dir(self.history_model):
            if attr_name.endswith('_id') and attr_name != 'id' and attr_name != 'supersedes_id':
                return attr_name
        raise ValueError("Could not determine entity ID field")
