from enum import Enum


class PriorityEnum(str, Enum):
    """Priority levels for corporate action processing"""
    URGENT = "URGENT"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
