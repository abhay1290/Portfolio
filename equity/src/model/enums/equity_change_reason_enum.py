from enum import Enum

from Identifier_management.enums.base_change_reason_enum import BaseChangeReasonEnum


class EquityChangeReasonEnum(Enum):
    """Complete enum with base reasons + equity-specific reasons"""

    # Include all base reasons
    CORPORATE_ACTION = BaseChangeReasonEnum.CORPORATE_ACTION.value
    DATA_CORRECTION = BaseChangeReasonEnum.DATA_CORRECTION.value
    INITIAL_ASSIGNMENT = BaseChangeReasonEnum.INITIAL_ASSIGNMENT.value
    SYSTEM_MIGRATION = BaseChangeReasonEnum.SYSTEM_MIGRATION.value

    # Add equity-specific reasons
    TICKER_CHANGE = "TICKER_CHANGE"
    EXCHANGE_MIGRATION = "EXCHANGE_MIGRATION"
    MERGER_ACQUISITION = "MERGER_ACQUISITION"
    SPIN_OFF = "SPIN_OFF"
    DELISTING = "DELISTING"
