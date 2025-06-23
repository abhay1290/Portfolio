from enum import Enum

from Identifier_management.enums.base_change_reason_enum import BaseChangeReasonEnum


class BondChangeReasonEnum(Enum):
    """Complete enum with base reasons + bond-specific reasons"""

    # Include all base reasons
    CORPORATE_ACTION = BaseChangeReasonEnum.CORPORATE_ACTION.value
    DATA_CORRECTION = BaseChangeReasonEnum.DATA_CORRECTION.value
    INITIAL_ASSIGNMENT = BaseChangeReasonEnum.INITIAL_ASSIGNMENT.value
    SYSTEM_MIGRATION = BaseChangeReasonEnum.SYSTEM_MIGRATION.value

    # Add bond-specific reasons
    RATING_CHANGE = "RATING_CHANGE"
    MATURITY_UPDATE = "MATURITY_UPDATE"
    ISSUER_CHANGE = "ISSUER_CHANGE"
    CALL_PROVISION = "CALL_PROVISION"
    DEFAULT_EVENT = "DEFAULT_EVENT"
    REFINANCING = "REFINANCING"
    COUPON_CHANGE = "COUPON_CHANGE"
