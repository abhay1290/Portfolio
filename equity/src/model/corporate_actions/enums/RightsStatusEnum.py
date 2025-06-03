from enum import Enum


class RightsStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    EXERCISED = "EXERCISED"
