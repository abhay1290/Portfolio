import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from portfolio.src.model import Constituent, Portfolio
from portfolio.src.model.PortfolioVersion import PortfolioStateSnapshot, PortfolioVersion
from portfolio.src.model.enums.VersionOperationEnum import VersionOperationTypeEnum


class PortfolioVersioningManager:
    """Manages all versioning operations for portfolios"""

    def __init__(self, db: Session):
        self.db = db

    def create_version(
            self,
            portfolio: Portfolio,
            operation_type: VersionOperationTypeEnum,
            created_by: str,
            change_reason: str = None,
            approved_by: str = None
    ) -> PortfolioVersion:
        """
        Creates a new version snapshot of the portfolio
        """
        # Create state snapshot
        snapshot = self._create_snapshot(portfolio)

        # Get next version number - Fix the query filter
        latest_version = (
            self.db.query(PortfolioVersion)
            .filter(PortfolioVersion.portfolio_id == portfolio.id)  # Fixed this line
            .order_by(PortfolioVersion.version_id.desc())
            .first()
        )
        next_version = (latest_version.version_id + 1) if latest_version else 1

        # Create version record
        version = PortfolioVersion(
            portfolio_id=portfolio.id,
            version_id=next_version,
            portfolio_state=snapshot.portfolio_data,
            constituents_state=snapshot.constituents_data,
            operation_type=operation_type,
            change_reason=change_reason,
            approved_by=approved_by,
            created_by=created_by,
            state_hash=snapshot.state_hash,  # Use snapshot's state hash
            previous_version_id=latest_version.id if latest_version else None
        )

        self.db.add(version)
        self.db.flush()

        return version

    def get_version(self, portfolio_id: int, version_id: int) -> Optional[PortfolioVersion]:
        """
        Retrieves a specific version of a portfolio
        """
        return (
            self.db.query(PortfolioVersion)
            .filter(
                PortfolioVersion.portfolio_id == portfolio_id,
                PortfolioVersion.version_id == version_id
            )
            .first()
        )

    def get_latest_version(self, portfolio_id: int) -> Optional[PortfolioVersion]:
        """
        Gets the latest version of a portfolio
        """
        return (
            self.db.query(PortfolioVersion)
            .filter(PortfolioVersion.portfolio_id == portfolio_id)
            .order_by(PortfolioVersion.version_id.desc())
            .first()
        )

    def get_version_history(self, portfolio_id: int) -> List[PortfolioVersion]:
        """
        Gets the complete version history for a portfolio
        """
        return (
            self.db.query(PortfolioVersion)
            .filter(PortfolioVersion.portfolio_id == portfolio_id)
            .order_by(PortfolioVersion.version_id.desc())
            .all()
        )

    def _create_snapshot(self, portfolio: Portfolio) -> PortfolioStateSnapshot:
        """
        Creates a complete snapshot of the portfolio state
        """
        import hashlib

        # Serialize portfolio data
        portfolio_data = {}
        for column in portfolio.__table__.columns:
            if column.name not in ['version_hash', 'updated_at']:  # Exclude volatile fields
                value = getattr(portfolio, column.name)
                portfolio_data[column.name] = self._serialize_value(value)

        # Serialize constituents
        constituents_data = []
        for constituent in portfolio.constituents:
            constituent_data = {}
            for column in constituent.__table__.columns:
                if column.name not in ['updated_at']:  # Exclude volatile fields
                    value = getattr(constituent, column.name)
                    constituent_data[column.name] = self._serialize_value(value)
            constituents_data.append(constituent_data)

        # Generate state hash
        state_dict = {
            'portfolio': portfolio_data,
            'constituents': constituents_data
        }
        state_str = json.dumps(state_dict, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()

        return PortfolioStateSnapshot(
            portfolio_data=portfolio_data,
            constituents_data=constituents_data,
            timestamp=datetime.now(),
            version_id=portfolio.current_version_id,
            state_hash=state_hash
        )

    def rollback_to_version(
            self,
            portfolio: Portfolio,
            target_version_id: int,
            rolled_back_by: str,
            change_reason: str = None
    ) -> Portfolio:
        """
        Rolls back a portfolio to a previous version
        """
        target_version = self.get_version(portfolio.id, target_version_id)
        if not target_version:
            raise ValueError(f"Version {target_version_id} not found")

        # Apply the target version state
        self._apply_version(portfolio, target_version)

        # Create a new version for the rollback
        rollback_version = self.create_version(
            portfolio=portfolio,
            operation_type=VersionOperationTypeEnum.ROLLBACK,
            change_reason=change_reason or f"Rollback to version {target_version_id}",
            created_by=rolled_back_by
        )

        # Update portfolio references
        portfolio.current_version_id = rollback_version.id
        portfolio.version = rollback_version.version_id
        portfolio.version_hash = rollback_version.state_hash
        portfolio.updated_at = datetime.now()

        return portfolio

    def _apply_version(self, portfolio: Portfolio, version: PortfolioVersion):
        """
        Applies a version's state to the portfolio
        """
        # Update portfolio fields
        for field, value in version.portfolio_state.items():
            if hasattr(portfolio, field) and field not in ['id', 'created_at']:
                setattr(portfolio, field, self._deserialize_value(field, value, portfolio))

        # Handle constituents - delete all and recreate
        # Remove existing constituents
        self.db.query(Constituent).filter(
            Constituent.portfolio_id == portfolio.id
        ).delete()

        # Recreate constituents from version
        for constituent_data in version.constituents_state:
            constituent_dict = {
                k: self._deserialize_value(k, v, Constituent())
                for k, v in constituent_data.items()
                if k not in ['id', 'created_at', 'updated_at']  # Don't try to set these fields
            }
            constituent_dict['portfolio_id'] = portfolio.id

            constituent = Constituent(**constituent_dict)
            self.db.add(constituent)

    def compare_versions(
            self,
            portfolio_id: int,
            version1_id: int,
            version2_id: int
    ) -> Dict[str, Any]:
        """
        Compares two versions of a portfolio
        """
        v1 = self.get_version(portfolio_id, version1_id)
        v2 = self.get_version(portfolio_id, version2_id)

        if not v1 or not v2:
            raise ValueError("One or both versions not found")

        diff = {
            'portfolio_changes': {},
            'constituents_changes': {
                'added': [],
                'removed': [],
                'modified': []
            }
        }

        # Compare portfolio fields
        for field in v1.portfolio_state.keys():
            if field in v2.portfolio_state:
                if v1.portfolio_state[field] != v2.portfolio_state[field]:
                    diff['portfolio_changes'][field] = {
                        'from': v1.portfolio_state[field],
                        'to': v2.portfolio_state[field]
                    }

        # Compare constituents
        constituents_v1 = {c['asset_id']: c for c in v1.constituents_state}
        constituents_v2 = {c['asset_id']: c for c in v2.constituents_state}

        all_asset_ids = set(constituents_v1.keys()).union(set(constituents_v2.keys()))

        for asset_id in all_asset_ids:
            if asset_id in constituents_v1 and asset_id not in constituents_v2:
                diff['constituents_changes']['removed'].append(constituents_v1[asset_id])
            elif asset_id not in constituents_v1 and asset_id in constituents_v2:
                diff['constituents_changes']['added'].append(constituents_v2[asset_id])
            else:
                # Compare constituent fields
                changes = {}
                for field in constituents_v1[asset_id].keys():
                    if field in constituents_v2[asset_id]:
                        if constituents_v1[asset_id][field] != constituents_v2[asset_id][field]:
                            changes[field] = {
                                'from': constituents_v1[asset_id][field],
                                'to': constituents_v2[asset_id][field]
                            }

                if changes:
                    diff['constituents_changes']['modified'].append({
                        'asset_id': asset_id,
                        'changes': changes
                    })

        return diff

    # Helper methods for serialization/deserialization
    @staticmethod
    def _serialize_value(value):
        """Serializes values for JSON storage"""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        elif hasattr(value, 'value'):  # Enum
            return value.value
        elif hasattr(value, '__dict__'):  # Complex objects
            return str(value)
        return value

    @staticmethod
    def _deserialize_value(field_name: str, value, model_instance):
        """Deserializes values from JSON to proper types"""
        if value is None:
            return None

        column = getattr(model_instance.__table__.columns, field_name, None)
        if not column:
            return value

        column_type = str(column.type)

        if 'DATETIME' in column_type.upper():
            return datetime.fromisoformat(value) if isinstance(value, str) else value
        elif 'DATE' in column_type.upper():
            return date.fromisoformat(value) if isinstance(value, str) else value
        elif 'ENUM' in column_type.upper():
            enum_class = column.type.enum_class
            return enum_class(value) if hasattr(enum_class, '__call__') else value
        elif 'NUMERIC' in column_type.upper() or 'DECIMAL' in column_type.upper():
            return Decimal(value) if value is not None else None
        return value
