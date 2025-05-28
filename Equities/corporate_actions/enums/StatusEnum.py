from enum import Enum


class StatusEnum(str, Enum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    CLOSED = "CLOSED"
