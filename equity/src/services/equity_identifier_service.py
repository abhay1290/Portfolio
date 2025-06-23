# equity_service/services/equity_identifier_service.py
from typing import Dict, List, Optional

from Identifier_management.enums.identifier_type_enum import IdentifierTypeEnum
from Identifier_management.generic_identifier_service_factory import GenericIdentifierServiceFactory
from equity.src.database import get_db
from equity.src.model.enums.equity_change_reason_enum import EquityChangeReasonEnum
from equity.src.model.equity.Equity import Equity
from equity.src.model.equity.equity_identifier_change_request import EquityIdentifierChangeRequest
from equity.src.model.equity.equity_identifier_history import EquityIdentifierHistory
from equity.src.model.equity.equity_identifier_snapshot import EquityIdentifierSnapshot


class EquityIdentifierService:
    """Service for managing equity identifiers using the generic framework"""

    def __init__(self):
        self.session = get_db()

        # Create the generic identifier manager
        self.identifier_manager = GenericIdentifierServiceFactory.create_identifier_manager(
            session=self.session,
            history_model=EquityIdentifierHistory,
            snapshot_model=EquityIdentifierSnapshot,
            change_request_model=EquityIdentifierChangeRequest,
            entity_model=Equity,
            identifier_enum_class=IdentifierTypeEnum,
            change_reason_enum_class=EquityChangeReasonEnum
        )

    # ==========================================
    # EQUITY-SPECIFIC CONVENIENCE METHODS
    # ==========================================

    def get_current_ticker(self, equity_id: int) -> Optional[str]:
        """Get current ticker symbol for an equity"""
        return self.identifier_manager.get_current_identifier(equity_id, IdentifierTypeEnum.TICKER)

    def get_current_isin(self, equity_id: int) -> Optional[str]:
        """Get current ISIN for an equity"""
        return self.identifier_manager.get_current_identifier(equity_id, IdentifierTypeEnum.ISIN)

    def get_current_cusip(self, equity_id: int) -> Optional[str]:
        """Get current CUSIP for an equity"""
        return self.identifier_manager.get_current_identifier(equity_id, IdentifierTypeEnum.CUSIP)

    def find_equity_by_ticker(self, ticker: str) -> Optional[Equity]:
        """Find equity by ticker symbol"""
        return self.identifier_manager.find_entity_by_identifier(IdentifierTypeEnum.TICKER, ticker)

    def find_equity_by_isin(self, isin: str) -> Optional[Equity]:
        """Find equity by ISIN"""
        return self.identifier_manager.find_entity_by_identifier(IdentifierTypeEnum.ISIN, isin)

    def find_equity_by_cusip(self, cusip: str) -> Optional[Equity]:
        """Find equity by CUSIP"""
        return self.identifier_manager.find_entity_by_identifier(IdentifierTypeEnum.CUSIP, cusip)

    def request_ticker_change(self, equity_id: int, new_ticker: str, requested_by: str,
                              description: str = None):
        """Request a ticker symbol change"""
        return self.identifier_manager.request_identifier_change(
            entity_id=equity_id,
            identifier_type=IdentifierTypeEnum.TICKER,
            new_value=new_ticker,
            reason=EquityChangeReasonEnum.TICKER_CHANGE,
            requested_by=requested_by,
            description=description or f"Ticker change to {new_ticker}"
        )

    def bulk_add_equity_identifiers(self, equity_id: int, ticker: str = None, isin: str = None,
                                    cusip: str = None, sedol: str = None, created_by: str = "system",
                                    source: str = None):
        """Add multiple identifiers to an equity at once"""
        identifiers = {}

        if ticker:
            identifiers[IdentifierTypeEnum.TICKER] = ticker
        if isin:
            identifiers[IdentifierTypeEnum.ISIN] = isin
        if cusip:
            identifiers[IdentifierTypeEnum.CUSIP] = cusip
        if sedol:
            identifiers[IdentifierTypeEnum.SEDOL] = sedol

        if identifiers:
            return self.identifier_manager.bulk_add_identifiers(
                entity_id=equity_id,
                identifiers=identifiers,
                created_by=created_by,
                source=source,
                reason=EquityChangeReasonEnum.INITIAL_ASSIGNMENT
            )
        return None

    def get_all_current_identifiers(self, equity_id: int) -> Dict[str, str]:
        """Get all current identifiers for an equity"""
        return self.identifier_manager.get_all_current_identifiers(equity_id)

    def get_identifier_history(self, equity_id: int, identifier_type: IdentifierTypeEnum) -> List:
        """Get identifier history"""
        return self.identifier_manager.get_identifier_history(equity_id, identifier_type)

    def get_identifier_at_date(self, equity_id: int, identifier_type: IdentifierTypeEnum, as_of_date):
        """Get identifier as of specific date"""
        return self.identifier_manager.get_identifier_at_date(equity_id, identifier_type, as_of_date)

    def approve_change_request(self, change_request_id, approved_by: str):
        """Approve identifier change request"""
        return self.identifier_manager.approve_identifier_change(change_request_id, approved_by)

    def reject_change_request(self, change_request_id, rejected_by: str, reason: str = None):
        """Reject identifier change request"""
        return self.identifier_manager.reject_identifier_change(change_request_id, rejected_by, reason)

    def get_pending_change_requests(self, equity_id: int = None):
        """Get pending change requests"""
        return self.identifier_manager.get_pending_change_requests(equity_id)

    def rollback_identifier(self, equity_id: int, identifier_type: IdentifierTypeEnum,
                            target_version: int, reason: str, performed_by: str):
        """Rollback identifier to specific version"""
        return self.identifier_manager.rollback_identifier(
            equity_id, identifier_type, target_version, reason, performed_by
        )

    def search_identifiers(self, search_term: str, identifier_types: List[IdentifierTypeEnum] = None):
        """Search for identifiers"""
        return self.identifier_manager.search_identifiers(search_term, identifier_types)

    def get_version_diff(self, equity_id: int, identifier_type: IdentifierTypeEnum,
                         version1: int, version2: int):
        """Compare two versions"""
        return self.identifier_manager.get_version_diff(equity_id, identifier_type, version1, version2)

    def get_identifier_statistics(self):
        """Get system statistics"""
        return self.identifier_manager.get_identifier_statistics()

    def validate_identifier_integrity(self, equity_id: int = None):
        """Validate data integrity"""
        return self.identifier_manager.validate_identifier_integrity(equity_id)


# Factory function
def get_equity_identifier_service() -> EquityIdentifierService:
    """Factory function for dependency injection"""
    return EquityIdentifierService()
