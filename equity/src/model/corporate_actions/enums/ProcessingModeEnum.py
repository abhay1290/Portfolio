from enum import Enum


class ProcessingModeEnum(str, Enum):
    """Processing modes for corporate actions"""
    AUTOMATIC = "AUTOMATIC"  # Fully automated processing
    SEMI_AUTOMATIC = "SEMI_AUTOMATIC"  # Requires some manual intervention
    MANUAL = "MANUAL"  # Fully manual processing required
    HOLD = "HOLD"  # Hold for manual review
