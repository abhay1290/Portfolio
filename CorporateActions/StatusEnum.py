from enum import Enum

class StatusEnum(Enum):
    OPEN = "Recorded for execution"
    PENDING = "Pending for execution"
    CLOSED = "Adjusted and Closed"

