from enum import Enum


class VersionOperationTypeEnum(str, Enum):
    """Types of operations that trigger versioning"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    REBALANCE = "REBALANCE"
    ADD_CONSTITUENT = "ADD_CONSTITUENT"
    REMOVE_CONSTITUENT = "REMOVE_CONSTITUENT"
    ROLLBACK = "ROLLBACK"
    MANUAL_EDIT = "MANUAL_EDIT"
