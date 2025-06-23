from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

from Identifier_management.enums.base_change_reason_enum import BaseChangeReasonEnum
from Identifier_management.enums.base_identifier_status_enum import BaseIdentifierStatusEnum
from Identifier_management.managers.generic_identifier_version_manager import GenericVersionManager

# Generic types for flexibility
TIdentifierType = TypeVar('TIdentifierType', bound=Enum)
TSecurityEntity = TypeVar('TSecurityEntity')
TChangeReason = TypeVar('TChangeReason', bound=Enum)
TIdentifierStatus = TypeVar('TIdentifierStatus', bound=Enum)


class GenericOperationsManager(Generic[TIdentifierType, TSecurityEntity]):
    """Enhanced generic operations manager with all equity functionality"""

    def __init__(self, session: Session, snapshot_model, entity_model, version_manager: GenericVersionManager,
                 identifier_enum_class, change_reason_enum_class=None):
        self.session = session
        self.snapshot_model = snapshot_model
        self.entity_model = entity_model
        self.version_manager = version_manager
        self.identifier_enum_class = identifier_enum_class
        self.change_reason_enum_class = change_reason_enum_class or BaseChangeReasonEnum

    def get_current_identifier(self, entity_id: int, identifier_type: TIdentifierType) -> Optional[str]:
        """Get current active identifier value for an entity"""
        entity_id_field = self._get_entity_id_field()
        snapshot = self.session.query(self.snapshot_model).filter(
            getattr(self.snapshot_model, entity_id_field) == entity_id
        ).first()

        if snapshot and snapshot.identifiers:
            id_data = snapshot.identifiers.get(identifier_type.value)
            return id_data['value'] if id_data else None
        return None

    def get_all_current_identifiers(self, entity_id: int) -> Dict[str, str]:
        """Get all current active identifiers for an entity"""
        entity_id_field = self._get_entity_id_field()
        snapshot = self.session.query(self.snapshot_model).filter(
            getattr(self.snapshot_model, entity_id_field) == entity_id
        ).first()

        if snapshot and snapshot.identifiers:
            return {k: v['value'] for k, v in snapshot.identifiers.items()}
        return {}

    def find_entity_by_identifier(self, identifier_type: TIdentifierType, value: str):
        """Find entity by any identifier value"""
        normalized_value = value.strip().upper()

        # Search in current snapshot first (faster)
        try:
            snapshot = self.session.query(self.snapshot_model).filter(
                self.snapshot_model.identifiers[identifier_type.value]['value'].astext == normalized_value
            ).first()

            if snapshot:
                entity_id_field = self._get_entity_id_field()
                entity_id = getattr(snapshot, entity_id_field)
                return self.session.query(self.entity_model).filter(
                    self.entity_model.id == entity_id
                ).first()
        except Exception:
            # JSONB query might fail, fallback to historical search
            pass

        # Fallback to historical search
        history_record = self.session.query(self.version_manager.history_model).filter(
            self.version_manager.history_model.identifier_type == identifier_type.value,
            self.version_manager.history_model.identifier_value == normalized_value,
            self.version_manager.history_model.effective_to.is_(None),
            self.version_manager.history_model.status == BaseIdentifierStatusEnum.ACTIVE.value
        ).first()

        if history_record:
            entity_id = history_record.get_entity_id()
            return self.session.query(self.entity_model).filter(
                self.entity_model.id == entity_id
            ).first()

        return None

    def search_identifiers(self, search_term: str,
                           identifier_types: Optional[List[TIdentifierType]] = None) -> List[Dict[str, Any]]:
        """Search for identifiers matching a term across multiple types"""
        search_term = search_term.strip().upper()
        results = []

        # Search in snapshots for current identifiers
        snapshots = self.session.query(self.snapshot_model).all()

        for snapshot in snapshots:
            if not snapshot.identifiers:
                continue

            entity_id_field = self._get_entity_id_field()
            entity_id = getattr(snapshot, entity_id_field)

            for id_type, id_data in snapshot.identifiers.items():
                # Filter by identifier types if specified
                if identifier_types:
                    try:
                        enum_type = self.identifier_enum_class(id_type)
                        if enum_type not in identifier_types:
                            continue
                    except ValueError:
                        continue

                if search_term in id_data['value'].upper():
                    results.append({
                        'entity_id': entity_id,
                        'identifier_type': id_type,
                        'identifier_value': id_data['value'],
                        'version': id_data.get('version'),
                        'source': id_data.get('source'),
                        'confidence_level': id_data.get('confidence_level')
                    })

        return results

    def bulk_add_identifiers(self, entity_id: int, identifiers: Dict[TIdentifierType, str],
                             created_by: str, source: str = None,
                             reason=None):
        """Add multiple identifiers to an entity in a single transaction"""

        if reason is None:
            reason = BaseChangeReasonEnum.INITIAL_ASSIGNMENT

        for identifier_type, value in identifiers.items():
            if not value:
                continue

            # Check if identifier already exists
            existing = self.version_manager.get_current_version(entity_id, identifier_type)
            if existing:
                continue  # Skip if already exists

            # Create new identifier record through version manager
            self.version_manager.create_new_version(
                entity_id=entity_id,
                identifier_type=identifier_type,
                new_value=value,
                change_reason=reason,
                change_description=f"Initial assignment of {identifier_type.value}",
                created_by=created_by,
                approved_by=created_by,
                source=source
            )

        # Rebuild snapshot after adding all identifiers
        self.rebuild_identifier_snapshot(entity_id)
        self.session.commit()

    def rebuild_identifier_snapshot(self, entity_id: int):
        """Rebuild snapshot from historical records for a specific entity"""
        entity_id_field = self._get_entity_id_field()
        snapshot = self.session.query(self.snapshot_model).filter(
            getattr(self.snapshot_model, entity_id_field) == entity_id
        ).first()

        if not snapshot:
            snapshot_kwargs = {entity_id_field: entity_id}
            snapshot = self.snapshot_model(**snapshot_kwargs)
            self.session.add(snapshot)

        # Get all current active identifiers
        current_identifiers = self.session.query(self.version_manager.history_model).filter(
            self.version_manager.history_model.get_entity_id() == entity_id,
            self.version_manager.history_model.effective_to.is_(None),
            self.version_manager.history_model.status == BaseIdentifierStatusEnum.ACTIVE.value
        ).all()

        snapshot.identifiers = {
            record.identifier_type: {
                'value': record.identifier_value,
                'version': record.version,
                'effective_from': record.effective_from.isoformat(),
                'source': getattr(record, 'source', None),
                'exchange_mic': getattr(record, 'exchange_mic', None),
                'currency': getattr(record, 'currency', None),
                'confidence_level': getattr(record, 'confidence_level', None)
            } for record in current_identifiers
        }

        # Set primary identifier (business logic can be customized)
        primary = next((r for r in current_identifiers if r.identifier_type == 'TICKER'), None)
        if not primary:
            primary = next((r for r in current_identifiers if r.identifier_type == 'ISIN'), None)

        if primary:
            snapshot.primary_identifier_type = primary.identifier_type
            snapshot.primary_identifier_value = primary.identifier_value

        snapshot.snapshot_version = getattr(snapshot, 'snapshot_version', 0) + 1
        snapshot.last_updated = datetime.now()

        # Update entity primary symbol cache if applicable
        if hasattr(self.entity_model, 'primary_symbol'):
            entity = self.session.query(self.entity_model).get(entity_id)
            if entity and snapshot.primary_identifier_value:
                entity.primary_symbol = snapshot.primary_identifier_value

    def rebuild_all_snapshots(self):
        """Rebuild all identifier snapshots - useful for maintenance"""
        entity_ids = self.session.query(self.entity_model.id).all()

        for (entity_id,) in entity_ids:
            self.rebuild_identifier_snapshot(entity_id)

        self.session.commit()

    def get_identifier_statistics(self) -> Dict[str, Any]:
        """Get statistics about identifier usage across the system"""
        stats = {}

        # Count identifiers by type
        for id_type in self.identifier_enum_class:
            count = self.session.query(self.version_manager.history_model).filter(
                self.version_manager.history_model.identifier_type == id_type.value,
                self.version_manager.history_model.effective_to.is_(None),
                self.version_manager.history_model.status == BaseIdentifierStatusEnum.ACTIVE.value
            ).count()
            stats[id_type.value] = count

        # Get total entities with identifiers
        total_entities = self.session.query(self.snapshot_model).count()
        stats['total_entities_with_identifiers'] = total_entities

        # Get average identifiers per entity
        if total_entities > 0:
            snapshots = self.session.query(self.snapshot_model).all()
            total_identifiers = sum(len(s.identifiers or {}) for s in snapshots)
            stats['average_identifiers_per_entity'] = total_identifiers / total_entities
        else:
            stats['average_identifiers_per_entity'] = 0

        return stats

    def validate_identifier_integrity(self, entity_id: Optional[int] = None) -> Dict[str, List[str]]:
        """Validate identifier data integrity"""
        issues = {
            'missing_snapshots': [],
            'orphaned_snapshots': [],
            'inconsistent_data': [],
            'format_violations': []
        }

        # Check for missing snapshots
        if entity_id:
            entity_ids = [entity_id]
        else:
            entity_ids = [id_element[0] for id_element in self.session.query(self.entity_model.id).all()]

        entity_id_field = self._get_entity_id_field()

        for ent_id in entity_ids:
            # Check if entity has history but no snapshot
            has_history = self.session.query(self.version_manager.history_model).filter(
                self.version_manager.history_model.get_entity_id() == ent_id,
                self.version_manager.history_model.effective_to.is_(None)
            ).first()

            has_snapshot = self.session.query(self.snapshot_model).filter(
                getattr(self.snapshot_model, entity_id_field) == ent_id
            ).first()

            if has_history and not has_snapshot:
                issues['missing_snapshots'].append(f"Entity {ent_id} has history but no snapshot")
            elif has_snapshot and not has_history:
                issues['orphaned_snapshots'].append(f"Entity {ent_id} has snapshot but no history")

        return issues

    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """Clean up orphaned data (snapshots without history, etc.)"""
        cleanup_stats = {
            'orphaned_snapshots_removed': 0,
            'inconsistent_snapshots_fixed': 0
        }

        # Find snapshots without corresponding active history
        snapshots = self.session.query(self.snapshot_model).all()
        entity_id_field = self._get_entity_id_field()

        for snapshot in snapshots:
            entity_id = getattr(snapshot, entity_id_field)
            has_active_history = self.session.query(self.version_manager.history_model).filter(
                self.version_manager.history_model.get_entity_id() == entity_id,
                self.version_manager.history_model.effective_to.is_(None),
                self.version_manager.history_model.status == BaseIdentifierStatusEnum.ACTIVE.value
            ).first()

            if not has_active_history:
                self.session.delete(snapshot)
                cleanup_stats['orphaned_snapshots_removed'] += 1

        self.session.commit()
        return cleanup_stats

    def _get_entity_id_field(self) -> str:
        """Get the entity ID field name"""
        for attr_name in dir(self.snapshot_model):
            if attr_name.endswith('_id') and attr_name != 'id':
                return attr_name
        raise ValueError("Could not determine entity ID field")
