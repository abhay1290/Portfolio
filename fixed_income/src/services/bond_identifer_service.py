# fixed_income_service/services/bond_identifier_service.py
from typing import Dict, List, Optional

from Identifier_management.generic_identifier_service_factory import GenericIdentifierServiceFactory
from fixed_income.src.database import get_db
from fixed_income.src.model.bonds import BondBase
from fixed_income.src.model.bonds.bond_identifer_snapshot import BondIdentifierSnapshot
from fixed_income.src.model.bonds.bond_identifier_change_request import BondIdentifierChangeRequest
from fixed_income.src.model.bonds.bond_identifier_history import BondIdentifierHistory
from fixed_income.src.model.enums.bond_change_reason_enum import BondChangeReasonEnum
from fixed_income.src.model.enums.bond_identifier_type_enum import BondIdentifierTypeEnum


class BondIdentifierService:
    """Service for managing bond identifiers using the generic framework"""

    def __init__(self):
        self.session = get_db()

        # Create the generic identifier manager
        self.identifier_manager = GenericIdentifierServiceFactory.create_identifier_manager(
            session=self.session,
            history_model=BondIdentifierHistory,
            snapshot_model=BondIdentifierSnapshot,
            change_request_model=BondIdentifierChangeRequest,
            entity_model=BondBase,
            identifier_enum_class=BondIdentifierTypeEnum,
            change_reason_enum_class=BondChangeReasonEnum
        )

    # ==========================================
    # BOND-SPECIFIC CONVENIENCE METHODS
    # ==========================================

    def get_current_isin(self, bond_id: int) -> Optional[str]:
        """Get current ISIN for a bond"""
        return self.identifier_manager.get_current_identifier(bond_id, BondIdentifierTypeEnum.ISIN)

    def get_current_cusip(self, bond_id: int) -> Optional[str]:
        """Get current CUSIP for a bond"""
        return self.identifier_manager.get_current_identifier(bond_id, BondIdentifierTypeEnum.CUSIP)

    def get_current_rating(self, bond_id: int, agency: str = "MOODY") -> Optional[str]:
        """Get current rating for a bond from specific agency"""
        rating_type = getattr(BondIdentifierTypeEnum, f"RATING_{agency.upper()}", None)
        if rating_type:
            return self.identifier_manager.get_current_identifier(bond_id, rating_type)
        return None

    def find_bond_by_isin(self, isin: str) -> Optional[BondBase]:
        """Find bond by ISIN"""
        return self.identifier_manager.find_entity_by_identifier(BondIdentifierTypeEnum.ISIN, isin)

    def find_bond_by_cusip(self, cusip: str) -> Optional[BondBase]:
        """Find bond by CUSIP"""
        return self.identifier_manager.find_entity_by_identifier(BondIdentifierTypeEnum.CUSIP, cusip)

    def get_bonds_by_rating(self, agency: str, rating: str) -> List[BondBase]:
        """Find all bonds with specific rating"""
        rating_type = getattr(BondIdentifierTypeEnum, f"RATING_{agency.upper()}", None)
        if not rating_type:
            return []

        # Search in snapshots
        snapshots = self.session.query(BondIdentifierSnapshot).all()
        matching_bonds = []

        for snapshot in snapshots:
            if snapshot.identifiers and rating_type.value in snapshot.identifiers:
                if snapshot.identifiers[rating_type.value]['value'] == rating:
                    matching_bonds.append(snapshot.bond)

        return matching_bonds

    def request_rating_change(self, bond_id: int, agency: str, new_rating: str,
                              requested_by: str, rating_rationale: str = None):
        """Request a rating change for a bond"""
        rating_type = getattr(BondIdentifierTypeEnum, f"RATING_{agency.upper()}")

        change_request = self.identifier_manager.request_identifier_change(
            entity_id=bond_id,
            identifier_type=rating_type,
            new_value=new_rating,
            reason=BondChangeReasonEnum.RATING_CHANGE,
            requested_by=requested_by,
            description=f"{agency} rating change to {new_rating}. Rationale: {rating_rationale}",
            requires_rating_review=True  # Bond-specific field
        )

        return change_request

    def bulk_add_bond_identifiers(self, bond_id: int, isin: str = None, cusip: str = None,
                                  rating_moody: str = None, rating_sp: str = None,
                                  created_by: str = "system", source: str = None):
        """Add multiple identifiers to a bond at once"""
        identifiers = {}

        if isin:
            identifiers[BondIdentifierTypeEnum.ISIN] = isin
        if cusip:
            identifiers[BondIdentifierTypeEnum.CUSIP] = cusip
        if rating_moody:
            identifiers[BondIdentifierTypeEnum.RATING_MOODY] = rating_moody
        if rating_sp:
            identifiers[BondIdentifierTypeEnum.RATING_SP] = rating_sp

        if identifiers:
            return self.identifier_manager.bulk_add_identifiers(
                entity_id=bond_id,
                identifiers=identifiers,
                created_by=created_by,
                source=source,
                reason=BondChangeReasonEnum.INITIAL_ASSIGNMENT
            )
        return None

    def validate_rating_format(self, rating: str, agency: str) -> bool:
        """Validate rating format for specific agency"""
        agency = agency.upper()
        rating = rating.upper()

        if agency == "MOODY":
            valid_ratings = ['AAA', 'AA1', 'AA2', 'AA3', 'A1', 'A2', 'A3',
                             'BAA1', 'BAA2', 'BAA3', 'BA1', 'BA2', 'BA3',
                             'B1', 'B2', 'B3', 'CAA1', 'CAA2', 'CAA3', 'CA', 'C']
            return rating in valid_ratings

        elif agency in ["SP", "FITCH"]:
            valid_ratings = ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-',
                             'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-',
                             'B+', 'B', 'B-', 'CCC+', 'CCC', 'CCC-', 'CC', 'C', 'D']
            return rating in valid_ratings

        return True  # Unknown agency, assume valid

    # ==========================================
    # DELEGATE ALL OTHER METHODS TO GENERIC MANAGER
    # ==========================================

    def get_all_current_identifiers(self, bond_id: int) -> Dict[str, str]:
        """Get all current identifiers for a bond"""
        return self.identifier_manager.get_all_current_identifiers(bond_id)

    def get_identifier_history(self, bond_id: int, identifier_type: BondIdentifierTypeEnum) -> List:
        """Get identifier history"""
        return self.identifier_manager.get_identifier_history(bond_id, identifier_type)

    def approve_change_request(self, change_request_id, approved_by: str):
        """Approve identifier change request"""
        return self.identifier_manager.approve_identifier_change(change_request_id, approved_by)

    def reject_change_request(self, change_request_id, rejected_by: str, reason: str = None):
        """Reject identifier change request"""
        return self.identifier_manager.reject_identifier_change(change_request_id, rejected_by, reason)

    def get_pending_change_requests(self, bond_id: int = None):
        """Get pending change requests"""
        return self.identifier_manager.get_pending_change_requests(bond_id)

    def rollback_identifier(self, bond_id: int, identifier_type: BondIdentifierTypeEnum,
                            target_version: int, reason: str, performed_by: str):
        """Rollback identifier to specific version"""
        return self.identifier_manager.rollback_identifier(
            bond_id, identifier_type, target_version, reason, performed_by
        )

    def search_identifiers(self, search_term: str, identifier_types: List[BondIdentifierTypeEnum] = None):
        """Search for identifiers"""
        return self.identifier_manager.search_identifiers(search_term, identifier_types)

    def get_identifier_statistics(self):
        """Get system statistics"""
        return self.identifier_manager.get_identifier_statistics()


# Factory function
def get_bond_identifier_service() -> BondIdentifierService:
    """Factory function for dependency injection"""
    return BondIdentifierService()
