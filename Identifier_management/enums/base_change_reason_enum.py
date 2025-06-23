from enum import Enum


class BaseChangeReasonEnum(Enum):
    """Base change reasons - can be extended per service"""
    CORPORATE_ACTION = "CORPORATE_ACTION"
    DATA_CORRECTION = "DATA_CORRECTION"
    INITIAL_ASSIGNMENT = "INITIAL_ASSIGNMENT"
    SYSTEM_MIGRATION = "SYSTEM_MIGRATION"
