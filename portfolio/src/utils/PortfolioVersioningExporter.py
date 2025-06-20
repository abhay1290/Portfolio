import csv
import os
from datetime import datetime
from typing import List

from fastapi import Depends
from sqlalchemy.orm import Session

from portfolio.src.database import get_db
from portfolio.src.model.PortfolioVersion import PortfolioVersion
from portfolio.src.services.PortfolioVersioningManager import PortfolioVersioningManager


class PortfolioVersioningExporter:
    """Handles exporting portfolio versions to CSV files"""

    def __init__(self,
                 export_directory: str,
                 db: Session = Depends(get_db)):
        self.db = db
        self.versioning_manager = PortfolioVersioningManager(db)
        self.export_directory = export_directory
        os.makedirs(export_directory, exist_ok=True)

    def export_portfolio_states_to_csv(self, portfolio_id: int,
                                       start_date: datetime = None,
                                       end_date: datetime = None) -> str:
        """Export portfolio version states to CSV file"""

        versions = self.db.query(PortfolioVersion) \
            .filter(portfolio_id == PortfolioVersion.portfolio_id)

        if start_date:
            versions = versions.filter(PortfolioVersion.created_at >= start_date)
        if end_date:
            versions = versions.filter(PortfolioVersion.created_at <= end_date)

        versions = versions.order_by(PortfolioVersion.version_id).all()

        if not versions:
            return ""

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_{portfolio_id}_versions_{timestamp}.csv"
        filepath = os.path.join(self.export_directory, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            header = ['version_number', 'created_at', 'operation_type', 'change_reason',
                      'approved_by', 'state_hash']

            # Add portfolio fields
            if versions:
                portfolio_fields = list(versions[0].portfolio_state.keys())
                header.extend([f'portfolio_{field}' for field in portfolio_fields])

            writer.writerow(header)

            # Write data
            for version in versions:
                row = [
                    version.version_id,
                    version.created_at.isoformat(),
                    version.operation_type,
                    version.change_reason or '',
                    version.approved_by or '',
                    version.state_hash
                ]

                # Add portfolio field values
                for field in portfolio_fields:
                    row.append(version.portfolio_state.get(field, ''))

                writer.writerow(row)

        # Also export constituents data
        self._export_constituents_csv(portfolio_id, versions, timestamp)

        return filepath

    def _export_constituents_csv(self, portfolio_id: int, versions: List[PortfolioVersion],
                                 timestamp: str):
        """Export constituents data for all versions"""

        filename = f"portfolio_{portfolio_id}_constituents_{timestamp}.csv"
        filepath = os.path.join(self.export_directory, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            header = ['version_number', 'created_at', 'constituent_id', 'asset_id',
                      'asset_class', 'currency', 'weight', 'target_weight', 'units',
                      'market_price', 'is_active']
            writer.writerow(header)

            # Write data
            for version in versions:
                for constituent in version.constituents_state:
                    row = [
                        version.version_id,
                        version.created_at.isoformat(),
                        constituent.get('id', ''),
                        constituent.get('asset_id', ''),
                        constituent.get('asset_class', ''),
                        constituent.get('currency', ''),
                        constituent.get('weight', ''),
                        constituent.get('target_weight', ''),
                        constituent.get('units', ''),
                        constituent.get('market_price', ''),
                        constituent.get('is_active', '')
                    ]
                    writer.writerow(row)

    def schedule_monthly_export(self, portfolio_id: int):
        """Schedule monthly export (placeholder for actual scheduler integration)"""
        # This would integrate with your Celery task system
        # For now, it's just a method signature
        pass
